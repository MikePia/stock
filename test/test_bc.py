'''
@author: Mike Petersen

@creation_date: 2019-01-14
'''

import datetime as dt
import unittest
import pandas as pd

from stock import mybarchart as bc
import inspect
# from itertools import ifilter
# pylint: disable = C0103
# pylint: disable = R0914


def getPrevTuesWed(td):
    '''
    Utility method to get a probable market open day prior to td. The least likely
    closed days are Tuesday and Wednesday. This will occassionally return  a closed
    day but wtf.
    :params td: A Datetime object
    '''
    deltdays = 7
    if td.weekday() == 0:
        deltdays = 5
    elif td.weekday() < 3:
        deltdays = 0
    elif td.weekday() < 5:
        deltdays = 2
    else:
        deltdays = 4
    before = td - dt.timedelta(deltdays)
    return before


class TestMybarchart(unittest.TestCase):
    '''
    Test functions in module bybarchart
    '''

    def test_getbc_intraday(self):
        '''
        This API will not retrieve todays data until 15 minutes after close. Given todays date at 14:00
        it will retrive the previous business days stuff. 
        '''

        # def test_getbc_intraday(self):
        now = dt.datetime.today()
        tomorrow= now + dt.timedelta(1)
        y = now - dt.timedelta(1)
        ymorn = dt.datetime(y.year, y.month, y.day, 7, 30)
        yaft = dt.datetime(y.year, y.month, y.day, 17, 30)
        ymorn = getPrevTuesWed(ymorn)
        yaft = getPrevTuesWed(yaft)
        beginDay = dt.datetime(now.year, now.month, now.day, 9,30)
        endDay = dt.datetime(now.year, now.month, now.day, 16,0)

        # These should all retrieve the same data. No start date and today trigger a 1 
        # day query for the most current biz day (which may be yesterday if its before 16:30 on Tuesday)
        dateArray = [(None, None),
                    (beginDay, None),
                    (None, endDay),
                    (beginDay, endDay),
                    (None, tomorrow)] # Same as both None
        
        #? I think the first gets more than one day (from start to current) and the second gets one historical day
        dateArray2 = [(ymorn, None), (ymorn, yaft)]

        # These should retrive 0 results with no Exception
        dateArray3 = [(None, yaft), (tomorrow, None)]

        bdays=list()
        # edays=list()
        for start, end in dateArray:
            x, df = bc.getbc_intraday('SQ', start=start, end=end, showUrl = True)
            if x['code'] == 666:
                print('Abandon all hope of retrieving barchart data today. You have run out of free queries')
                return
            self.assertGreater(len(df), 0)
            bdays.append((df.index[0], df.index[-1]))
        for i in range(len(bdays) - 1):
            self.assertEqual(bdays[i][0], bdays[i+1][0])
            self.assertEqual(bdays[i][1], bdays[i+1][1])

        for start, end in dateArray2:
            x, df = bc.getbc_intraday('SQ', start=start, end=end)
            self.assertGreater(len(df), 0)

        for start, end in dateArray3:
            x, df = bc.getbc_intraday('SQ', start=start, end=end)
            # print(df)
            # print(len(df.index))
            print(x['message'])
            self.assertEqual(len(df), 0)

    def test_getbc_intraday_interval(self):
        '''Test the candle intvarls by subtracting strings processed into times'''
        intervals = [2, 6, 60, 15]
        for interval in intervals:
            x, df = bc.getbc_intraday("SQ", minutes=interval)

            # HACK ALERT -- there has got to be a better way to find the differnce in minutes
            # of a time string ---
            min0 = df.index[0]
            min1 = df.index[1]

            self.assertEqual((min1-min0).seconds, interval*60)

def main():
    '''test discovery is not working in vscode. Use this for debugging. Then run cl python -m unittest discovery'''
    f = TestMybarchart()
    for name in dir(f):
        if name.startswith('test'):
            attr = getattr(f, name)
            class B(): 
                def a():pass
            b=B()
            if isinstance(attr, type(b.a)):
                attr()

def notmain():
    f = TestMybarchart()
    # f.test_getbc_intraday()
    f.test_getbc_intraday_interval()

if __name__ == '__main__':
    main()
    # notmain()

    