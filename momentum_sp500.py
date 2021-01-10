import pandas as pd
import numpy as np
import requests
import math
from scipy import stats
import xlsxwriter

from secrets import IEX_CLOUD_API_TOKEN

stocks = pd.read_csv('sp_500_stocks.csv')