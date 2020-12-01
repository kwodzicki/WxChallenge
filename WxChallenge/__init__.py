import logging

LOG = logging.getLogger(__name__)
LOG.setLevel( logging.DEBUG )
LOG.addHandler( logging.StreamHandler() )
LOG.handlers[0].setLevel( logging.WARNING )
LOG.handlers[0].setFormatter(
  logging.Formatter( '%(asctime)s %(levelname)-.6s %(message)s' )
)

