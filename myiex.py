'''
A module to access iex API. From the REStful source. No wrapeere packages
@author: Mike Petersen
@creation_date: 12/20/18
'''
import pandas as pd
import requests
# pylint: disable=C0103


apiurl = 'https://api.iextrading.com/1.0/stock/aapl/chart/5y?format=json'
newsurl = 'https://api.iextrading.com/1.0/stock/aapl/batch?types=quote,news,chart&range=1m&last=10'
apidocs = "https://iextrading.com/developer/docs/#getting-started"

BASE_URL = 'https://api.iextrading.com/1.0'

def get_trading_chart_web(symb, start=None, end=None, minutes = None, theDate=None):
    '''
    Limited to getting minute data intended to chart day trades
    :params:symb: The stock ticker
    :parms:start: A time string formatted hh:mm to indicate the begin time for the data
    :params:end: A time string formatted hh:mm to indicate the end time for the data
    :params:minutes: An int for the candle time, 5 minute, 15 minute etc
    :params:theDate: A date string formatted yyyymmdd. It will default to today
    '''
    url = "chart"
    rng = "1d"
    if theDate:
        rng = f"date/{theDate}"
    params = {}
    if minutes:

        params['chartInterval'] = minutes
    params['filter'] = 'minute,open,high,low,close,average,volume'

    request_url =f"{BASE_URL}/stock/{symb}/{url}/{rng}"

    response = requests.get(request_url, params=params)
    if response.status_code != 200:
        raise Exception(f"{response.status_code}: {response.content.decode('utf-8')}")
    result = response.json()

    df = pd.DataFrame(result)
    
    df.set_index('minute', inplace=True)
    
    df = df.loc[df.index >= start] if start else df
    df = df.loc[df.index <= end] if end else df
    return df
get_trading_chart_web("MSFT", "10:23", "16:37", minutes=2, theDate="20181214").head()

