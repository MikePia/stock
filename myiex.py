'''
A module to access iex API. From the REStful source. No wrapeere packages
@author: Mike Petersen
@creation_date: 12/20/18
'''
import datetime as dt
import pandas as pd
import requests
# pylint: disable=C0103


apiurl = 'https://api.iextrading.com/1.0/stock/aapl/chart/5y?format=json'
newsurl = 'https://api.iextrading.com/1.0/stock/aapl/batch?types=quote,news,chart&range=1m&last=10'
apidocs = 'https://iextrading.com/developer/docs/#getting-started'
termsofuse = 'https://iextrading.com/api-exhibit-a/'

BASE_URL = 'https://api.iextrading.com/1.0'

# Follows the Chart API
# API = f"/stock/{symbol}/{range}/"
RANGE = ['5y', '2y', '1y', 'ytd', '6m', '3m',
         '1m', '1d', 'date/{date}', 'dynamic']
# Minute data is only provided by 1d, assumed by a given date/YYYYMMdd,
# or determined by dynamic, and is only available for a trailing 30 days

# Provided as documentation in code. Could use it to validate key if provided by user.
PARAMS = {'chartReset': True,                           # Default False
          'chartSimplify': True,                        # Default False
          'chartInterval': [1, 2, 5, 10, 15, 30, 60],    # Will accept any int
          'changeFromClose': True,                      # Default False
          'chartLast': 100                               # Will accept any int
          }

DAY_COLUMNS = ['minute', 'marketAverage', 'marketNotional', 'marketNumberOfTrades', 'marketOpen',
               'marketClose', 'marketHigh', 'marketLow', 'marketVolume', 'marketChangeOverTime',
               'average', 'notional', 'numberOfTrades', 'simplifyFactor']

ALL_COLUMNS = ['high', 'low', 'volume', 'label',
               'changeOverTime', 'date', 'open', 'close']

# vwap here makes no sen=se as it has no meaning except on the intraday chart. Do they provide
# a single vwap value for each day?

XDAY_COLUMNS = ['unadjustedVolume', 'change', 'changePercent', 'vwap']


def get_trading_chart(symb, start=None, end=None, minutes=None, theDate=None):
    '''
    Limited to getting minute data intended to chart day trades.
    :params symb: The stock ticker
    :parms start: A time string formatted hh:mm to indicate the begin time for the data
    :params end: A time string formatted hh:mm to indicate the end time for the data
    :params minutes: An int for the candle time, 5 minute, 15 minute etc. Any int is accepted.
    :params theDate: A date string formatted yyyymmdd. It will default to today
    :returns: A DataFrame with indexed my minutes, columns ohlcv and date. The default
                is the most recent trading day
    '''
    url = "chart"
    rng = "1d"
    if theDate:
        rng = f"date/{theDate}"
    params = {}
    if minutes:

        params['chartInterval'] = minutes
    params['filter'] = 'minute,open,high,low,close,average,volume,date'

    request_url = f"{BASE_URL}/stock/{symb}/{url}/{rng}"

    response = requests.get(request_url, params=params)
    if response.status_code != 200:
        raise Exception(
            f"{response.status_code}: {response.content.decode('utf-8')}")
    result = response.json()

    df = pd.DataFrame(result)

    df.set_index('minute', inplace=True)

    df = df.loc[df.index >= start] if start else df
    df = df.loc[df.index <= end] if end else df
    return df
# get_trading_chart("MSFT", "10:23", "16:37", minutes=2, theDate="20181214").head()


BASE_URL = 'https://api.iextrading.com/1.0'


def get_historical_chart(symb, start=None, end=None):
    '''Gets daily information
    :parms:symbo: The stock ticker
    :params:start: Starting Date. A Datetime object
    :params:end: Ending date. A Datetime object
    '''
    now = dt.datetime.today()

    rng_d = {'5y': 60, '2y': 24, '1y': 12,
             '6m': 6, '3m': 3, '1m': 1}

    params = {}
    url = "chart"

    # Set the default to 2 years
    rng = '5y'
    # months = 60
    if start:
        # This will round up to get more data when its close to a limit
        reqmonths = (((now - start).days)/30) + 1
        if reqmonths > 60:
            print('You have requested data beginning {}'.format(
                start.strftime("%B,%Y")))
            print('This API is limited to 5 years historical data.')
        for key in rng_d:
            if rng_d[key] > reqmonths:
                rng = key
            else:
                break
    print(rng, start)
    params['filter'] = 'date,minute,open,high,low,close,average,volume'

    request_url = f"{BASE_URL}/stock/{symb}/{url}/{rng}"
    print(request_url)

    response = requests.get(request_url, params=params)
    if response.status_code != 200:
        raise Exception(
            f"{response.status_code}: {response.content.decode('utf-8')}")
    print(response.url)

    result = response.json()

    df = pd.DataFrame(result)

    df.set_index('date', inplace=True)
    if start:
        start = start.strftime("%Y-%m-%d")
        df = df.loc[df.index >= start]
    if end:
        end = end.strftime("%Y-%m-%d")
        df = df.loc[df.index <= end]
    return df
# df = get_historical_chart('AAPL', dt.datetime(2013,6,6), dt.datetime(2018,10,4))
# print (df.head(5))
# print (df.tail(5))
