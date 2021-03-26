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


class stock_alert():

    def __init__(self, ticker_name, profit_threshold, period):
        self.ticker_name = ticker_name
        self.profit_threshold = profit_threshold
        self.period = period
        self.live_stock_price = self.predictedPrice = self.profit = 0
        self.csv_dir = ""


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
        print(df.head())
        print(df['Datetime'].dtype)

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
        self.profit = self.predictedPrice - self.live_stock_price


    def send_email(self):
        sender_email = input("Enter the email address that you want to send FROM: ") #Sender's email 
        password = stdiomask.getpass(prompt="Enter the password of that email address: ", mask='*') #Sender's password
        email_to_send = input("Enter email address to send: ") #Receiver's email
        port = 465  # For SSL
        smtp_server = "smtp.gmail.com"
        receiver_email = email_to_send  # Enter receiver address
        # password = getpass.getpass("Type your password and press enter: ")
        message = """Subject: Buy {ticker_name} now!

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


# get user input for stock 
stock = stock_alert(
    str(input("Enter ticker: ")), float(input("Enter profit threshold: ")), str(input("Enter the number of days of prior data that you want to train the data on: ")+"d")
)

stock.get_live_price()
stock.get_csv()
stock.predict_price()


# if expected profit is greater than profit threshold, send email
if float(stock.profit) > float(stock.profit_threshold):
    stock.send_email()


