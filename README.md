# Stock Tracker

*Python module to get stock data, evaluate buy/sell, and send an email to the user with the buy/sell decision*

Python module to retrieve the following information based on the ticker provided by the user, from Alpha Vantage and Yahoo Finance: 
* Current stock price
* Bollinger Band
* Expontential Moving Average (EMA)
* Relative Strength Index 

The expected price of the stock is also predicted using regression of the HIGH, LOW and VOLUME at the point of running. 

Based on a set of selection criteria, an email alert is sent to the user urging the user to buy / sell the stock, with the following information: 
* Predicted price of the stock 
* Current stock price 
* Expected profit

## Selection Criteria

### 1. Bollinger Band 

Recommend to buy when: 
Current stock price > upper Bollinger Band and price goes up for 2 days consecutively 
Current stock price < lower Bollinger Band and price goes up for 2 days consecutively 
Recommend to sell when: 
Current stock price > upper Bollinger Band and price goes down for 2 days consecutively
Current stock price < lower Bollinger Band and price goes down for 2 days consecutively 

### 2. Exponential Moving Average 

Recommend to buy when: 
Weekly moving average < weekly moving average or monthly moving average
Recommend to sell when: 
All else 

### 3. Relative Strength Index

Recommend to buy when: 
25 < RSI < 50 
Recommend to sell when: 
All else 

### 4. Profit 

Recommend to buy when: 
Predicted stock price > current stock price 
Recommend to sell when: 
Profit > price bought 

## Usage 

1. Install requirements
```python
pip install requirements.txt
```

