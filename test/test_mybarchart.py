'''
@author: Mike Petersen

@creation_date: 2019-01-14
'''

import datetime as dt
import types
import unittest
import pandas as pd

from stock import mybarchart as bc
from stock import utilities as util
# import inspect
# from itertools import ifilter
# pylint: disable = C0103
# pylint: disable = R0914
# pylint: disable = C0111


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
        This API will not retrieve todays data until 15 minutes after close. It may not retrieve
        all of yesterday till after close today
        '''

        # def test_getbc_intraday(self):
        now = dt.datetime.today()
        nowbiz = util.getLastWorkDay()          # We want to retrieve a day with data for testing here
        tomorrow = now + dt.timedelta(1)
        y = now - dt.timedelta(1)
        ymorn = dt.datetime(y.year, y.month, y.day, 7, 30)
        yaft = dt.datetime(y.year, y.month, y.day, 17, 30)
        ymorn = getPrevTuesWed(ymorn)
        yaft = getPrevTuesWed(yaft)
        beginDay = dt.datetime(now.year, now.month, now.day, 9, 30)
        endDay = dt.datetime(now.year, now.month, now.day, 16, 0)

        # These should all retrieve the same data. unless the day is today before 4:30. No start
        # date and today trigger a 1day query
        # for the most current biz day (which may be yesterday if its before 16:30 on Tuesday)
        dateArray = [(None, None),
                     (beginDay, None),
                     (None, endDay),
                     (beginDay, endDay),
                     (None, tomorrow),
                     (ymorn, yaft),
                     (None, yaft),
                     (ymorn, None)]  # Same as both None

        dateArray2 = [(ymorn, None), (ymorn, yaft)]

        # These should retrive 0 results with no Exception
        dateArray3 = [(None, yaft), (tomorrow, None)]

        bdays = list()
        # edays=list()
        interval=5
        for start, end in dateArray:
            x, df = bc.getbc_intraday('SQ', start=start, end=end, showUrl=True)
            if x['code'] == 666:
                print('Abandon all hope of retrieving barchart data today.\n',
                      'You have run out of free queries.')
                return
            if not start or start.date() == now.date():
                magictime = pd.Timestamp(now.year, now.month, now.day, 16, 30)
                if now.time() < magictime.time():
                    self.assertTrue(df.empty)
                    continue
                else:
                    print('wtf', start, now)
            
            else:        
                self.assertGreater(len(df), 0)
                bdays.append((df.index[0], df.index[-1]))

            # Given start == None, barchart returns data from previous weekday (holidays ignored)
            now = pd.Timestamp.today()
            if not start:
                start = df.index[0]
                if now.isoweekday() > 5:
                    self.assertLess(df.index[0].isoweekday(), 6, "Is it a holiday? Go party now!")
            s = pd.Timestamp(start.year, start.month, start.day, 9, 29)
            e = pd.Timestamp(start.year, start.month, start.day, 16, 1)
            if start > s and start < e:
                self.assertEqual(df.index[0], start)

            msg = f'\nInput: {end} \nTest:  <> {e} \nIndex{df.index[-1]}'
            # print(msg)
            # Very internal noodly but barchart last index is always the next to the last time aka end - interval
            if end and end > s and end < e:
                end2 = end - pd.Timedelta(minutes=interval)
                msg = f'\nInput: {end} \nTest:  {e} \nIndex: {df.index[-1]}'
                delt = df.index[-1] - end if df.index[-1] > end else end - df.index[-1]

                self.assertLessEqual(int(delt.total_seconds()), interval*60)
                # self.assertEqual(df.index[-1], end2, msg)

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
        start = getPrevTuesWed(pd.Timestamp.today())
        for interval in intervals:
            dummy, df = bc.getbc_intraday("SQ", start=start, minutes=interval)

            # of a time string ---
            min0 = df.index[0]
            min1 = df.index[1]

            self.assertEqual((min1-min0).seconds, interval*60)


def main():
    '''test discovery is not working in vscode. Use this code for debugging.
    Then run cl python -m unittest discovery'''
    f = TestMybarchart()
    for name in dir(f):
        if name.startswith('test'):
            attr = getattr(f, name)

            class B():
                def a(self):
                    pass
            b = B()
            if isinstance(attr, type(b.a)):
                attr()


def notmain():
    '''Run some local stuff'''
    f = TestMybarchart()
    f.test_getbc_intraday()
    # f.test_getbc_intraday_interval()


if __name__ == '__main__':
    main()
    # notmain()
