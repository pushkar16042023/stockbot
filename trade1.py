
from lumibot.brokers import Alpaca
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader
from lumibot.traders import *
from datetime import datetime
from alpaca_trade_api import REST
from timedelta import Timedelta
from finberte import estimate_sentiment

import os
load_dotenv()

API_KEY = os.getenv("API_KEYY")
API_SECRET = os.getenv("API_SECRETT")
BASE_URL = os.getenv("BASE_URLL")

ALPACA_CONFIG = {
    "API_KEY":API_KEY,
    "API_SECRET":API_SECRET,
    "PAPER":True
}
class MyStrategy(Strategy):
    def initialize(self,symbol:str="SPY",cash_at_risk:float=.5):
        self.symbol = symbol
        self.sleeptime = "1D"
        self.last_trade = None
        self.cash_at_risk = cash_at_risk
        self.api = REST(base_url = BASE_URL,key_id = API_KEY,secret_key = API_SECRET)
        
    def position_sizing(self):
        cash = self.get_cash()
        last_price = self.get_last_price(self.symbol)
        quantity = round(cash*self.cash_at_risk/last_price,0)
        return cash,last_price,quantity
    
    def get_dates(self):
        today = self.get_datetime()
        days_three = today - Timedelta(days=3)
        return today.strftime('%Y-%m-%d'),days_three.strftime('%Y-%m-%d')
    
    def get_sentiment(self):
        today,days_three = self.get_dates()
        news = self.api.get_news(symbol = self.symbol,start = days_three,end = today)
        news = [ev.__dict__["_raw"]["headline"] for ev in news]
        probability,sentiment = estimate_sentiment(news)
        return probability,sentiment
    def on_trading_iteration(self):
        cash,last_price,quantity = self.position_sizing()
        probability,sentiment = self.get_sentiment()
        if cash>last_price:
            if sentiment == "positive" and probability > 0.98: 
                if self.last_trade == "sell":
                    self.sell_all()            
                order = self.create_order(
                    self.symbol,
                    quantity,
                    "buy",  
                    type = "bracket",
                    take_profit_price = last_price*1.20,
                    stop_loss_price = last_price*.95
                )
                self.submit_order(order)
                self.last_trade ="buy"
            elif sentiment == "negetive" and probability > 0.98: 
                if self.last_trade == "buy":
                    self.sell_all()            
                order = self.create_order(
                    self.symbol,
                    quantity,
                    "sell",  
                    type = "bracket",
                    take_profit_price = last_price*0.8,
                    stop_loss_price = last_price*1.05
                )
                self.submit_order(order)
                self.last_trade ="sell"
            
      
start_date = datetime(2020,1,1)
end_date = datetime(2023,12,31)        
broker = Alpaca(ALPACA_CONFIG)
strategy = MyStrategy(name = 'mlstrat',broker = broker,parameters = {"symbol":"SPY","cash_at_risk":.5})
strategy.backtest(
    YahooDataBacktesting,
    start_date,
    end_date,
    parameters={"symbol":"SPY"}
    
)