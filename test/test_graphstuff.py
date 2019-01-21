'''
@author: Mike Petersen

@creation_date: 2019-01-17
'''
import datetime as dt
import unittest

import numpy as np
from stock.graphstuff import FinPlot
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
            dummy, df = fp.apiChooser()(symbol, start=start, end=end, minutes=minutes, showUrl=True)
            self.assertEqual(len(df.columns), 5)
            self.assertTrue(isinstance(df.index[0], dt.datetime))
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

def notmain():
    '''
    Local run stuff for dev
    '''
    t = TestGraphstuff()
    t.test_apiChooser()
    # print(getLastWorkDay(dt.datetime(2019, 1, 22)))



if __name__ == '__main__':
    notmain()
