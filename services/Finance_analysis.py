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


finbert_model = AutoModelForSequenceClassification.from_pretrained("yiyanghkust/finbert-tone")
finbert_tokenizer = AutoTokenizer.from_pretrained("yiyanghkust/finbert-tone")

labels = ['Negative', 'Neutral', 'Positive']

def Get_news(ticker, num_articles=5):
    
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
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')
        content = ' '.join([p.get_text() for p in paragraphs])
        return content.strip()
    except requests.RequestException:
        return "Failed to retrieve article content."
    
def analyze_sentiments(articles_data):

    vader_analyzer = SentimentIntensityAnalyzer()
    results = []

    for article in articles_data:
        title = article.get('title', '') or ''
        link = article.get('link', '') or ''
        content = get_article_content(link) if link else ''

        TextBlob_sentiment = TextBlob(content).sentiment
        vader_sentiment = vader_analyzer.polarity_scores(content)

        
        text_for_finbert = (title + ". " + content) if content else title
        inputs = finbert_tokenizer(text_for_finbert, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = finbert_model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1).cpu().numpy()[0]
        finbert_sentiment = {labels[i]: float(probs[i]) for i in range(len(labels))}

        augmented = {
            **article,
            'content': content,
            'textblob': {
                'polarity': TextBlob_sentiment.polarity,
                'subjectivity': TextBlob_sentiment.subjectivity
            },
            'vader': vader_sentiment,
            'finbert': finbert_sentiment
        }
        results.append(augmented)
    return results

def analyze_overall_sentiment(articles_data):

    analyzer = SentimentIntensityAnalyzer()
    scores = analyzer.polarity_scores(articles_data)
    polarity = scores['compound']


    if polarity > 0.05:
        sentiment = 'Positive'
    elif polarity < -0.05:
        sentiment = 'Negative'
    else:
        sentiment = 'Neutral'
    
    return polarity, sentiment

def summarize_sentiments(results):
    summary = {
        "Positive": 0,
        "Neutral": 0,
        "Negative": 0
    }

    if not results:
        print("\n--- Market News Sentiment Summary ---")
        print("No articles to summarize.")
        return

    for article in results:
        
        finbert = article.get('finbert')
        if finbert:
            finbert_sentiment = max(finbert, key=finbert.get)
            summary[finbert_sentiment] += 1
        else:
            vader = article.get('vader', {})
            polarity = vader.get('compound', 0.0)
            if polarity > 0.05:
                summary['Positive'] += 1
            elif polarity < -0.05:
                summary['Negative'] += 1
            else:
                summary['Neutral'] += 1
    total_articles = len(results)
    print("\n--- Market News Sentiment Summary ---")
    print(f"Total articles analyzed: {total_articles}")
    for sentiment in ("Positive", "Neutral", "Negative"):
        count = summary[sentiment]
        percent = (count / total_articles) * 100 if total_articles > 0 else 0
        print(f"{sentiment} Sentiments: {count} ({percent:.2f}%)")

    
    return summary

def main():
    ticker = [
        "AAPL stock",
        "Apple Inc",
        "Apple earnings report",
        "Apple new product launch"
    ]
    num_articles_per_ticker = 5
    all_articles = []
    
    for term in ticker:
        articles = Get_news(term, num_articles=num_articles_per_ticker)
        all_articles.extend(articles)
    return all_articles
if __name__ == "__main__":
    print("Starting Financial News Sentiment Analysis...")
    articles = main()
    results = analyze_sentiments(articles)
    summarize_sentiments(results)
    for res in results:
        print("\nTitle:", res.get('title'))
        print("Link:", res.get('link'))
        print("Published:", res.get('published'))
        print("Summary:", (res.get('content') or '')[:200], "...")
        finbert = res.get('finbert') or {}
        if finbert:
            top_label = max(finbert, key=finbert.get)
            top_score = finbert.get(top_label, 0.0)
            print(f"FinBERT Top Sentiment: {top_label} ({top_score:.2f})")
            print("FinBERT Scores:", finbert)
        else:
            print("FinBERT Sentiment: N/A")