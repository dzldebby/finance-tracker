import yfinance as yf 
from yahoo_fin import stock_info as si
from datetime import datetime
import smtplib, ssl
import getpass
import pandas as pd
import numpy as np 
from sklearn.linear_model import LinearRegression
import tensorflow as tf


def get_ticker():
    global ticker_name, profit_threshold
    # ticker_name = input("Enter ticker: ")
    ticker_name = 'MSFT'
    # profit_threshold = input("Enter profit threshold: ")
    profit_threshold = 1.0

def get_live_price(ticker_name):
    global live_stock_price
    stock = yf.Ticker(ticker_name)
    live_stock_price = si.get_live_price(ticker_name)
    print("Current price for " + str(ticker_name) + " is " + str(live_stock_price))


def get_csv():
    data = yf.download(ticker_name, period='5d', interval='5m')
    data.to_csv(ticker_name + '.csv')

def send_email():
    global email_to_send
    # email_to_send = input("Enter email address to send: ")
    email_to_send = 'the.idiosyncrasies@gmail.com'
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = "the.idiosyncrasies@gmail.com"  # Enter your address
    password = 'g0k7yp3f'
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
        server.sendmail(sender_email, receiver_email, message.format(ticker_name=ticker_name, live_stock_price=live_stock_price, predictedPrice=float(predictedPrice), profit=float(predictedPrice)-float(live_stock_price), profit_threshold=profit_threshold))
    print("Email sent")

def predict_price():
    global predictedPrice, profit
    # get csv
    df = pd.read_csv(ticker_name + '.csv', parse_dates=['Datetime'])
    df = df.sort_values(by='Datetime', ascending=False)

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
    predictedPrice = model.predict(predictors)
    profit = predictedPrice - live_stock_price
    print(predictedPrice)

get_ticker()
get_live_price(ticker_name)
get_csv()
predict_price()

# if predicted price < price threshold 

if  profit > float(profit_threshold): 
    send_email()


