from fastapi import FastAPI, Query
from up_stock import *
import json

app = FastAPI()

@app.get("/search")
def double(ticker: str = Query(..., description="문자열을 입력하세요")):
    total_return, trades, signal, df = backtest_with_stop_loss(ticker, start="2025-01-01")
    b_data = []
    s_data = []
    for b, s in zip(df.to_dict()['buy_signal_rate'].values(), df.to_dict()['sell_signal_rate'].values()):
        b_data.append(b)
        s_data.append(s)
    b_data.reverse()
    s_data.reverse()
    return {"ticker": ticker, "total_return": total_return, "signal": signal.to_dict(), 'b_data': b_data[:20], 's_data': s_data[:20]}
