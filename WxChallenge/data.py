'''
Descriptions of key/value pairs in the dictionaries below
  name       : Specificies the name of the SQL column/name of attributes
                associated with these data.
  type       : The SQL type of the data.
  is_attr    : Is to be an attribute of the forecaster class. Done this way
                so that programming can be more dynamic. If all things are
                hard_coded, becomes more difficult to change later.
  pandas_col : Signifies if this variable is to be used as a pandas dataframe
                column.
  pandas_ind : Signifies if this variable is to be used as a pandas dataframe
                index, or row.
'''
# Columns for data in the WxChallenge resutls table
resultsCols = [
  {'name' : 'rank',            'type' : 'INTEGER', 'pandas_col' : True,  'pandas_ind' : False},
  {'name' : 'prev',            'type' : 'INTEGER', 'pandas_col' : True,  'pandas_ind' : False},
  {'name' : 'change',          'type' : 'INTEGER', 'pandas_col' : True,  'pandas_ind' : False},
  {'name' : 'name',            'type' : 'TEXT',    'pandas_col' : False, 'pandas_ind' : False},
  {'name' : 'school',          'type' : 'TEXT',    'pandas_col' : False, 'pandas_ind' : False},
  {'name' : 'category',        'type' : 'INTEGER', 'pandas_col' : False, 'pandas_ind' : False},
  {'name' : 'abs',             'type' : 'INTEGER', 'pandas_col' : True,  'pandas_ind' : False},
  {'name' : 'max',             'type' : 'INTEGER', 'pandas_col' : True,  'pandas_ind' : False}, 
  {'name' : 'min',             'type' : 'INTEGER', 'pandas_col' : True,  'pandas_ind' : False}, 
  {'name' : 'wind',            'type' : 'INTEGER', 'pandas_col' : True,  'pandas_ind' : False}, 
  {'name' : 'precip',          'type' : 'REAL',    'pandas_col' : True,  'pandas_ind' : False}, 
  {'name' : 'type',            'type' : 'TEXT',    'pandas_col' : True,  'pandas_ind' : False},
  {'name' : 'err_max',         'type' : 'INTEGER', 'pandas_col' : True,  'pandas_ind' : False}, 
  {'name' : 'err_min',         'type' : 'INTEGER', 'pandas_col' : True,  'pandas_ind' : False}, 
  {'name' : 'err_wind',        'type' : 'REAL',    'pandas_col' : True,  'pandas_ind' : False}, 
  {'name' : 'err_precip',      'type' : 'REAL',    'pandas_col' : True,  'pandas_ind' : False}, 
  {'name' : 'err_penalty',     'type' : 'INTEGER', 'pandas_col' : True,  'pandas_ind' : False}, 
  {'name' : 'err_total',       'type' : 'REAL',    'pandas_col' : True,  'pandas_ind' : False}, 
  {'name' : 'cum_err_max',     'type' : 'INTEGER', 'pandas_col' : True,  'pandas_ind' : False}, 
  {'name' : 'cum_err_min',     'type' : 'INTEGER', 'pandas_col' : True,  'pandas_ind' : False}, 
  {'name' : 'cum_err_wind',    'type' : 'REAL',    'pandas_col' : True,  'pandas_ind' : False}, 
  {'name' : 'cum_err_precip',  'type' : 'REAL',    'pandas_col' : True,  'pandas_ind' : False}, 
  {'name' : 'cum_err_penalty', 'type' : 'INTEGER', 'pandas_col' : True,  'pandas_ind' : False}, 
  {'name' : 'cum_err_total',   'type' : 'REAL',    'pandas_col' : True,  'pandas_ind' : False}, 
  {'name' : 'norm_city',       'type' : 'REAL',    'pandas_col' : True,  'pandas_ind' : False},
  {'name' : 'norm_cum',        'type' : 'REAL',    'pandas_col' : True,  'pandas_ind' : False},
  {'name' : 'norm_rank',       'type' : 'INTEGER', 'pandas_col' : True,  'pandas_ind' : False}
];

# Columns for the SQL table containing forcests
forecastCols = resultsCols + [
  {'name' : 'date',       'type' : 'DATE',    'pandas_col' : False, 'pandas_ind' : True},
  {'name' : 'identifier', 'type' : 'TEXT',    'pandas_col' : True,  'pandas_ind' : False},
  {'name' : 'day',        'type' : 'INTEGER', 'pandas_col' : True,  'pandas_ind' : False},
  {'name' : 'semester',   'type' : 'TEXT',    'pandas_col' : False, 'pandas_ind' : False},
  {'name' : 'year',       'type' : 'INTEGER', 'pandas_col' : False, 'pandas_ind' : False}
];

# Columns for the SQL table containing forecast city schedule
scheduleCols = [{'name' : 'city',  'type' : 'TEXT'},
                {'name' : 'state', 'type' : 'TEXT'},
                {'name' : 'ident', 'type' : 'TEXT'},
                {'name' : 'start', 'type' : 'DATE'},
                {'name' : 'end',   'type' : 'DATE'}];

# Columns used for checking if a forecast exists in the SQL table of forecasts.
#  This is used to check if a forecast exists for the given date. If it does, then
#  check some more data to see if the forecast should be updated. Else, the forecast 
#  is inserted into the table
fcstChckCols = [ 'name', 'school', 'category', 'date' ];
