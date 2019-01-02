import datetime as dt

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.common import *
from ibapi.contract import *

import pandas as pd
import time

ID_COUNTER = 1500

# Needs to be a string in the form '3 D'
DURATION_STRING = ['S', 'D', 'W', 'M', 'Y']


BAR_SIZE = ['1 secs', '5 secs', '10 secs', '15 secs', '30 secs',
            '1 min', '2 mins', '3 mins', '5 mins', '10 mins', '15 mins', '20 mins', '30 mins',
            '1 hour', '2 hours', '3 hours', '4 hours', '8 hours',
            '1 day', '1 week', '1 month']

GDF=None


def validateDurString(s):
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

class Ib(EWrapper, EClient):
    '''
    Override the needed methods
    '''
    def __init__(self):
        EClient.__init__(self, self)
        self.counter = 0
        self.data = []

    def error(self, reqId: TickerId, errorCode: list, errorString: str):
        print(f"Error: {reqId} {errorCode} {errorString}")

    def contractDetails(self, reqId, contractDetails):
        print(f"ContractDetails: {reqId} {contractDetails}")

    # ! [historicaldata]
    def historicalData(self, reqId: int, bar):
        if self.counter == 0:
            print("beginning")
#             print("originally Type:", type(bar))
            l=[]
            l.append(bar)
            print('time', bar.date)
        self.counter = self.counter + 1
        self.data.append([bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume])
        
        # print(reqId, bar)
    # ! [historicaldata]

    # ! [historicaldataend]
    def historicalDataEnd(self, reqId: int, start: str, end: str):
        super().historicalDataEnd(reqId, start, end)
        print("HistoricalDataEnd. ReqId:", reqId, "from", start, "to", end)
        print("GOT LINES:", len(self.data))
        print("TYPE:", type(self.data[0]))
        df = pd.DataFrame(self.data, columns = ['date', 'open', 'high', 'low', 'close', 'volume'])
        GDF=df
        print(df)
#         print(df.tail(2))
        exit()
    # ! [historicaldataend]

def getHistorical(symbol, end, dur, interval):
    '''
    :params end: datetime object for the end time requested
    :params dur: a string for how long before end should the chart begin "1 D"
    :params interval: candle len
    '''

    if validateDurString(dur) == False:
        print("Duration must be formatted like '3 D' using S, D, W, M, or Y")
        return None

    if not isinstance(end, dt.datetime):
        print("end must be formatted as a datetime object")
        return None

    if interval not in BAR_SIZE:
        print('Bar size must be one of: {}'.format(interval))
        return None

    app = Ib()
    host = "127.0.0.1"
    port = 7496
    clientId = 7878
    app.connect(host, port, clientId)

    contract = Contract()
    contract.symbol = symbol
    contract.secType = "STK"
    contract.exchange = "SMART"
    contract.currency = "USD"
    contract.primaryExchange = "NASDAQ"

    # app.reqContractDetails(10, contract)

    timeStr = end.strftime('%Y%m%d %H:%M:%S')
    # self.reqHistoricalData(18002, ContractSamples.ContFut(), timeStr, "1 Y", "1 month", "TRADES", 0, 1, False, []);
    # queryTime = DateTime.Now.AddMonths(-6).ToString("yyyyMMdd HH:mm:ss");
    app.reqHistoricalData(4001, contract, timeStr, dur,
                          interval, "TRADES", 1, 1, False, [])
    # client.reqHistoricalData(4002, ContractSamples.EuropeanStock(), queryTime, "10 D", "1 min", "TRADES", 1, 1, false, null);

    app.run()

symb = "SQ"
d = dt.datetime(2018, 12, 27, 9, 0)
dur = "1 D"
interval = "1 min"
# chart(symb, d, dur, interval)
ib = Ib()
getHistorical(symb, d, dur, interval)