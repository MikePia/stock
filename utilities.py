'''
Local utility functions shared by some stock modules and test code.

@author: Mike Petersen

@creation_date: 2019-01-17
'''
# pylint: disable = C0103
import datetime as dt

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
    bizday = now - dt.timedelta(deltDays)
    return bizday


def notmain():
    '''run some local code'''
    now = dt.datetime.today()
    fmt = "%A, %B %d   %w"
    print()
    for i in range(7):
        d = now - dt.timedelta(i)
        print(f'{d.strftime(fmt)} ... : ... {getLastWorkDay(d).strftime(fmt)}')
        print(d.isoweekday())
if __name__ == '__main__':
    notmain()
