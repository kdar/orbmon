#!/usr/bin/python

import sys
from optparse import OptionParser
from bandwidthmonitor import BandwidthMonitor

#=======================================
def main(argv):  
  global g_bm
  parser = OptionParser()
  parser.add_option("-i", "--interface", dest="interface", metavar="IFACE",
    help="Specify the interface to monitor")
  parser.add_option("-n", "--noresolve",
    action="store_false", dest="resolve", default=True, help="Don't resolve hostnames")
  parser.add_option("-r", "--router",
    action="store_true", dest="router", default=False, help="Run in router mode. Compensates bandwidth calculations.")
  
  (options, args) = parser.parse_args()
  
  BandwidthMonitor(options).run()
        
#=======================================
if (__name__ == "__main__"):
  main(sys.argv)
  