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

# remove glamour stocks
# sort, remove negative, trim, reset index, drop new index column
final_dataframe.sort_values('P/E Ratio', inplace = True)
final_dataframe = final_dataframe[final_dataframe['P/E Ratio'] > 0]
final_dataframe = final_dataframe[:50]
final_dataframe.reset_index(inplace = True)
final_dataframe.drop('index', axis=1, inplace = True)

def portfolio_input():
  global portfolio_size
  portfolio_size = input('Enter portfolio size:')

  try: 
    val = float(portfolio_size)
  except ValueError:
    print("That's not a number. \nTry again:")
    portfolio_size = input('Enter portfolio size:')

portfolio_size = 100000

position_size = float(portfolio_size)/len(final_dataframe.index)
for row in final_dataframe.index:
  final_dataframe.loc[row, 'Shares to Buy'] = math.floor(position_size/final_dataframe.loc[row, 'Price'])

# making a composite of valuation metrics for more realistic valuation
symbol = 'AAPL'
batch_api_call = f'https://sandbox.iexapis.com/stable/stock/market/batch?symbols={symbol}&types=quote,advanced-stats&token={IEX_CLOUD_API_TOKEN}'
data = requests.get(batch_api_call).json()

#P/E RATIO
pe_ratio = data[symbol]['quote']['peRatio']

# Price to book ratio
pb_ratio = data[symbol]['advanced-stats']['priceToBook']

# price to sale ratio
ps_ratio = data[symbol]['advanced-stats']['priceToSales']

# enterprise value divided by earnings before interest, taxes, depreciation, and amortization
enterprise_value = data[symbol]['advanced-stats']['enterpriseValue']
ebitda = data[symbol]['advanced-stats']['EBITDA']
ev_to_ebitda = enterprise_value/ebitda

# enterprice value divided by gross profit
gross_profit = data[symbol]['advanced-stats']['grossProfit']
ev_to_gp = enterprise_value/gross_profit