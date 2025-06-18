import streamlit as st
import pandas as pd
import requests
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands
from ta.trend import SMAIndicator, EMAIndicator
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os
import time
time.sleep(60)  # App waits 60 seconds before updating automatically on refresh

load_dotenv()  # Load variables from .env

# Constants
API_KEY = os.getenv("API_KEY") 
API_URL = "https://api.exchangerate.host/latest?base=EUR&symbols=USD"
CURRENCY_PAIR = "EUR/USD"  # Focused currency pair (EUR to USD)
EMAIL_SUBSCRIBER = os.getenv("EMAIL_SUBSCRIBER")

# Email Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME") 
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD") 

def fetch_forex_data():
    """Fetches live forex data from Exchange Rates API."""
    try:
        response = requests.get(API_URL)
        data = response.json()

        # Debugging: Display the entire API response
        st.write(data)

        # Extract EUR/USD rate
        rates = data.get("rates", {})
        eur_usd = rates.get("USD")

        if eur_usd is None:
            st.error("Unable to fetch EUR/USD rates. Check the API response.")
            return None

        # Create a fake DataFrame for technical indicator calculations
        df = pd.DataFrame({"close": [eur_usd] * 100})  # Mock 100 rows with the same rate
        return df

    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None


def calculate_indicators(data):
    """Calculate key technical indicators - RSI, MACD, Bollinger Bands, SMA, and EMA."""
    indicators = {}

    # RSI
    rsi = RSIIndicator(data["close"]).rsi()
    indicators["RSI"] = rsi

    # MACD
    macd = MACD(data["close"]).macd()
    indicators["MACD"] = macd

    # Bollinger Bands
    bb = BollingerBands(data["close"])
    indicators["Bollinger High"] = bb.bollinger_hband()
    indicators["Bollinger Low"] = bb.bollinger_lband()

    # SMA and EMA
    sma20 = SMAIndicator(data["close"], window=20).sma_indicator()
    ema20 = EMAIndicator(data["close"], window=20).ema_indicator()
    indicators["SMA 20"] = sma20
    indicators["EMA 20"] = ema20

    return indicators


def analyze_signals(data, indicators):
    """Analyze signals based on technical indicators."""
    latest_close = data["close"].iloc[-1]
    signals = []

    # RSI
    rsi = indicators["RSI"].iloc[-1]
    if rsi < 30:
        signals.append("RSI indicates BUY (oversold)")
    elif rsi > 70:
        signals.append("RSI indicates SELL (overbought)")

    # MACD
    macd = indicators["MACD"].iloc[-1]
    if macd > 0:
        signals.append("MACD indicates BUY (bullish momentum)")
    else:
        signals.append("MACD indicates SELL (bearish momentum)")

    # Bollinger Bands
    upper_band = indicators["Bollinger High"].iloc[-1]
    lower_band = indicators["Bollinger Low"].iloc[-1]
    if latest_close < lower_band:
        signals.append("Price is below Bollinger Bands, potential BUY signal")
    elif latest_close > upper_band:
        signals.append("Price is above Bollinger Bands, potential SELL signal")

    # Overall recommendation
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
        # Set up the email server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Start encryption
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)

        # Create the email
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USERNAME
        msg["To"] = recipient
        msg["Subject"] = subject

        # Attach the body as plain text
        msg.attach(MIMEText(body, "plain"))

        # Send the email
        server.sendmail(EMAIL_USERNAME, recipient, msg.as_string())

        # Close the connection
        server.quit()

        st.success(f"Trade signal sent to {recipient}!")
    except Exception as e:
        st.error(f"Failed to send email: {e}")


def main():
    st.title("Forex Trading Signals for EUR/USD")
    st.sidebar.header("Trading Options")

    st.write(
        """
    This application provides live trading signals for the EUR/USD currency pair.
    It uses technical analysis with indicators like RSI, MACD, Bollinger Bands, SMA,
    and EMA to generate trade signals.
    """
    )

    st.sidebar.subheader("Real-Time Data Fetching")
    num_points = st.sidebar.slider("Number of Historical Points", 10, 200, 100)

    # Fetch and display data
    st.subheader("Live Forex Data - EUR/USD")
    data = fetch_forex_data()
    if data is not None:
        st.write(data.head(num_points))

        # Calculate indicators
        indicators = calculate_indicators(data)

        # Analyze signals
        signals, trade_decision = analyze_signals(data, indicators)

        # Display signals
        st.subheader("Trading Signals")
        for signal in signals:
            st.write(f"- {signal}")

        # Final recommendation
        st.subheader("Trade Recommendation")
        st.write(f"**{trade_decision}**")

        # Stop Loss and Take Profit
        st.subheader("Risk Management")
        latest_close = data["close"].iloc[-1]
        take_profit = latest_close * 0.99
        stop_loss = latest_close * 1.01
        st.write(f"Stop Loss: {stop_loss:.6f}")
        st.write(f"Take Profit: {take_profit:.6f}")

        # Send trade signal via email
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
        st.write("No data available. Please check your API key or internet connection.")


if __name__ == "__main__":
    main()