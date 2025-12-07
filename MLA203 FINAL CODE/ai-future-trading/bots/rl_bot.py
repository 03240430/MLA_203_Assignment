import os, time, random
import numpy as np
import pandas as pd
from utils.binance_client import create_client
from dotenv import load_dotenv

load_dotenv()
client = create_client()
SYMBOL = os.getenv("SYMBOL","BTCUSDT")
INTERVAL = os.getenv("INTERVAL","1m")
LIVE = os.getenv("LIVE_TRADING","0") == "1"

ACTIONS = {0:"HOLD", 1:"BUY", 2:"SELL"}

class QTrader:
    def __init__(self, state_bins=(10,)):
        self.q = {}  # dict mapping state->action values
        self.alpha = 0.1
        self.gamma = 0.95
        self.epsilon = 0.1
    
    def get_state(self, price, sma):
        # very simple discretization as example
        diff = price - sma
        bin_idx = int(np.digitize(diff, np.linspace(-200,200,21)))  # coarse
        return str(bin_idx)
    
    def best_action(self, state):
        vals = self.q.get(state, np.zeros(len(ACTIONS)))
        return int(np.argmax(vals))
    
    def update(self, s, a, r, s2):
        old = self.q.get(s, np.zeros(len(ACTIONS)))[a]
        future = 0 if s2 not in self.q else np.max(self.q[s2])
        new = old + self.alpha * (r + self.gamma * future - old)
        arr = self.q.get(s, np.zeros(len(ACTIONS)))
        arr[a] = new
        self.q[s] = arr

def fetch_close_series(symbol=SYMBOL, interval=INTERVAL, limit=500):
    raw = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(raw, columns=['open_time','open','high','low','close','volume','ct','qav','nt','tbv','tqv','ignore'])
    df['close'] = df['close'].astype(float)
    return df

def run_simulation(episodes=5):
    qt = QTrader()
    for ep in range(episodes):
        df = fetch_close_series()
        sma = df['close'].rolling(10).mean().bfill()

        balance = 1000.0
        pos = 0.0
        entry_price = 0.0
        for i in range(1, len(df)):
            price = df['close'].iloc[i]
            s = qt.get_state(price, sma.iloc[i-1])
            a = qt.best_action(s) if random.random() > qt.epsilon else random.choice(list(ACTIONS.keys()))
            # simulate simple reward
            reward = 0
            if a==1:  # buy
                pos = 1
                entry_price = price
            elif a==2 and pos==1:  # sell
                pnl = price - entry_price
                reward = pnl
                balance += pnl
                pos = 0
            # next state
            s2 = qt.get_state(price, sma.iloc[i])
            qt.update(s,a,reward,s2)
        print(f"Episode {ep} completed. Balance approx {balance:.2f}")
    return qt

if __name__ == "__main__":
    print("Running RL simulation...")
    trainer = run_simulation(episodes=3)
    print("Trained Q table size:", len(trainer.q))
    # if LIVE and you want to place a trade, you can implement order logic here carefully
