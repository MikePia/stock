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
Local utility functions shared by some stock modules and test code.

@author: Mike Petersen

@creation_date: 2019-01-17
'''

from collections import OrderedDict
import datetime as dt
import logging

import os
import random
import sys

from structjour.models.meta import ModelBase
from structjour.models.api_keymodel import ApiKey

import numpy as np
import pandas as pd
from sqlalchemy.sql import text
from PyQt5.QtCore import QSettings, QDate, QDateTime
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QIcon


def setLimitReached(token, resetTime, settings=None):
    if token not in ['av', 'bc', 'fh']:
        raise ValueError(f'Not a valid stock api token: {token}')
    if settings is None:
        settings = QSettings('zero_substance/stockapi', 'structjour')
    token = token + 'limitreached'
    resetTime = pd.Timestamp(resetTime)
    now = pd.Timestamp.now()
    if now > resetTime:
        settings.remove(token)
    else:
        settings.setValue(token, resetTime)


def getLimitReached(token, settings=None):

    if token not in ['av', 'bc', 'fh', 'tgo']:
        raise ValueError(f'Not a valid stock api token: {token}')
    if token == 'tgo':
        # Tiingo limit is 500/hr, 20k/month. For now while building it, treat as no limit
        return False
    if settings is None:
        settings = QSettings('zero_substance/stockapi', 'structjour')

    resetTime = settings.value(token + 'limitreached', None)
    if resetTime is None: return False

    now = pd.Timestamp.now()
    if now <= resetTime:
        return True
    settings.remove(token + 'limitreached')
    return False


def qtime2pd(qdt):
    '''Return a pandas Timestamp from a QDateTime'''
    if isinstance(qdt, QDateTime):
        d = pd.Timestamp(qdt.date().year(),
                         qdt.date().month(),
                         qdt.date().day(),
                         qdt.time().hour(),
                         qdt.time().minute(),
                         qdt.time().second())
    elif isinstance(qdt, QDate):
        d = pd.Timestamp(qdt.year(),
                         qdt.month(),
                         qdt.day())
    else:
        return qdt
    return d


def pd2qtime(pdt, qdate=False):
    '''
    Return a QDateTime or a QDate from a time object of Timestamp
    :qdate: Return QDateTime if False (by default) and QDate if True
    '''
    if not qdate:
        if isinstance(pdt, (QDate, QDateTime)):
            return QDateTime(pdt)
        pdt = pd.Timestamp(pdt)
        return QDateTime(pdt.year, pdt.month, pdt.day, pdt. hour, pdt.minute, pdt.second)
    if isinstance(pdt, (QDate, QDateTime)):
        return QDate(pdt)
    pdt = pd.Timestamp(pdt)
    return QDate(pdt.year, pdt.month, pdt.day)


def getMAKeys():
    cc1 = ['chart1ma1', 'chart1ma2', 'chart1ma3', 'chart1ma4', 'chart1vwap', 'chart1ma1spin',
           'chart1ma2spin', 'chart1ma3spin', 'chart1ma4spin', 'chart1ma1color', 'chart1ma2color',
           'chart1ma3color', 'chart1ma4color', 'chart1vwapcolor']
    cc2 = ['chart2ma1', 'chart2ma2', 'chart2ma3', 'chart2ma4', 'chart2vwap', 'chart2ma1spin',
           'chart2ma2spin', 'chart2ma3spin', 'chart2ma4spin', 'chart2ma1color', 'chart2ma2color',
           'chart2ma3color', 'chart2ma4color', 'chart2vwapcolor']
    cc3 = ['chart3ma1', 'chart3ma2', 'chart3ma3', 'chart3ma4', 'chart3vwap', 'chart3ma1spin',
           'chart3ma2spin', 'chart3ma3spin', 'chart3ma4spin', 'chart3ma1color', 'chart3ma2color',
           'chart3ma3color', 'chart3ma4color', 'chart3vwapcolor']
    return cc1, cc2, cc3


def getMASettings():
    chartSet = QSettings('zero_substance/chart', 'structjour')
    mas = chartSet.value('getmas', list)
    maDict = OrderedDict()
    for ma in mas[0]:
        maDict[ma[1]] = [ma[0], ma[2]]
    vwap = []
    if mas[1]:
        vwap.append(['vwap', mas[1][1]])

    return maDict, vwap


def vwap(df, bd=None):
    '''
    I believe the standard version of vwap begins at open and does not include previous MA stuff.
    I retrieved the algo from an SO post. Thankyou for that

    '''
    tz = df.index[0].tzinfo
    if not bd:
        # If no day is given, use the end day in df
        bd = df.index[-1]
        bd = pd.Timestamp(year=bd.year, month=bd.month, day=bd.day, tz=tz)
    begin = pd.Timestamp(year=bd.year, month=bd.month, day=bd.day, hour=9, minute=30, second=0, tz=tz)

    dfv = df.copy(deep=True)
    if begin > df.index[0]:
        dfv = dfv.loc[dfv.index >= begin]

    dfv['Cum_Vol'] = dfv['volume'].cumsum()
    dfv['Cum_Vol_Price'] = (dfv['volume'] * (dfv['high'] + dfv['low'] + dfv['close']) / 3).cumsum()
    dfv['VWAP'] = dfv['Cum_Vol_Price'] / dfv['Cum_Vol']
    return dfv['VWAP']


def excludeAfterHours(string=False):
    chartSet = QSettings('zero_substance/chart', 'structjour')
    if string:
        return chartSet.value('afterhours', 'false')
    return chartSet.value('afterhours', False, type=bool)


def movingAverage(values, df, beginDay=None):
    '''
    Creates a dictionary of moving averages based settings values. All window values in
    chartSettings will be processed. Returns a dict of MA: SMA for windows of 20 or less
    and EMA for windows greater than 20, and it always process and returns VWAP.
    :values:
    :return: A tuple (maDict, vwap). Keys for maDict are the window val
    '''
    mas = getMASettings()
    windows = list()
    windows = list(mas[0].keys())

    maDict = OrderedDict()

    for ma in windows:
        # Reduce this to one type of Moving average
        # if ma > 20:

        #     weights = np.repeat(1.0, ma) / ma
        #     smas = np.convolve(values, weights, 'valid')
        #     maDict[ma] = smas
        #     maDict[ma] = pd.DataFrame(maDict[ma])
        #     try:
        #         maDict[ma].index = df.index[ma - 1:]
        #     except ValueError:
        #         del maDict[ma]
        # else:
        # dataframe = pd.DataFrame(values)
        dfema = df['close'].ewm(span=ma, adjust=False, min_periods=ma, ignore_na=True).mean()
        maDict[ma] = dfema
        maDict[ma].index = df.index
    if mas[1]:
        maDict['vwap'] = vwap(df, beginDay)

    return maDict


def makeupEntries(df, minutes):
    if df.empty:
        return []
    start = df.index[0]
    end = df.index[-1]
    start = pd.Timestamp(start)
    end = pd.Timestamp(end)
    entries = []
    for i in range(random.randint(0, 5)):
        delta = end - start
        sec = delta.total_seconds()
        earliest = int(sec // 10)
        latest = int(sec - earliest)
        secs = random.randint(earliest, latest)
        entry = start + pd.Timedelta(seconds=secs)

        # Figure the candle index for our made up entry
        diff = entry - start
        candleindex = int(diff.total_seconds() / 60 // minutes)

        # Get the time index of the candle
        # tix = df.index[candleindex]

        # Set a random buy or sell
        side = 'B' if random.random() > .5 else 'S'

        # Set a random price within the chosen candle
        high = df.iloc[candleindex].high
        low = df.iloc[candleindex].low
        price = (random.random() * (high - low)) + low

        # [price, candle, side, entry]
        entries.append([price, candleindex, side, entry])

    return entries


def getLastWorkDay(d=None):
    '''
    Retrieve the last biz day from today or from d if the arg is given. Holidays are ignored
    :params d: A datetime object.
    :return: A datetime object of the last biz day.
    '''
    now = dt.datetime.today() if not d else d
    deltDays = 0
    if now.weekday() > 4:
        deltDays = now.weekday() - 4
    bizday = now - dt.timedelta(days=deltDays)
    return bizday


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


def clearTables(db):
    statements = ['delete from chart', 'delete from holidays', 'delete from ib_covered',
                 'delete from ib_trades', 'delete from ib_positions', 'delete from trade_sum']
    for statement in statements:
        ModelBase.engine.execute(text(statement))

class ManageKeys:
    def __init__(self, create=False, db=None):
        self.settings = QSettings('zero_substance', 'structjour')
        self.apiset = QSettings('zero_substance/stockapi', 'structjour')
        self.db = db
        if not self.db:
            self.setDB()

        if self.db or create:
            self.createTables()

    def getKeyDict(self):
        keydict = {}
        keydict['bc'] = self.getKey('bc')
        keydict['av'] = self.getKey('av')
        keydict['fh'] = self.getKey('fh')
        keydict['tgo'] = self.getKey('tgo')
        return keydict

    def getDB(self):
        '''Get the file location of the sqlite database'''
 
    def createTables(self):
        '''
        Creates the api_keys if it doesnt exist then adds a row for each api that requires a key
        if they dont exist
        '''
        ModelBase.connect(new_session=True)

        ModelBase.createAll()
        curapis = ['fh', 'av', 'bc', 'tgo']      # When this info changes, Use the apisettings control to abstract the data
        addit = False
        for api in curapis:
            key = ApiKey.getKey(api, keyonly=False)
            if not key:
                ApiKey.addKey(api)

    def updateKey(self, api, key):
        return ApiKey.updateKey(api, key)

    def getKey(self, api):
        return ApiKey.getKey(api)

    def setDB(self, db=None):
        '''
        Set the location of the sqlite db file. Store in main Settings
        '''
        if db:
            self.db = db
        else:
            self.db = self.settings.value('tradeDb')
        msg = None
        if not self.db or not os.path.exists(self.db):
            title = 'Warning'
            msg = ('<h3>Warning: Trade Db location does not exist.</h3>'
                   '<p>Please set a valid location when calling setDB or you may select or '
                   'create a new location by selecting file->filesettings</p>')

            msgbx = QMessageBox(QMessageBox.Warning, title, msg, QMessageBox.Ok)
            msgbx.setWindowIcon(QIcon("structjour/images/ZSLogo.png"))
            msgbx.exec()

            return

    def getDB(self):
        '''Get the file location of the sqlite database'''
        db = self.settings.value('tradeDb')
        if not db:
            logging.warning('Trying to retrieve db location, the database file location is not set.')
        return db
        

class IbSettings:
    def __init__(self):
        self.apiset = QSettings('zero_substance/stockapi', 'structjour')
        p = self.apiset.value('APIPref')
        if p:
            p = p.replace(' ', '')
            self.preferences = p.split(',')
        else:
            self.preferences = ['ib', 'bc', 'av', 'fh']
        self.setIbStuff()

    def setIbStuff(self):
        pref = self.preferences
        self.ibPort = None
        self.ibId = None
        if 'ib' in pref:
            ibreal = self.apiset.value('ibRealCb', False, bool)
            ibPaper = self.apiset.value('ibPaperCb', False, bool)
            # ibpref = self.apiset.value('ibPref')
            if ibreal:
                self.ibPort = self.apiset.value('ibRealPort', 7496, int)
                self.ibId = self.apiset.value('ibRealId', 7878, int)
            elif ibPaper:
                self.ibPort = self.apiset.value('ibPaperPort', 4001, int)
                self.ibId = self.apiset.value('ibPaperId', 7979, int)

    def getIbSettings(self):
        # TODO abstrast host like port and id-- set it in the stockapi dialog
        if not self.ibPort or not self.ibId:
            return None
        d = {'port': self.ibPort,
             'id': self.ibId,
             'host': '127.0.0.1'}
        return d


def checkForIbapi():
    '''
    If the ibapi is not installed or available, disable its use.
    '''
    apisettings = QSettings('zero_substance/stockapi', 'structjour')
    try:
        import ibapi     # noqa: F401
        apisettings.setValue('gotibapi', True)
        return True

    except ImportError:
        apisettings.setValue('gotibapi', False)
        return False

def dictDate2NYTime(d):
    '''
    Get the offset for ny time on the last index time and set
    the date values to a naive Timestamp adjusted from Grenwich (Aware) to NY Naive
    Note this returns the time index in terms of the end time. 
    :params d: A list of dict that includes 'date' as a key
    '''
    # Creates an aware ts from date string 
    end = pd.Timestamp(d[-1]['date'])
    # Gets the delta for end in NY tz
    delt = pd.Timestamp(end.strftime('%Y-%m-%d %H:%M:%S'), tz='US/Eastern').utcoffset() 
    # add the delta to each date and create a naive ts 
    for t in d:
        newdate = pd.Timestamp(t['date'])
        t['date'] = pd.Timestamp(newdate.strftime('%Y-%m-%d %H:%M:%S')) + delt
    return d
    


def notmain():
    '''Run local code. using a db path unique to this machine'''
    # from PyQt5.QtWidgets import QApplication
    # app = QApplication(sys.argv)     # noqa: F841
    mk = ManageKeys(create=True)
    print(mk.getKey('fh'))
    print(mk.getKey('bc'))
    print(mk.getKey('av'))
    # mk = ManageKeys()
    mk.setDB('notapath')


def localstuff():
    print(excludeAfterHours())


if __name__ == '__main__':
    notmain()
    # localstuff()
