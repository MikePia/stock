'''
@author: Mike Petersen

@creation_date: 2018-12-23
'''

import datetime as dt
import unittest

from stock import myiex as iex
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
    if td.weekday() > 2:
        deltdays = deltdays + (td.weekday() - 2)
    elif td.weekday() == 0:
        deltdays = 12
    before = td - dt.timedelta(deltdays)
    return before
    # print(f"from {td.day} {td.strftime('%A')}: {before.day} {before.strftime('%A')} ")


class TestMyiex(unittest.TestCase):
    '''Test functions in module myiex'''

    def test_get_trading_chart(self):
        '''
        Test it returns value for stocks that exist and raises Exception
        for stocks that don't exist
        '''
        df = iex.get_trading_chart("AAPL")

        self.assertGreater(len(df), 0)

        self.assertRaises(Exception, iex.get_trading_chart, "SNOORK")

    def test_get_trading_chart_dates(self):
        '''Test that it correctly retrieves the right times and date as requested'''
        b = getPrevTuesWed(dt.datetime.today())
        before = f"{b.year}{b.month}{b.day}"
        start = "09:32"
        end = "15:59"
        df = iex.get_trading_chart("SQ", start, end, theDate=before)
        self.assertEqual(df.iloc[0]['date'], before)
        msg1 = f"Was the market open on {before} at {start}"
        msg2 = f"Was the market open on {before} at {end}"
        self.assertEqual(df.index[0], start, msg=msg1)
        self.assertEqual(df.index[-1], end, msg=msg2)

    def test_get_trading_chart_interval(self):
        '''Test the candle intvarls by subtracting strings processed into times'''
        intervals = [6, 60, 15]
        for interval in intervals:
            df = iex.get_trading_chart("SQ", minutes=interval)

            # HACK ALERT -- there has got to be a better way to find the differnce in minutes
            # of a time string ---
            min0 = df.index[0].split(":")
            min1 = df.index[1].split(":")

            (hour0, minute0) = (int(min0[0]), int(min0[1]))
            (hour1, minute1) = (int(min1[0]), int(min1[1]))

            t0 = dt.datetime(1111, 11, 11, hour0, minute0)
            t1 = dt.datetime(1111, 11, 11, hour1, minute1)

            delt = t1-t0
            interval_actual = delt.seconds//60
            self.assertEqual(interval_actual, interval)

    def test_get_historical_chart(self):
        '''Test we got about 5 years of data within about 1 week leeway'''
        df = iex.get_historical_chart("AAPL")
        today = dt.datetime.today()
        d = df.index[0].split("-")
        before = dt.datetime(int(d[0]), int(d[1]), int(d[2]))
        delt = today-before

        # Assert we got data within about a week more or less of 5 years
        self.assertGreater(delt.days, 1819)
        self.assertLess(delt.days, 1832)

        d = df.index[-1].split("-")
        recent = dt.datetime(int(d[0]), int(d[1]), int(d[2]))
        delt = today-recent

        # Assert we got data at least to 3 days ago (account for weekends etc)
        self.assertLess(delt.days, 3)

    def test_get_historical_chart_start(self):
        '''Checking the correct start and end dates given open market days for start and end'''
        dateArray = [(dt.datetime(2017, 3, 3), dt.datetime(2017, 11, 3)),
                     (dt.datetime(2016, 12, 27), dt.datetime(2017, 2, 26))]

        for start, end in dateArray:
            df = iex.get_historical_chart("TEAM", start, end)

            s = df.index[0].split("-")
            e = df.index[-1].split("-")

            (y, m, d) = (int(s[0]), int(s[1]), int(s[2]))
            (y1, m1, d1) = (int(e[0]), int(e[1]), int(e[2]))

            actualStart = dt.datetime(y, m, d)
            actualEnd = dt.datetime(y1, m1, d1)
            msg0 = f"Was the market open on {start}?"
            msg1 = f"Was the market open on {end}?"
            self.assertEqual(actualStart, start, msg0)
            self.assertEqual(actualEnd, end, msg1)
