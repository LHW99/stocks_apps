import numpy as np
import pandas as pd
import xlsxwriter
import requests
from scipy import stats
import math

from secrets import IEX_CLOUD_API_TOKEN
stocks = pd.read_csv('sp_500_stocks.csv')

