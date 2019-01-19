'''
@author: Mike Petersen

@creation_date: 2019-01-17
'''
import datetime as dt
import unittest

import numpy as np
from stock.graphstuff import FinPlot
# pylint: disable = C0103

def getLastWorkDay(d=None):
    '''
    Retrieve the last biz day from today or from d if the arg is given
    :params d: A datetime object.
    :return: A datetime object of the last biz day.
    '''
    now = dt.datetime.today() if not d else d
    deltDays = 0
    if now.weekday() > 4:
        deltDays = now.weekday() - 4
    bizday = now - dt.timedelta(deltDays)
    return bizday

class TestGraphstuff(unittest.TestCase):
    '''
    Test functions and methods in the graphstuff module
    '''

    def test_apiChooser(self):
        '''
        Test the method FinPlot.apiChooser for the same interface in each api
        '''
        fp = FinPlot()
        fp.api = 'iex'
        biz = getLastWorkDay()
        start = dt.datetime(biz.year, biz.month, biz.day, 12, 30)
        end = dt.datetime(biz.year, biz.month, biz.day, 16, 1)
        x, df = fp.apiChooser()('SQ', start=start, end=end, showUrl=True)
        self.assertEqual(len(df.columns), 5)
        cols = ['open', 'high', 'low', 'close', 'volume']
        for col in cols:
            # print(col, type(df[col][0]), isinstance(df[col][0], (np.float, np.integer)))
            self.assertTrue(col in df.columns)
            self.assertTrue(isinstance(df[col][0], (np.float, np.integer)))
        
        self.assertTrue(isinstance(df.index[0], dt.datetime))
        
        print(df.columns)
        print(df.dtypes)
        print(type(df.index[0]))
        print(len(df))
        print(x)
        print(df.index[0])
        print(df.index[-1])

def notmain():
    '''
    Local run stuff for dev
    '''
    t = TestGraphstuff()
    t.test_apiChooser()
    # print(getLastWorkDay(dt.datetime(2019, 1, 22)))



if __name__ == '__main__':
    notmain()
