import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from mplfinance.original_flavor import candlestick_ohlc
import matplotlib.dates as mdates
from dotenv import load_dotenv
import openai

from utils.binance_client import create_client
from utils.indicators import ema, macd, rsi, vwap

load_dotenv()
client = create_client()
SYMBOL = os.getenv("SYMBOL", "BTCUSDT")
INTERVAL = os.getenv("INTERVAL", "1m")
openai.api_key = os.getenv("OPENAI_API_KEY", "")


def fetch_klines(symbol=SYMBOL, interval=INTERVAL, limit=500):
    raw = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(raw, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "num_trades",
        "taker_base_vol", "taker_quote_vol", "ignore"
    ])
    df[["open","high","low","close","volume"]] = df[["open","high","low","close","volume"]].astype(float)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df.set_index("open_time", inplace=True)
    return df


def analyze_and_plot(symbol=SYMBOL):
    df = fetch_klines(symbol)
    df["ema12"] = ema(df["close"], 12)
    df["ema26"] = ema(df["close"], 26)
    df["macd"], df["macd_signal"], df["macd_hist"] = macd(df)
    df["rsi"] = rsi(df["close"])
    df["vwap"] = vwap(df)

    # Summary
    last_close = df["close"].iloc[-1]
    rsi_val = df["rsi"].iloc[-1]
    macd_val = df["macd_hist"].iloc[-1]
    summary = f"Symbol: {symbol}\nLast Close: {last_close:.2f}\nRSI: {rsi_val:.2f}\nMACD Histogram: {macd_val:.6f}\n"

    # -----------------------------------------
    # Multi-panel chart
    fig, axs = plt.subplots(4, 1, figsize=(14,12), sharex=True)

    # ---- 1. PRICE + EMA + VWAP (Candlestick) ----
    df_ohlc = df[["open","high","low","close"]].copy()
    df_ohlc["time"] = mdates.date2num(df_ohlc.index)
    ohlc = df_ohlc[["time","open","high","low","close"]]

    axs[0].xaxis_date()
    candlestick_ohlc(axs[0], ohlc.values, width=0.0008, colorup='green', colordown='red', alpha=0.8)
    axs[0].plot(df.index, df["ema12"], label="EMA12", color="blue")
    axs[0].plot(df.index, df["ema26"], label="EMA26", color="orange")
    axs[0].plot(df.index, df["vwap"], label="VWAP", color="purple")
    axs[0].set_title(f"{symbol} Price + EMA + VWAP")
    axs[0].legend()
    axs[0].grid(True)

    # ---- 2. RSI ----
    axs[1].plot(df.index, df["rsi"], label="RSI", color="magenta")
    axs[1].axhline(70, color="red", linestyle="--")
    axs[1].axhline(30, color="green", linestyle="--")
    axs[1].fill_between(df.index, 70, 100, color='red', alpha=0.1)
    axs[1].fill_between(df.index, 0, 30, color='green', alpha=0.1)
    axs[1].set_title("RSI")
    axs[1].grid(True)

    # ---- 3. MACD ----
    colors = df["macd_hist"].apply(lambda x: 'g' if x>=0 else 'r')
    axs[2].bar(df.index, df["macd_hist"], color=colors, label="Histogram")
    axs[2].plot(df.index, df["macd"], color="blue", label="MACD")
    axs[2].plot(df.index, df["macd_signal"], color="orange", label="Signal")
    axs[2].set_title("MACD")
    axs[2].legend()
    axs[2].grid(True)

    # ---- 4. VOLUME ----
    vol_colors = ['g' if c>=o else 'r' for c,o in zip(df["close"], df["open"])]
    axs[3].bar(df.index, df["volume"], color=vol_colors)
    axs[3].set_title("Volume")
    axs[3].grid(True)

    plt.tight_layout()

    # Save chart
    output_folder = os.path.join(os.path.dirname(__file__), "..", "web", "output")
    os.makedirs(output_folder, exist_ok=True)
    chart_path = os.path.join(output_folder, f"{symbol}_chart.png")
    plt.savefig(chart_path)
    plt.close()

    # Recommendation
    if openai.api_key:
        try:
            prompt = f"Provide a short actionable crypto trading recommendation based on:\n\n{summary}"
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert crypto analyst."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150
            )
            recommendation = response["choices"][0]["message"]["content"].strip()
        except:
            recommendation = "OpenAI API error. Using fallback recommendation."
    else:
        recommendation = "RSI near neutral, MACD slightly positive. Market indecisive — wait for a clearer trend."

    # Save analysis
    analysis_path = os.path.join(output_folder, "analysis.txt")
    with open(analysis_path, "w") as f:
        f.write(summary + "\n" + recommendation)

    return chart_path, recommendation
