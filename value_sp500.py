import numpy as np
import pandas as pd
import xlsxwriter
import requests
from scipy import stats
import math
from secrets import IEX_CLOUD_API_TOKEN

stocks = pd.read_csv('sp_500_stocks.csv')
symbol = 'aapl'
api_url = f'https://sandbox.iexapis.com/stable/stock/{symbol}/quote?token={IEX_CLOUD_API_TOKEN}'
data = requests.get(api_url).json()

price = data['latestPrice']
pe_ratio = data['peRatio']

# chunks takes a list + variable n and returns several lists, max 100 i.e. chunks a big list
def chunks(lst, n):
  for i in range(0, len(lst), n):
    yield lst[i:i + n]

symbol_groups = list(chunks(stocks['Ticker'], 100))
symbol_strings = []
for i in range(0, len(symbol_groups)):
  symbol_strings.append(','.join(symbol_groups[i]))

my_columns = ['Ticker', 'Price', 'P/E Ratio', 'Shares to Buy']

final_dataframe = pd.DataFrame(columns = my_columns)
for symbol_string in symbol_strings:
  batch_api_call = f'https://sandbox.iexapis.com/stable/stock/market/batch?symbols={symbol_string}&types=quote&token={IEX_CLOUD_API_TOKEN}'
  data = requests.get(batch_api_call).json()
  for symbol in symbol_string.split(','):
    final_dataframe = final_dataframe.append(
      pd.Series(
        [
          symbol,
          data[symbol]['quote']['latestPrice'],
          data[symbol]['quote']['peRatio'],
          0.0,
        ],
        index = my_columns,
      ),
      ignore_index = True
    )

print(final_dataframe)
