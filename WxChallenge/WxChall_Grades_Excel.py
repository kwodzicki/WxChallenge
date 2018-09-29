#!/usr/bin/env python

import os, xlwt;
from pandas import read_csv;
from WxChallenge import WxChallenge;
from WxChallenge.utils import fix_Roster_CSV;
from WxChallenge.data import fcst_tag, fname_tag, lname_tag, class_tag;

home   = os.path.expanduser( '~' );
outDir = os.path.join( home, 'WxChall_Grades')

class ExcelBook( xlwt.Workbook ):
  def __init__(self, file):
    xlwt.Workbook.__init__(self, encoding="utf-8");
    self.file   = file
    self.fnames = []
    self.lnames = []
    self.ids    = []  
    self.sheets = {}
  ##############################################################################
  def addSheet(self, sheetName, columns = None):
    if sheetName not in self.sheets:
      self.sheets[sheetName] = {
        'id'   : self.add_sheet(sheetName),
        'row'  : 1
      };    
      if columns is not None:
        for i in range( len(columns) ):
          self.sheets[sheetName]['id'].write(0, i, columns[i]);
    return self.sheets[sheetName];
  ##############################################################################
  def addData(self, sheetName, values):
    self.sheets[sheetName] = {
      'id'   : self.add_sheet(sheetName),
      'row'  : 1
    };    
    for i in range( len(columns) ):
      self.sheets[sheetName]['id'].write(0, i, columns[i]);
    return self.sheets[sheetName];

  ##############################################################################
  def saveBook(self):
    dir = os.path.dirname( self.file );                                         # Parent directory of file path
    if not os.path.isdir( dir ): os.makedirs( dir );                            # If the output directory does NOT exist, create it
    self.save( self.file );                                                     # Save the Workbook object to a file
  
class WxChall_Grades_Excel( object ):
  '''
  A class for computing grades and output to Excel SpreadSheets.
  A SpreadSheet will be created for each class that is defined
  in the roster. In each class SpreadSheet there will be a
  sheet for each forecast city.
  '''
  def __init__(self, semester, year, roster, school=None, verbose=False, outdir=outDir):
    '''
    Name:
       __init___
    Purpose:
       To initialize the WxChall_Grades_Excel class
    Inputs:
       semester  : String of the semester of the data; 'fall' or 'spring'
       year      : Integer year
       roster    : Path to the roster CSV for the school; local Wx manager
                    has access to this.
    Outputs:
       Excel SpreadSheet(s)
    Keywords:
       school   : 3-character school tag
       verbose  : Set to increase verbosity
       outdir   : Top level output directory for SpreadSheet files
    '''
    inst  = WxChallenge();                                                        # Initialize the WxChallenge
    self.fcsts = inst.get_forecasts( 
      school   = school,
      semester = semester,
      year     = year
    );                                                                          # Get forecasts based on command line arguments
    inst.close();                                                               # Close SQL database
    if self.fcsts is None:                                                      # If no forecasts returned
      print( 'No forecasts found!' );                                           # Print a message
      return False;                                                             # Exit
    self.outDir  = os.path.join(outDir, '{}_{}'.format(year, semester) );       # Set output directory for files
    self.verbose = verbose;
    self.classes = self.getClassInfo( roster );                                 # Parse data from roster CSV
  ##############################################################################
  def grades(self):
    '''
    Name:
       grades
    Purpose:
       Main method for computing grades and saving data
       to Excel SpreadSheets.
    Inputs:
       None.
    Outputs:
       Will create Excel SpreadSheets
    Keywords:
       None.
    '''
    consensus, climo = self.getConsensClimo();                                  # Get consensus and climatology data
    for f in self.fcsts:                                                        # Iterate over all the forecasts again
      g = f.calc_grade(
        climatology    = climo,
        sch_consensus  = consensus[f.school],
        ntnl_consensus = consensus['xxx'],
        verbose        = self.verbose
      );                                                                        # Calculate the grade for a forecaster  
      self.updateSpreadSheets( f );                                             # Call method to update the spreadsheets with the current forecaster's grades
    self.saveSpreadSheets();                                                    # Save all the spreadsheets
  ##############################################################################
  def getConsensClimo(self):
    '''
    Name:
       getConsensClimo
    Purpose:
       A method to locate and return consensus and climatology data
       from the list of forecasts
    Inputs:
       None.
    Outputs:
       Returns a dictionary containing consensus data and
       a list containing climatology data
    Keywords:
       None.
    '''
    consensus, climo = {}, [];                                                  # Initialize a dictionary for consensus (school & national) and a list for climatology
    for f in self.fcsts:                                                        # Iterate over all forecasters in list
      if f.is_climo:                                                            # If a forecaster is climo
        if not any( [c == f for c in climo] ): climo.append(f);                 # If the forecaster is NOT in the list, then append it
      elif f.is_consen and f.school not in consensus:                           # Else, if the forecaster is consensus
        consensus[f.school] = f;                                                # Add it to the dictionary
    return consensus, climo;
  ##############################################################################
  def saveSpreadSheets(self):
    '''
    Name:
       saveSpreadSheets
    Purpose:
       A method to save all the xlwt.Workbook objects to
       Excel SpreadSheet files.
    Inputs:
       None.
    Outputs:
       Generate output files
    Keywords:
       None.
    '''
    if not os.path.isdir( self.outDir ): os.makedirs( self.outDir );            # If the output directory does NOT exist, create it
    for key in self.classes:                                                    # Iterate over all the keys in the classes dictionary
      if os.path.isfile( self.classes[key]['file'] ):                           # If the output file exists
        os.remove( self.classes[key]['file'] );                                 # Delete it
      self.classes[key]['book'].save( self.classes[key]['file'] );              # Save the Workbook object to a file
  ##############################################################################
  def updateSpreadSheets(self, fcstr):
    '''
    Name:
       updateSpreadSheets
    Purpose:
       A method to add a single forecasters grades to a spreadsheets.
       SpreadSheets are created for each class in the roster CSV
    Inputs:
       fcstr : A WxForecaster object that has grades calculated
    Outputs:
       None.
    Keywords:
       None.
    '''
    if len(self.classes) == 0: return None;                                     # If there is no classes data, return
    for cls in self.classes:                                                    # Iterate over all classes in the classes dictionary
      if fcstr.name in self.classes[cls]['ids']:                                # If the forecaster is in one of the classes
        id = self.classes[cls]['ids'].index( fcstr.name );                      # Get the index for the forecaster in the list of forecasters for the class
        for city in fcstr.grades.index:                                         # Iterate over all cities (rows) of the forecaster's grades
          sheet = self.__addSheet2Book(cls, city, fcstr);                       # Use a method to get the Sheet to write data to; 
          sheet['id'].write( sheet['row'], 0, self.classes[cls]['lnames'][id] );# Write the last name to the 1st (zeroth) column
          sheet['id'].write( sheet['row'], 1, self.classes[cls]['fnames'][id] );# Write the first name to the 2nd (first) column
          col = 2;                                                              # Set column counter to 2
          for info in fcstr.grades.columns:                                     # Iterate over all columns in the grades dataframe for the forecaster
            sheet['id'].write(sheet['row'], col, fcstr.grades.loc[city][info]); # Write the data to the SpreadSheet
            col += 1;                                                           # Increment the column index
          sheet['row'] += 1;                                                    # Increment the row index for the given sheet
  ##############################################################################
  def getClassInfo( self, csvfile ):
    '''
    Name:
       getClassInfo
    Purpose:
       A method to parse data from the roster CSV and generate
       a dictionary with the following layout:
         classes = { 
           'Class name key' : { 
             'fnames' : [list of first names],
             'lnames' : [list of last names],
             'ids'    : [forecaster ids]',
             'file'   : Full path to output file
             'book'   : xlwt.Workbook instance for class,
             'sheets' : {
               'Forecast city id' : {
                 'id'  : handle returned by book.add_sheet() method,
                 'row' : integer specifying current row in the sheet
               }
             }  
           }
         }
    Inputs:
       csvfile  : Full path to the roster CSV file
    Ouputs:
       Returns the classes dictionary defined above
    Keywords:
       None.
    '''
    classes = {}
    if not os.path.isfile( csvfile ):                                           # If the file does NOT exists
      print( 'Roster file NOT found!' );                                        # Print a message
    else:                                                                       # Else, it exists
      fix_Roster_CSV( csvfile );                                                # Fix the CSV file
      roster = read_csv( csvfile );                                             # Read in the data
      for col in class_tag:                                                     # Iterate over the class ids
        for cls in roster[col].unique():                                        # Iterate over the unique values in the column
          if 'NO CLASS' in cls.upper(): continue;                               # Skip the 'No Class' class
          if cls not in classes:                                                # If the cls key is NOT in the classes dictionary,
            xlsFile  = os.path.join(self.outDir, '_'.join( cls.split() ) );     # Generate file path for XLS file
            xlsFile += '.xls';
            classes[cls] = {  
              'fnames' : [],
              'lnames' : [],
              'ids'    : [],  
              'file'   : xlsFile,  
              'book'   : xlwt.Workbook(encoding="utf-8"),
              'sheets' : {}
            };                                                                  # Initialize dictionary under key
      for col in class_tag:                                                     # Iterate over the columns to sort students into classes
        for cls in classes:                                                     # Iterate over all tags in the classes dictionary
          tmp = roster.loc[ roster[col] == cls ];                               # Locate all rows where the class matches
          if len(tmp) > 0:                                                      # If rows located
            classes[cls]['ids']    += tmp[fcst_tag].values.tolist();            # Append forecaster id list to 'names' tag
            classes[cls]['fnames'] += tmp[fname_tag].values.tolist();           # Append forecaster id list to 'names' tag
            classes[cls]['lnames'] += tmp[lname_tag].values.tolist();           # Append forecaster id list to 'names' tag
    return classes;                                                             # Return the classes dictionary
  ##############################################################################
  def __addSheet2Book(self, cls, city, fcstr):
    if city not in self.classes[cls]['sheets']:
      self.classes[cls]['sheets'][city] = {
        'id'  : self.classes[cls]['book'].add_sheet( city ),
        'row' : 1
      }
      tmp = self.classes[cls]['sheets'][city];
      tmp['id'].write(0, 0, 'last name');
      tmp['id'].write(0, 1, 'first name');
      cols = fcstr.grades.columns;
      for col in range( len(cols) ): tmp['id'].write(0, col+2, cols[col]);
    return self.classes[cls]['sheets'][city];