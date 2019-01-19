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


class TestMyalphavantage(unittest.TestCase):
    '''Test methods and functions from the modulemyalphavantage'''

    def test_getmav_intraday(self):
        '''
        This will provide time based failures on market holidays. If you are woking on a holiday, 
        it serves you right :)
        '''

        biz = getLastWorkDay()
        bizMorn = dt.datetime(biz.year, biz.month, biz.day, 7, 0)
        bizAft = dt.datetime(biz.year, biz.month, biz.day, 16, 1)
        bef = getLastWorkDay(bizMorn - dt.timedelta(1))
        befAft = dt.datetime(bef.year, bef.month, bef.day, 16, 1)
        specificStart = dt.datetime(biz.year, biz.month, biz.day, 9, 37)
        specificEnd = dt.datetime(biz.year, biz.month, biz.day, 11, 37)
        longBef = getLastWorkDay(bizMorn - dt.timedelta(10))
        longBefAft = dt.datetime(longBef.year, longBef.month, longBef.day, 16, 1)

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
        dateArray2=[(bizAft, None)]
        now = pd.Timestamp.today()

        # Prevent more than 5 calls per minute, sleep after 5 for the remainder
        nextt = time() + 60
        count = 0
        for start, end in dateArray:

            # Each of these should get results every time,beginning times are either before 9:31 or
            # between 9:30 (short days won't produce failures)
            dummy, df = mav.getmav_intraday("SQ", start=start, end=end, minutes=minutes, showUrl=True)

            print("Requested...",  start, end)
            print("Received ...",  df.index[0], df.index[-1])
            print("     ", len(df))

            self.assertGreater(len(df), 0)

            # If the requested start time is befor 9:31 (an idiosyncracy of av-it begins 
            # (currently) at 9:31. Maybe they give the end of candle time.
            d = df.index[0]
            expected = dt.datetime(d.year, d.month, d.day, 9,31)
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

            if start < expected:
                self.assertEqual(d, expected)
            else:
                self.assertEqual(d, start)



            
                # If the request is for today, process here.
                # it is currently before 9:30, we should have no content
                # HACKALERT If you are running this in Hawaii, adjust this variable (or write some 
                #   hack free code)
            ZONE_DIFF = 2
            nowInNewYork = dt.datetime(now.year, now.month, now.day, 
                                       (now.hour + ZONE_DIFF) % 24, now.minute)

            # print("Now in NY", nowInNewYork)
            # print("Requested...",  start, end)
            # print("Received ...",  df.index[0], df.index[-1])
            # print("     ", len(df))
            if count %5 == 4:
                '''After 5 calls, sleep. 5 calls per minute is the max for the free API'''
                newnextt = nextt-time()
                print(f'Waiting for {int(newnextt)} seconds. 5 calls per minute allowed from Alpha Vantage free API')
                if newnextt < 0:
                    # It took a minute plus to get through those 5 calls- reset for the next 5
                    nextt = time() + 60
                    continue
                nextt = newnextt
                sleep(nextt)

            count = count+1             

                # # Without getting too noodly, this code just won't run between 9 and 10
                # if nowInNewYork.hour < 9:
                #     self.assertEqual(len(df), 0)
                # elif nowInNewYork.hour > 9 and nowInNewYork.hour < 16:

                #     # check that we got content, from  the day we asked, at the beginning of the day, ending now or at 16:00
                #     # or just now With a HACKED IN @ HOURS FOR tiME ZONE

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
