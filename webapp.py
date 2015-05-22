from bottle import default_app, route, template, static_file, request
import time, os, cStringIO, base64
import numpy as np
from scipy.interpolate import interp1d
from matplotlib.pyplot import subplots
from matplotlib import dates
from datalogger import datalogger_mysql

os.environ['TZ'] = 'Europe/Paris'
time.tzset()

basedir = '/home/jesteve72/sytadin'

formatter = dates.AutoDateFormatter()
formatter.scaled[1/(24.*60.)] = '%H:%M'
formatter.scaled[1/24.] = '%H:%M'

# Data logger class
sections = {'A10_Massy_Wissous':'A10 Massy => Wissous','A6B_Wissous_PItalie':'A6B Wissous => BP','BP_PItalie_PBercy':"BP P. d'Italie => P. de Bercy"}
section_loggers = dict([ (s, datalogger_mysql(s)) for s in sections.iterkeys()])


# Temperature and humidity logger plotter class
class road:
    def __init__(self, label, sections):
        self.sections = sections
        self.label = label
        fig, ax = subplots()
        fig.set_size_inches(8.675,  2.625)
        ax.hold(False)
        self.logplot = (fig, ax)

    def calculate(self, timespan=7200, points=512):
        current_time = time.time()
        time_axis = np.linspace(current_time-timespan, current_time, points)
        total_duration = 0
        self.lastvalues = []
        self.lastupdatetimes = []
        for s in self.sections:
            logger = section_loggers[s]
            xy = [ (t, data['duration']) for t,data in logger.select_timespan(timespan).iteritems() if 'duration' in data]
            x,y = zip( *sorted( xy ) ) if xy else (np.empty(0), np.empty(0))
            self.lastvalues.append( y[-1] if xy else np.nan )
            self.lastupdatetimes.append( x[-1] if xy else np.nan )
            if xy:
                x = np.array(x, dtype=float)
                y = np.array(y, dtype=float)
                interp = interp1d(x, y, bounds_error=False)
                total_duration += interp(time_axis)
            else:
                total_duration = time_axis*np.nan
        self.time_axis = time_axis
        self.total_duration = total_duration

    def plot(self, output):
        fig, ax = self.logplot
        ax.plot_date(dates.epoch2num(self.time_axis), self.total_duration, 'b-', tz='Europe/Paris')
        fig.autofmt_xdate()
        fig.tight_layout()
        fig.savefig( output, format='png' )


# Number to string formatting function
def mystr(x, fmt=None):
    if x is np.nan : return '??'
    if fmt=='float': return '{0:.1f}'.format( x )
    if fmt=='date' : return time.asctime( time.localtime( float(x) ) )
    if fmt=='time' :
        ts = time.struct_time(time.localtime(float(x)))
        return '{0:02d}h{1:02d}'.format(ts.tm_hour,ts.tm_min)
    return str(x)

# Web server
roads = {'italie' : road("Porte d'Italie",['A10_Massy_Wissous','A6B_Wissous_PItalie']),
         'bercy': road("Porte de Bercy",['A10_Massy_Wissous','A6B_Wissous_PItalie', "BP_PItalie_PBercy"]),
         }

@route('/<name>')
def main(name):
    # Load house
    if name not in roads: return 'Route inconnue.'
    road = roads[name]
    road.calculate()
    # Create figure
    fig = cStringIO.StringIO()
    road.plot(fig)
    fig = base64.b64encode(fig.getvalue())
    # Fill template
    return template('layout',
                    title = road.label + ' : ' + mystr(sum(road.lastvalues)) +' min',
                    section_durations = zip([sections[s] for s in road.sections], [mystr(x)+' min' for x in road.lastvalues], [mystr(x,'time') for x in road.lastupdatetimes]),
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
    logger.delete_timespan(7200)
    logger.logdata(timestamp=int(request.query.timestamp), duration=int(request.query.duration))
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
