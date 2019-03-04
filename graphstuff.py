'''
A couple plot methods driven by a chosen live data source. The charts available will be
single day minute charts (1,5, 10 min etc)
@author: Mike Petersen

@creation_date: 1/13/19
'''
import os, re
import datetime as dt
import random
import pandas as pd
from mpl_finance import candlestick_ohlc

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib import style
import matplotlib.ticker as mticker

from stock import mybarchart as bc
from stock import myalphavantage as mav
from stock import myiex as iex
from stock import myib as ib

# import urllib
# import datetime as dt
# from stock import myalphavantage as mav
# from stock import myiex as iex
# import numpy as np
# pylint: disable = C0103, E1121, W0603


FILL = 2
def dummyName(fp, symb, tradenum, begin, end, outdir = 'out'):
    '''
    This is a method function for use in developement. It will probably move up in the
        heirarchy to the inclusive program. Instructive to see all the elements that need
        go into this name.
    :params fp: FinPlot
    :params base: figure name icluding file type
    :params tradenum: An int or string indicating the trade number for the reporting period.
    :params symb: The stock ticker
    :params begin: Time date object or time string for the beginning of the chart
    :params end: End time date object or time string for the end of the chart
    :return: A string name
    :raise ValueError: If tradenum cannot be cnverted to a string representation of an int.
    :raise ValueError: If either begin or end are not time objects or strings.
    '''
    global FILL

    try:
        int(tradenum)
        tradenum = str(tradenum).zfill(FILL)
    except ValueError:
        raise ValueError("Unable to convert tradenum to string representation of an int")

    try:
        begin = pd.Timestamp(begin)
    except ValueError:
        raise ValueError(f'(begin {begin}) cannot be converted to a datetime object')

    try:
        end = pd.Timestamp(end)
    except ValueError:
        raise ValueError(f'(end {end}) cannot be converted to a datetime object')
    begin = begin.strftime(fp.format)
    end = end.strftime(fp.format)
    name = f'{fp.base}{tradenum}_{symb}_{begin}_{end}_{fp.api}{fp.ftype}'

    name  = os.path.join(outdir, name)

    return name


class FinPlot(object):
    '''
    Plot stock charts using single day minute interval charts
    '''

    def __init__(self, mplstyle='dark_background'):
        self.style = mplstyle
        self.randomStyle = False
        self.interactive = False
        self.preferences = ['ib', 'mav', 'iex', 'bc']

        # Pieces of the file name for the next FinPlot graph, format and base should rarely change.
        self.api = 'ib'
        self.ftype = '.png'
        self.format = "%H%M"
        self.base = 'trade'
        self.adjust = {'left': .12, 'bottom': .12, 'right': .88, 'top': .88}

    def setApiPreferences(self, lprefs):
        '''
        Set the order of preference for which API to use to for stock chart data.
        :params lprefs:An ordered list that may include the following members:
        ['iex', 'mav', 'bc', 'ib'] The order will determine which to to try first and what order to 
        proceed if the previous api failed to retrive the data.
        '''
        apis = ['iex', 'mav', 'bc', 'ib']
        self.preferences = []
        p = []
        for api in lprefs:
            if api in apis:
                p.append(api)
        self.preferences = p
        self.api = self.preferences[0]

    def matchFont(self, nm, default='arial$'):
        '''
        Retrieve font names from matplotlib matching the regex term nm. Search is not case dependent
        :params nm: The regex search parameter. To remove the font variants try adding $,
            e.g. 'arial$'
        :params default: A default font to return
        :return: A list of matching fonts or the default font if nm has no match
        '''
        nm = nm.lower()
        retList = []
        g = list(set([f.name for f in fm.fontManager.ttflist]))
        g.sort()
        for gg in g:
            if re.search(nm, gg.lower()):
                retList.append(gg)
        if not retList:
            retList = (self.matchFont(default))
        return retList

    def apiChooserList(self, start, end, api=None):
        '''
        Given the current list of apis as mav, bc, iex, and ib, determine if the given api will 
            likely return data for the given times. 
        :params start: A datetime object or time stamp indicating the intended start of the chart. 
        :params end: A datetime object or time stamp indicating the intended end of the chart.
        :params api: Param must be one of mab, bc, iex, or ib. If given, the return value in 
            (api, x, x)[0] will reflect the bool result of the api
        :return: (bool, rulesviolated, suggestedStocks) The first entry is only valid if api is 
            an argument.

        '''
        start = pd.Timestamp(start)
        end = pd.Timestamp(end)
        n = pd.Timestamp.now() + dt.timedelta(0, 60*120)        # Adding 2 hours for NY time

        violatedRules = []
        suggestedApis = self.preferences
        nopen = dt.datetime(n.year, n.month, n.day, 9, 30)
        nclose = dt.datetime(n.year, n.month, n.day, 16, 30)

        # Rule 1 Barchart will not return todays data till 16:30
        tradeday = pd.Timestamp(start.year, start.month, start.day)
        todayday = pd.Timestamp(n.year, n.month, n.day)
        if tradeday == todayday and n < nclose and 'bc' in suggestedApis:
            suggestedApis.remove('bc')
            violatedRules.append('Barchart will not return todays data till 16:30')

        # Rule 2 No support any charts greater than 7 days prior till today
        if n > start:
            delt = n - start
            if delt.days > 6 and 'mav' in suggestedApis:
                suggestedApis.remove('mav')
                lastday = n-pd.Timedelta(days=6)
                violatedRules.append('AlphaVantage data before {} is unavailable.'.format(lastday.strftime("%b %d")))

        # Rule 3 No data is available for the future
        if start > n:
            suggestedApis = []
            violatedRules.append('No data is available for the future.')

        
        api = api in suggestedApis if api else False

        return(api, violatedRules, suggestedApis)

    def apiChooser(self):
        '''
        Get a data method
        '''
        # self.api = api
        if self.api == 'bc':
            # retrieves previous biz day until about 16:30
            return bc.getbc_intraday
        elif self.api == 'mav':
            return mav.getmav_intraday
        elif self.api == 'ib':
            return ib.getib_intraday
        elif self.api == 'iex':
            return iex.getiex_intraday

        return

    def setTimeFrame(self, begin, end, interval):
        '''
        Set the amount of time before the first transaction and after the last transaction
        to include in the chart. This may include some trend examination in the future. 
        For now just add some time based on the time of day and the candle interval
        :params begin: A datetime object or time string for the first transaction time.
        :params end: A datetime object or time string for the last transaction time.
        :params interval: The candle length.
        return: A tuple (begin, end) for the suggested chart begin and end times.
        '''
        begin = pd.Timestamp(begin)
        end = pd.Timestamp(end)
        beginday = pd.Timestamp(begin.year, begin.month, begin.day, 0,0)
        endday = pd.Timestamp(end.year, end.month, end.day, 23,59) 
        xtime = 0
        if interval < 5:
            xtime = 20
        elif interval < 7:
            xtime = 40
        elif interval < 20:
            xtime = 60
        else:
            xtime = 180
        begin = begin - dt.timedelta(0, xtime*60)
        end = end + dt.timedelta(0, xtime*60)

        
        mopen = dt.datetime(beginday.year, beginday.month, beginday.day, 9, 30)
        mclose = dt.datetime(endday.year, endday.month, endday.day, 16, 0)

        begin = mopen if begin <= beginday else begin
        end = mclose if end >= endday else end

        begin = mopen if mopen > begin else begin
        end = mclose if mclose < end else end

        return begin, end

    def adjust(self, left=.12, bottom=.12, top=.99, right=.88):
        self.adjust['left'] = left
        self.adjust['right'] = right
        self.adjust['top'] = top
        self.adjust['bottom'] = bottom

        
    def graph_candlestick(self, symbol, start=None, end=None, minutes=1,
                          dtFormat="%H:%M", save='trade'):
        '''
        Currently this will retrieve the data using apiChooser
        :params symbol: The stock ticker
        :params start: A datetime object or time string for the begining of the graph. The day must
            be within the last 7 days. This may change in the future.
        :params end: A datetime object or time string for the end of a graph. Defaults to whatever
            the call gets.
        :params dtFormat: a strftime formt to display the dates on the x axis of the chart
        :parmas st: The matplot lib style for style.use(st)
        '''


        start = pd.Timestamp(start)
        end = pd.Timestamp(end)

        if self.randomStyle:
            r = random.randint(0, len(style.available)-1)
            self.style = style.available[r]
        style.use(self.style)

        dummy, df = (self.apiChooser())(
            symbol, start=start, end=end, minutes=minutes)
        df['date'] = df.index

        df['date'] = df['date'].map(mdates.date2num)

        df_ohlc = df[['date', 'open', 'high', 'low', 'close']]
        df_volume = df[['date','volume']]

        ax1 = plt.subplot2grid((6, 1), (0, 0), rowspan=5, colspan=1)
        fig = plt.gcf()
        ax2 = plt.subplot2grid((6,1), (5,0), rowspan=1, colspan=1, sharex=ax1)
        plt.ylabel('Volume')

        # width = ((60))//86400.0
        width = (minutes*35)/(3600 *24)
        candlestick_ohlc(ax1, df_ohlc.values, width, colorup='g')

        for date, volume, dopen, close in zip(df_volume.date.values, df_volume.volume.values,
                                         df_ohlc.open.values, df_ohlc.close.values): 
            color = 'g' if close > dopen else 'k' if close == dopen else 'r'
            ax2.bar(date, volume, width, color=color)
   
        # fig = plt.Figure

        # fdict = {'family': 'sans serif', 'color': 'darkred', 'size': 15}
        for label in ax1.xaxis.get_ticklabels():
            label.set_rotation(-45)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter(dtFormat))
        ax1.xaxis.set_major_locator(mticker.MaxNLocator(10))

        # print("=======", list(df_ohlc['close'])[-1])

        bbox_props = dict(boxstyle='round', fc='w', ec='k', lw=1)
        ax1.annotate(f'{list(df_ohlc.close)[-1]}',
                     (list(df_ohlc.date)[-1], list(df_ohlc.close)[-1]),
                     xytext=(list(df_ohlc.date)
                             [-1] + .5/24, list(df_ohlc.close)[-1]),
                     bbox=bbox_props)
                      # , textcoords= 'axes fraction',arrowprops=dict(color='grey'))

        # fdict = {'family': 'serif', 'color': 'darkred', 'size': 15}
        # ax1.text(df_ohlc.date[20], 340,'Animated Parrot Department', fontdict=fdict)
        idx = int(len(df_ohlc.date)*.75)
        ax1.text(df_ohlc.date[idx], df_ohlc.low.min(), 'ZeroSubstance',
                 fontdict={'fontname': self.matchFont('onyx'), 'size': 32, 'color': '161616'})

        plt.xlabel('I am an xlabel. what are you?')
        plt.ylabel('Prices over here')
        plt.title(f'{symbol} Daily chart\nWith empty weekends and holidays!')
    #     plt.legend()
        ad = self.adjust
        plt.subplots_adjust(left=ad['left'], bottom=ad['bottom'], right=ad['right'],
                            top=ad['top'], wspace=0.2, hspace=0.2)

        # If the data is missing for a candle, the low registers as -1 and the chart boundaries
        # go to 0 and the data is smushed at the top.
        # It seems the iex data is on average much more sparse. So far with my test data, only iex
        # requires this bit.
        if save.find('iex') > 0:
            if df_ohlc.low.min() == -1:
                margin = .08
                lows = df_ohlc.low.values
                lows = sorted(lows)
                print(lows[0], lows[1], lows[-2], lows[-1])
                actuallow = -1
                actualhigh = df_ohlc.high.max()
                for i in range(len(lows)):
                    if lows[i] > -1:
                        actuallow = lows[i]
                        break
                diff = actualhigh - actuallow
                plt.gca().set_autoscale_on(False)
                plt.ylim(bottom=actuallow - (diff*margin))
                plt.ylim(top=actualhigh+(diff*margin))
                plt.gca().set_adjustable('box')
                print(save, '\nylimit is ', plt.ylim())






        # fig=plt.gcf()
        if self.interactive:
            plt.savefig('out/figure_1.png')
            plt.show()
        fig.savefig(save)


def localRun():
    '''Just running through the paces'''

    # tdy = dt.datetime.today()

    start = '2019-01-17 13:30'
    end = '2019-01-17 15:30'
    fp = FinPlot()
    symb = 'SPY'
    tn = 2

    fp.randomStyle = True
    fp.api = 'mav'

    # print(dummyName(fp, tn, symb, start, end))
    # fp.graph_candlestick("SPY", start=start, dtFormat='%H:%M')

    # fnts = fp.matchFont('onyx')
    # if fnts:
    #     print(fnts)

    odate = dt.datetime(2019, 1,19, 9, 40)
    cdate = dt.datetime(2019, 1,19, 16, 30)
    interval = 60
    for i in range(1, 10):
        s,e  = fp.setTimeFrame(odate, cdate, interval)
        print (odate.strftime("%B %d %H:%M"), ' .../... ', cdate.strftime("%B %d %H:%M"))

        print (s.strftime("%B %d %H:%M"), ' .../... ', e.strftime("%B %d %H:%M"))
        print()
        mins =  40
        odate = odate + dt.timedelta(0, mins * 60)
        cdate = cdate - dt.timedelta(0, mins * 60)





if __name__ == '__main__':
    localRun()
