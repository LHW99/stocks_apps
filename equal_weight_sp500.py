import numpy as np
import pandas as pd 
# for making http requests
import requests
import xlsxwriter
import math

from secrets import IEX_CLOUD_API_TOKEN

stocks = pd.read_csv('sp_500_stocks.csv')

symbol = 'AAPL'
api_url = f"https://sandbox.iexapis.com/stock/{symbol}/quote/?token={IEX_CLOUD_API_TOKEN}"

print (api_url)