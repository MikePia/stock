import re
import pandas as pd
# from stock import myalphavantage as mav
# from stock import myiex as iex
from stock import mybarchart as bc
import datetime as dt

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib import style
import matplotlib.ticker as mticker

import numpy as np
import urllib

from mpl_finance import candlestick_ohlc






def matchFont(nm, default='arial$'):
    '''
    Retrieve font names from matplotlib matching the regex term nm. Search is not case dependent
    :params nm: The regex search parameter. To remove the font variants try adding $, e.g. 'arial$'
    :params default: A default font to return
    :return: A list of matching fonts or the default font if nm has no match
    '''
    nm = nm.lower()
    retList=[]
    g=list(set([f.name for f in fm.fontManager.ttflist]) )
    g.sort()
    for gg in g:
        if re.search(nm, gg.lower()):
            retList.append(gg)
    if not retList:
        retList = (matchFont('arial$'))
    return retList


def graph_candlestick(symbol, start=None, end=None, dtFormat="%b %d", st = 'ggplot', save=''):
    '''
    :Programmer Info: Configuring date is weird. matplotlib has its date format. The usage here is
        first change the date from string to timestamp using pd.to_datetime
        second, use pd's map(mdates.date2num) to convert from timestamp to matplotlib.dates -- aka mdate
        Finally, format the weird pd date using ax1.xaxis.set_major_formatter(mdates.DateFormatter(dtFormat))
    Currently this will retrieve the data from barchart. This will move to a chooser method to select among
    available sources like iex, alphavantage, quandl, and ib api.
    :params symbol: The stock ticker
    :params start:A datetime object or time string for the begining of the graph. Defaults to whatever the call gets
    :params end: A datetime object or time string for the end of a graph. Defaults to whatever the call gets
    :params dtFormat: a strftime formt to display the dates on the x axis of the chart
    :parmas st: The matplot lib style for style.use(st)
    '''
    
   
    style.use(st)

    #     df=mav.getmav_intraday(stock)
    #     df = iex.get_trading_chart(stock)

    # df = iex.get_historical_chart(symbol, start, end)
    x, df = bc.getbc_intraday(symbol, start)
    df.reset_index(level=0, inplace=True)

    df['date'] = pd.to_datetime(df['date'])
    df['date'] = df['date'].map(mdates.date2num)

    df_ohlc=df[['date', 'open', 'high', 'low', 'close']]
    df_volume = df['volume']

    # Arguments( shape=(1,1), starting point = (0,0), rowspan, columnspan)
    ax1 = plt.subplot2grid((6,1), (0,0), rowspan=5, colspan=1)
    fig=plt.gcf()

   

    candlestick_ohlc(ax1, df_ohlc.values, width=100/86400.0, colorup='g' )
    # fig = plt.Figure
    
    fdict={'family': 'sans serif',
           'color': 'darkred',
           'size':15}
    for label in ax1.xaxis.get_ticklabels():
        label.set_rotation(-45)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter(dtFormat))
    ax1.xaxis.set_major_locator(mticker.MaxNLocator(10))

    # print("=======", list(df_ohlc['close'])[-1])
    
    bbox_props =  dict(boxstyle='round', fc='w', ec='k', lw=1)
    ax1.annotate(f'{list(df_ohlc.close)[-1]}', 
                 (list(df_ohlc.date)[-1], list(df_ohlc.close)[-1]),
                 xytext=(list(df_ohlc.date)[-1] + .5/24, list(df_ohlc.close)[-1]),
                 bbox=bbox_props) #, textcoords= 'axes fraction',arrowprops=dict(color='grey'))
    
    fdict={'family': 'serif', 'color': 'darkred', 'size':15}
    # ax1.text(df_ohlc.date[20], 340,'Animated Parrot Department', fontdict=fdict)
    ax1.text(df_ohlc.date[20], df_ohlc.low.min(),'Animated Parrot Department',  
             fontdict = {'fontname': matchFont('onyx'), 'size': 32, 'color': '161616'})
    
    plt.xlabel('I am an xlabel. what are you?')
    plt.ylabel('Prices over here' )
    plt.title(f'{symbol} Daily chart\nWith empty weekends and holidays!')
#     plt.legend()

    plt.subplots_adjust(left=0.08, bottom = 0.04, right = 0.86, top = 0.84, wspace = 0.2, hspace=0.2)
    plt.savefig('figure_1.png')

    # fig=plt.gcf()
    plt.show()
    fig.savefig("figure_2.png")

def localRun():
    '''Just running through the paces'''
    import random
    # tdy = dt.datetime.today()
    start='2019-01-16'
    r = random.randint(0, len(style.available)-1)
    s = style.available[r]
    print(s)

    graph_candlestick("TSLA", start=start, dtFormat='%H:%M', st=s)



    fnts = matchFont('onyx')
    if fnts:
        print(fnts)


if __name__ == '__main__':
    localRun()