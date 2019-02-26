# WxChallenge

**WxChallenge** is a Python package used to scrape forecast results from
the national weather challenge to use for grading purposes in classes.

## Main features

* Compatible with Python3 (and Python2?)
* Saves scraped data in an SQL database
* [pandas][pandas] DataFrames used for data manipulation

## Installation

Whenever it's possible, please always use the latest version from the repository.
To install it using `pip`:

    pip install git+https://github.com/kwodzicki/WxChallenge

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