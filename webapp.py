from bottle import default_app, route, template, static_file, request
import time, os, cStringIO, base64
import numpy as np
from scipy.interpolate import interp1d
from matplotlib.pyplot import subplots
from matplotlib import dates
from datalogger import datalogger_mysql
from pytz import timezone

os.environ['TZ'] = 'Europe/Paris'
time.tzset()

basedir = '/home/jesteve72/sytadin'

# Data logger class
sections = {'A10_Massy_Wissous':'A10 Massy => Wissous','A6B_Wissous_PItalie':'A6B Wissous => BP','BP_PItalie_PBercy':"BP P. d'Italie => P. de Bercy"}
section_loggers = dict([ (s, datalogger_mysql(s)) for s in sections.iterkeys()])

# Temperature and humidity logger plotter class
class road:
    dateformatter = dates.DateFormatter('%H:%M', tz=timezone('Europe/Paris'))
    def __init__(self, label, sections):
        self.sections = sections
        self.label = label
        fig, ax = subplots()
        fig.set_size_inches(8.675,  1.5*2.625)
        self.logplot = (fig, ax)

    @staticmethod
    def __interp__(logger, timespan, key, time_axis):
        xy = [ (t, float(data[key])) for t,data in logger.select_timespan(timespan).iteritems() if key in data]
        if xy:
            x,y = zip( *sorted( xy ) )
            x = np.array(x, dtype=float)
            y = np.array(y, dtype=float)
            if len(x)>1:
                interp = interp1d(x, y, bounds_error=False)
                res = interp(time_axis)
            else:
                res = time_axis*np.nan
            return y[-1], x[-1], res
        else:
            return np.nan, np.nan, time_axis*np.nan


    def calculate(self, timespan, points=512):
        current_time = time.time()
        time_axis = np.linspace(current_time-timespan, current_time, points)
        total_duration = 0
        total_duration_average = 0
        self.lastvalues = []
        self.lastupdatetimes = []
        for s in self.sections:
            lastvalue, lastupdate, duration = self.__interp__(section_loggers[s], timespan, 'duration', time_axis)
            self.lastvalues.append( lastvalue )
            self.lastupdatetimes.append(lastupdate )
            total_duration += duration
        for s in self.sections:
            lastvalue, lastupdate, average = self.__interp__(section_loggers[s], timespan, 'average', time_axis)
            total_duration_average += average
        self.time_axis = time_axis
        self.total_duration = total_duration
        self.total_duration_average = total_duration_average

    def plot(self, output):
        fig, ax = self.logplot
        x = dates.epoch2num(self.time_axis)
        ax.cla()
        ax.plot_date(x, self.total_duration, 'b-')
        ax.plot_date(x, self.total_duration_average, 'r-')
        ax.xaxis.set_major_formatter(self.dateformatter)
        ax.set_ylabel('Temps de parcours (min)')
        ax.set_ylim(np.nanmin(self.total_duration)-2., np.nanmax(self.total_duration)+2.)
        fig.autofmt_xdate()
        fig.tight_layout()
        fig.savefig( output, format='png' )


# Number to string formatting function
def mystr(x, fmt=None):
    if np.isnan(x) : return '??'
    if fmt=='float': return '{0:.1f}'.format( x )
    if fmt=='int'  : return str(int(x))
    if fmt=='date' : return time.asctime( time.localtime( float(x) ) )
    if fmt=='time' :
        ts = time.struct_time(time.localtime(float(x)))
        return '{0:02d}h{1:02d}'.format(ts.tm_hour,ts.tm_min)
    return str(x)

# Web server
roads = {'italie' : road("Porte d'Italie",['A10_Massy_Wissous','A6B_Wissous_PItalie']),
         'bercy': road("Porte de Bercy",['A10_Massy_Wissous','A6B_Wissous_PItalie', "BP_PItalie_PBercy"]),
         }
timespan = 14400

@route('/<name>')
def main(name):
    # Load house
    if name not in roads: return 'Route inconnue.'
    road = roads[name]
    road.calculate(timespan)
    # Create figure
    fig = cStringIO.StringIO()
    road.plot(fig)
    fig = base64.b64encode(fig.getvalue())
    # Fill template
    return template('layout',
                    title = road.label + ' : ' + mystr(sum(road.lastvalues),'int') +' min',
                    section_durations = zip([sections[s] for s in road.sections],
                        [mystr(x,'int')+' min' for x in road.lastvalues],
                        [mystr(x,'time') for x in road.lastupdatetimes]),
                    figure = fig,
                    )

@route('/<name>/logview')
def logview(name):
    if name not in section_loggers: return 'Invalid section name.\n'
    logger = section_loggers[name]
    logentries = [ (t,data) for t,data in logger.select_all() ]
    logentries.sort(key = lambda x : -x[0])
    str = 'Log entries for {0} :<BR>\n'.format(name)
    for t,data in logentries:
        str += """{date} : {msg}<BR>\n""".format(date=mystr(t,'date'), msg=str(data) )
    return str


@route('/<name>/log')
def log(name):
    if name not in section_loggers: return 'Invalid section name.\n'
    logger = section_loggers[name]
    logger.delete_timespan(timespan)
    logger.logdata(**request.query)
    return 'OK\n'

@route('/<name>/reset')
def reset(name):
    if name not in section_loggers: return 'Invalid section name.\n'
    logger = section_loggers[name]
    logger.reset()
    return 'OK\n'

@route('/resetall')
def resetall():
    for logger in section_loggers.itervalues():
        logger.reset()
    return 'OK\n'

@route('/static/<filename>')
def server_static(filename):
    return static_file(filename, os.path.join(basedir, 'static') )


application = default_app()
