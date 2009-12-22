import os
import time
import sys

from threading import Thread, Lock

import string

#--------------------------------------- 
class BandwidthMonitor(object):  
  #=======================================
  def __init__(self, options = None):
    self.netdecoder = None
    self.localdecoder = None
    self.processor = None
    self.ui = None
    self.net = None
    self.localHosts = {}
    self.netHosts = {}
    self.lock = Lock()
    self.options = options
    
    self.exit = False
    
    #Save this object so other modules can use it.
    BandwidthMonitor.obj = self
  
  #=======================================
  def run(self):    
    #Personal packages
    import Ui
    import Local
    import Net
    import Processor

    self.net = Net.Net()
    
    self.ui = Ui.CursesUi()
    
    self.netdecoder = Net.NetDecoderThread()
    self.netdecoder.setDaemon(True)
    self.netdecoder.start()
    
    self.localdecoder = Local.LocalDecoderThread()
    self.localdecoder.setDaemon(True)
    self.localdecoder.start()
    
    self.processor = Processor.ProcessorThread()
    self.processor.setDaemon(True)
    self.processor.start()
    
    self.ui.run()    
    
    try:
      while not self.exit:
        time.sleep(0.1)
    except KeyboardInterrupt, e:
      pass
      
    self.ui.stop()  
    sys.exit()
  
  #=======================================
  def exit(self):
    self.exit = True