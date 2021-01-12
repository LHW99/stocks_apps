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

def portfolio_input():
  global portfolio_size
  portfolio_size = input('Enter the size of your portfolio:')

  try:
    float(portfolio_size)
  except ValueError:
    print('That is not a number. \nPlease try again.')
    portfolio_size = input('Enter the size of your portfolio:')

portfolio_size = 1000000

position_size = float(portfolio_size)/len(final_dataframe.index)
for i in range(0, len(final_dataframe)):
  final_dataframe.loc[i, 'Number of Shares to Buy'] = math.floor(position_size/final_dataframe.loc[i, 'Price'])

#print(final_dataframe[:50])

# identifying high quality momentum (hqm)
hqm_columns = [
  'Ticker',
  'Price',
  'Number of Shares to Buy',
  'One-Year Price Return',
  'One-Year Return Percentile',
  'Six-Month Price Return',
  'Six-Month Return Percentile',
  'Three-Month Price Return',
  'Three-Month Return Percentile',
  'One-Month Price Return',
  'One-Month Return Percentile',
]

hqm_dataframe = pd.DataFrame(columns = hqm_columns)

for symbol_string in symbol_strings:
  batch_api_call_url = F"https://sandbox.iexapis.com/stable/stock/market/batch?symbols={symbol_string}&types=price,stats&token={IEX_CLOUD_API_TOKEN}"
  data = requests.get(batch_api_call_url).json()
  for symbol in symbol_string.split(','):
    hqm_dataframe = hqm_dataframe.append(
      pd.Series(
        [
          symbol,
          data[symbol]['price'],
          'N/A',
          data[symbol]['stats']['year1ChangePercent'],
          'N/A',
          data[symbol]['stats']['month6ChangePercent'],
          'N/A',
          data[symbol]['stats']['month3ChangePercent'],
          'N/A',
          data[symbol]['stats']['month1ChangePercent'],
          'N/A',
        ],
        index = hqm_columns),
        ignore_index = True
      )

print(hqm_dataframe)