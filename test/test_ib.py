'''
@author: Mike Petersen

@creation_date: 2018-12-23
'''

# import datetime as dt
import unittest
# import pandas as pd

from stock import myib as ib


class TestMyib(unittest.TestCase):
    '''Test methods and functions in the myib module'''

    def test_ni(self):
        print(ib.ni(13))
        tests = [([1,'1','1 min'], '1 min'),
            ([2, '2', '2 mins'], '2 mins'),
            ([3, '3', '3 mins'], '3 mins'),
            ([4], '3 mins'),
            ([5, '5', '5 mins'], '5 mins'),
            ([6], '5 mins'),
            ([7], '5 mins'),
            ([8], '5 mins'),
            ([9], '5 mins'),
            ([10, '10', '10 mins'], '10 mins'),
            ([11], '10 mins'),
            ([12], '10 mins'),
            ([13], '10 mins'),
            ([14], '10 mins'),
            ([15, '15', '15 mins'], '15 mins'),          
            ([16], '15 mins'),
            ([20, '20', '20 mins'], '20 mins'),          
            ([21], '20 mins'),
            ([30, '30', '30 mins'], '30 mins'),          
            ([31], '30 mins'),
            
            ([60, '60', '1 hour'], '1 hour'),          
            ([61], '1 hour'),



            (['gg', '0bledygook'], '1 min')]

        for x in tests:
            for xx in x[0]:
                # print(f'From {xx}, and expecting {x[1]}  ....   {ib.ni(xx)}')
                self.assertEqual(ib.ni(xx), x[1])



def notmain():
    t = TestMyib()
    t.test_ni()
    
    

if __name__ == '__main__':
    notmain()