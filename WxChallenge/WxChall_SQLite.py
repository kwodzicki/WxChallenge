import sqlite3, os;
# Handle both Python2 and Python3
try:
  from utils import updateSchedule, nestedDictSort, unique_cols;
  import data as WxData;
  from WxForecast import forecaster, forecasts;
except:
  from .utils import updateSchedule, nestedDictSort, unique_cols;
  from . import data as WxData;
  from .WxForecast import forecaster, forecasts;
from pandas import DataFrame;

_dir = os.path.dirname(os.path.abspath(__file__));
_sql_file = os.path.join(_dir, 'WxChall.sql');

class WxChall_SQLite( object ):
  ##############################################################################
  def __init__(self, file = _sql_file):
    self.sqlFile = file;
    self.db      = sqlite3.connect( self.sqlFile, detect_types=sqlite3.PARSE_DECLTYPES );
    self.cursor  = self.db.cursor();
    self.__createTables();
  ##############################################################################
  def add_forecasts(self, forecasts):
    '''Method for adding a forecast to the database'''
    for tag in forecasts:
      vars = [ ele['name'] for ele in WxData.forecastCols ];                    # Get list of names for each column in the schedule table
      vals = [ forecasts[tag][v] for v in vars ];                               # Get value to go in each column from the info dictionary
      whr  = self.__buildWhere( vars );                                         # Build a 'WHERE (var1=? AND var2=?...)' statement based on the columns in the schedule table
      cmd  = 'SELECT * from forecasts {}'.format( whr );                        # Build full command to look for entry
      self.cursor.execute( cmd, vals );                                         # Execute the command
      if not self.cursor.fetchone():                                            # If there is nothing found, then
        ins = self.__buildInsert( vars );
        cmd = 'INSERT INTO forecasts {}'.format( ins );
        self.cursor.execute( cmd, vals );
    self.db.commit();
  ##############################################################################
  def get_forecasts(self, name = None, school = None, category = None, semester = None, year = None, models = True):
    '''
    Method for getting forecasts from the database
    Keywords:
      name     : Name of the forecaster; if only this used, all forecasts
                  for this forecaster returned.
      school   : School to filter by; if only this used, all forecasts
                  for this school are returned.
      category : category to filter by; if only this used, all forecasts
                  for this category are returned.
      semester : Subset data by given semester
      year     : Subset data by given year
      models   : Default to True: gets category 8, set to False to NOT get data
    '''
    vars, vals = [], [];                                                        # Initialize lists for var names and values to search by in the SQL table
    if name is not None:                                                        # If name is NOT None
      if type(name) is not list and type(name) is not tuple:                    # Ensure that name is type list; checking if not list and not tuple
        name = [name];    
      for n in name:                                                            # Iterate over all values in name
        vars.append('name');                                                    # Append 'name' string to vars list
        vals.append(n);                                                         # Append input name to vals list
    if school is not None:                                                      # If school is NOT None;
      if type(school) is not list and type(school) is not tuple:                # Ensure that school is type list; checking if not list and not tuple
        school = [school];
      for s in school:                                                          # Iterate over all values in school
        vars.append('school');                                                  # Append 'school' string to vars list
        vals.append(s);                                                         # Append input school to vals list
      if models:                                                                # If models is True
        vars.append('school');                                                  # Append 'school' string to vars list
        vals.append('xxx');                                                     # Append 'xxx' to vals list
    if category is not None:                                                    # If category is NOT None
      if type(category) is not list and type(category) is not tuple:            # Ensure that category is type list; checking if not list and not tuple
        category = [category];
      for c in category:                                                        # Iterate over all values in category
        vars.append('category');                                                # Append 'category' string to vars list
        vals.append(c);                                                         # Append input category to vals list
    if semester is not None:
      if type(semester) is not list and type(semester) is not tuple:            # Because semYear IS a tuple or list because they are paired, make certain that zeroth element is NOT a list OR tuple. If it is, then already multiple values
        semester = [semester];                                                  # Convert to list
      for s in semester:                                                        # Iterate over all values in semYear
        vars.append('semester');                                                # Append 'semester' string to vars list
        vals.append(s);                                                         # Append input semester to vals list
    if year is not None:
      if type(year) is not list and type(year) is not tuple:                    # Because semYear IS a tuple or list because they are paired, make certain that zeroth element is NOT a list OR tuple. If it is, then already multiple values
        year = [year];                                                          # Convert to list
      for y in year:                                                            # Iterate over all values in semYear
        vars.append('year');                                                    # Append 'year' string to vars list
        vals.append(y);                                                         # Append input year to vals list
    
    
    if len(vars) == 0:                                                          # If the length of vars is zero
      cmd = 'SELECT * FROM forecasts';                                          # Set the command to select all forecasts
    else:                                                                       # Else,
      whr = self.__buildWhere( vars );                                          # Use the private method to build a where statement for the command
      cmd = 'SELECT * FROM forecasts {}'.format( whr );                         # Set command with where statment
    self.cursor.execute(cmd, vals);                                             # Execute the command
    fcs = DataFrame( self.cursor.fetchall(), 
      columns = [i['name'] for i in WxData.forecastCols]
    );                                                                          # Fetch all the information from the SQL table and convert it to a pandas DataFrame using the forecastCols column names
    fcs = fcs.set_index('date');                                                # Set the date column to be the index values
    out, uColNames = [], [];                                                    # Initialize output list and list that will contain column names to sort for unique forecasters
    for i in WxData.forecastCols:                                               # Iterate over all column names in forecastCols
      if not i['pandas_col'] and not i['pandas_ind']:                           # If the name is NOT a pandas_col name and NOT a pandas_ind name
        uColNames.append( i['name'] );                                          # Append it to the uColNames
    ucols = unique_cols( fcs[ uColNames ].values );                             # Get list of all unique (name, category, school, semester, year) combinations
    for col in ucols:                                                           # Iterate over unique forecaster ids
      vals = fcs.loc[
        (fcs.name     == col[0]) & (fcs.school   == col[1]) & \
        (fcs.category == col[2]) & (fcs.semester == col[3]) & \
        (fcs.year     == col[4]) 
      ];                                                                        # Get rows form the main table where the forecaster is unique
      tmp = forecaster( data = vals.drop( uColNames, axis=1 ),
        name     = col[0], 
        school   = col[1], 
        category = col[2], 
        semester = col[3], 
        year     = col[4]
      );                                                                        # Create new forecaster instance using the vals for the unique forecaster making sure to drop all the uColName columns
      out.append( tmp );                                                        # Append the new forecaster instance to the out list
    return sorted(out, key=lambda k: k.name) 
#     return out

  ##############################################################################
  def __get_forecasts(self, name = None, school = None, category = None, semYear = None):
    '''
    Method for getting forecasts from the database
    Keywords:
      name     : Name of the forecaster; if only this used, all forecasts
                  for this forecaster returned.
      school   : School to filter by; if only this used, all forecasts
                  for this school are returned.
      category : category to filter by; if only this used, all forecasts
                  for this category are returned.
      semYear  : Tuple of (semester, year) to filter by; if only this used,
                  all forecasts for this semester/year are returned.
    '''
    vars, vals = [], [];
    if name is not None:
      vars.append('name');
      vals.append(name);
    if school is not None:
      vars.append('school')
      vals.append(school);
    if category is not None:
      vars.append('category')
      vals.append(category);
    if semYear is not None:
      vars.append('semester')
      vals.append(semYear[0].lower());
      vars.append('year')
      vals.append(semYear[1]);
    
    if len(vars) == 0:
      cmd = 'SELECT * FROM forecasts';
    else:
      whr = self.__buildWhere( vars );
      cmd = 'SELECT * FROM forecasts {}'.format( whr );
    self.cursor.execute(cmd, vals);
    fcs = self.cursor.fetchall();
    out = {};
    for fc in fcs:
      nameTag   = fc[3]; # Name tag
      schoolTag = fc[4]; # School tag
      categTag  = fc[5]; # Category tag
 
      if schoolTag not in out: 
        out[schoolTag] = {};      
      if categTag  not in out[schoolTag]: 
        out[schoolTag][categTag] = {};
      if nameTag   not in out[schoolTag][categTag]: 
        out[schoolTag][categTag][nameTag] = {};
        for col in WxData.forecastCols:
          col = col['name']
          if col is 'name' or col is 'school' or col is 'category': continue;
          out[schoolTag][categTag][nameTag][col] = [];
      for i in range( len(fc) ):
        tag = WxData.forecastCols[i]['name']
        if tag is 'name' or tag is 'school' or tag is 'category': continue;
        out[schoolTag][categTag][nameTag][tag].append( fc[i] );
    return nestedDictSort(out);
    
  ##############################################################################
  def get_forecaster(self, name, sch, cat):
    '''
    Method to get unique key for given forecaster based on 
    name, school, and category. If no forecaster is found matching 
    information, then None is returned.
    '''
    cmd = "SELECT * FROM forecasts WHERE (name=? AND school=? AND category=?)";
    self.cursor.execute( cmd, (name, sch, cat,) );
    entry = self.cursor.fetchone();
    if entry:
      return entry[-1];
    else:
      return None;
  ##############################################################################
  def get_schedule(self):
    '''Method to get full schedule'''
    print('loading schedule');
    schedDict = {}
    self.cursor.execute('SELECT * FROM schedule');
    sched = self.cursor.fetchall();
    if len(sched) > 0: 
      for city in sched:
        info = {};
        for col, val in zip(WxData.scheduleCols, city):
          info[col['name']] = val;
        schedDict = updateSchedule( schedDict, info );
    return schedDict;
  ##############################################################################
  def update_schedule(self, schedDict):
    '''Method to update the schedule in the database'''
    for semYear in schedDict:                        # Iterate over the semester:year tags in schedDict
      for ident in schedDict[semYear]:               # Iterate over the identifier tags in schedDict[semYear]
        info = schedDict[semYear][ident];
        vars = [ ele['name'] for ele in WxData.scheduleCols ];                  # Get list of names for each column in the schedule table
        vals = [ info[ v ] for v in vars ];                                     # Get value to go in each column from the info dictionary
        whr  = self.__buildWhere( vars );                                       # Build a 'WHERE (var1=? AND var2=?...)' statement based on the columns in the schedule table
        cmd  = 'SELECT * FROM schedule {}'.format( whr );                       # Build full command to look for entry
        self.cursor.execute( cmd, vals );                                       # Execute the command
        if not self.cursor.fetchone():                                          # If there is nothing found, then
          ins = self.__buildInsert( vars );
          cmd = 'INSERT INTO schedule {}'.format( ins );
          self.cursor.execute( cmd, vals );
          self.db.commit();
  ##############################################################################
  def __createTables(self):
    '''Method to create tables if None exist in the file'''
    buildCols = lambda info: ['{} {}'.format(i['name'],i['type']) for i in info]
    table1 = 'forecasts ({})'.format(   ', '.join(buildCols(WxData.forecastCols)) );
    table2 = 'schedule ({})'.format(   ', '.join(buildCols(WxData.scheduleCols)) );
    self.cursor.execute( "CREATE TABLE IF NOT EXISTS {}".format(table1) );
    self.cursor.execute( "CREATE TABLE IF NOT EXISTS {}".format(table2) );
    self.db.commit();
  ##############################################################################
  def __check_city(self, city, state, ident, start, end):
    '''
    Method to get unique key for given forecaster based on 
    name, school, and category. If no forecaster is found matching 
    information, then None is returned.
    '''
    cmd = "SELECT * FROM schedule WHERE ({})";
    cmd = cmd.format( ','.join(['{}=?'.format(i[0]) for i in WxData.scheduleCols]) )
    self.cursor.execute( cmd, (city, state, ident, start, end,) );
    entry = self.cursor.fetchone();
    if entry:
      return entry[-1];
    else:
      return None;
  ##############################################################################
  def __buildWhere(self, cols):
    vars, i = [], 0;
    while i < len(cols):
      n = cols.count( cols[i] );
      if n == 1:
        vars.append( '{}=?'.format( cols[i] ) );
      else:
        tmp = ['{}=?'.format( cols[i] )] * n;
        tmp = ' OR '.join( tmp )
        vars.append( '({})'.format(tmp) );  
      i += n      
    return "WHERE ({})".format( ' AND '.join( vars ) );
  def __buildInsert(self, cols):
    vars = [ele for ele in cols];
    vals = ['?'] * len(vars)
    return "({}) VALUES ({})".format( ','.join( vars ), ','.join( vals ) );

  ##############################################################################
  def close(self): 
    self.db.commit();
    self.db.close();