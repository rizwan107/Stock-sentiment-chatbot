import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
from textblob import TextBlob
from datetime import datetime, timedelta
from wordcloud import WordCloud
import re
import yfinance as yf
import ssl

# Constants
NEWS_API_KEY = "b5ca976121fd464986d365b4b123d877"
TWITTER_BEARER_TOKEN = "fbdjf343bfb56"  # Optional if using Twitter

# Disable SSL verification for yfinance (Not recommended for production)
ssl._create_default_https_context = ssl._create_unverified_context

# Stock name to ticker symbol mapping (including Indian companies)
stock_name_to_ticker = {
    "apple": "AAPL", "tesla": "TSLA", "microsoft": "MSFT", "google": "GOOG", "amazon": "AMZN",
    "meta": "META", "netflix": "NFLX", "nvidia": "NVDA", "reliance": "RELIANCE.NS",
    "infosys": "INFY.NS", "tcs": "TCS.NS", "hdfc": "HDFC.NS", "icici": "ICICI.NS", "sbi": "SBIN.NS",
    "vodafone idea": "IDEA.NS", "wipro": "WIPRO.NS", "larsen": "LT.NS", "ongc": "ONGC.NS",
    "tata motors": "TATAMOTORS.NS", "hcl": "HCLTECH.NS", "itc": "ITC.NS", "kotak": "KOTAKBANK.NS",
    "axis": "AXISBANK.NS", "hindustan unilever": "HINDUNILVR.NS", "bharat petroleum": "BPCL.NS",
    "maruti suzuki": "MARUTI.NS", "mahindra & mahindra": "M&M.NS", "indusind bank": "INDUSINDBK.NS",
    "sun pharma": "SUNPHARMA.NS", "dr. reddy's laboratories": "DRREDDY.NS", "bharti airtel": "BHARTIARTL.NS"
}

# Utility Functions
def fetch_news(stock_name):
    url = (
        f"https://newsapi.org/v2/everything?q={stock_name}&sortBy=publishedAt&language=en&apiKey={NEWS_API_KEY}"
    )
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data.get("articles"):
            return data.get("articles")
        else:
            st.warning("No recent news articles returned by the API. Try using a more popular stock name or ticker.")
            return []
    else:
        st.error(f"Error {response.status_code}: {response.text}")
        return []

def analyze_sentiment(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.1:
        return "Positive"
    elif polarity < -0.1:
        return "Negative"
    else:
        return "Neutral"

def summarize_articles(articles):
    sentiment_data = []
    for article in articles:
        sentiment = analyze_sentiment(article["title"] + " " + (article["description"] or ""))
        sentiment_data.append({
            "title": article["title"],
            "publishedAt": article["publishedAt"],
            "sentiment": sentiment,
        })
    return pd.DataFrame(sentiment_data)

def display_sentiment_chart(df):
    sentiment_counts = df["sentiment"].value_counts()
    st.subheader("Sentiment Overview")
    fig, ax = plt.subplots()
    sentiment_counts.plot(kind="bar", color=["green", "red", "gray"], ax=ax)
    st.pyplot(fig)

def generate_wordcloud(df):
    if not df.empty:
        df["description"] = df["description"].fillna("")
        text = " ".join(df["title"] + " " + df["description"])
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
        st.subheader("Word Cloud from Headlines and Descriptions")
        st.image(wordcloud.to_array())

def provide_advice(df):
    pos = df[df["sentiment"] == "Positive"].shape[0]
    neg = df[df["sentiment"] == "Negative"].shape[0]
    total = len(df)
    if total == 0:
        return "No data to provide advice."
    if pos > neg:
        return "📈 Based on current news, the stock sentiment is mostly positive. Yeah, you can consider buying it, but always do further research."
    elif neg > pos:
        return "📉 Current news sentiment leans negative. It might not be the best time to buy. Consider waiting or looking into other options."
    else:
        return "⚖️ Sentiment is mixed or neutral. You might want to monitor it further before investing."

def suggest_stocks(trend='gain'):
    positive_stocks = ["Reliance", "Infosys", "TCS", "HDFC Bank", "ICICI Bank"]
    negative_stocks = ["Adani Power", "Yes Bank", "Vodafone Idea"]
    if trend == 'gain':
        return f"📊 Some potentially strong performers are: {', '.join(positive_stocks)}. Yeah, these might be good options to consider buying."
    else:
        return f"📉 Avoidable or high-risk stocks include: {', '.join(negative_stocks)}. You might consider switching to: {', '.join(positive_stocks)}."

def extract_stock_from_query(query):
    # Check if a full name exists in the query, then map it to the ticker symbol
    query = query.lower()
    for name, ticker in stock_name_to_ticker.items():
        if name in query:
            return ticker
    matches = re.findall(r"\b[A-Z]{2,5}\b", query)
    return matches[0] if matches else None

def get_stock_price(stock_symbol):
    try:
        stock = yf.Ticker(stock_symbol)
        hist = stock.history(period="1mo")
        if hist.empty:
            st.error(f"Could not fetch stock price for {stock_symbol}. Please verify the ticker symbol.")
            return None
        latest_price = hist['Close'].iloc[-1]
        return latest_price
    except Exception as e:
        st.error(f"Error fetching stock data: {e}")
        return None

# Streamlit UI
st.set_page_config(page_title="Stock Sentiment Chatbot", layout="wide")
st.title("📈 Stock Sentiment Chatbot")

# Sidebar
st.sidebar.title("Navigation")
stock_query = st.sidebar.text_input("Enter Stock Name or Ticker (e.g., AAPL, TSLA):")

if st.sidebar.button("Analyze Sentiment"):
    st.session_state["user_input"] = ""
    if not stock_query:
        st.sidebar.error("Please enter a stock name or ticker.")
    else:
        with st.spinner("Fetching news and analyzing sentiment..."):
            articles = fetch_news(stock_query)
            if not articles:
                st.error("No articles found. Try a different stock name.")
            else:
                df = summarize_articles(articles)
                for article in articles:
                    article["description"] = article.get("description", "")
                df_full = pd.DataFrame(articles)
                df = df.join(df_full[["description"]])
                st.success(f"Showing results for '{stock_query.upper()}'")
                st.write(df[["title", "publishedAt", "sentiment"]])
                display_sentiment_chart(df)
                generate_wordcloud(df)
                st.markdown("**Advice:** " + provide_advice(df))

                # Get the stock price for the given symbol
                latest_price = get_stock_price(stock_query)
                if latest_price:
                    st.subheader(f"Latest Price of {stock_query.upper()}: ₹{latest_price:.2f}")

# Chat Interface
st.markdown("---")
st.subheader("💬 Ask Me Anything")
user_input = st.text_input("Type your question here:", value=st.session_state.get("user_input", ""))

if user_input:
    st.session_state["user_input"] = ""
    user_input_lower = user_input.lower()
    stock_guess = extract_stock_from_query(user_input)

    if stock_guess:
        with st.spinner(f"Analyzing sentiment for {stock_guess.upper()}..."):
            articles = fetch_news(stock_guess)
            if not articles:
                st.warning("No recent news found. Try using a well-known stock name like 'Tesla' or 'Apple'.")
            else:
                df = summarize_articles(articles)
                for article in articles:
                    article["description"] = article.get("description", "")
                df_full = pd.DataFrame(articles)
                df = df.join(df_full[["description"]])
                st.success(f"Sentiment analysis results for '{stock_guess.upper()}'")
                st.write(df[["title", "publishedAt", "sentiment"]])
                display_sentiment_chart(df)
                generate_wordcloud(df)
                st.markdown("**Advice:** " + provide_advice(df))

        latest_price = get_stock_price(stock_guess)
        if latest_price:
            st.subheader(f"Latest Price of {stock_guess.upper()}: ₹{latest_price:.2f}")
    else:
        st.warning("Couldn't extract any stock symbol from your input. Please mention a stock name or symbol.")
