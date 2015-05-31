import requests
from bs4 import BeautifulSoup
import re
import time
import array
import os
import datetime

class Sytadin:
    def __init__(self):
        r = requests.get('http://www.sytadin.fr/sys/temps_de_parcours.jsp.html?type=secteur')
        self.soup = BeautifulSoup(r.text)
    def gettime(self, s):
        try:
            data = self.soup.find('td', text=re.compile(re.escape(s)))
            t = data.find_next('td')
            t = int(t.text.strip('mn'))
        except:
            t = None
        return t

def make_average(fname, index, value):
    refname = fname if os.path.isfile(fname) else "zeros.dat"
    with open(refname) as f:
        a = array.array('f')
        a.fromfile(f, 1441)
    N = a[-1] + 1.
    a[index] = (a[index]*(N-1) + value)/N
    a[-1] = N
    with open(fname, 'w') as f:
        a.tofile(f)
    return a[index]

sections = {'A10_Massy_Wissous':"Massy(D444) => Wissous(A6B)",
            'A6B_Wissous_PItalie':"Wissous(A6xA10) => P. Italie(BP)",
            'BP_PItalie_PBercy':"P. Italie(A6B) => P. Bercy(A4)",
            }

z = array.array('f')
for i in range(1441) : z.append(0)
with open('zeros.dat','w') as f:
    z.tofile(f)

if __name__ == '__main__':
    while True:
        try:
            timestamp = time.time()
            syt = Sytadin()
        except:
            syt = None
            print time.asctime(), "Connection to Sytadin failed"
        if syt:
            for s,r in sections.iteritems():
                t = syt.gettime(r)
                if t :
                    body = 'timestamp={1}&duration={2}'.format(int(timestamp), t)
                    if datetime.datetime.today().weekday()<=40:
                        index = time.localtime(timestamp).tm_min + time.localtime(timestamp).tm_hour*60
                        tm = make_average('{0}.dat'.format(s) , index, t)
                        body+='&average={0:.2f}'.format(tm)
                    try:
                        r = requests.get('http://jesteve72.pythonanywhere.com/{0}/log?{1}'.format(s, body))
                        if r.text.strip() != "OK":
                            print r.text
                            raise
                    except:
                        print time.asctime(), 'Connection to pythonanywhere failed'
                else:
                    print time.asctime(), "Could not retrieve duration for", s
        time.sleep(60)
