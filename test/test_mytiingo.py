# Structjour -- a daily trade review helper
# Copyright (C) 2019 Zero Substance Trading
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

'''
Test code for mytiingo module.
@author: Mike Petersen
@creation_date: 12/11/20
'''

import unittest
import random
import datetime as dt
from structjour.stock.mytiingo import Tingo_REST
from structjour.stock.utilities import getPrevTuesWed

class TestTingo_REST(unittest.TestCase):
    '''Test methods and functions from the Tingo_REST class'''
    tickers = ['NIO', 'BA', 'ACB', 'IMMP', 'TSLA', 'XPEV', 'PLTR', 'GME', 'APPL', 'NCLH', 'CCL']

    def test_getMetadata(self):
        t = Tingo_REST()
        r = t.getMetadata(self.tickers[random.randint(0, len(self.tickers)-1)])
        for x in ['startDate', 'endDate', 'exchangeCode', 'name', 'ticker', 'description']:
            self.assertIsNotNone(r[x])

    def test_getMetadata_fail(self):
        t = Tingo_REST()
        r = t.getMetadata('SCHNORK')
        self.assertEqual(r['code'], 404)
        self.assertIsInstance(r['message'], str)

    def test_getLatestprice(self):
        t = Tingo_REST()
        r = t.getLatestprice(self.tickers[random.randint(0, len(self.tickers)-1)])
        self.assertEqual(len(r), 1)
        for x in ['open', 'high', 'low', 'close', 'volume', 'date']:
            self.assertIsNotNone(r[0][x])
    

    def test_getLatestprice_fail(self):
        t = Tingo_REST()
        r = t.getLatestprice('SCHNORK')
        self.assertEqual(r['code'], 404)
        self.assertIsInstance(r['message'], str)

    def test_getHistoricalDailyPrice(self):
        daticks = self.tickers.copy()
        daticks.remove('IMMP')  # Too new of an IPO
        start = dt.datetime.today() - dt.timedelta(days=180)
        end = dt.datetime.today() - dt.timedelta(days=150)
        t = Tingo_REST()
        r = t.getHistoricalDailyPrice(daticks[random.randint(0, len(daticks)-1)], start, end)
        self.assertTrue(set(['date', 'open', 'low', 'high', 'close', 'volume']).issubset(r[0].keys()))
        s = dt.datetime.strptime(r[0]['date'], '%Y-%m-%dT%H:%M:%S.000Z')
        e = dt.datetime.strptime(r[-1]['date'], '%Y-%m-%dT%H:%M:%S.000Z')
        self.assertGreater(e-s, dt.timedelta(days=27))
        self.assertLess(e-s, dt.timedelta(days=31))

    def test_getHistoricalDailyPrice_fail(self):
        start = dt.datetime.today() - dt.timedelta(days=180)
        end = dt.datetime.today() - dt.timedelta(days=150)
        t = Tingo_REST()
        r = t.getHistoricalDailyPrice('SCHNORK', start, end)
        self.assertEqual(r['code'], 404)
        self.assertIsInstance(r['message'], str)

    def test_getIntraday(self):
        '''
        Test the usual case, Get chart data for an equity on a particular day/time
        During regular trading hours within the last 2 months
        Test that the result start and end are within the candle interval
        '''
        dayspast = random.randint(0,60)
        d = dt.datetime.today() - dt.timedelta(days=dayspast)
        d = getPrevTuesWed(d)
        start = dt.datetime(d.year, d.month, d.day, 9, 31, 2)
        end = dt.datetime(d.year, d.month, d.day, 12, 31, 2)
        interval = random.randint(1,15)
        ticker = self.tickers[random.randint(0, len(self.tickers)-1)]

        t = Tingo_REST()
        meta, df, maDict  = t.getIntraday(ticker, start, end, interval)
        startdiff = df.index[0]-start if df.index[0] >= start else start-df.index[0]
        enddiff = df.index[-1]-end if df.index[-1] >= end else end-df.index[-1]
        self.assertLessEqual((startdiff.seconds) // 60, interval)
        self.assertLessEqual((enddiff.seconds) // 60, interval)


if __name__ == '__main__':
    t = TestTingo_REST()
    # t.test_getHistoricalDailyPrice()
    # t.test_getHistoricalDailyPrice_fail()
    # t.test_getLatestprice_fail()
    t.test_getIntraday()
    print()


