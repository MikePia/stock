'''
@author: Mike Petersen

@creation_date: 2019-01-17
'''
import datetime as dt
import unittest

import numpy as np
from stock.graphstuff import FinPlot, dummyName
from stock import utilities as util
# pylint: disable = C0103

class TestGraphstuff(unittest.TestCase):
    '''
    Test functions and methods in the graphstuff module
    '''

    def test_apiChooser(self):
        '''
        Test the method FinPlot.apiChooser for the same interface in each api
        '''
        fp = FinPlot()
        biz = util.getLastWorkDay()
        start = dt.datetime(biz.year, biz.month, biz.day, 12, 30)
        end = dt.datetime(biz.year, biz.month, biz.day, 16, 1)
        minutes = 1
        apis = ['iex', 'mav', 'bc', 'ib']
        symbol = 'SQ'
        for api in apis:
            fp.api = api
            result = fp.apiChooserList(start, end, api)
            if result[0]:
                dummy, df = fp.apiChooser()(symbol, start=start, end=end, minutes=minutes, showUrl=True)
                self.assertEqual(len(df.columns), 5, f"Failed to retrieve data with the {fp.api} api")
                self.assertTrue(isinstance(df.index[0], dt.datetime),
                                f'Failed to set index to datetime in {fp.api} api')
                cols = ['open', 'high', 'low', 'close', 'volume']
                for col in cols:
                    # print(col, type(df[col][0]), isinstance(df[col][0], (np.float, np.integer)))
                    self.assertTrue(col in df.columns)
                    self.assertTrue(isinstance(df[col][0], (np.float, np.integer)))

                # This call should retrieve data within 1 bar of the requested start and finish.
                # Idiosyncracies of the APIs vary as to inclusion of first and last time index
                delt = df.index[0] - start if df.index[0] > start else start - df.index[0]
                self.assertLessEqual(delt.seconds, minutes*60)

                print(f'Retrieved {len(df)} candles from {df.index[0]} to {df.index[-1]} for {symbol}')
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
        self.assertTrue(n.find(fp.base) > 0, "Check that outdir was sent to dummyName")

        # pylint: disable = W0104
        try:
            # Finding the assertRaises not reliable
            n = None
            tradenum = 'three'          #bad value
            n = dummyName(fp, symbol, tradenum, begin, end)
            self.assertTrue(n is None, 'Failed to raise ValueError')
        except ValueError:
            pass

        try:
            n is None
            tradenum = 4
            begin = '1019091212:13'       #bad timestamp
            n = dummyName(fp, symbol, tradenum, begin, end)
            self.assertTrue(n is None, 'Failed to raise ValueError')
        except ValueError:
            pass

        try:
            n is None
            begin = '2019-01-20 08:30'
            end = '2019012015:15'       #bad timestamp
            n = dummyName(fp, symbol, tradenum, begin, end)
            self.assertTrue(n is None, 'Failed to raise ValueError')
        except ValueError:
            pass

    def test_graph_candlestick(self):
        '''
        Test the FinPlot.graph_candlestick method.
        '''
        fp = FinPlot()
        fp.randomStyle = True

        trades = [
            ['AAPL', 1, '2019-01-18 08:31', '2019-01-18 09:38', 1],
            ['AMD', 2, '2019-01-18 08:32', '2019-01-18 09:41', 1],
            ['NFLX', 3, '2019-01-18 09:39', '2019-01-18 09:46', 1],
            ['NFLX', 4, '2019-01-18 09:47', '2019-01-18 09:51', 1]]
        for trade in trades:
            start, end = fp.setTimeFrame(trade[2], trade[3], trade[4] )
            name = dummyName(fp, trade[0], trade[1], trade[2], trade[3])
            fp.graph_candlestick(trade[0], start, end, save=name)

    def test_setTimeFrame(self):
        '''
        setTimeFrame will require usage to figure out the right settings. Its purpose is to frame
        the chart with enough time before and after the transactions to give perspective to the
        trade. Ideally, it will include some intelligence with trending information and evaluation
        of the highs and lows within the day. The point here is this method is not done. 
        '''
        fp = FinPlot()
        odate = dt.datetime(2019, 1,19, 9, 40)
        cdate = dt.datetime(2019, 1,19, 16, 30)
        opening = dt.datetime(2019, 1, 19, 9, 30)
        closing = dt.datetime(2019, 1, 19, 16, 00)
        interval = 1
        interval2 = 60
        #tests dependent on interval -- setting to 1
        for i in range(1, 10):
            s,e  = fp.setTimeFrame(odate, cdate, interval)
            s2,e2  = fp.setTimeFrame(odate, cdate, interval2)
            if odate < opening:
                self.assertEqual(s, opening)
                self.assertEqual(s2, opening)
            else:
                delt = odate - s
                delt2 = odate - s2
                self.assertLess(delt.seconds, 3600)
                self.assertLess(delt2.seconds, 3600 * 3.1)
            mins =  40
            odate = odate + dt.timedelta(0, mins * 60)
            cdate = cdate - dt.timedelta(0, mins * 60)

def main():
    '''test discovery is not working in vscode. Use this for debugging. Then run cl python -m unittest discovery'''
    f = TestGraphstuff()
    for name in dir(f):
        if name.startswith('test'):
            attr = getattr(f, name)
            if isinstance(attr, type(f.test_apiChooser)):
                attr()


def notmain():
    '''
    Local run stuff for dev
    '''
    t = TestGraphstuff()
    # t.test_apiChooser()
    # t.test_dummyName()
    # t.test_graph_candlestick()
    # print(getLastWorkDay(dt.datetime(2019, 1, 22)))
    t.test_setTimeFrame()



if __name__ == '__main__':
    # notmain()
    main()
