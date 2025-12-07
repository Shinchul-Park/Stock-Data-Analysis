from datetime import datetime
import backtrader as bt
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os
#from .Analyzer import MarketDB #상대경로 import
#%matplotlib inline
plt.rcParams['font.family'] = 'Malgun Gothic' 
plt.rcParams['axes.unicode_minus'] = False
try:
    # 패키지 내 모듈로 실행될 때 (Jupyter/다른 모듈에서 import 시)
    from .Analyzer import MarketDB 
except ImportError:
    # 단독 스크립트로 실행될 때 (오류 발생 시 대체)
    # 현재 디렉토리 또는 sys.path에 있는 Analyzer.py를 찾음
    from Analyzer import MarketDB

mk = MarketDB()

company = '207940'
start_date = "2025-01-01"

# 1) Strategy
class MyStrategy(bt.Strategy):
    params = (('rsi_period', 21), ('oversold', 30), ('overbought', 70),)

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.rsi = bt.indicators.RSI_SMA(self.data.close, period=self.p.rsi_period)

    def notify_order(self, order):  # ①
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:  # ② 
            if order.isbuy():
                self.log(f'BUY  : 주가 {order.executed.price:,.0f}, '
                    f'수량 {order.executed.size:,.0f}, '
                    f'수수료 {order.executed.comm:,.0f}, '
                    f'자산 {cerebro.broker.getvalue():,.0f}') 
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log(f'SELL : 주가 {order.executed.price:,.0f}, '
                    f'수량 {order.executed.size:,.0f}, '
                    f'수수료 {order.executed.comm:,.0f}, '
                    f'자산 {cerebro.broker.getvalue():,.0f}') 
            self.bar_executed = len(self)
        elif order.status in [order.Canceled]:
            self.log('ORDER CANCELD')
        elif order.status in [order.Margin]:
            self.log('ORDER MARGIN')
        elif order.status in [order.Rejected]:
            self.log('ORDER REJECTED')
        self.order = None
   
    def next(self):
        if not self.position:
            if self.rsi < self.p.oversold:
                self.order = self.buy()
        else:
            if self.rsi > self.p.overbought:
                self.order = self.sell()
                
    def log(self, txt, dt=None):
        dt = self.datas[0].datetime.date(0)
        print(f'[{dt.isoformat()}] {txt}')

# 2) Download data using MariaDB
df = mk.get_daily_price(company, start_date)
# 컬럼 Rename (반드시 필요!)
df = df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})
# date 컬럼이 있을 경우 인덱스로 지정
if 'date' in df.columns:
    df.index = pd.to_datetime(df['date'])
#print(df)a

# 3) Set up Backtrader
data = bt.feeds.PandasData(dataname=df)

cerebro = bt.Cerebro()
cerebro.addstrategy(MyStrategy)

cerebro.adddata(data)
cerebro.broker.setcash(10000000)
cerebro.broker.setcommission(commission=0.0014)
cerebro.addsizer(bt.sizers.PercentSizer, percents=90)

# 4) Run backtest
print(f"Initial Portfolio Value : {cerebro.broker.getvalue():,.0f} KRW")
cerebro.run()
print(f"Final Portfolio Value   : {cerebro.broker.getvalue():,.0f} KRW")

# 5) Plot (avoid Javascript error)
cerebro.plot(iplot=False, style='candlestick', figsize=(20, 15)) 
#Backtrader’s plotting uses matplotlib + some JavaScript that Jupyter does not load correctly
#IDLE 실행하거나, %matplotlib inline 추가
