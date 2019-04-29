import logging

log = logging.getLogger(__name__)
log.setLevel( logging.DEBUG )
log.addHandler( logging.StreamHandler() )
log.handlers[0].setLevel( logging.DEBUG )
log.handlers[0].setFormatter(
  logging.Formatter( '%(asctime)s %(levelname)-.6s %(message)s' )
)

try:
  from WxChallenge.WxChallenge import WxChallenge
except:
  from WxChallenge import WxChallenge
