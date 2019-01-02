'''
Alphavantage stuff using their own RESTful  API
@author: Mike Petersens
@creation_date:2018-12-11
'''
# pylint: disable = C0103
# pylint: disable = C0301

import datetime as dt
import requests
import pandas as pd
from stock.picklekey import getKey
# import pickle

EXAMPLES = {
    'api1': 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=MSFT&interval=5min&apikey=VPQRQR8VUQ8PFX5B',
    'api2': 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=MSFT&interval=5min&outputsize=full&apikey=VPQRQR8VUQ8PFX5B',
    'api3': 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=MSFT&apikey=VPQRQR8VUQ8PFX5B',
    'api4': 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=MSFT&outputsize=full&apikey=VPQRQR8VUQ8PFX5B',
    'api5': 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=MSFT&apikey=VPQRQR8VUQ8PFX5B',
    'web_site': 'https://www.alphavantage.co/documentation/#intraday'
}

def getkey():
    '''My Personal key'''
    k = getKey('alphavantage')
    return k


BASE_URL = 'https://www.alphavantage.co/query?'

# Stock only here, FX and bit currency are available. Also, many other technical indicators
# are provided beyond ma and vwap
FUNCTION = {'intraday':  'TIME_SERIES_INTRADAY',
            'daily': 'TIME_SERIES_DAILY',
            'dailyadj': 'TIME_SERIES_DAILY_ADJUSTED',
            'weekly': 'TIME_SERIES_WEEKLY',
            'weeklyadj': 'TIME_SERIES_WEEKLY_ADJUSTED',
            'monthly': 'TIME_SERIES_MONTHLY',
            'monthlyadj': 'TIME_SERIES_MONTHLY_ADJUSTED',
            'quote': 'GLOBAL_QUOTE',
            'search': 'SYMBOL_SEARCH',
            'sma': 'SMA',
            'ema': 'EMA',
            'atr': 'ATR'
            }

# The redundancy serves as documentation in code. These are the params required for each function
PARAMS = {'intraday':  ['symbol', 'datatype', 'apikey', 'outputsize', 'interval'],
          'daily':  ['symbol', 'datatype', 'apikey', 'outputsize'],
          'dailyadj':  ['symbol', 'datatype', 'apikey', 'outputsize'],
          'weekly':  ['symbol', 'datatype', 'apikey'],
          'weeklyadj':  ['symbol', 'datatype', 'apikey'],
          'monthly':  ['symbol', 'datatype', 'apikey'],
          'monthlyadj':  ['symbol', 'datatype', 'apikey'],
          'quote':  ['symbol', 'datatype', 'apikey'],
          'search':  ['keywords', 'datatype', 'apikey'],
          'sma':  ['symbol', 'datatype', 'apikey', 'interval', 'time_period', 'series_type'],
          'ema':  ['symbol', 'datatype', 'apikey', 'interval', 'time_period', 'series_type'],
          'atr':  ['symbol', 'datatype', 'apikey', 'interval', 'time_period']
          }

DATATYPES = ('json', 'csv')       # json is default
APIKEY = getKey('alphavantage')['key']
OUTPUTSIZE = ('compact', 'full')  # compact is default
INTERVAL = ('1min', '5min', '15min', '30min',
            '60min', 'daily', 'weekly', 'monthly')


def getapis():
    '''some RESTful APIS'''
    return[EXAMPLES['api1'], EXAMPLES['api2'], EXAMPLES['api3'], EXAMPLES['api4'], EXAMPLES['api5']]


def getlimits():
    '''alphavantage limits on usage'''
    print()
    print('Your api key is:', getKey('alphavantage')['key'])
    print('Limits 5 calls per minute, 500 per day')


def pt(t, theDate=None):
    '''
    process_time
    Verify the time formatting. Must be formatted as hh:mm
    Example call pt('13:30')
    :params:t: Time formatted as str hh:mm
    :params:theDate: A datetime date object. Defaults to today
    :return: A timestamp str yyyy-mm-dd hh:mm:ss
    '''

    d = theDate if theDate else dt.datetime.today()

    if not isinstance(t, str) or d and not isinstance(d, dt.datetime) \
                              or len(t) != 5 or t.find(":") != 2:
        print(f"Invalid time or date: {d}, {t}.")
        print("     Date must be datetime object. Time must be formatted HH:MM\n")
        return None
    try:
        s = int(t[:2])
        x = int(t[3:])
        assert s < 25
        assert x < 61

    except ValueError:
        print("Invalid time {}. Must be formatted string hh:mm".format(t))
    except AssertionError:
        print("Invalid time {}. Must be legitamte 24 hour time formatted hh:mm".format(t))
    return f'{d.year}-{d.month}-{d.day} {t}'


def ni(i):
    '''
    Utility to normalizee the the interval parameter.
        :params:i: ['1min', '5min', '15min', '30min', '60min', 'daily', 'weekly', 'monthly']
                   ['1', '5', '15', '30', '60', 'd', 'w', 'm', 1, 5, 15, 30, 60]
        :return:   an entry from the 1st list above or None
    '''
    if i in INTERVAL:
        return i
    if i in ['1', '5', '15', '30', '60', 'd', 'w', 'm', 1, 5, 15, 30, 60]:
        return {'1': '1min', '5': '5min', '15': '15min', '30': '30min', '60': '60min',
                'd': 'daily', 'w': 'weekly', 'm': 'monthly', 1: '1min', 5: '5min',
                15: '15min', 30: '30min', 60: '60min'
                }[i]
    print(f"interval={i} is not supported by alphavantage")
    return None


# This is good enough for now. Maybe write a general method for all the alphavantage APIs.
# Alternately do the minimum by implementing a daily method and a moving average method. 

# Set the apikey in the module or class
# Set datatype in the module or class but return pandas for all
# set outputsize here, Could get compact if the request is less than 100 data points
def getmav_intraday(symbol, start=None, end=None, minutes=None, theDate=None):
    '''
    Limited to getting minute data intended to chart day trades
    :params symb: The stock ticker
    :params start: A time string formatted hh:mm to indicate the begin time for the data
    :params end: A time string formatted hh:mm to indicate the end time for the data
    :params minutes: An int for the candle time, 5 minute, 15 minute etc
    :params theDate: A date string formatted yyyymmdd. It will default to today
    :returns: A DataFrame of minute indexed by time with columns open, high, low, 
         low, close, volume
    '''

    minutes = ni(minutes)
    minutes = minutes if minutes else '1min'

    params = {}
    params['function'] = FUNCTION['intraday']
    if minutes:
        params['interval'] = minutes
    params['symbol'] = symbol
    params['outputsize'] = 'full'
    params['datatype'] = DATATYPES[0]
    params['apikey'] = APIKEY
    request_url = f"{BASE_URL}"

    response = requests.get(request_url, params=params)

    print(response.url)

    if response.status_code != 200:
        raise Exception(
            f"{response.status_code}: {response.content.decode('utf-8')}")
    result = response.json()
    tsj = dict()
    keys = list(result.keys())

    if 'Error Message' in keys:
        raise Exception(f"{result['Error Message']}")

    # Don't know if this is guaranteed: either 'Error Message' above,
    # or ['Meta Data', 'Time Series (1min)'] and the data (below):
    # Look for an error over a few months of use (12/18)
    # metaj = result[keys[0]]
    tsj = result[keys[1]]

    df = pd.DataFrame(tsj).T

    start = pt(start, theDate) if start else start
    end = pt(end, theDate) if end else end

    if start:
        df = df.loc[df.index >= start]
    if end:
        df = df.loc[df.index <= end]
    df.sort_index(inplace=True)

    df.rename(columns={'1. open': 'open',
                       '2. high': 'high',
                       '3. low': 'low',
                       '4. close': 'close',
                       '5. volume': 'volume'}, inplace=True)
    return df




# if __name__ == '__main__':
#     print()
#     print('Your api key is:', getkey()['key'])
#     print('Here is a restful api:', EXAMPLES['api1'])
#     print('docs at:', EXAMPLES['web_site'])
#     print('Limits 5 calls per minute, 500 per day\n\n')

# start = "10:30"
# end = "16:00"
# df = getmav_intraday("TEAM", start, end, minutes=60, theDate=dt.datetime(2018, 12, 19))
# print(df)
# print(APIKEY)
getlimits()
