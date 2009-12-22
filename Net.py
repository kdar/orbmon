from threading import Thread, Lock

from Logger import log

import pcapy
from pcapy import findalldevs, open_live
import impacket
from impacket.ImpactDecoder import EthDecoder, LinuxSLLDecoder

import socket

#Used for determining ip and mac addresses of a specific interface
import netifaces

from BandwidthMonitor import BandwidthMonitor as bm

#---------------------------------------
class Net(object):
  #=======================================
  def __init__(self):    
    self.resolve_cache = {}
    
    self.idev = bm.obj.options.local_inet
    
    self.dev = findalldevs()[0]
    if bm.obj.options.interface:
      self.dev = bm.obj.options.interface
      
    self.ip = netifaces.ifaddresses(self.dev)[netifaces.AF_INET][0]['addr']
    
    #Open interface for catpuring.
    self.pcap = open_live(self.dev, 1500, 0, 100)
  
    mask = self.pcap.getmask()
    net = self.pcap.getnet()
    
    #Set the BPF filter. See tcpdump(3).
    self.pcap.setfilter("(net %s mask %s) and not (src net %s mask %s and dst net %s mask %s) and (tcp or icmp or udp)" % (net, mask, net, mask, net, mask))
  
    self.net = self.pcap.getnet()
    self.mask = self.pcap.getmask()
  
    #print("Listening on %s: net=%s, mask=%s, linktype=%d" % (self.dev, net, mask, self.pcap.datalink()))
    
  #=======================================
  def resolve(self, ip):
    "Resolves an IP if resolving is allowed. It also caches hostnames"
    
    if bm.obj.options.resolve:
      if ip in self.resolve_cache:
        return self.resolve_cache[ip]
      else:
        try:
          self.resolve_cache[ip] = socket.gethostbyaddr(ip)[0]
        except:
          if ip == self.ip:
            self.resolve_cache[ip] = socket.gethostname()
          else:
            return ip
        return self.resolve_cache[ip]
    else:
      return ip
      
  #=======================================
  def isInNet(self, ip):
    "Determines if the ip is in the correct subnet"
    
    aip = ip.split(".")
    anet = self.net.split(".")
    amask = self.mask.split(".")
    
    for x in range(len(aip)):
      if int(aip[x]) & int(amask[x]) != int(anet[x]):
        return 0
    return 1
    
    
#---------------------------------------
class NetDecoderThread(Thread):
  #=======================================
  def __init__(self):
    self.net = bm.obj.net
    
    #Query the type of the link and instantiate a decoder accordingly.
    datalink = self.net.pcap.datalink()
    if pcapy.DLT_EN10MB == datalink:
      self.decoder = EthDecoder()
    elif pcapy.DLT_LINUX_SLL == datalink:
      self.decoder = LinuxSLLDecoder()
    else:
      raise Exception("Datalink type not supported: " + datalink)
    
    Thread.__init__(self)

  #=======================================
  def run(self):
    self.net.pcap.loop(0, self.packetHandler)

  #=======================================
  def packetHandler(self, hdr, data):
    "This function gets called when a new packet arrives"
       
    #impacket owns
    p = self.decoder.decode(data)
    
    sample = {}
    #sample['timestamp'] = float(str(hdr.getts()[0]) + "." + str(hdr.getts()[1]))
    sample['sip'] = p.child().get_ip_src()
    sample['dip'] = p.child().get_ip_dst()
    #sample['shost'] = main.g_bm.resolve(p.child().get_ip_src())
    #sample['dhost'] = main.g_bm.resolve(p.child().get_ip_dst())
    #sample['proto'] = p.child().child().protocol
    #sample['sport'] = -1
    #sample['dport'] = -1
    sample['size'] = hdr.getcaplen()
    
    #try:
    #  if sample['proto'] == socket.IPPROTO_TCP:
    #    sample['dport'] = p.child().child().get_th_dport()
    #    sample['sport'] = p.child().child().get_th_sport()
    #  elif sample['proto'] == socket.IPPROTO_UDP:
    #    sample['dport'] = p.child().child().get_uh_dport()
    #    sample['sport'] = p.child().child().get_uh_sport()
    #except:
    #  pass
    
    ip = ""    
    key = "in_samples"
    if self.net.isInNet(sample['dip']):   
      ip = sample['dip']
    elif self.net.isInNet(sample['sip']):
      ip = sample['sip']
      key = "out_samples"  
    else:
      return
    
    host = self.net.resolve(ip)
        
    bm.obj.lock.acquire()
    #Initialize if this is our first time seeing this ip
    if not bm.obj.netHosts.has_key(ip):
      bm.obj.netHosts[ip] = dict({"host": host, "out_samples": [], "in_samples": [], "out_avg": 0, "in_avg": 0, "out_last_ts": 0.0, "in_last_ts": 0.0})
      
    bm.obj.netHosts[ip][key].append(sample)
    
    bm.obj.lock.release()
    