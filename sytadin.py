import requests
from bs4 import BeautifulSoup
import re
import time

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

sections = {'A10_Massy_Wissous':"Massy(D444) => Wissous(A6B)",
            'A6B_Wissous_PItalie':"Wissous(A6xA10) => P. Italie(BP)",
            'BP_PItalie_PBercy':"P. Italie(A6B) => P. Bercy(A4)",
            }


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
                    try:
                        r = requests.get('http://jesteve72.pythonanywhere.com/{0}/log?timestamp={1}&duration={2}'.format(s, int(timestamp), t))
                        if r.text.strip() != "OK":
                            print r.text
                            raise
                    except:
                        print time.asctime(), 'Connection to pythonanywhere failed'
                else:
                    print time.asctime(), "Could not retrieve duration for", s
        time.sleep(60)
