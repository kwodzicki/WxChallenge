resultsCols = [
  {'name' : 'rank',            'type' : 'INTEGER'},
  {'name' : 'prev',            'type' : 'INTEGER'},
  {'name' : 'change',          'type' : 'INTEGER'},
  {'name' : 'name',            'type' : 'TEXT'},
  {'name' : 'school',          'type' : 'TEXT'},
  {'name' : 'category',        'type' : 'INTEGER'},
  {'name' : 'abs',             'type' : 'TEXT'},
  {'name' : 'max',             'type' : 'INTEGER'}, 
  {'name' : 'min',             'type' : 'INTEGER'}, 
  {'name' : 'wind',            'type' : 'INTEGER'}, 
  {'name' : 'precip',          'type' : 'REAL'}, 
  {'name' : 'type',            'type' : 'TEXT'},
  {'name' : 'err_max',         'type' : 'INTEGER'}, 
  {'name' : 'err_min',         'type' : 'INTEGER'}, 
  {'name' : 'err_wind',        'type' : 'REAL'}, 
  {'name' : 'err_precip',      'type' : 'REAL'}, 
  {'name' : 'err_penalty',     'type' : 'INTEGER'}, 
  {'name' : 'err_total',       'type' : 'REAL'}, 
  {'name' : 'cum_err_max',     'type' : 'INTEGER'}, 
  {'name' : 'cum_err_min',     'type' : 'INTEGER'}, 
  {'name' : 'cum_err_wind',    'type' : 'REAL'}, 
  {'name' : 'cum_err_precip',  'type' : 'REAL'}, 
  {'name' : 'cum_err_penalty', 'type' : 'INTEGER'}, 
  {'name' : 'cum_err_total',   'type' : 'REAL'}, 
  {'name' : 'norm_city',       'type' : 'REAL'},
  {'name' : 'norm_cum',        'type' : 'REAL'},
  {'name' : 'norm_rank',       'type' : 'INTEGER'}
];
forecastCols = resultsCols + [
  {'name' : 'date',       'type' : 'DATE'},
  {'name' : 'identifier', 'type' : 'TEXT'},
  {'name' : 'day',        'type' : 'INTEGER'},
  {'name' : 'semester',   'type' : 'TEXT'},
  {'name' : 'year',       'type' : 'INTEGER'}
]; # These are the columns in the SQL database
  
scheduleCols = [{'name' : 'city',  'type' : 'TEXT'},
                {'name' : 'state', 'type' : 'TEXT'},
                {'name' : 'ident', 'type' : 'TEXT'},
                {'name' : 'start', 'type' : 'DATE'},
                {'name' : 'end',   'type' : 'DATE'}];