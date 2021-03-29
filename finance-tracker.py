import yfinance as yf 
from yahoo_fin import stock_info as si
from datetime import datetime
import smtplib, ssl
import getpass
import pandas as pd
import numpy as np 
import os 
import stdiomask
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.techindicators import TechIndicators
from sklearn import datasets, linear_model

from sklearn.linear_model import LinearRegression

class stock_alert():

    def __init__(self, ticker_name, profit_threshold, period, price_bought):
        self.ticker_name = ticker_name
        self.profit_threshold = profit_threshold
        self.period = period
        self.live_stock_price = self.predictedPrice = self.profit = 0
        self.csv_dir = self.order = ""
        self.price_bought = price_bought
        self.bb_condition_buy = self.bb_condition_sell = self.ema_condition_buy = self.ema_condition_sell = self.rsi_condition_sell = self.rsi_condition_buy = False 


    def get_live_price(self):
        stock = yf.Ticker(self.ticker_name)
        self.live_stock_price = si.get_live_price(self.ticker_name)
        print("Current price for " + str(self.ticker_name) + " is " + str(self.live_stock_price))
        print(self.price_bought)


    def get_csv(self):
        data = yf.download(self.ticker_name, period=self.period, interval='5m')
        current_dir = os.path.join(os.getcwd(), 'finance-tracker\data')
        self.csv_dir = os.path.join(current_dir, self.ticker_name + '.csv')
        data.to_csv(self.csv_dir)

    def predict_price(self):
        # get csv and sort
        df = pd.read_csv(self.csv_dir)
        df = df.sort_values(by='Datetime', ascending=False)
        df['Datetime'] = pd.to_datetime(df['Datetime'], errors='raise', utc=True)
        # print(df.head())
        # print(df['Datetime'].dtype)

        #use High, Low, Volume as variables for prediction 
        variables = df[['High', 'Low', 'Volume']]
        price = df[['Close']]

        # getting day's high, low, volume 
        df_day = df.resample('D', on='Datetime').mean().sort_values(by='Datetime', ascending=False).head(1)
        print(df_day)

        #model fit 
        model = LinearRegression().fit(variables, price)

        predictors = np.array([df_day['High'], df_day['Low'], df_day['Volume']], dtype=object)
        predictors = predictors.reshape(1,-1)

        #predict 
        self.predictedPrice = model.predict(predictors)
        print("Predicted price:", self.predictedPrice)

        # if user is selling, profit is calculated by predicted - price_bought, otherwise profit is calculated by predicted price - current price 
        if self.price_bought > 0:
            self.profit = self.predictedPrice - self.price_bought
        else:
            self.profit = self.predictedPrice - self.live_stock_price

    def check_bb(self):
        # get bollinger band data
        ti = TechIndicators(key='YOUR_API_KEY', output_format='pandas')
        bbdata, meta_data= ti.get_bbands(symbol='MSFT', interval='60min', time_period=60)

        bbdata.reset_index(inplace=True)
        bbdata['date'] = pd.to_datetime(bbdata['date'], utc=True)
        bbdata = bbdata.resample('D', on='date').mean().sort_values(by='date', ascending=False)

        bb2days_middle = bbdata.iloc[2,0]
        bb2days_upper = bbdata.iloc[2,1]
        bb2days_lower = bbdata.iloc[2,2]

        df = pd.read_csv(self.csv_dir)
        df = df.sort_values(by='Datetime', ascending=False)
        df['Datetime'] = pd.to_datetime(df['Datetime'], utc=True)
        df_day = df.resample('D', on='Datetime').mean().sort_values(by='Datetime', ascending=False).head()

        # get price day from 2 days and 1 day ago 
        price2days = df_day.iloc[2,3]
        price1day = df_day.iloc[1,3]
        currentprice = df_day.iloc[0,3]

        # if price2days > bb2days_upper 
            # if price2days > price1day AND price1day > current, SELL
            # if price2days < price1day AND price1day < current, BUY
        if price2days > bb2days_upper or price2days < bb2days_lower or price2days == bb2days_middle:
            if price2days > price1day and price1day > currentprice:
                self.bb_condition_sell = True
            if price2days < price1day and price1day < currentprice:
                self.bb_condition_buy = True
            
    def sort_values_date(self,df):
        return df.sort_values(by='date', ascending=False).iloc[0,1]

    def check_ema(self):
        # daily_emadata, meta_data = ti.get_ema(symbol='MSFT', interval='daily', time_period=20, series_type='close')
        # weekly_emadata, meta_data = ti.get_ema(symbol='MSFT', interval='weekly', time_period=20, series_type='close')
        # monthly_emadata, meta_data = ti.get_ema(symbol='MSFT', interval='monthly', time_period=20, series_type='close')

        # daily_emadata = daily_emadata.to_csv('dailyema.csv')
        # weekly_emadata = weekly_emadata.to_csv('weeklyema.csv')
        # monthly_emadata = monthly_emadata.to_csv('monthlyema.csv')

        daily_emadata = pd.read_csv('dailyema.csv')
        weekly_emadata = pd.read_csv('weeklyema.csv')
        monthly_emadata = pd.read_csv('monthlyema.csv')

        # get last value
        sorted_daily_emadata = stock.sort_values_date(daily_emadata)
        sorted_weekly_emadata = stock.sort_values_date(weekly_emadata)
        sorted_monthly_emadata = stock.sort_values_date(monthly_emadata)
        
        print("sorted", sorted_daily_emadata)

        if sorted_daily_emadata < sorted_weekly_emadata or sorted_daily_emadata < sorted_monthly_emadata or sorted_weekly_emadata < sorted_monthly_emadata:
            self.ema_condition_buy = True
        else:
            self.ema_condition_sell = True

        print("ëma", self.ema_condition_buy)


    def check_rsi(self):
        # rsidata, meta_data = ti.get_rsi(symbol='MSFT', interval='1min',time_period=60, series_type='close')
        # rsidata = rsidata.to_csv('rsi.csv')
        rsidata = pd.read_csv('rsi.csv')
        currentrsi = stock.sort_values_date(rsidata)

        print("currentrsi", currentrsi)

        if 25 <= currentrsi <= 50:
            self.rsi_condition_buy = True 
        else:
            self.rsi_condition_sell = True

           

    def send_email(self, order):
        sender_email = input("Enter the email address that you want to send FROM: ") #Sender's email 
        password = stdiomask.getpass(prompt="Enter the password of that email address: ", mask='*') #Sender's password
        email_to_send = input("Enter email address to send: ") #Receiver's email
        port = 465  # For SSL
        smtp_server = "smtp.gmail.com"
        receiver_email = email_to_send  # Enter receiver address
        # password = getpass.getpass("Type your password and press enter: ")
        message = """Subject: {order} {ticker_name} now!

        The PREDICTED END OF DAY closing price of {ticker_name} is USD{predictedPrice}. 
        The CURRENT price is USD{live_stock_price}
        The estimated profit threshold is USD {profit} per lot.
        This is above the profit threshold you set of USD{profit_threshold}.
        
        PREDICTED END OF DAY price is generated through regression of the High, Low, and Volume for {ticker_name} the past 5 days of data. Sent from the python script I built."""


        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.format(ticker_name=self.ticker_name, order = self.order, live_stock_price=self.live_stock_price, predictedPrice=float(self.predictedPrice), profit=float(self.predictedPrice)-float(self.live_stock_price), profit_threshold=self.profit_threshold))
        print("Email sent")    


# # get user input for stock 

check = int(input("Enter 0 if buying and 1 if selling: "))

stock = stock_alert(
    str(input("Enter ticker: ")), 
    float(input("Enter profit threshold: ")), 
    str(input("Enter the number of days of prior data that you want to train the data on: ")+"d"),
    float(input("Enter price you bought the stock for: ")) if check == 1 else 0
)

stock.get_live_price()
stock.get_csv()
stock.predict_price()
stock.check_bb()
stock.check_ema()
stock.check_rsi()

# if expected profit is greater than profit threshold and all 3 conditions are to sell (bb, ema, and rsi) send email
if float(stock.profit) > float(stock.profit_threshold) and stock.bb_condition_sell and stock.ema_condition_sell and stock.rsi_condition_sell:
    stock.order = "SELL" 
    stock.send_email(stock.order)

# if expected profit is greater than profit threshold and all 3 conditions are to buy (bb, ema, and rsi) send email
if float(stock.profit) > float(stock.profit_threshold) and stock.bb_condition_buy and stock.ema_condition_buy and stock.rsi_condition_sell:
    stock.order = "BUY" 
    stock.send_email(stock.order)
