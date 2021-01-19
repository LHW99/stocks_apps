import numpy as np
import pandas as pd
import xlsxwriter
import requests
from scipy.stats import percentileofscore as score
from statistics import mean
import math
from secrets import IEX_CLOUD_API_TOKEN

stocks = pd.read_csv('sp_500_stocks.csv')
portfolio_size = 100000

def chunks(lst, n):
  for i in range(0, len(lst), n):
    yield lst[i:i + n]

symbol_groups = list(chunks(stocks['Ticker'], 100))
symbol_strings = []
for i in range(0, len(symbol_groups)):
  symbol_strings.append(','.join(symbol_groups[i]))

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
rv_dataframe.sort_values('RV Score', ascending = True, inplace = True)
rv_dataframe = rv_dataframe[:5]
rv_dataframe.reset_index(drop = True, inplace = True)

# shares to buy
position_size = float(portfolio_size)/len(rv_dataframe.index)

for row in rv_dataframe.index:
  rv_dataframe.loc[row, 'Shares to Buy'] = math.floor(position_size/rv_dataframe.loc[row, 'Price'])

# make excel
writer = pd.ExcelWriter('value_strategy.xlsx', engine = 'xlsxwriter')
rv_dataframe.to_excel(writer, sheet_name = 'Value Strategy', index = False)

background_color = '#0a0a23'
font_color = '#ffffff'

string_format = writer.book.add_format(
  {
    'font_color': font_color,
    'bg_color': background_color,
    'border': 1
  }
)

dollar_format = writer.book.add_format(
  {
    'num_format': '$0.00',
    'font_color': font_color,
    'bg_color': background_color,
    'border': 1
  }
)

integer_format = writer.book.add_format(
  {
    "num_format": '0.0',
    'font_color': font_color,
    'bg_color': background_color,
    'border': 1
  }
)

percent_format = writer.book.add_format(
  {
    "num_format": '0.0%',
    'font_color': font_color,
    'bg_color': background_color,
    'border': 1
  }
)

column_formats = {
  'A': ['Ticker', string_format],
  'B': ['Price', dollar_format],
  'C': ['Shares to Buy', integer_format],
  'D': ['P/E Ratio', integer_format],
  'E': ['P/E Percentile', percent_format],
  'F': ['Price to Book Ratio', integer_format],
  'G': ['PB Percentile', percent_format],
  'H': ['Price to Sales Ratio', integer_format],
  'I': ['PS Percentile', percent_format],
  'J': ['EV/EBITDA', integer_format],
  'K': ['EV/EBITDA Percentile', percent_format],
  'L': ['EV/GP', integer_format],
  'M': ['EV/GP Percentile', percent_format],
  'N': ['RV Score', integer_format],
}

for column in column_formats.keys():
  writer.sheets['Value Strategy'].set_column(f'{column}:{column}', 25, column_formats[column][1])
  writer.sheets['Value Strategy'].write(f'{column}1', column_formats[column][0], column_formats[column][1])
#writer.save()