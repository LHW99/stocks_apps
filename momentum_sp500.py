import pandas as pd
import numpy as np
import requests
import math
from scipy import stats
import xlsxwriter

from secrets import IEX_CLOUD_API_TOKEN

stocks = pd.read_csv('sp_500_stocks.csv')
symbol = 'AAPL'

api_url = f"https://sandbox.iexapis.com/stable/stock/{symbol}/stats?token={IEX_CLOUD_API_TOKEN}"
data = requests.get(api_url).json()

def chunks(lst, n):
  for i in range(0, len(lst), n):
    yield lst[i:i + n]

symbol_groups = list(chunks(stocks['Ticker'], 100))
symbol_strings = []
for i in range(0, len(symbol_groups)):
  symbol_strings.append(','.join(symbol_groups[i]))

# make columns
my_columns = ['Ticker', 'Price', 'One-Year Price Return', 'Number of Shares to Buy']

# create empty dataframe with premade columns
final_dataframe = pd.DataFrame(columns = my_columns)

# call batch api to fill empty dataframe
for symbol_string in symbol_strings:
  batch_api_call_url = F"https://sandbox.iexapis.com/stable/stock/market/batch?symbols={symbol_string}&types=price,stats&token={IEX_CLOUD_API_TOKEN}"
  data = requests.get(batch_api_call_url).json()
  for symbol in symbol_string.split(','):
    final_dataframe = final_dataframe.append(
      pd.Series(
        [
          symbol, 
          data[symbol]['price'],
          data[symbol]['stats']['year1ChangePercent'],
          'N/A'
        ],
        index = my_columns),
        ignore_index = True
      )

# remove low-momentum stocks
# inplace modifies original dataframe
final_dataframe.sort_values('One-Year Price Return', ascending = False, inplace = True)
# resets index numbers to go from 0-49
final_dataframe.reset_index(inplace = True)
print(final_dataframe[:50])
