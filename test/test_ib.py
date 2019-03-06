'''
@author: Mike Petersen

@creation_date: 2018-12-23
'''

import datetime as dt
import random
import unittest
import pandas as pd

from stock import myib as ib
from stock import utilities as util
# pylint: disable = C0103


class TestMyib(unittest.TestCase):
    '''
    Test methods and functions in the myib module
    This will currently retrive only market hours data. It will match the other APIs. But we 
    can and should accomodate after hours data even with API chooser.
    '''

    def test_ni(self):
        '''
        Test the function ni. The purpose of ni is to format the interval paramete correctly'''
        print(ib.ni(13))
        tests = [([1, '1', '1 min'], '1 min'),
                 ([2, '2', '2 mins'], '2 mins'),
                 ([3, '3', '3 mins'], '3 mins'),
                 ([4], '3 mins'),
                 ([5, '5', '5 mins'], '5 mins'),
                 ([6], '5 mins'),
                 ([7], '5 mins'),
                 ([8], '5 mins'),
                 ([9], '5 mins'),
                 ([10, '10', '10 mins'], '10 mins'),
                 ([11], '10 mins'),
                 ([12], '10 mins'),
                 ([13], '10 mins'),
                 ([14], '10 mins'),
                 ([15, '15', '15 mins'], '15 mins'),
                 ([16], '15 mins'),
                 ([20, '20', '20 mins'], '20 mins'),
                 ([21], '20 mins'),
                 ([30, '30', '30 mins'], '30 mins'),
                 ([31], '30 mins'),

                 ([60, '60', '1 hour'], '1 hour'),
                 ([61], '1 hour'),



                 (['gg', '0bledygook'], '1 min')]

        for x in tests:
            for xx in x[0]:
                print(f'From {xx}, and expecting {x[1]}  ....   {ib.ni(xx)}')
                self.assertEqual(ib.ni(xx), x[1])

    def test_getib_intraday(self):
        '''
        This will provide time based failures on market holidays. If you are woking on a holiday,
        it serves you right :)
        '''
        if not ib.isConnected():
            msg = 'IB is not connected. TestMyib cannot run'
            self.assertTrue(ib.isConnected(), msg)
            return

        biz = util.getLastWorkDay()
        bizMorn = dt.datetime(biz.year, biz.month, biz.day, 7, 0)
        bizAft = dt.datetime(biz.year, biz.month, biz.day, 16, 1)
        bef = util.getLastWorkDay(bizMorn - dt.timedelta(1))
        befAft = dt.datetime(bef.year, bef.month, bef.day, 16, 1)
        specificStart = dt.datetime(biz.year, biz.month, biz.day, 9, 37)
        specificEnd = dt.datetime(biz.year, biz.month, biz.day, 11, 37)
        longBef = util.getLastWorkDay(bizMorn - dt.timedelta(10))
        # longBefAft = dt.datetime(longBef.year, longBef.month, longBef.day, 16, 1)

        # dateArray = [(biz, bizAft), (biz, None), (None, bizAft) ]
        minutes = random.randint(1,10)

        dateArray = [(bizMorn, bizAft),
                     (bizMorn, None),
                     (bef, befAft),
                     (specificStart, specificEnd),
                     (befAft, None),
                     (longBef, None),
                     (None, None)
                    ]

        for start, end in dateArray:

            # Each of these should get results every time,beginning times are either before 9:31 or
            # between 9:30 (short days won't produce failures)
            l, df = ib.getib_intraday("SQ", start=start, end=end,
                                            minutes=minutes, showUrl=True)

            print("Requested...", start, end)
            print("Received ...", df.index[0], df.index[-1])
            print("     ", l)

            self.assertGreater(l, 0)
            delt = int((df.index[1] - df.index[0]).total_seconds()/60)
            self.assertEqual(delt, minutes)


            # If the requested start time is before 9:30, start should be 9:30
            d = df.index[0]
            expected = dt.datetime(d.year, d.month, d.day, 9, 30)
            if start < expected:
                self.assertEqual(d, expected)
            else:
                # The start should be within the amount of the candle length
                # if d != start:
                delt = pd.Timedelta(minutes=minutes)
                delt2 = d - start if d > start else start - d
                self.assertLessEqual(delt2, delt)


def notmain():
    '''Run some local code'''
    t = TestMyib()
    # t.test_ni()
    t.test_getib_intraday()


if __name__ == '__main__':
    notmain()
