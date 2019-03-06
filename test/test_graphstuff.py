'''
@author: Mike Petersen

@creation_date: 2019-01-17
'''
import datetime as dt
import os
import random
import types
import unittest

import numpy as np
import pandas as pd

from stock.graphstuff import FinPlot, dummyName
import stock.myib as ib

from stock import utilities as util
# pylint: disable = C0103


def getTicker():
    '''
    Get a random ticker symbol
    '''
    tickers = ['SQ', 'AAPL', 'TSLA', 'ROKU', 'NVDA', 'NUGT',
               'MSFT', 'CAG', 'ACRS', 'FRED', 'NFLX', 'MU', 'AAPL']
    return tickers[random.randint(0, 12)]


class TestGraphstuff(unittest.TestCase):
    '''
    Test functions and methods in the graphstuff module
    '''

    def __init__(self, *args, **kwargs):
        super(TestGraphstuff, self).__init__(*args, **kwargs)

        ddiirr = os.path.dirname(__file__)
        os.chdir(os.path.realpath(ddiirr + '/../'))

    def test_apiChooser(self):
        '''
        Test the method FinPlot.apiChooser for the same interface in each api
        '''
        fp = FinPlot()
        biz = util.getLastWorkDay()
        start = dt.datetime(biz.year, biz.month, biz.day, 12, 30)
        end = dt.datetime(biz.year, biz.month, biz.day, 16, 1)
        minutes = 1
        apis = fp.preferences
        symbol = 'SQ'
        for api in apis:
            fp.api = api
            result = fp.apiChooserList(start, end, api)
            if result[0]:
                dummy, df = fp.apiChooser()(symbol, start=start, end=end,
                                            minutes=minutes, showUrl=True)
                self.assertEqual(len(df.columns), 5,
                                 f"Failed to retrieve data with the {fp.api} api.")
                self.assertTrue(isinstance(df.index[0], dt.datetime),
                                f'Failed to set index to datetime in {fp.api} api')
                cols = ['open', 'high', 'low', 'close', 'volume']
                for col in cols:
                    # print(col, type(df[col][0]), isinstance(df[col][0], (np.float, np.integer)))
                    self.assertTrue(col in df.columns)
                    self.assertTrue(isinstance(
                        df[col][0], (np.float, np.integer)))

                # This call should retrieve data within 1 bar of the requested start and finish.
                # Idiosyncracies of the APIs vary as to inclusion of first and last time index
                delt = df.index[0] - \
                    start if df.index[0] > start else start - df.index[0]
                self.assertLessEqual(delt.seconds, minutes*60)

                print('Retrieved {} candles from {} to {} for {}'.format(
                    len(df), df.index[0], df.index[-1], symbol))
                print()
            else:
                print('Skipped {api} at {start} to {end} because...')
                for rule in result[1]:
                    print(rule)

    def test_dummyName(self):
        '''
        Testing method dummyName in the graphstuff module. This is temporary- it will move.
        '''
        fp = FinPlot()
        tradenum = 3
        symbol = 'AAPL'
        begin = '2019-01-20 08:30'
        end = '2019-01-20 15:15'
        n = dummyName(fp, symbol, tradenum, begin, end)
        self.assertTrue(n.find(fp.api) > 0)
        self.assertTrue(n.find(symbol) > 0)
        self.assertTrue(n.endswith(fp.ftype))
        self.assertTrue(n.find(fp.base) > 0,
                        "Check that outdir was sent to dummyName")

        # pylint: disable = W0104
        try:
            # Finding the assertRaises not reliable
            n = None
            tradenum = 'three'  # bad value
            n = dummyName(fp, symbol, tradenum, begin, end)
            self.assertTrue(n is None, 'Failed to raise ValueError')
        except ValueError:
            pass

        try:
            n is None
            tradenum = 4
            begin = '1019091212:13'  # bad timestamp
            n = dummyName(fp, symbol, tradenum, begin, end)
            self.assertTrue(n is None, 'Failed to raise ValueError')
        except ValueError:
            pass

        try:
            n is None
            begin = '2019-01-20 08:30'
            end = '2019012015:15'  # bad timestamp
            n = dummyName(fp, symbol, tradenum, begin, end)
            self.assertTrue(n is None, 'Failed to raise ValueError')
        except ValueError:
            pass

    def makeupEntries(self, symbol, start, end, minutes, fp):
        if not ib.isConnected():
            print()
            print("IB Gateway is not connected. Running this test",
                  "correctly depends on connecting IB Gateway.")
            print()
            return

        meta, df = ib.getib_intraday(symbol, start, end, minutes)
        entries = []
        exits = []
        for i in range(random.randint(2, 9)):
            candle = random.randint(0, len(df)-1)
            high = df.iloc[candle].high
            low = df.iloc[candle].low
            entry = ((high - low) * random.random()) + low
            x = int(minutes*60 * random.random())
            tix = df.index[candle]
            tix = tix + pd.Timedelta(seconds=x)

            if random.random() < .35:
                entries.append([entry, candle, minutes, tix])
            else:
                exits.append([entry, candle, minutes, tix])
        fp.entries = entries
        fp.exits = exits

    def test_graph_candlestick(self):
        '''
        Test the FinPlot.graph_candlestick method.
        '''
        fp = FinPlot()
        # fp.interactive = True
        fp.randomStyle = True

        # trades = [
        #     ['AAPL', 1, '2019-01-18 08:31', '2019-01-18 09:38', 1],
        #     ['AMD', 2, '2019-01-18 08:32', '2019-01-18 09:41', 1],
        #     ['NFLX', 3, '2019-01-18 09:39', '2019-01-18 09:46', 1],
        #     ['NFLX', 4, '2019-01-18 09:47', '2019-01-18 09:51', 1]]

        d = util.getPrevTuesWed(pd.Timestamp.now())
        # d = pd.Timestamp('2019-02-25')
        times = [['08:31', '09:38'],
                 ['08:32', '09:41'],
                 ['09:39', '12:46'],
                 ['09:47', '13:51']]

        tickers = []
        for i in range(4):
            tickers.append(getTicker())

        trades = []
        for count, (tick, time) in enumerate(zip(tickers, times)):
            start = d.strftime('%Y-%m-%d ') + time[0]
            end = d.strftime('%Y-%m-%d ') + time[1]
            trades.append([tick, count+1, start, end, 1])
            # print (trades[-1])
        for trade in trades:
            start, end = fp.setTimeFrame(trade[2], trade[3], trade[4])
            (dummy, rules, apilist) = fp.apiChooserList(trade[2], trade[3])
            print(f'{apilist}/n{rules}')
            minutes = 2
            self.makeupEntries(trade[0], start, end, minutes, fp)
            for api in apilist:
                fp.api = api
                # if api == 'iex':
                #     fp.interactive = True
                name = dummyName(fp, trade[0], trade[1], trade[2], trade[3])
                fp.graph_candlestick(
                    trade[0], start, end, minutes=minutes, save=name)
                cwd = os.getcwd()
                msg = 'error creating ' + name + " IN ", cwd
                self.assertTrue(os.path.exists(name), msg)

    def test_setTimeFrame(self):
        '''
        setTimeFrame will require usage to figure out the right settings. Its purpose is to frame
        the chart with enough time before and after the transactions to give perspective to the
        trade. Ideally, it will include some intelligence with trending information and evaluation
        of the highs and lows within the day. The point here is this method is not done.
        '''
        fp = FinPlot()
        early = dt.datetime(2019, 1, 19, 0, 0)
        late = dt.datetime(2019, 1, 19, 23, 55)
        odate = dt.datetime(2019, 1, 19, 9, 40)
        cdate = dt.datetime(2019, 1, 19, 16, 30)
        opening = dt.datetime(2019, 1, 19, 9, 30)
        closing = dt.datetime(2019, 1, 19, 16, 00)
        interval = 1
        interval2 = 60
        # tests dependent on interval -- setting to 1
        for i in range(1, 10):
            s, e = fp.setTimeFrame(odate, cdate, interval)
            s2, e2 = fp.setTimeFrame(odate, cdate, interval2)
            s3, e3 = fp.setTimeFrame(early, late, interval)
            if odate < opening:
                self.assertEqual(s, opening)
                self.assertEqual(s2, opening)
            else:
                delt = odate - s
                delt2 = odate - s2
                self.assertLess(delt.seconds, 3600)
                self.assertLess(delt2.seconds, 3600 * 3.51)
            if early < opening:
                self.assertEqual(s3, opening)
            if late > closing:
                self.assertEqual(e3, closing)
            mins = 40
            odate = odate + dt.timedelta(0, mins * 60)
            cdate = cdate - dt.timedelta(0, mins * 60)
            early = early + dt.timedelta(0, mins * 60)
            late = late - dt.timedelta(0, mins * 60)


def main():
    '''
    test discovery is not working in vscode. Use this for debugging. Then run cl python -m unittest
    discovery
    '''
    f = TestGraphstuff()
    for name in dir(f):
        if name.startswith('test'):
            attr = getattr(f, name)
            if isinstance(attr, types.MethodType):
                attr()


def notmain():
    '''
    Local run stuff for dev
    '''
    t = TestGraphstuff()
    # t.test_apiChooser()
    # t.test_dummyName()
    t.test_graph_candlestick()
    # print(getLastWorkDay(dt.datetime(2019, 1, 22)))
    # t.test_setTimeFrame()


if __name__ == '__main__':
    notmain()
    # main()
