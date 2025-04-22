from fastapi import FastAPI, Query
from up_stock import *
import json

app = FastAPI()

@app.get("/search")
def double(ticker: str = Query(..., description="문자열을 입력하세요")):
    total_return, trades, signal, df = backtest_with_stop_loss(ticker, start="2025-01-01")
    b_data = []
    s_data = []
    c_data = []
    
    for b, s, c in zip(df.to_dict()['buy_signal_rate'].values(), df.to_dict()['sell_signal_rate'].values(), df.to_dict()['Close'].values()):
        b_data.append(b)
        s_data.append(s)
        c_data.append(c)

    tmp = []
    for index in range(0, len(c_data) - 1):
        tmp.append(c_data[index+1] - c_data[index])
    c_data = tmp

    #print(df.to_dict()['Close'])
    #print(df.to_dict()['buy_signal_rate'])
    #print(df.to_dict()['sell_signal_rate'])

    chart = {"b_data": b_data[-20:], "s_data": s_data[-20:], "c_data": c_data[-20:]}
    return {"ticker": ticker, "total_return": total_return, "signal": signal.to_dict(), "chart": chart}
