'''
Test code for myalphavantage module. 
@author: Mike Petersen
@creation_date: 1/15/19
'''
import datetime as dt
import pandas as pd
from stock import myalphavantage as mav
import unittest

def getLastWorkDay(d=None):
    '''
    Retrieve the last biz day from today or d if the arg is given
    :params d: A datetime object.
    :return: A datetime object of the last biz day.
    '''
    now = dt.datetime.today() if not d else d
    deltDays = 0
    if now.weekday() > 4:
        deltDays = now.weekday() - 4
    bizday = now - dt.timedelta(deltDays)
    return bizday
getLastWorkDay(dt.datetime(2019,1,17))

class TestMyalphavantage(unittest.TestCase):

    def test_getmav_intraday(self):

        biz = getLastWorkDay()
        bizMorn = dt.datetime(biz.year, biz.month, biz.day, 7, 0) 
        bizAft = dt.datetime(biz.year, biz.month, biz.day, 16, 0)
        bef = getLastWorkDay(biz  - dt.timedelta(4))
        befAft = dt.datetime(bef.year, bef.month, bef.day, 16, 0)
        spec =  dt.datetime(biz.year, biz.month, biz.day, 9, 37)

        dateArray = [ (biz, bizAft),
                    (biz, None),
                    (None, bizAft)
                    ]
        minutes = '1min'

        # these should get the same content
        meta, df1 = mav.getmav_intraday("SQ", start=bizMorn, end=bizAft, minutes=minutes, showUrl=True)
        meta2, df2 = mav.getmav_intraday("SQ", start=bizMorn, end=None, minutes=minutes, showUrl=True)

        for df in [df1, df2]:
            now = pd.Timestamp.today()
            if now.date() == df.index[0].date():
                # If it is currently before 9:30, we should have no content
                #HACKALERT If you are running this in Hawaii, adjust this variable (or write some hack free code)
                ZONE_DIFF = 2
                nowInNewYork = dt.datetime(now.year, now.month, now.day, now.hour + ZONE_DIFF, now.minute )

                # Without getting too noodly, this code just won't run between 9 and 10
                if nowInNewYork.hour <  9:
                    self.assertEqual(len(df), 0)
                elif nowInNewYork.hour >  9 and nowInNewYork.hour < 16:

                    # check that we got content, from  the day we asked, at the beginning of the day, ending now or at 16:00
                    # or just now With a HACKED IN @ HOURS FOR tiME ZONE

                    self.assertGreater(len(df), 0)
                    self.assertEqual(bizMorn.date(), df.index[0].date())
                    self.assertEqual(df.index[0].date(), df.index[-1].date())
                
                    delt= (nowInNewYork - df.index[-1])
                    self.assertLess(delt.seconds, 60*5)
                    print( now, df.index[-1])
                    print(delt.seconds)
                else:
                    quittingTime = dt.datetime(now.year, now.month, now.day, 16, 0 )
                    delt = quittingTime - df.index[-1]
                    self.assertLess(delt.seconds, 60*5)
         
    def test_ni(self):
        self.assertEqual(mav.ni(3), '1min')
        self.assertEqual(mav.ni(45), '30min')
        self.assertEqual(mav.ni(112), '60min')
        self.assertEqual(mav.ni(11), '5min')
        self.assertEqual(mav.ni(0), '1min')
        self.assertEqual(mav.ni('gobbledegook'), '1min')
       
        # print
        # for start, end in dateArray:
        #     meta, df = mav.getmav_intraday("SQ", start=start, end=end, minutes=minutes, showUrl=True)
        #     print(df.close[-1])
        #     print(f'{minutes}   \n     x0: {df.index[0]} \n     x-1:{df.index[-1]} \n           len: {len(df)}')
        #     print(f'     start:{start}\n     end:{end}\n')
    

def notmain():
    m = TestMyalphavantage()
    # m.test_getmav_intraday()
    m.test_ni()
if __name__ == '__main__':
    notmain()        