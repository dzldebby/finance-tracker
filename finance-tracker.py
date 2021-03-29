import yfinance as yf 
from yahoo_fin import stock_info as si
from datetime import datetime
import smtplib, ssl
import getpass
import pandas as pd
import numpy as np 
from sklearn.linear_model import LinearRegression
import os 
import stdiomask
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.techindicators import TechIndicators

class stock_alert():

    def __init__(self, ticker_name, profit_threshold, period, price_bought):
        self.ticker_name = ticker_name
        self.profit_threshold = profit_threshold
        self.period = period
        self.live_stock_price = self.predictedPrice = self.profit = 0
        self.csv_dir = ""
        self.price_bought = price_bought


    def get_live_price(self):
        stock = yf.Ticker(self.ticker_name)
        self.live_stock_price = si.get_live_price(self.ticker_name)
        print("Current price for " + str(self.ticker_name) + " is " + str(self.live_stock_price))


    def get_csv(self):
        data = yf.download(self.ticker_name, period=self.period, interval='5m')
        current_dir = os.path.join(os.getcwd(), 'data')
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
        self.profit = self.predictedPrice - self.live_stock_price


    def send_email(self):
        sender_email = input("Enter the email address that you want to send FROM: ") #Sender's email 
        password = stdiomask.getpass(prompt="Enter the password of that email address: ", mask='*') #Sender's password
        email_to_send = input("Enter email address to send: ") #Receiver's email
        port = 465  # For SSL
        smtp_server = "smtp.gmail.com"
        receiver_email = email_to_send  # Enter receiver address
        # password = getpass.getpass("Type your password and press enter: ")
        message = """Subject: Sell {ticker_name} now!

        The PREDICTED END OF DAY closing price of {ticker_name} is USD{predictedPrice}. 
        The CURRENT price is USD{live_stock_price}
        The estimated profit threshold is USD {profit} per lot.
        This is above the profit threshold you set of USD{profit_threshold}.
        
        PREDICTED END OF DAY price is generated through regression of the High, Low, and Volume for {ticker_name} the past 5 days of data. Sent from the python script I built."""


        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.format(ticker_name=self.ticker_name, live_stock_price=self.live_stock_price, predictedPrice=float(self.predictedPrice), profit=float(self.predictedPrice)-float(self.live_stock_price), profit_threshold=self.profit_threshold))
        print("Email sent")    


# # get user input for stock 
# stock = stock_alert(
#     str(input("Enter ticker: ")), 
#     float(input("Enter profit threshold: ")), 
#     str(input("Enter the number of days of prior data that you want to train the data on: ")+"d"),
#     float(input("Enter price you bought the stock for: "))
# )

# stock.get_live_price()
# stock.get_csv()
# stock.predict_price()


# # if expected profit is greater than profit threshold, send email
# if float(stock.profit) > float(stock.profit_threshold):
#     stock.send_email()


###########################################################################


### BB CONDITION ## 


ti = TechIndicators(key='XM023JSA9B0G33XD', output_format='pandas')
bbdata, meta_data = ti.get_bbands(symbol='MSFT', interval='60min', time_period=60)

bbdata.reset_index(inplace=True)


bbdata['date'] = pd.to_datetime(bbdata['date'], utc=True)
bbdata = bbdata.resample('D', on='date').mean().sort_values(by='date', ascending=False)

print("bbdata", bbdata)


# bbdata_upper = bbdata[['date', 'Real Upper Band']]
# bbdata_middle = bbdata[['date', 'Real Middle Band']]
# bbdata_lower = bbdata[['date', 'Real Lower Band']]


bb2days_middle = bbdata.iloc[2,0]
bb2days_upper = bbdata.iloc[2,1]
bb2days_lower = bbdata.iloc[2,2]


current_dir = os.path.join(os.getcwd(), 'data/MSFT.csv')
df = pd.read_csv(current_dir)
df = df.sort_values(by='Datetime', ascending=False)
df['Datetime'] = pd.to_datetime(df['Datetime'], utc=True)
df_day = df.resample('D', on='Datetime').mean().sort_values(by='Datetime', ascending=False).head()

price2days = df_day.iloc[2,3]
price1day = df_day.iloc[1,3]
currentprice = si.get_live_price('MSFT')

# if price2days > bb2days_upper 
    # if price2days > price1day AND price1day > current, SELL
    # if price2days < price1day AND price1day < current, BUY
if price2days > bb2days_upper or price2days < bb2days_lower or price2days == bb2days_middle:
    if price2days > price1day and price1day > currentprice:
        print("Sell")
    if price2days < price1day and price1day < currentprice:
        print("Buy")


### EMA CONDITION 

daily_emadata, meta_data = ti.get_ema(symbol='MSFT', interval='daily', time_period=20, series_type='close')
weekly_emadata, meta_data = ti.get_ema(symbol='MSFT', interval='weekly', time_period=20, series_type='close')
monthly_emadata, meta_data = ti.get_ema(symbol='MSFT', interval='monthly', time_period=20, series_type='close')



print(daily_emadata.head())