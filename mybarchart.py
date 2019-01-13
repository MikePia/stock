'''
Some barchart calls beginning (and ending now) with getHistory. Note that the docs show SOAP code to run this
in python but as of 12/29/18 the suds module (suds not suds-py3) does not work on my system.
I am goingto implement the straight RESTful free API using request

@author: Mike Petersen
@creation_data: 12/19/18
'''
import requests
import datetime as dt
# from stock import myalphavantage as mav
import pandas as pd
# from stock import mybarchart as bc
from stock.picklekey import getKey as getReg

# pylint: disable = C0103
APIKEY = getReg('barchart')['key']

# https://marketdata.websol.barchart.com/getHistory.json?apikey={APIKEY}&symbol=AAPL&type=minutes&startDate=20181001&maxRecords=100&interval=5&order=asc&sessionFilter=EFK&splits=true&dividends=true&volume=sum&nearby=1&jerq=true

def getApiKey():
    return APIKEY


def getLimits():
    return '''Every user is able to make 400 getQuote queries and 150 getHistory queries per day.
              One coud track a single stock for open hours updating once a minute.
              Or one could track a single stock for one hour updating every 9 seconds.
              https://www.barchart.com/ondemand/free-market-data-api/faq'''


BASE_URL = f'https://marketdata.websol.barchart.com/getHistory.json?'


def getFaq():
    faq = '''
        https://www.barchart.com/ondemand/free-market-data-api/faq
        https://www.barchart.com/ondemand/api gives api for several dozen calls.
        The free api is limited to getQuote and getHistory. 
            https://www.barchart.com/ondemand/free-market-data-api
        Exchanges iclude AMEX, NYSE, NASDAQ.
        Within the last couple of years, the free API shrunk without warning.
        Every user is able to make 400 getQuote queries and 150 getHistory queries per day.
        When your daily API account query limit is reached, the data will be disabled then 
            reset until the next day.
        pricing info for other apis requires you contact a sales person (shudder).
        '''
    return faq


APIS = {'history': 'getHistory.json?',
        'closeprice': 'getClosePrice.json?'}


PARAMS = {'getHistory': ['apikey', 'symbol', 'type',
                         'startDate', 'maxRecords', 'interval', 'order', 'sessionFilter',
                         'splits', 'dividends', 'volume', 'nearby', 'jerq'],
          'getQuote': ['symbols', 'fields', 'only']
          }


TYPE = ['minutes', 'nearbyMinutes', 'formTMinutes',
        'daily', 'dailyNearest', 'dailyContinue',
        'weekly', 'weeklyNearest', 'weeklyContinue',
        'monthly', 'monthlyNearest', 'monthlyContinue',
        'quarterly', 'quarterlyNearest', 'quarterlyContinue',
        'yearly', 'yearlyNearest', 'yearlyContinue']
ORDER = ['asc', 'desc']
VOLUME = ['total', 'sum', 'contract', 'sumcontract', 'sumtotal']

# For testing
DEMO_PARAMS = {'apikey': APIKEY,
               'symbol': 'AAPL',
               'type': 'minutes',
               'startDate': '2018-12-03 12:45',
               'maxRecords': 500,
               'interval': 30,
               #    'order': 'asc',
               #    'sessionFilter': 'EFK',
               #    'splits': 'true',
               #    'dividends': 'true',
               'volume': 'sum',
               #    'nearby': 1,
               #    'jerq': 'true'
               }


# Not getting the current date-- maybe after the market closes?
def getbc_intraday(symbol,  start, end=None, minutes=5,  daType='minutes', showUrl=False):
    '''
    Note that getHistory will return previous day's prices until 15 minutes after the market closes. We will
        generate a warning if our start or end date differ from the date of the response 
    :params symbol: The stock ticker
    :params start: A datetime object or time string to indicate the begin time for the data
    :params end: A datetime object or time string to indicate the end time for the data
    :params minutes: An int for the candle time, 5 minute, 15 minute etc
    :params daType: Possible values include  ['minutes', 'daily', 'weekly', 'monthly', 'quarterly', 'yearly'] print(TYPE) (a module variable) for full list.
    :return: A tuple of (status as dictionary, data as a DataFrame ) This status is seperate from request status_code
    :raise: ValueError if response.status_code from getHistory is not 200 or if daType is not recognized.
    '''
    request_url = BASE_URL

    if not end:
        tdy = dt.datetime.today()
        end = dt.datetime(tdy.year, tdy.month, tdy.day, 17, 0)
    if not start:
        tdy = dt.datetime.today()
        start = dt.datetime(tdy.year, tdy.month, tdy.day, 6, 0)
    end = pd.to_datetime(end)    
    start = pd.to_datetime(start)    
        
 
    if daType not in TYPE:
        raise ValueError(f"daType must be one of {TYPE}")
        
    # s = start.strftime("%Y-%m-%d %H:%M")
    # e = end.strftime("%Y-%m-%d %H:%M")
    
    params={}
    params['apikey'] = APIKEY
    params['symbol'] = symbol
    params['type'] = daType
    params['interval'] = minutes
    params['startDate'] = start
#     if end:
#         params['endDate'] = end
    params['order'] = 'asc'
#     params['maxRecords'] = 5
    params['sessionFilter'] = 'EFK'
    params['volume'] = 'sum'
    params['nearby'] = 1
    params['jerq'] = 'true'
        
    response = requests.get(request_url,params=params)
    if showUrl:
        print(response.url)

    if response.status_code != 200:
        raise Exception(f"{response.status_code}: {response.content.decode('utf-8')}")
    result = response.json()
    if not result['results']:
        print('WARNING: Failed to retrieve any data. Barchart sends the following greeting:')
        print(result['status'])
        return result['status'], None
    
    keys = list(result.keys())
    meta = result[keys[0]]
    JSONTimeSeries = result[keys[1]]
    df = pd.DataFrame(JSONTimeSeries)
    df.set_index(df.timestamp, inplace=True)
    df.index.rename('date', inplace=True)

    # HACKALERT hacky code alert Retrieve the tz hour and minutes  from the funky timestamp
    # Subtradct Timedelta from to_datetime (Amazed the Series thing works like a matrix, written like a straight expression)
    hour= df.index[0][20:-3]
    minutes = df.index[0][23:]
    minutes = int(minutes)
    hour=int(hour)
    seconds = minutes*60
    df.index = pd.to_datetime(df.index, utc=False) - pd.Timedelta(hours=5, seconds=seconds)

    firstTime = df.index[0]
    firstDay = df.iloc[0].tradingDay
    
    lastDate = df.iloc[-1].tradingDay
    lastTime = df.index[-1]
        
    if start.date() < firstTime.date():
        
        print("\nWARNING: Requested start date is not included in response. Did you request a weekend or holiday?")
        print(f"First timestamp: {firstTime}")
        print(f"Requested start of data: {start}\n")

    # getHistory trims the start nicely. We will trim the end here if requested by the end parameter. 
    # (I think the premium API does handle this. There is some mention of an endDate parameter)
    if end < lastTime:
        df = df.loc[df.index <= end]
    
    #Note we are dropping columns  ['symbol', 'timestamp', 'tradingDay[]
    df = df[['open', 'high', 'low', 'close', 'volume']].copy(deep=True)
    return meta, df

if __name__ == '__main__':



    # tdy = dt.datetime.today()
    # start = dt.datetime(tdy.year, tdy.month, tdy.day, 7)
    # end = dt.datetime(tdy.year, tdy.month, tdy.day, 15, 48)
    start = '2019-01-09'
    end = None
    interval=1
    symbol='AAPL'
    x,bcdf = getbc_intraday(symbol, start=start, end=end, minutes=interval)
    print(x)
    print (bcdf.head(2))
    print(bcdf.tail(2))


# graph_candlestick("AAPL", start=start, dtFormat='%m %d', st=s )
#     import random
# # tdy = dt.datetime.today()
# start='2019-11-20'
# r = random.randint(0, len(style.available))
# s = style.available[r]
# print(s)

# classic, greyscale, seaborn-poster, bmh, dark_background
# print(getApiKey())
