import numpy as np
import pandas as pd 
# for making http requests
import requests
# for excel things
import xlsxwriter
import math

from secrets import IEX_CLOUD_API_TOKEN

stocks = pd.read_csv('sp_500_stocks.csv')

my_columns = [ 'Ticker', 'Stock Price', 'Market Capitalization', 'Number of Shares to Buy' ]
final_dataframe = pd.DataFrame(columns = my_columns)

for stock in stocks['Ticker'][:5]:
  api_url = f"https://sandbox.iexapis.com/stable/stock/{stock}/quote/?token={IEX_CLOUD_API_TOKEN}"
  data = requests.get(api_url).json()
  final_dataframe = final_dataframe.append(
    pd.Series(
      [
        stock,
        data['latestPrice'],
        data['marketCap'],
        'N/A'
      ],
      index = my_columns,
    ),
    ignore_index=True,
  )

print (final_dataframe)