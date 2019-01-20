'''
Test code for myalphavantage module.
@author: Mike Petersen
@creation_date: 1/15/19
'''
import datetime as dt
import unittest
from time import time, sleep

import pandas as pd

from stock import myalphavantage as mav
from stock import utilities as util
# pylint: disable = C0103

class TestMyalphavantage(unittest.TestCase):
    '''Test methods and functions from the modulemyalphavantage'''

    def test_getmav_intraday(self):
        '''
        This will provide time based failures on market holidays. If you are woking on a holiday,
        it serves you right :)
        '''

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
        minutes = '1min'

        dateArray = [(bizMorn, bizAft),
                     (bizMorn, None),
                     (bef, befAft),
                     (specificStart, specificEnd),
                     (befAft, None),
                     (longBef, None),
                     (None, None)
                    ]
        # dateArray2 = [(bizAft, None)]
        # now = pd.Timestamp.today()

        # Prevent more than 5 calls per minute, sleep after 5 for the remainder
        nextt = time() + 60
        count = 0
        for start, end in dateArray:

            # Each of these should get results every time,beginning times are either before 9:31 or
            # between 9:30 (short days won't produce failures)
            dummy, df = mav.getmav_intraday("SQ", start=start, end=end,
                                            minutes=minutes, showUrl=True)

            print("Requested...", start, end)
            print("Received ...", df.index[0], df.index[-1])
            print("     ", len(df))

            self.assertGreater(len(df), 0)

            if not start and not end:
                # This will retrieve the full set available. It should cover 5 days data.
                #  We will just test that the results cover 4 days and ends on the last biz day.
                # We are at the mercy of AV-- if they change, this should fail. (that's good)
                lt = df.index[-1]
                self.assertGreater((lt - df.index[0]).days, 3)
                lastDay = dt.datetime(lt.year, lt.month, lt.day)
                bizDay = pd.Timestamp(biz.year, biz.month, biz.day)
                self.assertEqual(lastDay, bizDay)
                start = df.index[0]

            # If the requested start time is before 9:31, start should be 9:31
            d = df.index[0]
            expected = dt.datetime(d.year, d.month, d.day, 9, 31)
            if start < expected:
                self.assertEqual(d, expected)
            else:
                self.assertEqual(d, start)

            # Could add some tests for what happens when request is for today during market hours

            if count %5 == 4:
                # After 5 calls, sleep. 5 calls per minute is the max for the free API
                newnextt = nextt-time()
                nx = int(newnextt)
                print(f'''Waiting for {nx} seconds. 5 calls per minute max
                       from AVantage free API''')
                if newnextt < 0:
                    # It took a minute plus to get through those 5 calls- reset for the next 5
                    nextt = time() + 60
                    continue
                nextt = newnextt
                sleep(nextt)

            count = count + 1

                # # Without getting too noodly, this code just won't run between 9 and 10
                # if nowInNewYork.hour < 9:
                #     self.assertEqual(len(df), 0)
                # elif nowInNewYork.hour > 9 and nowInNewYork.hour < 16:

                # check that we got content, from  the day we asked, at the beginning of the day,
                # ending now or at 16:00 or just now With a HACKED IN @ HOURS FOR tiME ZONE

                #     self.assertGreater(len(df), 0)
                #     self.assertEqual(bizMorn.date(), df.index[0].date())
                #     self.assertEqual(df.index[0].date(), df.index[-1].date())

                #     delt = (nowInNewYork - df.index[-1])
                #     self.assertLess(delt.seconds, 60*5)
                #     print(now, df.index[-1])
                #     print(delt.seconds)
                # else:
                #     quittingTime = dt.datetime(
                #         now.year, now.month, now.day, 16, 0)
                #     delt = quittingTime - df.index[-1]
                #     self.assertLess(delt.seconds, 60*5)

    def test_ni(self):
        '''
        Test the utility for mav
        '''
        self.assertEqual(mav.ni(3), '1min')
        self.assertEqual(mav.ni(45), '30min')
        self.assertEqual(mav.ni(112), '60min')
        self.assertEqual(mav.ni(11), '5min')
        self.assertEqual(mav.ni(0), '1min')
        self.assertEqual(mav.ni('gobbledegook'), '1min')

def notmain():
    '''Run some local code for dev'''
    m = TestMyalphavantage()
    m.test_getmav_intraday()


    # m.test_ni()
if __name__ == '__main__':
    notmain()
