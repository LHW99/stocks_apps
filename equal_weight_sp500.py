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

# dataframe for stocks 
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

def chunks(lst, n):
  # yield successive n-sized chunks from lst.
  for i in range(0, len(lst), n):
    yield lst[i:i+n]

symbol_groups = list(chunks(stocks['Ticker'], 100))
symbol_strings = []
for i in range(0, len(symbol_groups)):
  symbol_strings.append(','.join(symbol_groups[i]))
  #print(symbol_strings[i])

for symbol_string in symbol_strings:
  batch_api_call_url = f"https://sandbox.iexapis.com/stable/stock/market/batch?symbols={symbol_string}&types=quote&token={IEX_CLOUD_API_TOKEN}"
  data = requests.get(batch_api_call_url).json()
  for symbol in symbol_string.split(','):
    final_dataframe = final_dataframe.append(
      pd.Series(
        [
          symbol,
          data[symbol]['quote']['latestPrice'],
          data[symbol]['quote']['marketCap'],
          'N/A',
        ],
        index = my_columns
      ),
      ignore_index = True,
    )

portfolio_size = input('Enter the value of your portfolio:')

try:
  val = float(portfolio_size)
except ValueError:
  print("That's not a number \nPlease try again:")
  portfolio_size = input('Enter the value of your portfolio:')
  val = float(portfolio_size)

position_size = val/len(final_dataframe.index)
for i in range(0, len(final_dataframe.index)):
  # easy accessing rows/columns in pandas
  final_dataframe.loc[i, 'Number of Shares to Buy'] = math.floor(position_size/final_dataframe.loc[i, 'Stock Price'])

print(final_dataframe)