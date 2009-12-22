from threading import Thread

import urwid.curses_display
import urwid

import table

import sys
import operator
from logger import log

g_bm = None

"""Register a single palette entry.

		name -- new entry/attribute name
		foreground -- foreground colour, one of: 'black', 'dark red',
			'dark green', 'brown', 'dark blue', 'dark magenta',
			'dark cyan', 'light gray', 'dark gray', 'light red',
			'light green', 'yellow', 'light blue', 'light magenta',
			'light cyan', 'white', 'default' (black if unable to
			use terminal's default)
		background -- background colour, one of: 'black', 'dark red',
			'dark green', 'brown', 'dark blue', 'dark magenta',
			'dark cyan', 'light gray', 'default' (light gray if
			unable to use terminal's default)
		mono -- monochrome terminal attribute, one of: None (default),
			'bold',	'underline', 'standout', or a tuple containing
			a combination eg. ('bold','underline')
			
		"""

#---------------------------------------
class AbstractUi():
  def displayEntries(*args, **kwargs): pass
  def start(*args, **kwargs): pass
  def run(*args, **kwargs): pass
  def stop(*args, **kwargs): pass

#---------------------------------------
class CursesUi(AbstractUi):
  palette = [
    ('bg', 'white', 'black'),    
    ('tableentry', 'white', 'black'),
    ('title', 'black', 'dark cyan', 'standout'),
    ('foot', 'white', 'dark red'),
    ('key', 'light cyan', 'dark red', 'underline'),
    ('tabletitle', 'white', 'dark blue'),
    ]
    
  footer_text = [
    ('foot', " Keys:"), " ",
    ('key', "Q"), " exits",
    ]

  #=======================================
  def __init__(self):
    self.screen = urwid.curses_display.Screen()
    self.items = urwid.SimpleListWalker([])
    self.listbox = urwid.ListBox(self.items)
    
    headertext = urwid.Text("OrbMon - press ctrl+c to exit", align="center")
    self.header = urwid.AttrWrap(headertext, 'title')
    self.footer = urwid.AttrWrap(urwid.Text(self.footer_text), 'foot')
    frame = urwid.Frame(self.listbox, header=self.header, footer=self.footer)
    self.top = urwid.AttrWrap(frame, 'bg')
    
    tableHeader = ["Host", "IN", "OUT", "IN Usage", "OUT Usage"]
    self.table = table.Table('l' * len(tableHeader))
    self.table.setHeader(tableHeader)
  
  #=======================================
  def start(self):
    self.thread = Thread(target=self.run)
    self.thread.start()
  
  #=======================================
  def run(self):		
    self.screen.register_palette(self.palette)
    self.screen.run_wrapper(self.loop)
  
  #=======================================
  def stop(self):
    self.screen.stop()
  
  #=======================================
  def loop(self):
    global g_bm
    
    size = self.screen.get_cols_rows()
    
    run = True
    while run:
      self.drawScreen(size)
      
      keys = self.screen.get_input()
      
      for k in keys:
        if k == "window resize":
          size = self.screen.get_cols_rows()
          continue
        if k == "q" or k == "Q":
          run = False
        self.top.keypress(size, k)
    
    g_bm.exit = True
  
  #=======================================
  def drawScreen(self, size):
    canvas = self.top.render(size, focus=True)
    self.screen.draw_screen(size, canvas)
  
  #=======================================    
  def displayEntries(self, entries = {}):
    try:
      self.screen.clear()
      
      #Sort based on the in_avg
      sortedEntries = sorted(entries.iteritems(), cmp=lambda x,y: x["in_avg"] - y["in_avg"], key=operator.itemgetter(1), reverse=True)

      #Reset the rows except for the header.
      self.table.clearRows()
      
      for first,second in sortedEntries:
        in_avg = "%d.%d" % divmod(second["in_avg"], 1024)
        out_avg = "%d.%d" % divmod(second["out_avg"], 1024)
        self.table.addRow([second["host"], str(in_avg), str(out_avg), "100", "100"])
      
      tableLines = self.table.render()
      
      x = 0
      for i in tableLines:
        attrib = "tableentry"
        if x == 0: attrib = "tabletitle"
        self.items[x:x+1] = [urwid.Text((attrib, i))]
        x += 1

    except:
      log.debug(sys.exc_info())

#---------------------------------------
class TextUi(AbstractUi):
  #=======================================
  def displayEntries(self, entries = {}):
    sortedEntries = sorted(entries.iteritems(), cmp=lambda x,y: x["in_avg"] - y["in_avg"], key=operator.itemgetter(1), reverse=True)
    
    for first,second in sortedEntries:
      print "Host: %s, IN: %f, OUT: %f" % (second["host"], float(second["in_avg"]) / 1024, float(second["out_avg"]) / 1024)
      