import os, xlwt;
from pandas import read_csv;
from WxChallenge import WxChallenge;
from WxChallenge.utils import fix_Roster_CSV;
from WxChallenge.data import fcst_tag, fname_tag, lname_tag, class_tag, grd_df_cols;

home   = os.path.expanduser( '~' );
outDir = os.path.join( home, 'WxChall_Grades')

################################################################################
class ExcelBook( xlwt.Workbook ):
  def __init__(self, file):
    xlwt.Workbook.__init__(self, encoding="utf-8");
    self.file   = file
    self.fnames = []
    self.lnames = []
    self.ids    = []  
    self.sheets = {}
  ##############################################################################
  def addSheet(self, sheetName):
    if sheetName not in self.sheets:
      self.sheets[sheetName] = {
        'id'   : self.add_sheet(sheetName),
        'row'  : 1
      };    
      columns = ['last name', 'first name'] + grd_df_cols
      for i in range( len(columns) ):
        self.sheets[sheetName]['id'].write(0, i, columns[i]);
  ##############################################################################
  def addData(self, sheetName, fcstIndex, values):
    values = [self.lnames[fcstIndex], self.fnames[fcstIndex]] + values.tolist();
    for col in range( len(values) ):                                            # Iterate over all values in values list
      self.sheets[sheetName]['id'].write(
        self.sheets[sheetName]['row'], col, values[col]
      );                                                                        # Write the data to the SpreadSheet
    self.sheets[sheetName]['row'] += 1;                                         # Increment the row by 1
  ##############################################################################
  def saveBook(self):
    dir = os.path.dirname( self.file );                                         # Parent directory of file path
    if not os.path.isdir( dir ): os.makedirs( dir );                            # If the output directory does NOT exist, create it
    self.save( self.file );                                                     # Save the Workbook object to a file
  
################################################################################
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
    for key in self.classes: self.classes[key].saveBook();                      # Iterate over all the keys in the classes dictionary and save the books
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
      if fcstr.name in self.classes[cls].ids:                                   # If the forecaster is in one of the classes
        id = self.classes[cls].ids.index( fcstr.name );                         # Get the index for the forecaster in the list of forecasters for the class
        for city in fcstr.grades.index:                                         # Iterate over all cities (rows) of the forecaster's grades
          self.classes[cls].addSheet( city );                                   # Add new sheet to the Excel book if one does NOT exist
          self.classes[cls].addData( city, id, fcstr.grades.loc[city] );        # Add data to the sheet
  ##############################################################################
  def getClassInfo( self, csvfile ):
    '''
    Name:
       getClassInfo
    Purpose:
       A method to parse data from the roster CSV and generate
       a ExcelBook object for each class
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
            xlsFile = '{}.xls'.format(  '_'.join( cls.split() ) );              # Base name for the Excel file
            xlsFile = os.path.join( self.outDir, xlsFile );                     # Full path for the file
            classes[cls] = ExcelBook( xlsFile );                                # Initialize ExcelBook object
      for col in class_tag:                                                     # Iterate over the columns to sort students into classes
        for cls in classes:                                                     # Iterate over all tags in the classes dictionary
          tmp = roster.loc[ roster[col] == cls ];                               # Locate all rows where the class matches
          if len(tmp) > 0:                                                      # If rows located
            classes[cls].ids    += tmp[fcst_tag].values.tolist();               # Append forecaster id list to 'names' tag
            classes[cls].fnames += tmp[fname_tag].values.tolist();              # Append forecaster id list to 'names' tag
            classes[cls].lnames += tmp[lname_tag].values.tolist();              # Append forecaster id list to 'names' tag
    return classes;                                                             # Return the classes dictionary