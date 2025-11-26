from importlib.resources import contents
import feedparser
import requests
from bs4 import BeautifulSoup
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
from datetime import datetime
from urllib.parse import quote_plus
import yfinance as yf
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np
from statistics import mean


finbert_model = AutoModelForSequenceClassification.from_pretrained("yiyanghkust/finbert-tone")
finbert_tokenizer = AutoTokenizer.from_pretrained("yiyanghkust/finbert-tone")

labels = ['Negative', 'Neutral', 'Positive']

def Get_news(ticker, num_articles=10):
    
    base_url = f"https://news.google.com/rss/search?q={quote_plus(ticker)}&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(base_url)
    news_articles = feed.entries[:num_articles]

    articles_data = []
    for entry in news_articles:
        article = {}
        article['title'] = entry.title
        article['link'] = entry.link
        article['published'] = getattr(entry, 'published', None)
        article['content'] = getattr(entry, 'summary', None)

        articles_data.append({
            "title": article['title'],
            "link": article['link'],
            "published": article['published'],
            "content": article['content']
        })
    return articles_data
    
def get_article_content(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; FinanceScraper/1.0)"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        if response.encoding:
            text = response.text
        else:
            response.encoding = response.apparent_encoding
            text = response.text

        soup = BeautifulSoup(text, 'html.parser')

        
        article_tag = soup.find('article')
        if article_tag:
            paragraphs = article_tag.find_all('p')
        else:
            paragraphs = soup.find_all('p')

        parts = []
        for p in paragraphs:
            try:
                txt = p.get_text(separator=' ', strip=True)
            except Exception:
                continue
            if txt:
                parts.append(txt)
        content = ' '.join(parts).strip()

       
        if not content:
            meta = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
            if meta and meta.get('content'):
                content = meta.get('content').strip()
            else:
                content = soup.get_text(separator=' ', strip=True)

        return content if content else ''
    except requests.RequestException:
        return ""


def generate_sentiment_message(finbert_scores=None, vader_scores=None, textblob_scores=None):
    """
    Determine a single sentiment label (Positive/Neutral/Negative) from available scorers
    and return a descriptive message:
      - Positive: describes event with positive benefits -> price increase
      - Negative: describes event with negative impact -> price decrease
      - Neutral: describes event with no clear impact -> price unchanged

    Preferred source: finbert_scores (if provided). Fallback: vader compound, then textblob polarity.
    """

    
    label = "Neutral"

    
    if finbert_scores:
        mapping = {k.capitalize(): v for k, v in finbert_scores.items()}
        if mapping:
            label = max(mapping, key=mapping.get)


    messages = {
        "Positive": "Describes an event that has positive benefits to the company leading to an increase in its stock market price.",
        "Negative": "Describes an event that has negative impact to the company leading to a decrease in its stock market price.",
        "Neutral":  "Describes an event that has no true indication on its impact which leads to the stock market price not being changed."
    }

    return messages.get(label, messages["Neutral"])
    
id2label = {0: "negative", 1: "neutral", 2: "positive"}

def finbert_sentiment(text):
    inputs = finbert_tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    outputs = finbert_model(**inputs)
    probs = torch.nn.functional.softmax(outputs.logits, dim=1)[0].detach().numpy()

    label_idx = probs.argmax()
    label = id2label[label_idx]

    return {
        "label": label,
        "negative": float(probs[0]),
        "neutral": float(probs[1]),
        "positive": float(probs[2]),
    }

def summarize_articles(articles):
    """
    Accepts a list of article dicts (each with keys: title, link, published, content)
    and returns a list of result dicts containing sentiment scores from FinBERT, VADER, and TextBlob.
    """
    analyzer = SentimentIntensityAnalyzer()
    results = []

    for art in articles:
        title = art.get('title', '') or ''
        link = art.get('link', '') or ''
        published = art.get('published', None)
        content = art.get('content', '') or ''

       
        if not content and link:
            try:
                fetched = get_article_content(link)
                content = fetched or ''
            except Exception:
                content = ''

        text = (title + " " + content).strip()
        if not text:
            text = title or content or ""

        
        fin = finbert_sentiment(text)
       
        finbert_scores = {
            "positive": float(fin.get("positive", 0.0)),
            "neutral": float(fin.get("neutral", 0.0)),
            "negative": float(fin.get("negative", 0.0)),
        }

        finbert_avg_score = mean(finbert_scores.values()) if finbert_scores else 0.0
        vader_scores = analyzer.polarity_scores(text)

        
        try:
            tb_polarity = float(TextBlob(text).sentiment.polarity)
        except Exception:
            tb_polarity = 0.0

        result = {
            "title": title,
            "link": link,
            "published": published,
            "content": content,
            "finbert": finbert_scores,
            "vader": vader_scores,
            "textblob": {"polarity": tb_polarity}
        }

        results.append(result)

    return results

def analyze_overall_sentiment(articles_data):

    try:
        fin_scores = finbert_sentiment(articles_data)
        polarity = float(fin_scores.get("positive", 0.0)) - float(fin_scores.get("negative", 0.0))
    except Exception:
        polarity = 0.0


    if polarity > 0.05:
        sentiment = 'Positive'
    elif polarity < -0.05:
        sentiment = 'Negative'
    else:
        sentiment = 'Neutral'
    
    return polarity, sentiment

def summarize_sentiments(results):
    summary = {
        'finbert': {'positive': 0, 'neutral': 0, 'negative': 0}
    }

    for res in results:
        finbert = res.get('finbert', {})
        if finbert:
            top_label = max(finbert, key=finbert.get)
            summary['finbert'][top_label.lower()] += 1

    return summary

def summary(results):
    if not results:
        return "No articles to summarize."
    total_articles = len(results)

    counts = summarize_sentiments(results)

    combined_text = " ".join([(r.get('title', '') + " " + r.get('content', '')).strip() for r in results])
    polarity, overall_sentiment = analyze_overall_sentiment(combined_text)

    report_lines = []
    report_lines.append("\n--- Market News Sentiment Summary ---")
    report_lines.append(f"Total Articles Analyzed: {total_articles}\n")
    report_lines.append(f"Overall Compound Polarity: {polarity:.4f} => {overall_sentiment}\n")
    report_lines.append("FinBERT: Positive={pos}, Neutral={neu}, Negative={neg}".format(
        pos=counts['finbert']['positive'], neu=counts['finbert']['neutral'], neg=counts['finbert']['negative']))

    
    return "\n".join(report_lines)

def main(ticker="MSFT", num_articles=10):
    articles = Get_news(ticker, num_articles)
    results = summarize_articles(articles)
    report = summary(results)
    print(report)

    
    for res in results:
        print("\nTitle:", res.get('title'))
        print("Link:", res.get('link'))
        print("Published:", res.get('published'))
        msg = generate_sentiment_message(          
            finbert_scores=res.get('finbert'),
        )

        print("Indication of Sentiment Analysis:", msg)
        tb = res.get('textblob', {})
        finbert = res.get('finbert') or {}
        if finbert:
            top_label = max(finbert, key=finbert.get)
            top_score = finbert.get(top_label, 0.0)
            print(f"FinBERT Top Sentiment: {top_label} ({top_score:.2f})")
            print("FinBERT Scores:", finbert)
        else:
            print("FinBERT Sentiment: N/A")
    return results

def calculate_pb_ratio(ticker):
    ticker_obj = yf.Ticker(ticker)
    info = ticker_obj.info
    book_value = info.get('bookValue', None)
    price = info.get('regularMarketPrice', None)

    
    if book_value is None or price is None or book_value == 0:
        return None

    try:
        ratio = float(price) / float(book_value)
        return round(ratio, 2)
    except Exception:
        return None

def pb_ratio(ticker):
    ratio = calculate_pb_ratio(ticker)
    if ratio is None:
        return "P/B ratio data not available."
    elif ratio < 1.00:
        return "The stock may be undervalued."
    elif ratio > 1.00:
        return "The stock may be overvalued."
    else:
        return "The stock is fairly valued."

if __name__ == "__main__":
    
    ticker = input("What ticker symbol would you like to analyze?: ")
    print("Starting Financial News Sentiment Analysis...")

    try:
        main(ticker)
    except Exception as e:
        print("Error during analysis:", e)
    print("Analysis Complete.")
    pb_message = pb_ratio(ticker)
    print(f"P/B Ratio Analysis:{calculate_pb_ratio(ticker)}, {pb_message}")