'''
    Some barchart calls beginning with getHistory. Note that the docs show SOAP code to run this
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

# barchart = {'key': '634dc287dbe9544d75765554c9238641',
#             'web': 'https://www.barchart.com/ondemand/free-market-data-api/faq',
#             'date': '12/29/18',
#             'registered': 'lynnpete11@gmail.com'}


# https://marketdata.websol.barchart.com/getHistory.json?apikey=634dc287dbe9544d75765554c9238641&symbol=AAPL&type=minutes&startDate=20181001&maxRecords=100&interval=5&order=asc&sessionFilter=EFK&splits=true&dividends=true&volume=sum&nearby=1&jerq=true

def getApiKey():
    return APIKEY


def getLimits():
    return ['Every user is able to make 400 getQuote queries and 150 getHistory queries per day.',
            'https://www.barchart.com/ondemand/free-market-data-api/faq']


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
def getbc_intraday(symbol,  start, end=dt.datetime.today(), minutes=5,  daType='minutes'):
    '''
    Note that getHistory will return previous day's prices until 15 minutes after the market closes. We will
        generate a warning if our start or end date differ from the response 
    :params symbol: The stock ticker
    :parms start: A datetime object to indicate the begin time for the data
    :params end: A datetime object to indicate the end time for the data
    :params minutes: An int for the candle time, 5 minute, 15 minute etc
    :params theDate: A date string formatted yyyymmdd. It will default to today
    :returns: A tuple of (status as dictionary, data as a DataFrame ) This status is seperate from response.status_code
    :raises ValueError: If start, end or daType are misformatted
    :raises Exception is response.status_code from getHistory is not 200
    '''
    request_url = BASE_URL
    
    if not isinstance(start, dt.datetime) or not isinstance(end, dt.datetime):
        print("start", type(start))
        print("end", type(end))
        raise ValueError("start and end must be datetime objects")
 
    if daType not in TYPE:
        raise ValueError(f"daType must be one of {TYPE}")
        
    s = start.strftime("%Y-%m-%d %H:%M")
    e = end.strftime("%Y-%m-%d %H:%M")
    
    params={}
    params['apikey'] = APIKEY
    params['symbol'] = symbol
    params['type'] = daType
    params['interval'] = minutes
    params['startDate'] = s
#     if end:
#         params['endDate'] = end
    params['order'] = 'asc'
#     params['maxRecords'] = 5
    params['sessionFilter'] = 'EFK'
    params['volume'] = 'sum'
    params['nearby'] = 1
    params['jerq'] = 'true'
        
    response = requests.get(request_url,params=params)
    
    print(response.url)

    if response.status_code != 200:
        raise Exception(f"{response.status_code}: {response.content.decode('utf-8')}")
    result = response.json()
    
    keys = list(result.keys())
    meta = result[keys[0]]
    tsj = result[keys[1]]

    df = pd.DataFrame(tsj)
    
    # Comparing and trimming the end  using strings in barchart's date and timestamp format strings
    compareStartDate = dt.datetime(start.year, start.month, start.day).strftime("%Y-%m-%d")
    compareEndDate = dt.datetime(end.year, end.month, end.day).strftime("%Y-%m-%d")
    compareEndTime = end.strftime("%Y-%m-%dT%H:%M")#  + df.iloc[-1].timestamp[16:] # Copy the seconds and TimeZone from response
    
    firstDate = df.iloc[0].tradingDay
    lastDate = df.iloc[-1].tradingDay
    lastTime = df.iloc[-1].timestamp
    
    # These warnings remain dumb and subtlely pass the blame for requesting a non-trading day.
    if compareEndDate > lastDate:
        
        print("\nWARNING: Requested end date is not included in response. Did you request a weekend or holiday?")
        print(f"Last timestamp: {lastDate}")
        print(f"Requested end of data: {compareEndDate}\n")
        
    if compareStartDate < firstDate:
        
        print("\nWARNING: Requested start date is not included in response. Did you request a weekend or holiday?")
        print(f"First timestamp: {firstDate}")
        print(f"Requested start of data: {compareStartDate}\n")

#     print(f"compareDate: {compareDate}\ncompareTime: {compareTime}\nlastDate:    {lastDate}\nlastTime:    {lastTime}")
    df.set_index(df.timestamp, inplace=True)

    # getHistory trims the start nicely. We will trim the end here if requested by the end parameter. 
    # (I think the premium API does handle this. There is some mention of endDate parameter)
    if compareEndTime < lastTime:
        print("Supa Dupa. Filtering end time")
        df = df.loc[df.index <= compareEndTime]
    else:
        print("Still SUPER")
    
    
    return meta, df

if __name__ == '__main__':
    pass

# print(getApiKey())
