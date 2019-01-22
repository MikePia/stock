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

        # Pieces of the file name for the next FinPlot graph, format and base should rarely change.
        self.api = 'bc'
        self.ftype = '.png'
        self.format = "%H%M"
        self.base = 'trade'

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
        '''
        begin = pd.Timestamp(begin)
        end = pd.Timestamp(end)
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
        
        mopen = dt.datetime(begin.year, begin.month, begin.day, 9, 30)
        mclose = dt.datetime(end.year, end.month, end.day, 16, 0)

        begin = mopen if mopen > begin else begin
        end = mclose if mclose < end else end

        return begin, end

        
    def graph_candlestick(self, symbol, start=None, end=None, minutes=1,
                          dtFormat="%H:%M", save='trade'):
        '''
        :Programmer Info: Configuring date is weird. matplotlib has its date format. The usage here
            is first change the date from string to timestamp using pd.to_datetime. Second, use
            pd's map(mdates.date2num) to convert from timestamp to matplotlib.dates -- aka mdate
            Finally, format the weird pd date using
            ax1.xaxis.set_major_formatter(mdates.DateFormatter(dtFormat))
        Currently this will retrieve the data from barchart. This will move to a chooser method to
            select among available sources like iex, alphavantage, quandl, and ib api.
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
        now = pd.Timestamp.today()
        delt = now - start
        if delt.days > 7:
            print("graph_candlestick is unable to retrieve graphs older than 7 days")
            s = start.strftime("%A, %B %d")
            print('WARING: no graph created for {symbol} beginning {s}')
            return

        if self.randomStyle:
            r = random.randint(0, len(style.available)-1)
            self.style = style.available[r]
        style.use(self.style)

        #     df=mav.getmav_intraday(stock)
        #     df = iex.get_trading_chart(stock)

        # df = iex.get_historical_chart(symbol, start, end)
        dummy, df = (self.apiChooser())(
            symbol, start=start, end=end, minutes=minutes)
        # df.index = df.rename(columns={df.index.name:'date'})
        df['date'] = df.index
        # df.reset_index(level=0, inplace=True)
        print(type(df.date))

        # df['date'] = pd.to_datetime(df['date'])
        df['date'] = df['date'].map(mdates.date2num)

        df_ohlc = df[['date', 'open', 'high', 'low', 'close']]
        # df_volume = df['volume']

        # Arguments( shape=(1,1), starting point = (0,0), rowspan, columnspan)
        ax1 = plt.subplot2grid((6, 1), (0, 0), rowspan=5, colspan=1)
        fig = plt.gcf()

        # width = ((60))//86400.0
        width = (minutes*35)/(3600 *24)
        candlestick_ohlc(ax1, df_ohlc.values, width, colorup='g')
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
        ax1.text(df_ohlc.date[20], df_ohlc.low.min(), 'Animated Parrot Department',
                 fontdict={'fontname': self.matchFont('onyx'), 'size': 32, 'color': '161616'})

        plt.xlabel('I am an xlabel. what are you?')
        plt.ylabel('Prices over here')
        plt.title(f'{symbol} Daily chart\nWith empty weekends and holidays!')
    #     plt.legend()

        plt.subplots_adjust(left=0.08, bottom=0.04, right=0.86,
                            top=0.84, wspace=0.2, hspace=0.2)

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
