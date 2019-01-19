'''
A couple plot methods driven by a chosen live data source. The charts available will be
single day minute charts (1,5, 10 min etc)
@author: Mike Petersen

@creation_date: 1/13/19
'''
import re
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
# pylint: disable = C0103


class FinPlot(object):
    '''
    Plot stock charts using single day minute interval charts
    '''

    def __init__(self, mplstyle='DarkBackgrouond'):
        self.style = mplstyle
        self.randomStyle = False
        self.interactive = True
        self.api = 'bc'

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

    def graph_candlestick(self, symbol, start=None, end=None, minutes=1,
                          dtFormat="%b %d", save='out/figure1.png'):
        '''
        :Programmer Info: Configuring date is weird. matplotlib has its date format. The usage here
            is first change the date from string to timestamp using pd.to_datetime. Second, use
            pd's map(mdates.date2num) to convert from timestamp to matplotlib.dates -- aka mdate
            Finally, format the weird pd date using
            ax1.xaxis.set_major_formatter(mdates.DateFormatter(dtFormat))
        Currently this will retrieve the data from barchart. This will move to a chooser method to
            select among available sources like iex, alphavantage, quandl, and ib api.
        :params symbol: The stock ticker
        :params start:A datetime object or time string for the begining of the graph. Defaults to
            whatever the call gets.
        :params end: A datetime object or time string for the end of a graph. Defaults to whatever
            the call gets.
        :params dtFormat: a strftime formt to display the dates on the x axis of the chart
        :parmas st: The matplot lib style for style.use(st)
        '''

        if self.randomStyle:
            r = random.randint(0, len(style.available)-1)
            self.style = style.available[r]
        style.use(self.style)

        #     df=mav.getmav_intraday(stock)
        #     df = iex.get_trading_chart(stock)

        # df = iex.get_historical_chart(symbol, start, end)
        dummy, df = (self.apiChooser())(
            symbol, start=start, end=end, minutes=minutes)
        df.reset_index(level=0, inplace=True)

        df['date'] = pd.to_datetime(df['date'])
        df['date'] = df['date'].map(mdates.date2num)

        df_ohlc = df[['date', 'open', 'high', 'low', 'close']]
        # df_volume = df['volume']

        # Arguments( shape=(1,1), starting point = (0,0), rowspan, columnspan)
        ax1 = plt.subplot2grid((6, 1), (0, 0), rowspan=5, colspan=1)
        fig = plt.gcf()

        candlestick_ohlc(ax1, df_ohlc.values, width=100/86400.0, colorup='g')
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
        # plt.savefig('figure_1.png')

        # fig=plt.gcf()
        if self.interactive:
            plt.show()
        fig.savefig(save)


def localRun():
    '''Just running through the paces'''

    # tdy = dt.datetime.today()

    start = '2019-01-17 13:30'
    # end = '2019-01-17 15:30'
    fp = FinPlot()
    fp.randomStyle = True
    fp.api = 'mav'
    fp.graph_candlestick("SPY", start=start, dtFormat='%H:%M')

    fnts = fp.matchFont('onyx')
    if fnts:
        print(fnts)


if __name__ == '__main__':
    localRun()
