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

resultsCols = [
  {'name' : 'rank',            'type' : 'INTEGER', 'is_attr' : True,  'pandas_col' : False, 'pandas_ind' : False},
  {'name' : 'prev',            'type' : 'INTEGER', 'is_attr' : True,  'pandas_col' : False, 'pandas_ind' : False},
  {'name' : 'change',          'type' : 'INTEGER', 'is_attr' : True,  'pandas_col' : False, 'pandas_ind' : False},
  {'name' : 'name',            'type' : 'TEXT',    'is_attr' : False, 'pandas_col' : False, 'pandas_ind' : False},
  {'name' : 'school',          'type' : 'TEXT',    'is_attr' : False, 'pandas_col' : False, 'pandas_ind' : False},
  {'name' : 'category',        'type' : 'INTEGER', 'is_attr' : False, 'pandas_col' : False, 'pandas_ind' : False},
  {'name' : 'abs',             'type' : 'INTEGER', 'is_attr' : True,  'pandas_col' : False, 'pandas_ind' : False},
  {'name' : 'max',             'type' : 'INTEGER', 'is_attr' : True,  'pandas_col' : False, 'pandas_ind' : False}, 
  {'name' : 'min',             'type' : 'INTEGER', 'is_attr' : True,  'pandas_col' : False, 'pandas_ind' : False}, 
  {'name' : 'wind',            'type' : 'INTEGER', 'is_attr' : True,  'pandas_col' : False, 'pandas_ind' : False}, 
  {'name' : 'precip',          'type' : 'REAL',    'is_attr' : True,  'pandas_col' : False, 'pandas_ind' : False}, 
  {'name' : 'type',            'type' : 'TEXT',    'is_attr' : True,  'pandas_col' : False, 'pandas_ind' : False},
  {'name' : 'err_max',         'type' : 'INTEGER', 'is_attr' : True,  'pandas_col' : False, 'pandas_ind' : False}, 
  {'name' : 'err_min',         'type' : 'INTEGER', 'is_attr' : True,  'pandas_col' : False, 'pandas_ind' : False}, 
  {'name' : 'err_wind',        'type' : 'REAL',    'is_attr' : True,  'pandas_col' : False, 'pandas_ind' : False}, 
  {'name' : 'err_precip',      'type' : 'REAL',    'is_attr' : True,  'pandas_col' : False, 'pandas_ind' : False}, 
  {'name' : 'err_penalty',     'type' : 'INTEGER', 'is_attr' : True,  'pandas_col' : False, 'pandas_ind' : False}, 
  {'name' : 'err_total',       'type' : 'REAL',    'is_attr' : True,  'pandas_col' : False, 'pandas_ind' : False}, 
  {'name' : 'cum_err_max',     'type' : 'INTEGER', 'is_attr' : True,  'pandas_col' : False, 'pandas_ind' : False}, 
  {'name' : 'cum_err_min',     'type' : 'INTEGER', 'is_attr' : True,  'pandas_col' : False, 'pandas_ind' : False}, 
  {'name' : 'cum_err_wind',    'type' : 'REAL',    'is_attr' : True,  'pandas_col' : False, 'pandas_ind' : False}, 
  {'name' : 'cum_err_precip',  'type' : 'REAL',    'is_attr' : True,  'pandas_col' : False, 'pandas_ind' : False}, 
  {'name' : 'cum_err_penalty', 'type' : 'INTEGER', 'is_attr' : True,  'pandas_col' : False, 'pandas_ind' : False}, 
  {'name' : 'cum_err_total',   'type' : 'REAL',    'is_attr' : True,  'pandas_col' : False, 'pandas_ind' : False}, 
  {'name' : 'norm_city',       'type' : 'REAL',    'is_attr' : True,  'pandas_col' : False, 'pandas_ind' : False},
  {'name' : 'norm_cum',        'type' : 'REAL',    'is_attr' : True,  'pandas_col' : False, 'pandas_ind' : False},
  {'name' : 'norm_rank',       'type' : 'INTEGER', 'is_attr' : True,  'pandas_col' : False, 'pandas_ind' : False}
];
forecastCols = resultsCols + [
  {'name' : 'date',       'type' : 'DATE',    'is_attr' : True,  'pandas_col' : False, 'pandas_ind' : False},
  {'name' : 'identifier', 'type' : 'TEXT',    'is_attr' : False, 'pandas_col' : True,  'pandas_ind' : False},
  {'name' : 'day',        'type' : 'INTEGER', 'is_attr' : False, 'pandas_col' : False, 'pandas_ind' : True},
  {'name' : 'semester',   'type' : 'TEXT',    'is_attr' : True,  'pandas_col' : False, 'pandas_ind' : False},
  {'name' : 'year',       'type' : 'INTEGER', 'is_attr' : True,  'pandas_col' : False, 'pandas_ind' : False}
]; # These are the columns in the SQL database
  
scheduleCols = [{'name' : 'city',  'type' : 'TEXT'},
                {'name' : 'state', 'type' : 'TEXT'},
                {'name' : 'ident', 'type' : 'TEXT'},
                {'name' : 'start', 'type' : 'DATE'},
                {'name' : 'end',   'type' : 'DATE'}];