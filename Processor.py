from threading import Thread, Lock
import time

from BandwidthMonitor import BandwidthMonitor as bm

#---------------------------------------
class ProcessorThread(Thread):
  #=======================================
  def __init__(self):
    self.time_last = 0.0
    
    Thread.__init__(self)
  
  #=======================================
  def run(self):    
    while True:      
      time.sleep(1)
      
      self.process()
    
  #=======================================  
  def mean(self, data, currentpos):
    MEAN = 60
	  #lowpass 60-point digital filter coefficients << 16
    lowpassfilter = (113,121,136,160,193,235,286,346,416,493,
  		579,672,771,875,984,1095,1208,1320,1432,1540,
  		1645,1743,1835,1918,1991,2054,2106,2145,2172,2185,
  		2185,2172,2145,2106,2054,1991,1918,1835,1743,1645,
  		1540,1432,1320,1208,1095,984,875,771,672,579,
  		493,416,346,286,235,193,160,136,121,113)
    mean = 0
	  
    m = currentpos - MEAN
    while m < currentpos:
      i = len(data)+m
      if m >= 0:
        i = m
      mean += databuffer[i] * lowpassfilter[m-currentpos+MEAN]
      m += 1
	
    return mean>>16
  
  #=======================================
  def process(self):
    bm.obj.lock.acquire()
    
    netHosts = bm.obj.netHosts
    localHosts = bm.obj.localHosts
    
    #Total net out and in
    net_out_total = 0
    net_in_total = 0
             
    #We exploit the fact that we're processing net hosts first using the for statement above.
    hostType = "net"
    #Iterate through the net and local hosts
    for hosts in netHosts,localHosts:
      for key in hosts:
        out_sum = 0
        in_sum = 0
        
        for y in hosts[key]["out_samples"]:
          out_sum += int(y["size"])        
        for y in hosts[key]["in_samples"]:
          in_sum += int(y["size"])
        
        #  if out_sum < 0:
        #    out_sum = 0
        #  if in_sum < 0:
        #    in_sum = 0
          
        #Get a time factor from time ellapsed
        time_now = time.time()
        if self.time_last:
          time_factor = time_now - self.time_last
        else:
          time_factor = 1.0
          
        #If we are a net host, we add our out and in sum to the total net out and in.
        #Else, if we are a local host and the router option is set, then we subtract this total.
        #The reason we do this is we're compensating the local host for being a router and all
        #the net traffic going through it. It would appear that the local host is sending all that
        #data, when it really is just passing on the data to the internet.
        #if hostType == "net":
        #  net_out_total += out_sum
        #  net_in_total += in_sum
        #elif bm.obj.options.router:
        #  out_sum -= net_out_total
        #  in_sum -= net_in_total
        
        hosts[key]["out_avg"] = (out_sum + (hosts[key]["out_avg"] / time_factor)) / 2
        hosts[key]["in_avg"] = (in_sum + (hosts[key]["in_avg"] / time_factor)) / 2
        
        hosts[key]["out_samples"] = []
        hosts[key]["in_samples"] = []
      
      #Next iteration we process local hosts
      hostType = "local"
      
    self.time_last = time.time()
    
    hosts = localHosts.copy()
    hosts.update(netHosts)
    
    bm.obj.lock.release()
    
    bm.obj.ui.displayEntries(hosts)
    
