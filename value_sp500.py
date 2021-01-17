import numpy as np
import pandas as pd
import xlsxwriter
import requests
from scipy.stats import percentileofscore as score
from statistics import mean
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
batch_api_call = f'https://sandbox.iexapis.com/stable/stock/market/batch?symbols=AAPL&types=quote,advanced-stats&token={IEX_CLOUD_API_TOKEN}'
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

# making robust value
rv_columns = [
  'Ticker',
  'Price',
  'Shares to Buy',
  'P/E Ratio',
  'P/E Percentile',
  'Price to Book Ratio',
  'PB Percentile',
  'Price to Sales Ratio',
  'PS Percentile',
  'EV/EBITDA',
  'EV/EBITDA Percentile',
  'EV/GP',
  'EV/GP Percentile',
  'RV Score',
]

# making rv dataframe
rv_dataframe = pd.DataFrame(columns = rv_columns)

for symbol_string in symbol_strings:
  batch_api_call = f'https://sandbox.iexapis.com/stable/stock/market/batch?symbols={symbol_string}&types=quote,advanced-stats&token={IEX_CLOUD_API_TOKEN}'
  data = requests.get(batch_api_call).json()
  for symbol in symbol_string.split(','):
    enterprise_value = data[symbol]['advanced-stats']['enterpriseValue']
    ebitda = data[symbol]['advanced-stats']['EBITDA']
    gross_profit = data[symbol]['advanced-stats']['grossProfit']

    try:
      ev_to_ebitda = enterprise_value/ebitda
    except TypeError:
      ev_to_ebitda = np.NaN

    try:
      ev_to_gp = enterprise_value/gross_profit
    except TypeError:
      ev_to_gp = np.NaN

    rv_dataframe = rv_dataframe.append(
      pd.Series(
        [
          symbol,
          data[symbol]['quote']['latestPrice'],
          0.0,
          data[symbol]['quote']['peRatio'],
          0.0,
          data[symbol]['advanced-stats']['priceToBook'],
          0.0,
          data[symbol]['advanced-stats']['priceToSales'],
          0.0,
          ev_to_ebitda,
          0.0,
          ev_to_gp,
          0.0,
          0.0,
        ],
        index = rv_columns
      ),
      ignore_index = True
    )

# deal with missing data in dataframe
for column in ['P/E Ratio', 'Price to Book Ratio', 'Price to Sales Ratio', 'EV/EBITDA', 'EV/GP']:
  rv_dataframe[column].fillna(rv_dataframe[column].mean(), inplace = True)

rv_dataframe[rv_dataframe.isnull().any(axis=1)]

# make dictionary of metrics for percentile scores
metrics = {
  'P/E Ratio': 'P/E Percentile',
  'Price to Book Ratio': 'PB Percentile',
  'Price to Sales Ratio': 'PS Percentile',
  'EV/EBITDA': 'EV/EBITDA Percentile',
  'EV/GP': 'EV/GP Percentile',
}

# calculate percentile scores and modify existing rv_dataframe
for metric in metrics.keys():
  for row in rv_dataframe.index:
    rv_dataframe.loc[row, metrics[metric]] = score( rv_dataframe[metric], rv_dataframe.loc[row, metric] )

# calculating rv score by taking the mean of all percentile scores
for row in rv_dataframe.index:
  value_percentiles = []
  for metric in metrics.keys():
    value_percentiles.append(rv_dataframe.loc[row, metrics[metric]])
  rv_dataframe.loc[row, 'RV Score'] = mean(value_percentiles)

# selecting 50 best value stocks
rv_dataframe.sort(values('RV Score', ascending = True, inplace = True))
rv_dataframe = rv_dataframe[:50]
rv_dataframe.reset_index(drop = True, inplace = True)




