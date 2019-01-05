'''
Implement historicalData method from the IB API
@author: Mike Petersen
@creation_date: 1/2/19
'''

import datetime as dt

from ibapi import wrapper
from ibapi.client import EClient
# from ibapi.wrapper import EWrapper
from ibapi.common import TickerId
from ibapi.contract import Contract

from threading import Thread

import queue

import pandas as pd
# import time
# pylint: disable=C0103


BAR_SIZE = ['1 secs', '5 secs', '10 secs', '15 secs', '30 secs',
            '1 min', '2 mins', '3 mins', '5 mins', '10 mins', '15 mins', '20 mins', '30 mins',
            '1 hour', '2 hours', '3 hours', '4 hours', '8 hours',
            '1 day', '1 week', '1 month']

# Needs to be a string in the form '3 D'
DURATION_STRING = ['S', 'D', 'W', 'M', 'Y']


def getLimits():
    l = ''.join(['We are only interested, in this app, in chart info, aka historical data.\n',
                 '     IB will issue a Pacing violation when:...\n',
                 '       Making identical historical data requests within 15 seconds.\n',
                 '       Making six or more historical data requests for the same Contract, Exchange and Tick Type within two seconds.\n',
                 '       Making more than 60 requests within any ten minute period.\n\n',
                 'Data older than 6 months for candles of 1 minute or less in unavailable.\n',
                 '     No hard limit for older data for intervals greater than 1 min (so they say in spite of the docs)\n'])
    return l

class TestClient(EClient):
    def __init__(self, wrapprr):
        EClient.__init__(self, wrapprr)
        self.storage = queue.Queue()


class TestWrapper(wrapper.EWrapper):
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
        print(f"Error: {reqId} {errorCode} {errorString}")

    def historicalData(self, reqId: int, bar):
        '''
        Overriden Callback from EWrapper. Drops off data 1 bar at a time in each call. 
        '''
        if self.counter == 0:
            print("beginning")
#             print("originally Type:", type(bar))
            l = []
            l.append(bar)
            print('time', bar.date)
        self.counter = self.counter + 1
        self.data.append([bar.date, bar.open, bar.high,
                          bar.low, bar.close, bar.volume])

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        '''
        Overriden callback is called when all bars have been delivered to historicalData provided
        keepUpToDate=False, parameter in reqHistoricalData.
        '''

        super().historicalDataEnd(reqId, start, end)
        print("HistoricalDataEnd. ReqId:", reqId, "from", start, "to", end)
        print("GOT LINES:", len(self.data))
        print("TYPE:", type(self.data[0]))
        df = pd.DataFrame(self.data, columns=[
                          'date', 'open', 'high', 'low', 'close', 'volume'])
        print('filling the queue')
        self.storage.put(df)
        # GDF=df
        # print(df)
#         print(df.tail(2))
        # exit()


class TestApp(TestWrapper, TestClient):
    def __init__(self):
        TestWrapper.__init__(self)
        TestClient.__init__(self, wrapprr=self)
        # ! [socket_init]

        self.started = False

    def start(self):
        if self.started:
            return
        self.started = True

        self.historicalDataOperations_req()

    def historicalDataOperations_req(self):
        pass
        #  self.reqHistoricalData(4103, ContractSamples.EuropeanStock(), queryTime, "10 D", "1 min", "TRADES", 1, 1, False, [])

    def getHistorical(self, symbol, end, dur, interval, exchange='NASDAQ'):
        '''
        :params end: datetime object for the end time requested
        :params dur: a string for how long before end should the chart begin "1 D"
        :params interval: candle len
        '''

        if self.validateDurString(dur) == False:
            print("Duration must be formatted like '3 D' using S, D, W, M, or Y")
            return None

        if not isinstance(end, dt.datetime):
            print("end must be formatted as a datetime object")
            return None

        if interval not in BAR_SIZE:
            print('Bar size ({}) must be one of: {}'.format(interval, BAR_SIZE))
            return None

        # app = Ib()
        host = "127.0.0.1"
        port = 7496
        clientId = 7878
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
        print('Requesting access')

        # self.run()
        thread = Thread(target=self.run)
        thread.start()

        setattr(self, "_thread", thread)

        x = self.storage.get()
        x.set_index('date', inplace=True)
        # print("About to print the Da
        return x

    def validateDurString(self, s):
        '''
        Utility method to enforce an IB requirement.
        '''
        d = ['S', 'D', 'W', 'M', 'Y']
        sp = s.split()
        print(sp)
        if len(sp) != 2:
            return False
        if sp[1] not in d:
            return False
        try:
            int(sp[0])
        except ValueError:
            return False
        return True

def getIb_Hist(symbol, end, interval='1 min'):
    '''
    Wrapper of getHistorical(symb,end, dur, interval, exchange). This method is designed for stocks.
            IB Data subscriptions may limit this to stocks only.  IB requires TWS or IBGW to send and receive 
            any data. 
    :params symb: The stock ticker  like 'SQ or AAPL
    :params end: The end datetime of your request
    :params interval: Candle length. Legitimate values are found in the BAR_SIZE property

    '''
    symb = symbol
    # daDate = end
    interval = interval
    daDur = "1 D"
    # interval = "1 min"
    # chart(symb, d, dur, interval)
    ib = TestApp()
    # def getHistorical(self, symbol, end, dur, interval, exchange='NASDAQ'):
    df = ib.getHistorical(symb, end=end, dur=daDur, interval=interval, exchange = 'NASDAQ')
    ib.disconnect()
    return df

def help():
    sig=df = 'ib.getHistorical(symb, end=end, dur=daDur, interval=interval, exchange = "NASDAQ")'

if __name__ == '__main__':
    end=dt.datetime.today()
    df=getIb_Hist('SQ', end=end, interval='5 mins')
    print(df)
