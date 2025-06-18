import streamlit as st
import pandas as pd
import requests
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator, EMAIndicator
from ta.volatility import BollingerBands
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

# Delay before refreshing (if needed)
time.sleep(60)

# Load from Streamlit Secrets
API_KEY = st.secrets["api"]["246b3f60bb878d9a34c80443fb30e963"]
API_URL = f"https://api.exchangerate.host/latest?base=EUR&access_key={API_KEY}"
CURRENCY_PAIR = "EUR/USD"
EMAIL_SUBSCRIBER = st.secrets["email"]["kadegbie@gmail.com"]

# Email Config
SMTP_SERVER = st.secrets["email"]["smtp.gmail.com"]
SMTP_PORT = st.secrets["email"][587]
EMAIL_USERNAME = st.secrets["email"]["kadegbie@gmail.com"]
EMAIL_PASSWORD = st.secrets["email"]["auma rvdb lxxj qukc"]

def fetch_forex_data():
    """Fetches live forex data from Exchange Rates API."""
    try:
        response = requests.get(API_URL)
        data = response.json()
        st.write(data)

        rates = data.get("rates", {})
        eur_usd = rates.get("USD")

        if eur_usd is None:
            st.error("Unable to fetch EUR/USD rates. Check the API response.")
            return None

        df = pd.DataFrame({"close": [eur_usd] * 25})
        return df

    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

def calculate_indicators(data):
    """Calculate key technical indicators - RSI, MACD, Bollinger Bands, SMA, EMA."""
    indicators = {}
    rsi = RSIIndicator(data["close"]).rsi()
    indicators["RSI"] = rsi
    macd = MACD(data["close"]).macd()
    indicators["MACD"] = macd
    bb = BollingerBands(data["close"])
    indicators["Bollinger High"] = bb.bollinger_hband()
    indicators["Bollinger Low"] = bb.bollinger_lband()
    sma20 = SMAIndicator(data["close"], window=20).sma_indicator()
    ema20 = EMAIndicator(data["close"], window=20).ema_indicator()
    indicators["SMA 20"] = sma20
    indicators["EMA 20"] = ema20
    return indicators

def analyze_signals(data, indicators):
    """Analyze signals based on technical indicators."""
    latest_close = data["close"].iloc[-1]
    signals = []
    rsi = indicators["RSI"].iloc[-1]
    if rsi < 30:
        signals.append("RSI indicates BUY (oversold)")
    elif rsi > 70:
        signals.append("RSI indicates SELL (overbought)")

    macd = indicators["MACD"].iloc[-1]
    if macd > 0:
        signals.append("MACD indicates BUY (bullish momentum)")
    else:
        signals.append("MACD indicates SELL (bearish momentum)")

    upper_band = indicators["Bollinger High"].iloc[-1]
    lower_band = indicators["Bollinger Low"].iloc[-1]
    if latest_close < lower_band:
        signals.append("Price is below Bollinger Bands, potential BUY signal")
    elif latest_close > upper_band:
        signals.append("Price is above Bollinger Bands, potential SELL signal")

    if "BUY" in " ".join(signals):
        trade_decision = "BUY"
    elif "SELL" in " ".join(signals):
        trade_decision = "SELL"
    else:
        trade_decision = "HOLD"

    return signals, trade_decision

def send_email(subject, body, recipient=EMAIL_SUBSCRIBER):
    """Sends an email alert with the trade signal."""
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)

        msg = MIMEMultipart()
        msg["From"] = EMAIL_USERNAME
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        server.sendmail(EMAIL_USERNAME, recipient, msg.as_string())
        server.quit()

        st.success(f"Trade signal sent to {recipient}!")
    except Exception as e:
        st.error(f"Failed to send email: {e}")

def main():
    st.title("Forex Trading Signals for EUR/USD")
    st.sidebar.header("Trading Options")

    st.write("""
    This app provides live trading signals for the EUR/USD pair using technical indicators: 
    RSI, MACD, Bollinger Bands, SMA, and EMA.
    """)

    st.sidebar.subheader("Data Settings")
    num_points = st.sidebar.slider("Number of Historical Points", 10, 200, 100)

    st.subheader("Live Forex Data - EUR/USD")
    data = fetch_forex_data()

    if data is not None:
        st.write(data.head(num_points))
        indicators = calculate_indicators(data)
        signals, trade_decision = analyze_signals(data, indicators)

        st.subheader("Trading Signals")
        for signal in signals:
            st.write(f"- {signal}")

        st.subheader("Trade Recommendation")
        st.write(f"**{trade_decision}**")

        st.subheader("Risk Management")
        latest_close = data["close"].iloc[-1]
        take_profit = latest_close * 0.99
        stop_loss = latest_close * 1.01
        st.write(f"Stop Loss: {stop_loss:.6f}")
        st.write(f"Take Profit: {take_profit:.6f}")

        email_subject = f"Forex Trade Alert - {trade_decision}"
        email_body = (
            f"Trade Signal: {trade_decision}\n"
            f"Latest Price: {latest_close}\n"
            f"Take Profit: {take_profit:.6f}\n"
            f"Stop Loss: {stop_loss:.6f}\n\n"
            f"Indicators:\n" + "\n".join(signals)
        )
        send_email(email_subject, email_body)
    else:
        st.write("No data available. Check your API key or internet connection.")

if __name__ == "__main__":
    main()
