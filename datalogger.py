import MySQLdb, json, time

param = dict(
    host = 'mysql.server',
    user = 'jesteve72',
    passwd = 'sql1502',
    db = 'jesteve72$default')


class mySQL_DB(object):
  def __init__(self):
    self.conn = MySQLdb.connect(**param)
  def query(self, sql):
    try:
      cursor = self.conn.cursor()
      cursor.execute(sql)
    except (AttributeError, MySQLdb.OperationalError):
      self.__init__()
      cursor = self.conn.cursor()
      cursor.execute(sql)
    return cursor
  def close(self):
    self.conn.close()


db_connection = mySQL_DB()

class datalogger_mysql(mySQL_DB):
    def __init__(self, name):
        self.query("CREATE TABLE IF NOT EXISTS {0} (time INT, data VARCHAR(512));".format(name))
        self.name = name
    @staticmethod
    def query(sql):
        return db_connection.query(sql)
    def logdata(self, timestamp=None, **data):
        timestamp = int(time.time() ) if timestamp is None else timestamp
        data = json.dumps(data)
        self.query("INSERT INTO {0} () VALUES({1},'{2}');".format(self.name, timestamp, data))
        self.conn.commit()
    def query_decode(self, query):
        c = self.query(query)
        d = dict(c.fetchall())
        for k,v in d.iteritems():
            d[k] = json.loads(v)
        return d
    def select_all(self):
        return self.query_decode("SELECT * FROM {0};".format(self.name))
    def select_timespan(self, timespan):
        now = int( time.time() )
        return self.query_decode("SELECT * FROM {0} WHERE time>{1};".format(self.name, now-timespan))
    def reset(self):
        self.query("DROP TABLE {0}".format(self.name))
        self.conn.commit()
        self.query("CREATE TABLE IF NOT EXISTS {0} (time INT, data VARCHAR(512));".format(self.name))
        self.conn.commit()
    def delete_timespan(self, timespan):
        now = int( time.time() )
        self.query("DELETE FROM {0} WHERE time<{1};".format(self.name, now-timespan))
