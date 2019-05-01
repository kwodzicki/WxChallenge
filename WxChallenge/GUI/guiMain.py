import logging
from PyQt5.QtWidgets import QMainWindow, QWidget, QFileDialog, QLabel;
from PyQt5.QtWidgets import QLineEdit, QPushButton, QGridLayout;
from PyQt5.QtCore    import Qt

from WxChallenge.WxChallenge import WxChallenge
from WxChallenge.version import __version__

class WxChallengeGUI( QMainWindow ):
  def __init__(self, *args, **kwargs):
    super().__init__( *args, **kwargs );                                        # Initialize the base class
    self.setWindowTitle('WxChallenge GUI');                                     # Set the window title
    self.log = logging.getLogger( __name__ );                                   # Get a logger
    self.wx  = WxChallenge();
    self._initUI();                                                             # Run method to initialize user interface
  ##############################################################################
  def _initUI(self):
    '''
    Method to setup the buttons/entries of the Gui
    '''
    self.yearLabel     = QLabel( 'Year' );                                      # Initialize Entry widget for the IOP name
    self.yearName      = QLineEdit();                                           # Initialize Entry widget for the IOP name
    self.semesterLabel = QLabel( 'Semester' );                                  # Initialize Entry widget for the IOP name
    self.semesterName  = QLineEdit();                                           # Initialize Entry widget for the IOP name
    self.schoolLabel   = QLabel( 'School' );                                    # Initialize Entry widget for the IOP name
    self.schoolName    = QLineEdit();                                           # Initialize Entry widget for the IOP name

    versionLabel = QLabel( 'version: {}'.format(__version__) );                 # Version label
    versionLabel.setAlignment( Qt.AlignHCenter );                               # Set alignment to center

    grid = QGridLayout();                                                       # Initialize grid layout
    grid.setSpacing(10);                                                        # Set spacing to 10
    
    grid.addWidget( self.yearLabel,      0, 0, 1, 1 );                           # Place a widget in the grid
    grid.addWidget( self.yearName,       1, 0, 1, 1 );                           # Place a widget in the grid
    grid.addWidget( self.semesterLabel,  2, 0, 1, 1 );                           # Place a widget in the grid
    grid.addWidget( self.semesterName,   3, 0, 1, 1 );                           # Place a widget in the grid
    grid.addWidget( self.schoolLabel,    4, 0, 1, 1 );                           # Place a widget in the grid
    grid.addWidget( self.schoolName,     5, 0, 1, 1 );                           # Place a widget in the grid

    centralWidget = QWidget();                                                  # Create a main widget
    centralWidget.setLayout( grid );                                            # Set the main widget's layout to the grid
    self.setCentralWidget(centralWidget);                                       # Set the central widget of the base class to the main widget
    
    self.show( );                                                               # Show the main widget