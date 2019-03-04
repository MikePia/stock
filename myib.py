'''
Implement historicalData method from the IB API
@author: Mike Petersen
@creation_date: 1/2/19
'''

import sys
import datetime as dt
from threading import Thread
import queue
import pandas as pd

from ibapi import wrapper
from ibapi.client import EClient

# from ibapi.wrapper import EWrapper
from ibapi.common import TickerId
from ibapi.contract import Contract


# import time
# pylint: disable=C0103
# pylint: disable=C0301


BAR_SIZE = ['1 sec', '5 secs', '10 secs', '15 secs', '30 secs',
            '1 min', '2 mins', '3 mins', '5 mins', '10 mins', '15 mins', '20 mins', '30 mins',
            '1 hour', '2 hours', '3 hours', '4 hours', '8 hours',
            '1 day', '1 week', '1 month']

# Needs to be a string in the form '3 D'
DURATION_STRING = ['S', 'D', 'W', 'M', 'Y']


def getLimits():
    '''
    Tell a little bit about the getHistory call
    '''
    l = ''.join(['We are only interested, in this app, in chart info, aka historical data.\n',
                 'IB will issue a Pacing violation when:...\n',
                 '       Making identical historical data requests within 15 seconds.\n',
                 '       Making six or more historical data requests for the same Contract',
                 '       Exchange and Tick Type within two seconds.\n',
                 '       Making more than 60 requests within any ten minute period.\n\n',
                 'Data older than 6 months for candles of 1 minute or less in unavailable.\n',
                 '      No hard limit for older data for intervals greater than 1 min (so they',
                 '      say in spite of the docs)\n'])
    return l

def ni(i, minutes='minutes'):
    '''
    Utility to normalize the the interval parameter.
    '''
    if minutes != 'minutes':
        print(f'{minutes} is not supported yet. Setting to 1 min')
    if i in BAR_SIZE:
        return i
    if i in ['1', '2', '3', '5', '10', '15', '20', '30', '60']:
        return {'1': '1 min', '2': '2 mins', '3': '3 mins', '5': '5 mins', '10': '10 mins',
                '15': '15 mins', '20': '20 mins', '30': '30 mins', '60': '1 hour'}[i]
    if isinstance(i, int):
        ret = '1 hour'
        if i < 2:
            ret = '1 min'
        elif i < 3:
            ret = '2 mins'
        elif i < 5:
            ret = '3 mins'
        elif i < 10:
            ret = '5 mins'
        elif i < 15:
            ret = '10 mins'
        elif i < 20:
            ret = '15 mins'
        elif i < 30:
            ret = '20 mins'
        elif i < 60:
            ret = '30 mins'
        return ret
    print(
        f"interval = '{i}' is not supported by alphavantage. Setting to 1min candle.")
    return '1 min'

def validateDurString(s):
    '''
    Utility method to enforce an IB requirement.
    '''
    d = ['S', 'D', 'W', 'M', 'Y']
    sp = s.split()
    # print(sp)
    if len(sp) != 2:
        return False
    if sp[1] not in d:
        return False
    try:
        int(sp[0])
    except ValueError:
        return False
    return True


class TestClient(EClient):
    '''
    Inherit from the sample code
    '''

    def __init__(self, wrapprr):
        EClient.__init__(self, wrapprr)
        self.storage = queue.Queue()


class TestWrapper(wrapper.EWrapper):
    '''
    Inherit from the sample code.
    '''
    def __init__(self):
        wrapper.EWrapper.__init__(self)

        self.counter = 0
        self.data = []

    def contractDetails(self, reqId, contractDetails):
        '''
        Overriden method that returns to us all the contract details from the instrument.
        I think if we receive this without asking for it, it means IB failed to locate a single
        match for a requested instrument
        '''
        print("(POSSIBLE) WARNING: Is this the droid you were looking for?")
        print(f"ContractDetails: {reqId} {contractDetails}")

    def error(self, reqId: TickerId, errorCode: list, errorString: str):
        '''
        Overriden method to return all errors to us
        '''
        if reqId != -1:
            print(f"Error: {reqId} {errorCode} {errorString}")

    def historicalData(self, reqId: int, bar):
        '''
        Overriden Callback from EWrapper. Drops off data 1 bar at a time in each call.
        '''
        if self.counter == 0:
            l = []
            l.append(bar)
        self.counter = self.counter + 1
        self.data.append([bar.date, bar.open, bar.high,
                          bar.low, bar.close, bar.volume])

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        '''
        Overriden callback is called when all bars have been delivered to historicalData provided
        keepUpToDate=False, parameter in reqHistoricalData.
        '''

        super().historicalDataEnd(reqId, start, end)
        df = pd.DataFrame(self.data,
                          columns=['date', 'open', 'high', 'low', 'close', 'volume'])
        self.storage.put(df)
        # GDF=df
        # print(df)
#         print(df.tail(2))
        # exit()


class TestApp(TestWrapper, TestClient):
    '''
    My very own double
    '''
    def __init__(self, port, cid):
        TestWrapper.__init__(self)
        TestClient.__init__(self, wrapprr=self)
        self.port = port
        self.cid = cid
        # ! [socket_init]

        self.started = False

    def start(self):
        '''
        Run the thread
        '''
        if self.started:
            return
        self.started = True

        self.historicalDataOperations_req()

    def historicalDataOperations_req(self):
        '''Overridder'''
        pass
        #  self.reqHistoricalData(4103, ContractSamples.EuropeanStock(), queryTime, "10 D", "1 min", "TRADES", 1, 1, False, [])

    def getHistorical(self, symbol, end, dur, interval, exchange='NASDAQ'):
        '''
        :params end: datetime object for the end time requested
        :params dur: a string for how long before end should the chart begin "1 D"
        :params interval: candle len
        '''

        if not validateDurString(dur):
            print("Duration must be formatted like '3 D' using S, D, W, M, or Y")
            return pd.DataFrame()

        if not isinstance(end, dt.datetime):
            print("end must be formatted as a datetime object")
            return pd.DataFrame()

        if interval not in BAR_SIZE:
            print('Bar size ({}) must be one of: {}'.format(interval, BAR_SIZE))
            return pd.DataFrame()

        # app = Ib()
        host = "127.0.0.1"
        port = self.port
        clientId = self.cid
        self.connect(host, port, clientId)

        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        contract.primaryExchange = exchange

        # app.reqContractDetails(10, contract)

        timeStr = end.strftime('%Y%m%d %H:%M:%S')
        # self.reqHistoricalData(18002, ContractSamples.ContFut(), timeStr, "1 Y", "1 month", "TRADES", 0, 1, False, []);
        # queryTime = DateTime.Now.AddMonths(-6).ToString("yyyyMMdd HH:mm:ss");
        self.reqHistoricalData(4001, contract, timeStr, dur,
                               interval, "TRADES", 1, 1, False, [])
        # client.reqHistoricalData(4002, ContractSamples.EuropeanStock(), queryTime, "10 D", "1 min", "TRADES", 1, 1, false, null);
        # print('Requesting access')

        # self.run()
        thread = Thread(target=self.run)
        thread.start()

        setattr(self, "_thread", thread)

        try:
            x = self.storage.get(timeout=10)
            x.set_index('date', inplace=True)
            # print("About to print the Da
            return x
        except queue.Empty as ex:
            print("Request came back empty", ex.__class__.__name__, ex)
            return pd.DataFrame()


def getib_intraday(symbol, start, end, minutes, showUrl='dummy'):
    '''
    An interface API to match the other getters. In this case its a substantial
    dumbing down of the capabilities to our one specific need. Output will be limited
    to minute candles (1,5,10,7 whatever) within a single day.
    :params symbol: The stock to get
    :params start: A timedate object or time string for when to start.
    :params end: a timedate object or time string for when to end.
    :params minutes: the length of the candle.
    return a DataFrame of the requested stuff
    '''
    start = pd.Timestamp(start)
    end = pd.Timestamp(end)
    if (end-start).days < 1:
        if ((end-start).seconds//3600) > 8:
            dur = '1 D'
        else:
            dur = f'{(end-start).seconds} S'
    elif (end-start).days < 7:
        dur = f'{(end-start).days + 1} D'
    else:
        dur = f'{(end-start).days} D'
        print('Requests longer than 6 days are not supported.')
        return pd.DataFrame([], [])
    
    # if the end = 9:31 and dur = 3 minutes, ib will retrieve a start of the preceding day @ 15:58
    # This is unique behavior in implemeted apis. We will just let ib do whatever and cut off the 
    # beginning below. 

    symb = symbol
    # daDate = end
    interval = ni(minutes)
    # chart(symb, d, dur/, interval)
    ib = TestApp(7496, 7878)
    # def getHistorical(self, symbol, end, dur, interval, exchange='NASDAQ'):
    df = ib.getHistorical(symb, end=end, dur=dur,
                          interval=interval, exchange='NASDAQ')
    if len(df) == 0:
        return 0, df

    # df.set_index(df.date)
    df.index = pd.to_datetime(df.index)
    if start > df.index[0]:
        df = df.loc[df.index >= start]

    ib.disconnect()
    return len(df), df


    # df = getIb_Hist(symbol, end=end, dur=dur, interval=minutes)
    # return df
def isConnected():
    host ='127.0.0.1'
    port = 7496
    clientId = 7878
    ib = TestApp(host, port)
    ib.connect(host, port, clientId)
    connected = ib.isConnected()
    if connected:
        ib.disconnect()
    return connected

def main():
    '''test run'''
    start = dt.datetime(2019, 1, 15, 9, 19)
    end = dt.datetime(2019, 1, 15, 15, 5)
    minutes='1 min'
    x, ddf = getib_intraday('SQ', start, end, minutes)
    # ddf = getIb_Hist('W', end=end, dur='14400 S', interval='30 mins')
    # print(f'Requested {start} 
    # /... {end}')
    # print(f'Received  {ddf.index[0]} .../... {ddf.index[-1]}')
    # print(f'Index type: {type(ddf.index[0])}')
    # cols = ddf.columns
    # for col in cols:
    #     # print(f"Col types: {col}: {type([df[col][0])}")
    #     print(f'{col} {type(ddf[col][0])}')
    # print(ddf.head(3))
    print(ddf.tail(3))



    # ddf = getib_intraday('JNJ', start=start, end=end, minutes=minutes )
    # print(ddf.columns)

def notmain():
    print("We are connected? ", isConnected())


if __name__ == '__main__':
    # main()
    notmain()
    