'''
Alphavantage  stuff using their own intraday RESTful  API
@author: Mike Petersen
@creation_date:2018-12-11
Calls the RESTapi for intraday. There is a limit on the free API of 5 calls per minute 
    500 calls per day. But the data is good. The Premium option is rather pricey.
        Free for 5/min  1 every 12 seconds.  Write a API chooser, maybe cache the data
        $20 for 15/min  1 every 4 seconds (might be doable for 500 clients -- stick wi barchart for now)
        $50 for 60/min
        $100 for 120/min
        $250 for 600/min
        As of 1/9/19
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

# These module vars are just documentation. These are the params required for each function 
# We are only using intraday stocks and we might use some of the studies eventually
# FX and bit currency are available. Also, many other technical indicators
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
    # print('Your api key is:', getKey('alphavantage')['key'])
    print('Limits 5 calls per minute, 500 per day')
    print("Intraday goes back 1 week (I think).")
    print(__doc__)



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
    print(f"interval={i} is not supported by alphavantage. Set to 1min candle default.")
    return '1min'

# Set the apikey in the module or class
# Set datatype in the module or class but return pandas for all
# set outputsize here, Could get compact if the request is less than 100 data points
def getmav_intraday(symbol, start, end, minutes=None, theDate=None):
    '''
    Limited to getting minute data intended to chart day trades
    :params symb: The stock ticker
    :params start: A date time string or datetime object to indicate the beginning time.
    :params end: A datetime string or datetime object to indicate the end time.
    :params minutes: An int for the candle time, 5 minute, 15 minute etc
    :params theDate: A date string or object. It will default to today
    :returns: A DataFrame of minute indexed by time with columns open, high, low, 
         low, close, volume and indexed by pd timestamp. If not specified, this 
         will return a weeks data. For now, we will enforce start and end as
         required parameters in order to require precision from user.
    '''

    start = pd.to_datetime(start)
    end = pd.to_datetime(end)


    minutes = ni(minutes)


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
    # print(response.url)

    if response.status_code != 200:
        raise Exception(
            f"{response.status_code}: {response.content.decode('utf-8')}")
    result = response.json()
    tsj = dict()
    keys = list(result.keys())

    if 'Error Message' in keys:
        raise Exception(f"{result['Error Message']}")
    
        


    # If we exceed the requests/min, we get a friendly html string sales pitch.
    metaj = result[keys[0]]
    if len(keys) < 2:
        #This tells us we have exceeded the limit and gives the premium link. AARRGH. Yahoo come back
        print(metaj)
        return None

    dataJson = result[keys[1]]

    df = pd.DataFrame(dataJson).T

    df.index = pd.to_datetime(df.index)
    df.index[0]

    if df.index[0] > df.index[-1]:
        df.sort_index(inplace=True)

    if end < df.index[0] :
        print('WARNING: You have requested data that is unavailable:')
        print(f'Your end date ({end}) is before the earliest first date ({df.index[0]}).')
        return None

    if start and start > df.index[0]:
        df = df[df.index >= start]


    if end and  end < df.index[-1]:
        df = df[df.index <= end]


    df.rename(columns={'1. open': 'open',
                       '2. high': 'high',
                       '3. low': 'low',
                       '4. close': 'close',
                       '5. volume': 'volume'}, inplace=True)

    # We got strings, probably because we had to invert the JSON data after creating a DataFrame
    # TODO Find out how to invert the data in JSON before creating the DataFrame
    df.open = pd.to_numeric(df.open)
    df.high = pd.to_numeric(df.high)
    df.low = pd.to_numeric(df.low)
    df.close = pd.to_numeric(df.close)
    df.volume = pd.to_numeric(df.volume)


    return df



#TODO write getLastWeekday()

if __name__ == '__main__':
    df = getmav_intraday('SQ')
#     print()
#     print('Your api key is:', getkey()['key'])
#     print('Here is a restful api:', EXAMPLES['api1'])
#     print('docs at:', EXAMPLES['web_site'])
#     print('Limits 5 calls per minute, 500 per day\n\n')

# symbol='SQ'
# start = "20190109 10:30"
# end = "20190109 15:00"
# minutes=None
# theDate=None
# # theDate = dt.datetime(2019, 1, 3)

# df = getmav_intraday(symbol, start, end, minutes=minutes, theDate=theDate)
# print (df.head())
# print(df.tail())
