from importlib.resources import contents
import feedparser
import requests
from bs4 import BeautifulSoup
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
from datetime import datetime
from urllib.parse import quote_plus

from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np

# Financial News RSS Feed URL
finbert_model = AutoModelForSequenceClassification.from_pretrained("yiyanghkust/finbert-tone")
finbert_tokenizer = AutoTokenizer.from_pretrained("yiyanghkust/finbert-tone")

labels = ['Negative', 'Neutral', 'Positive']

def Get_news(query, num_articles=15):
    base_url = f"https://news.yahoo.com/rss/search?p={quote_plus(query)}"
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
        content = ' '.join([para.get_text() for para in paragraphs])
        return content.strip()
    except requests.RequestException:
        return "Failed to retrieve article content."
    
def analyze_sentiments(articles_data):
    """
    articles_data: list of dicts with keys 'title' and 'link' (and optional 'published')
    returns: list of article dicts augmented with 'content', 'vader', 'textblob', and 'finbert' sentiment results
    """
    vader_analyzer = SentimentIntensityAnalyzer()
    results = []

    for article in articles_data:
        title = article.get('title', '') or ''
        link = article.get('link', '') or ''
        content = get_article_content(link) if link else ''

        # choose text for general sentiment (prefer content, fallback to title)
        text_for_sent = content if content and not content.startswith("Failed to retrieve") else title

        # VADER sentiment
        vader_scores = vader_analyzer.polarity_scores(text_for_sent)

        # TextBlob sentiment
        tb = TextBlob(text_for_sent)
        textblob_sent = {
            'polarity': tb.sentiment.polarity,
            'subjectivity': tb.sentiment.subjectivity
        }

        # FinBERT sentiment (use title for classification to limit token length)
        inputs = finbert_tokenizer(title, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = finbert_model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1).numpy()[0]
        finbert_sentiment = {labels[i]: float(probs[i]) for i in range(len(labels))}

        augmented = {
            **article,
            'content': content,
            'vader': vader_scores,
            'textblob': textblob_sent,
            'finbert': finbert_sentiment
        }
        results.append(augmented)

    return results


ticker = "AAPL"
articles = Get_news(f"{ticker} stock")
results = analyze_sentiments(articles)
print(results)