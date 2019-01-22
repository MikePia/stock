'''
Some barchart calls beginning (and ending now) with getHistory. Note that the docs show SOAP code
to run this in python but as of 12/29/18 the suds module (suds not suds-py3) does not work on my
system. I am goingto implement the straight RESTful free API using request.

@author: Mike Petersen
@creation_data: 12/19/18
'''
import datetime as dt
import requests
# from stock import myalphavantage as mav
import pandas as pd
# from stock import mybarchart as bc
from stock.picklekey import getKey as getReg
from stock import utilities as util
# pylint: disable = C0103
APIKEY = getReg('barchart')['key']

# https://marketdata.websol.barchart.com/getHistory.json?apikey={APIKEY}&symbol=AAPL&type=minutes&startDate=20181001&maxRecords=100&interval=5&order=asc&sessionFilter=EFK&splits=true&dividends=true&volume=sum&nearby=1&jerq=true


def getApiKey():
    '''Returns the key for the barchart API
    '''
    return APIKEY


def getLimits():
    '''Some useful info regarding barchart maximum usage.'''
    return '''Every user is able to make 400 getQuote queries and 150 getHistory queries per day.
              Using getQuote, One coud track a single stock for open hours updating once a minute.
              Or one could track a single stock for one hour updating every 9 seconds.
              https://www.barchart.com/ondemand/free-market-data-api/faq.'''


BASE_URL = f'https://marketdata.websol.barchart.com/getHistory.json?'


def getFaq():
    '''Intersting info'''
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
        Pricing info for other apis requires you contact a sales person (shudder).
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

def setParams(symbol, minutes, startDay):
    '''Internal utility method'''
    params = {}
    params['apikey'] = APIKEY
    params['symbol'] = symbol
    params['type'] = 'minutes'
    params['interval'] = minutes
    params['startDate'] = startDay
    params['order'] = 'asc'
    # params['maxRecords'] = 5
    params['sessionFilter'] = 'EFK'
    params['volume'] = 'sum'
    params['nearby'] = 1
    params['jerq'] = 'true'
    return params

# Not getting the current date-- maybe after the market closes?
def getbc_intraday(symbol, start=None, end=None, minutes=5, showUrl=False):
    '''
    Note that getHistory will return previous day's prices until 15 minutes after the market
        closes. We will generate a warning if our start or end date differ from the date of the
        response. Given todays date at 14:00, it will retrive the previous business days stuff.
        Given not start parameter, we will return data for the last weekday. Today or earlier.
    Retrieve candle data measured in minutes as given in the minutes parameter
    :params start: A datetime object or time string to indicate the begin time for the data. During
        trading hours, a start for today is ignored by barchart, it retrieves the previous biz day.
    :params end: A datetime object or time string to indicate the end time for the data
    :params minutes: An int for the candle time, 5 minute, 15 minute etc
    :return: A tuple of (status as dictionary, data as a DataFrame ) This status is seperate from
        request status_code.
    :raise: ValueError if response.status_code is not 200 or if daType is not recognized.
    '''
    if not end:
        tdy = dt.datetime.today()
        end = dt.datetime(tdy.year, tdy.month, tdy.day, 17, 0)
    if not start:
        tdy = dt.datetime.today()
        start = dt.datetime(tdy.year, tdy.month, tdy.day, 6, 0)
        start = util.getLastWorkDay(start)
    end = pd.to_datetime(end)
    start = pd.to_datetime(start)
    startDay = start.strftime("%Y%m%d")

    # if daType not in TYPE:
    #     raise ValueError(f"daType must be one of {TYPE}")

    # s = start.strftime("%Y-%m-%d %H:%M")
    # e = end.strftime("%Y-%m-%d %H:%M")

    params = setParams(symbol, minutes, startDay)
    # params['apikey'] = APIKEY
    # params['symbol'] = symbol
    # params['type'] = 'minutes'
    # params['interval'] = minutes
    # params['startDate'] = startDay
    # params['order'] = 'asc'
    # # params['maxRecords'] = 5
    # params['sessionFilter'] = 'EFK'
    # params['volume'] = 'sum'
    # params['nearby'] = 1
    # params['jerq'] = 'true'

    response = requests.get(BASE_URL, params=params)
    if showUrl:
        print(response.url)

    if response.status_code != 200:
        raise Exception(
            f"{response.status_code}: {response.content.decode('utf-8')}")
    if (
            response.text
            and isinstance(response.text, str)
            and response.text.startswith('You have reached')):
        print('WARNING: API max queries:\n', response.text)
        meta = {'code': 666, 'message': response.text}
        return meta, pd.DataFrame()
    result = response.json()
    if not result['results']:
        print(
            'WARNING: Failed to retrieve any data. Barchart sends the following greeting:')
        print(result['status'])
        return result['status'], pd.DataFrame()

    keys = list(result.keys())
    meta = result[keys[0]]
    # JSONTimeSeries = result[keys[1]]
    df = pd.DataFrame(result[keys[1]])
    df.set_index(df.timestamp, inplace=True)
    df.index.rename('date', inplace=True)

    # HACKALERT hacky code alert Retrieve the tz hour and minutes  from the funky timestamp.
    # Subtract Timedelta from to_datetime
    hour = int(df.index[0][20:-3])
    seconds = int(df.index[0][23:])*60
    df.index = pd.to_datetime(df.index, utc=False) - \
        pd.Timedelta(hours=hour, seconds=seconds)

    msg = ''
    if start.date() < df.index[0].date():
        msg = ' '.join(["\nWARNING: Requested start date is not included in response. ",
                        "Did you request a weekend or holiday?",
                        f"First timestamp: {df.index[0]}\n",
                        f"Requested start of data: {start}\n"])
        print(msg)

    elif start.date() > df.index[0].date():
        msg = "\nWARNING: Requested start date is after the barchart response. If the market is\n"
        msg = msg + " still open? Barchart will retrieve today after the close and not before.\n"
        msg = msg + f"First timestamp: {df.index[0]}\n"
        msg = msg + f"Requested start of data: {start}\n"
        print(msg)

    if start > df.index[0]:
        df = df.loc[df.index >= start]
        if len(df) == 0:
            msg = '\nWARNING: all data has been removed.'
            msg = msg + f'\nThe Requested start was({start}).'
            print(msg)
            meta['code2'] = 199
            meta['message'] = meta['message'] + msg
            return meta, df

    if end < df.index[-1]:
        df = df.loc[df.index <= end]
        # If we just sliced off all our data. Set warning message
        if len(df) == 0:
            msg = msg + '\nWARNING: all data has been removed.'
            msg = msg + f'\nThe Requested end was({end}).'
            meta['code2'] = 199
            meta['message'] = meta['message'] + msg
            return meta, df

    # Note we are dropping columns  ['symbol', 'timestamp', 'tradingDay[]
    df = df[['open', 'high', 'low', 'close', 'volume']].copy(deep=True)
    return meta, df


def main():
    '''Local runs for debugging'''
    # tdy = dt.datetime.today()
    # start = dt.datetime(tdy.year, tdy.month, tdy.day, 7)
    # end = dt.datetime(tdy.year, tdy.month, tdy.day, 15, 48)
    start = '2019-01-09'
    end = '2019-01-14'
    interval = 1
    symbol = 'AAPL'
    x, bcdf = getbc_intraday(symbol, start=start, end=end, minutes=interval)
    print(x)
    print(bcdf.head(2))
    print(bcdf.tail(2))


if __name__ == '__main__':
    main()


# graph_candlestick("AAPL", start=start, dtFormat='%m %d', st=s )
#     import random
# # tdy = dt.datetime.today()
# start='2019-11-20'
# r = random.randint(0, len(style.available))
# s = style.available[r]
# print(s)

# classic, greyscale, seaborn-poster, bmh, dark_background
# print(getApiKey())
