import pandas as pd
import numpy as np
import yfinance as yf
import FinanceDataReader as fdr
from datetime import datetime, timedelta
from discord import send_message, send_message_table

# 기술적 분석 함수
def calculate_macd(data, short_window=12, long_window=26, signal_window=9):
    data['EMA12'] = data['Close'].ewm(span=short_window, adjust=False).mean()
    data['EMA26'] = data['Close'].ewm(span=long_window, adjust=False).mean()
    data['MACD'] = data['EMA12'] - data['EMA26']
    data['MACD_Signal'] = data['MACD'].ewm(span=signal_window, adjust=False).mean()
    return data


def calculate_stochastic(data, k_window=14, d_window=3):
    low_min = data['Low'].rolling(window=k_window).min()
    high_max = data['High'].rolling(window=k_window).max()
    data['%K'] = 100 * ((data['Close'] - low_min) / (high_max - low_min))
    data['%D'] = data['%K'].rolling(window=d_window).mean()
    return data


def calculate_rsi(data, window=7):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    return data


def calculate_bollinger_bands(data, window=10):
    data['Middle_BB'] = data['Close'].rolling(window=window).mean()
    data['Upper_BB'] = data['Middle_BB'] + (data['Close'].rolling(window=window).std() * 2)
    data['Lower_BB'] = data['Middle_BB'] - (data['Close'].rolling(window=window).std() * 2)
    return data


def calculate_moving_averages(data):
    data['MA_5'] = data['Close'].rolling(window=5).mean()
    data['MA_20'] = data['Close'].rolling(window=20).mean()
    return data


def calculate_volume_metrics(data):
    data['Volume_MA_20'] = data['Volume'].rolling(window=20).mean()
    return data


def find_signal(data):
    data = calculate_macd(data)
    data = calculate_stochastic(data)
    data = calculate_rsi(data)
    data = calculate_bollinger_bands(data)
    data = calculate_moving_averages(data)
    data = calculate_volume_metrics(data)

    buy_conditions = [
        #('MACD', data['MACD'] > data['MACD_Signal']),
        #('Stochastic', data['%K'] > data['%D']),
        ('RSI', data['RSI'] > 30),
        ('Bollinger Lower', data['Close'] > data['Lower_BB']),
        ('Moving Average', data['MA_5'] > data['MA_20']),
        ('Volume', data['Volume'] > data['Volume_MA_20'])
    ]

    sell_conditions = [
        ('MACD', data['MACD'] < data['MACD_Signal']),
        ('Stochastic', data['%K'] < data['%D']),
        ('RSI', data['RSI'] > 70),
        ('Bollinger Upper', data['Close'] > data['Upper_BB']),
        ('Volume', data['Volume'] > data['Volume_MA_20'])
    ]
    
    data['buy_signal'] = True
    for _, cond in buy_conditions:
        data['buy_signal'] &= cond

    data['sell_signal'] = True
    for _, cond in sell_conditions:
        data['sell_signal'] &= cond    

    num_buy_conditions = len(buy_conditions)
    num_sell_conditions = len(sell_conditions)
    
    data['buy_signal_rate'] = sum(cond for _, cond in buy_conditions) / num_buy_conditions * 100
    data['sell_signal_rate'] = sum(cond for _, cond in sell_conditions) / num_sell_conditions * 100

    #print(data['buy_signal_rate'])
    return data

# 실시간 펀더멘털 데이터 가져오기
def get_fundamentals(symbols):
    financials = []
    for symbol in symbols:
        stock = yf.Ticker(symbol)
        try:
            per = stock.info.get('forwardPE', np.nan)
            pbr = stock.info.get('priceToBook', np.nan)
            roe = stock.info.get('returnOnEquity', np.nan) * 100 if stock.info.get('returnOnEquity') else np.nan
            revenue_growth = stock.info.get('revenueGrowth', np.nan)
            eps_growth = stock.info.get('earningsGrowth', np.nan)
            div_yield = stock.info.get('dividendYield', np.nan) * 100 if stock.info.get('dividendYield') else 0
            roic = stock.info.get('returnOnAssets', np.nan) * 100 if stock.info.get('returnOnAssets') else np.nan
            
            if not np.isnan([per, pbr, roe, revenue_growth, eps_growth, div_yield, roic]).any():
                financials.append((symbol, per, pbr, roe, revenue_growth, eps_growth, div_yield, roic))
        except:
            #print("ABC")
            continue
    return financials

# 펀더멘털 분석 함수
def filter_stocks(financials, min_roic=5, min_eps_growth=0.05, min_revenue_growth=0.02, min_roe=1, max_per=100, max_pbr=30, min_div_yield=0):
    filtered_stocks = []
    for stock in financials:
        symbol, per, pbr, roe, revenue_growth, eps_growth, div_yield, roic = stock
        #print(symbol, per, pbr, roe)
        if per < max_per and pbr < max_pbr and roe > min_roe:
        #if revenue_growth > min_revenue_growth and eps_growth > min_eps_growth and per < max_per and pbr < max_pbr and roe > min_roe and div_yield > min_div_yield and roic > min_roic:
            filtered_stocks.append(symbol)
    return filtered_stocks

# 백테스트 함수
def backtest_with_stop_loss(symbol, start="2024-01-01", stop_loss=-5):
    end = (datetime.strptime(start, "%Y-%m-%d") + timedelta(days=365)).strftime("%Y-%m-%d")
    df = fdr.DataReader(symbol, start, end)
    df = df[['Close', 'Volume', 'High', 'Low']]
    df = find_signal(df)
    
    initial_cash = 1500
    cash = initial_cash
    position = 0
    buy_price = 0
    trade_log = []
    
    for i in range(len(df)):
        date = df.index[i].strftime("%Y-%m-%d")
        close_price = df['Close'].iloc[i]

        if df['buy_signal_rate'].iloc[i] > 70 and cash > 0:
            buy_amount = initial_cash * 0.2
            buy_quantity = buy_amount / close_price
            position += buy_quantity
            cash -= buy_amount
            buy_price = close_price
            trade_log.append(f"[{date}] 매수: 가격 {close_price:.2f}, 매수량 {buy_quantity:.4f}, 남은 현금 ${cash:.2f}")
        
        if position > 0 and ((close_price - buy_price) / buy_price) * 100 <= stop_loss:
            #sell_quantity = position * 0.2  # 보유 주식의 20% 매도
            sell_amount = position * close_price
            cash += sell_amount
            trade_log.append(f"[{date}] 손절 매도: 가격 {close_price:.2f}, 손실률: {((close_price - buy_price) / buy_price) * 100:.2f}%, 보유 현금 ${cash:.2f}")
            position = 0
            buy_price = 0
        
        elif df['sell_signal_rate'].iloc[i] > 70 and position > 0:
            sell_quantity = position * 0.2
            sell_amount = sell_quantity * close_price
            position -= sell_quantity
            cash += sell_amount
            trade_log.append(f"[{date}] 매도: 가격 {close_price:.2f}, 매도량 {sell_quantity:.4f}, 보유 현금 ${cash:.2f}")
    
    final_value = cash + (position * df['Close'].iloc[-1])
    total_return = (final_value - initial_cash) / initial_cash * 100

    df.dropna(inplace=True)
    today = datetime.today() - timedelta(days=1)
    if today.weekday() in [5, 6]:  # 토요일(5) 또는 일요일(6)이라면
        today -= timedelta(days=today.weekday() - 4)
    today_str = today.strftime("%Y-%m-%d")
    
    signal = df.iloc[-1]
    #print(signal)
    #print(today_str, df.index[-1].strftime("%Y-%m-%d"))
    if today_str == df.index[-1].strftime("%Y-%m-%d"):
        #today_signals = df.loc[today_str, ["buy_signal_growth", "sell_signal_growth", "buy_signal_bluechip", "sell_signal_bluechip"]]
        #if today_signals.any():
        #print(df.loc[today_str])
        signal = df.loc[today_str]

    return total_return, trade_log, signal, df

# 백테스트 실행
symbols = ['QQQ', 'DIA', 'TSLA', 'PLTR', 'ACHR', 'JOBY', 'QUBT', 'RGTI', 'SMR', 'OKLO', 'O', 'SCHD']
filtered_symbols = symbols
#financials = get_fundamentals(symbols)
#filtered_symbols = filter_stocks(financials)
#print(filtered_symbols)
results = {}
signals = {}
stock_df = {}

for symbol in filtered_symbols:
    total_return, trades, signal, df = backtest_with_stop_loss(symbol, start="2025-01-01")
    results[symbol] = total_return
    signals[symbol] = signal
    stock_df[symbol] = df
    print(f"\n📊 [{symbol}] 손절 적용 후 총 수익률: {total_return:.2f}%")
    for trade in trades[-5:]:
        print(trade)

sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
print("\n📈 필터링 후 수익률 TOP 종목:")
for symbol, return_rate in sorted_results:
    print(f"{symbol}: {return_rate:.2f}%")

best_symbol = sorted_results[0][0]
print(f"\n🚀 가장 높은 수익률을 기록한 종목: {best_symbol}")

send_message(signals)
send_message_table(stock_df)

#print(signals)