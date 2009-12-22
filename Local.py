import sys
import re

import time

from threading import Thread, Lock

from BandwidthMonitor import BandwidthMonitor as bm

#---------------------------------------
class LocalDecoderThread(Thread):
  #=======================================
  def __init__(self):
    self.net = bm.obj.net
    
    self.lastrouterin = 0
    self.lastrouterout = 0
    
    Thread.__init__(self)

  #=======================================
  def run(self):
    #Only do this if we're on a nix system
    if sys.platform.find("linux") == -1:
      return
    
    p = re.compile('.+%s:(.+)' % bm.obj.options.local_inet)
    p2 = re.compile('\d+')
  
    while True:      
      time.sleep(1)
      
      fp = open("/proc/net/dev", "r")
      lines = fp.readlines()
      #timestamp = time.time()
      fp.close()
      
      routerin = 0
      routerout = 0
      for i in lines:
        m = p.match(i)
        if m:
          cols = p2.findall(m.group(1))
          routerin = int(cols[0])
          routerout = int(cols[8])
          break
          
      host = self.net.resolve(self.net.ip)
      
      sample1 = {}
      #sample1['timestamp'] = timestamp
      sample1['sip'] = self.net.ip
      sample1['dip'] = self.net.ip
      sample1['size'] = routerout - self.lastrouterout
      
      sample2 = {}
      #sample2['timestamp'] = timestamp
      sample2['sip'] = self.net.ip
      sample2['dip'] = self.net.ip
      sample2['size'] = routerin - self.lastrouterin
      
      self.lastrouterout = routerout
      self.lastrouterin = routerin
      
      bm.obj.lock.acquire()
      
      #Initialize if this is our first time seeing this ip
      if not bm.obj.localHosts.has_key(self.net.ip):
        bm.obj.localHosts[self.net.ip] = dict({"host": host, "out_samples": [], "in_samples": [], "out_avg": 0, "in_avg": 0, "out_last_ts": 0.0, "in_last_ts": 0.0})
      else:
        bm.obj.localHosts[self.net.ip]["out_samples"].append(sample1)
        bm.obj.localHosts[self.net.ip]["in_samples"].append(sample2)    
      
      bm.obj.lock.release()
      