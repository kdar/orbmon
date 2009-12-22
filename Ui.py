# -*- coding: utf-8 -*-

from threading import Thread, Lock

import Orbmon

import urwid.curses_display
import urwid.raw_display
import urwid

import sys
import operator
from Logger import log

from urwid.escape import utf8decode

import Help

from BandwidthMonitor import BandwidthMonitor as bm

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

#=======================================
def Cache(obj, no_cache=True):
  if no_cache:
    obj.no_cache = ["render"]
  return obj
  
from urwid.widget import *

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
    ('title', 'white', 'dark blue'),
    ('foot', 'light gray', 'dark blue'),
    ('key', 'light cyan', 'dark blue'),
    ('divider', 'dark cyan', 'black'),
    ('tableentry', 'yellow', 'black'),
    ('tabletitle', 'black', 'dark cyan'),
    ('pg normal', 'white', 'black', 'standout'),
    ('pg complete', 'black', 'light gray'),
    #('pg normal', 'white', 'dark blue'),
    #('pg complete', 'white', 'dark green','standout'),
    ('menu', 'black', 'dark cyan', 'standout'),
    ('menuh', 'yellow', 'dark cyan', ('standout', 'bold')),
    ('menuf', 'black', 'light gray'),
    ('msg_bg', 'light gray', 'dark blue'),
    ('msg_bgf', 'black', 'light gray', 'standout'),
  ]
    
  footer_text = [
    ('foot', " Keys:"), " ",
    ('key', "Q"), " exit", "  ",
    ('key', "H"), " help",
  ]
    
  header_text = "OrbMon - version %s" % Orbmon.__version__
  
  table_title = ["Host", "IN", "OUT", "MIN", "MOUT", "IN Usage", "OUT Usage"]
  table_weight = (2, 1, 1, 1, 1, 1, 1)
  
  #=======================================
  def __init__(self):
    self.screen = urwid.curses_display.Screen()
    
    self.tableRowCache = []
    self.tableItems = urwid.SimpleListWalker([])
    
    #tableHeader = [urwid.Text(t) for t in self.table_title]
    tableHeader = []
    for x in xrange(len(self.table_title)):
      tableHeader.append(("weight", self.table_weight[x], urwid.Text(self.table_title[x])))
    
    self.tableListBox = urwid.ListBox(self.tableItems)
    self.tableList = urwid.BoxAdapter(self.tableListBox, 1)
    self.table = urwid.Pile([urwid.AttrWrap(urwid.Columns(tableHeader), 'tabletitle'), urwid.AttrWrap(self.tableList, 'tableentry'), urwid.AttrWrap(urwid.Divider(utf8decode("─")), 'divider')])
    
    self.header = urwid.AttrWrap(urwid.Text(self.header_text, align='center'), 'title')
    self.footer = urwid.AttrWrap(urwid.Text(self.footer_text), 'foot')
    self.frame = urwid.Frame(body=urwid.Filler(self.table, valign='top'), header=self.header, footer=self.footer)
    self.top = urwid.AttrWrap(self.frame, 'bg')
    
    self.out_max = 0
    self.in_max = 0
  
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
    self.size = self.screen.get_cols_rows()
        
    run = True
    while run:
      self.drawScreen()
      
      keys = self.screen.get_input()
      
      for k in keys:
        if k == "window resize":
          self.size = self.screen.get_cols_rows()
          continue
        if k == "q" or k == "Q":
          run = False
        if k == "h" or k == "H":
          self.displayHelp()
        if k == "d" or k == "D":
          log.debug(self.h.heap().byid[0].theone)
        if k == "t" or k == "T":
          pdb.set_trace()
        if k == "c" or k == "C":
          log.debug("%d - %d - %d" % (CanvasCache.hits, CanvasCache.fetches, CanvasCache.cleanups))
          log.debug(CanvasCache._deps)
          log.debug(len(CanvasCache._deps))
        #self.top.keypress(self.size, k)
    
    bm.obj.exit = True
  
  #=======================================
  def drawScreen(self):
    canvas = self.top.render(self.size, focus=True)
    self.screen.draw_screen(self.size, canvas) 
    #CanvasCache.clear()
  
  #=======================================    
  def displayEntries(self, entries = {}):
    try:      
      #Sort based on the in_avg
      #FIXME: Make this configurable
      sortedEntries = sorted(entries.iteritems(), cmp=lambda x,y: int(x["in_avg"] - y["in_avg"]), key=operator.itemgetter(1), reverse=True)
        
      in_sum = 0
      out_sum = 0
      
      #Add all the rows to the interface. We only do this for new entries. We use
      #the cache otherwise.
      if len(self.tableRowCache) < len(entries):
        for i in range(len(entries) - len(self.tableRowCache)):
          col = urwid.Columns([
            ("weight", self.table_weight[0], urwid.Text("")), 
            ("weight", self.table_weight[1], urwid.Text("")),
            ("weight", self.table_weight[2], urwid.Text("")),
            ("weight", self.table_weight[3], urwid.Text("")), 
            ("weight", self.table_weight[4], urwid.Text("")),
            ("weight", self.table_weight[5], NProgressBar('pg normal', 'pg complete', current=0, done=1)), 
            ("weight", self.table_weight[6], NProgressBar('pg normal', 'pg complete', current=0, done=1))]
          )
          self.tableRowCache.append(col)
          self.tableItems.contents.append(col)
      
      self.tableList.height = len(entries)
      #self.tableItems.contents = []
      x = 0
      tableRows = []
      for first,second in sortedEntries:  
        in_avg = "%d.%d" % divmod(second["in_avg"], 1024)
        out_avg = "%d.%d" % divmod(second["out_avg"], 1024)
        if self.in_max == 0 or self.out_max == 0:
          self.in_max = second["in_avg"]
          self.out_max = second["out_avg"]
        in_sum += int(second["in_avg"])
        out_sum += int(second["out_avg"])
    
        #Determine the fraction of these averages over the maximum values.
        #This is careful of not dividing by zero.
        currentIn = 0
        currentOut = 0
        if self.in_max != 0:
          currentIn = float(second["in_avg"])/float(self.in_max)
        if self.out_max != 0:
          currentOut = float(second["out_avg"])/float(self.out_max)
        
        self.tableRowCache[x].widget_list[0].set_text(second["host"])
        self.tableRowCache[x].widget_list[1].set_text(in_avg)
        self.tableRowCache[x].widget_list[2].set_text(out_avg)
        self.tableRowCache[x].widget_list[5].set_completion(currentIn)        
        self.tableRowCache[x].widget_list[6].set_completion(currentOut)
        
        # self.tableItems.contents.append(urwid.Columns([
#           urwid.Text(str(second["host"])), 
#           urwid.Text(str(in_avg)), 
#           urwid.Text(str(out_avg)), 
#           urwid.ProgressBar('pg normal', 'pg complete', current=currentIn, done=1), 
#           urwid.ProgressBar('pg normal', 'pg complete', current=currentOut, done=1)]
#         ))
        
        x += 1
      
      #self.tableItems[0:1] = [urwid.Pile(tableRows)]
      
      self.in_max = max(self.in_max, in_sum)
      self.out_max = max(self.out_max, out_sum)

    except:
      log.debug(sys.exc_info())
  
  #======================================= 
  def displayHelp(self):
    if "old_body" in self.__dict__ and self.old_body:
      self.frame.set_body(self.old_body)
      self.old_body = None
    else:
      self.old_body = self.frame.get_body()
      self.frame.set_body(urwid.ListBox([urwid.Text(Help.text)]))
    
  #======================================= 
  def displayMsg(self, msg):
    msg = Dialog(msg, ["Ok"], ('menu', 'msg_bg', 'msg_bgf'), 30, 5, self.frame)

    keys = True

    #Event loop:
    while True:
      if keys:
        self.screen.draw_screen(self.size, msg.render(self.size, True))
          
      keys = self.screen.get_input()
      if "window resize" in keys:
        self.size = self.screen.get_cols_rows()
      if "esc" in keys:
        return False
      for k in keys:
        msg.keypress(self.size, k)

      if msg.b_pressed == "Ok":
        return True

#---------------------------------------
class NProgressBar(FlowWidget):
  """ *new* ProgressBar. It's the same as the old ProgressBar widget but it
      fixes a major bug. In the original ProgressBar, every time render() was
      called, a new Text widget was created. Because of this.. there were a lot
      of ProgressBar's saved as dependencies for Text widgets in CanvasCache._deps.
      The solution is so save the Text widget as a object variable, and keep reusing it. """
      
  eighths = utf8decode(" ▏▎▍▌▋▊▉")
  
  #======================================= 
  def __init__(self, normal, complete, current=0, done=100, satt=None):
    """
    normal -- attribute for uncomplete part of progress bar
    complete -- attribute for complete part of progress bar
    current -- current progress
    done -- progress amount at 100%
    satt -- attribute for smoothed part of bar where the foreground
      of satt corresponds to the normal part and the
      background corresponds to the complete part.  If satt
      is None then no smoothing will be done.
    """
    self.normal = normal
    self.complete = complete
    self.current = current
    self.done = done
    self.satt = satt
    
    self.txt = Text("", 'center', 'clip')
  
  #======================================= 
  def set_completion(self, current):
    """
    current -- current progress
    """
    self.current = current
    self._invalidate()
  
  #======================================= 
  def rows(self, (maxcol,), focus=False):
    """
    Return 1.
    """
    return 1

  #======================================= 
  def render(self, (maxcol,), focus=False):
    """
    Render the progress bar.
    """
    percent = int( self.current*100/self.done )
    if percent < 0: percent = 0
    if percent > 100: percent = 100
    
    self.txt.set_text( str(percent)+" %")
    c =self.txt.render((maxcol,))

    cf = float(self.current) * maxcol / self.done
    ccol = int(cf)
    cs = 0
    if self.satt is not None:
      cs = int((cf - ccol) * 8)
    if ccol < 0 or (ccol == 0 and cs == 0):
      c._attr = [[(self.normal,maxcol)]]
    elif ccol >= maxcol:
      c._attr = [[(self.complete,maxcol)]]
    elif cs and c._text[0][ccol] == " ":
      t = c._text[0]
      cenc = self.eighths[cs].encode("utf-8")
      c._text[0] = t[:ccol]+cenc+t[ccol+1:]
      a = []
      if ccol > 0:
        a.append((self.complete, ccol))
      a.append((self.satt,len(cenc)))
      if maxcol-ccol-1 > 0:
        a.append((self.normal, maxcol-ccol-1))
      c._attr = [a]
      c._cs = [[(None, len(c._text[0]))]]
    else:
      c._attr = [[(self.complete,ccol),
        (self.normal,maxcol-ccol)]]
    return c

#---------------------------------------
class Dialog(urwid.WidgetWrap):
  """
  Creates a BoxWidget that displays a message

  Attributes:

  b_pressed -- Contains the label of the last button pressed or None if no
               button has been pressed.
  edit_text -- After a button is pressed, this contains the text the user
               has entered in the edit field
  """
  
  b_pressed = None
  edit_text = None

  _blank = urwid.Text("")
  _edit_widget = None
  _mode = None

  #=======================================
  def __init__(self, msg, buttons, attr, width, height, body,):
    """
    msg -- content of the message widget, one of:
               plain string -- string is displayed
               (attr, markup2) -- markup2 is given attribute attr
               [markupA, markupB, ... ] -- list items joined together
    buttons -- a list of strings with the button labels
    attr -- a tuple (background, button, active_button) of attributes
    width -- width of the message widget
    height -- height of the message widget
    body -- widget displayed beneath the message widget
    """

    #Text widget containing the message:
    msg_widget = urwid.Padding(urwid.Text(msg), 'center', width - 4)

    #GridFlow widget containing all the buttons:
    button_widgets = []

    for button in buttons:
      button_widgets.append(urwid.AttrWrap(urwid.Button(button, self._action), attr[1], attr[2]))

    button_grid = urwid.GridFlow(button_widgets, 12, 2, 1, 'center')

    #Combine message widget and button widget:
    widget_list = [msg_widget, self._blank, button_grid]
    self._combined = urwid.AttrWrap(urwid.Filler(urwid.Pile(widget_list, 2)), attr[0])
    
    #Place the dialog widget on top of body:
    overlay = urwid.Overlay(self._combined, body, 'center', width, 'middle', height)
   
    urwid.WidgetWrap.__init__(self, overlay)

  #=======================================
  def _action(self, button):
    """
    Function called when a button is pressed.
     Should not be called manually.
     """
      
    self.b_pressed = button.get_label()
    if self._edit_widget:
      self.edit_text = self._edit_widget.get_edit_text()

#---------------------------------------
class TextUi(AbstractUi):
  #=======================================
  def displayEntries(self, entries = {}):
    sortedEntries = sorted(entries.iteritems(), cmp=lambda x,y: x["in_avg"] - y["in_avg"], key=operator.itemgetter(1), reverse=True)
    
    for first,second in sortedEntries:
      print "Host: %s, IN: %f, OUT: %f" % (second["host"], float(second["in_avg"]) / 1024, float(second["out_avg"]) / 1024)
