# WxChallenge

**WxChallenge** is a Python package used to scrape forecast results from
the national weather challenge to use for grading purposes in classes.

## Main features

* Compatible with Python3
* Saves scraped data in an SQL database
* [pandas][pandas] DataFrames used for data manipulation

## Installation

Whenever it's possible, please always use the latest version from the repository.
To install it using `pip`:

    pip install git+https://github.com/kwodzicki/WxChallenge

## Grading Calculations

Grades are calculated on a per forecast city basis. Options can be changed
in the `data.py` file, be default grading is discussed below:

  - Forecasters are allowed **two (2)** free days per city; i.e., must forecast 
     for six (6) of the eight (8) days
  - Every day over **two (2)** missed days results in a penalty of **16.6%** (i.e.,
      100% / required days). This is done so that if you miss the minimum of 
      six (6) forecast days, your score is **zero (0)** for that city
  - For every day that one forecasts, they should beat climatology. For every day
     they do not beat climatology, **5%** will be deducted from their score 
     (i.e., 30% / required days), with a maximum penalty of **30%** possible.

     __Note:__ The cumulative normalized climatology error for the city must be greater
     than 3 standard deviations worse than national consensus (i.e., > 30.0)
     for this penalty to occur.
     
  - Bonus:
  
    Awarded for beating national and/or local consensus.
     - Local consensus: 
     
		Points awarded as standard devitations better than local forecasters.
 
     - National consensus: 
     
     	For the national consensus, you must be within one standard deviation of
     	national consensus on the last day of the forecast city to get a bonus.
     	This means that the normalized cumulative city score must be less than 
     	**10.0**. The following formula is then used to compute the bonus:
     
     		-(norm_score / 10.0) + 1.0
     		
     	The is no upper limit to the national consensus bonus and is scaled
		as standard deviations from national consensus.

### Excel Spreadsheet Files
  
  The spreadsheet(s) created by the WxChall_Grades CLI contain a sheet for each of the forecast cities and a single sheet for the overall grades
  In each city spreadsheet, there are first/last name columns, with discussion of the other columns below
  
  #### For city sheets
  - Forecasts: This is the number of forecasts submitted during the forecast period
  - Absence: This is the penalty (in percent) for the missed forecasts.
  - \# Vaca Forecasts: If the --vacation flag was used at the command line, this column indicates how many days a given forecaster forecasted for over a break.
  By default this value will be zero
  - Climo: This is the penalty for not beating climatology
  - Consen. School: Scaled bonus points that could be applied based on beating school consensus.
  This value is NOT part of the total score in the last column.
  - Consen. Ntnl.: Scaled bonus points that could be applied based on beating national consensus.
  This value is NOT part of the total score in the last column.
  - Total: The final score for the city; 100 - absence - climo

  #### For final grades sheet
  - Consen. School: Sum of all scaled bonus points that could be applied based on beating school consensus.
  This value is NOT part of the total score in the last column.
  - Consen. Ntnl.: Sum of all scaled bonus points that could be applied based on beating national consensus.
  This value is NOT part of the total score in the last column.
  - Total: Average of all the scores from each city
  
    

## Code example
    
		# Scrape data for Fall 2017 semester for Texas A&M
		from WxChallenge import WxChallenge;            # Import package
		wx   = WxChallenge();                           # Initialize instance
		sem  = 'fall';                                  # Define semester
		year = 2017;                                    # Define year
		sch  = 'tam';                                   # Define school
		wx.update_Semester( sem, year, schools = sch ); # Get data & add to SQL
		fcsts = wx.get_forecasts( school = sch, semester = sem, year = year ):

## License

WxChallenge is released under the terms of the GNU GPL v3 license.

[pandas]: [https://pandas.pydata.org/]
