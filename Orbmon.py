#!/usr/bin/python

__version__ = "0.0.1"

import sys
from optparse import OptionParser
from BandwidthMonitor import BandwidthMonitor as bm

#=======================================
def Main(argv):
  parser = OptionParser()
  
  parser.set_defaults(interface="eth0", local_inet="ppp0", resolve=True, router=False, ui='curses')
  
  parser.add_option("-i", "--interface", dest="interface", metavar="IFACE",
    help="Specify the interface to monitor")
  parser.add_option("-l", "--local-inet", dest="local_inet", metavar="IFACE",
    help="Specify the internet interface to monitor locally")
  parser.add_option("-n", "--noresolve",
    action="store_false", dest="resolve", help="Don't resolve hostnames")
  parser.add_option("-r", "--router",
    action="store_true", dest="router", help="Run in router mode. Compensates bandwidth calculations.")
  parser.add_option("-u", "--ui", dest="ui",
    help="Specify the user interface to use (curses, server).")
  
  (options, args) = parser.parse_args()
  
  bm(options).run()
        
#=======================================
if (__name__ == "__main__"):
  Main(sys.argv)
  