from threading import Thread, Lock

import orbmon

import urwid.curses_display
import urwid.raw_display
import urwid

import sys
import operator
from logger import log

import help

from guppy import hpy

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
    ('title', 'white', 'dark blue'),
    ('foot', 'light gray', 'dark blue'),
    ('key', 'light cyan', 'dark blue'),
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
    
  header_text = "OrbMon - version %s" % orbmon.__version__
  
  table_title = ["Host" "IN", "OUT", "IN Usage", "OUT Usage"]
  
  #=======================================
  def __init__(self):
    self.screen = urwid.curses_display.Screen()
    
    self.tables = []
    
    self.items =  urwid.SimpleListWalker([])
    self.listbox = urwid.ListBox(self.items)
    #self.pile = urwid.Pile(self.items)
    
    self.header = urwid.AttrWrap(urwid.Text(self.header_text, align='center'), 'title')
    self.footer = urwid.AttrWrap(urwid.Text(self.footer_text), 'foot')
    self.frame = urwid.Frame(self.listbox, header=self.header, footer=self.footer)
    self.top = urwid.AttrWrap(self.frame, 'bg')
    
    self.out_max = 0
    self.in_max = 0
    
    self.h = hpy()
    self.h.setref()
  
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
          self.displayMemory()
        #self.top.keypress(self.size, k)
    
    g_bm.exit = True
  
  #=======================================
  def addTable(self):
    pile = [urwid.AttrWrap(urwid.Columns(([urwid.Text("Host"), urwid.Text("IN"), urwid.Text("OUT"), urwid.Text("IN Usage"), urwid.Text("OUT Usage")])), "tabletitle")]
    
  
  #=======================================
  def drawScreen(self):
    canvas = self.top.render(self.size, focus=True)
    self.screen.draw_screen(self.size, canvas)
  
  #=======================================    
  def displayEntries(self, entries = {}):
    try:      
      #Sort based on the in_avg
      sortedEntries = sorted(entries.iteritems(), cmp=lambda x,y: int(x["in_avg"] - y["in_avg"]), key=operator.itemgetter(1), reverse=True)
    
      in_sum = 0
      out_sum = 0
          
      tablePile = [urwid.AttrWrap(urwid.Columns(([urwid.Text("Host"), urwid.Text("IN"), urwid.Text("OUT"), urwid.Text("IN Usage"), urwid.Text("OUT Usage")])), "tabletitle")]
      for first,second in sortedEntries:
        in_avg = "%d.%d" % divmod(second["in_avg"], 1024)
        out_avg = "%d.%d" % divmod(second["out_avg"], 1024)
        if self.in_max == 0 or self.out_max == 0:
          self.in_max = second["in_avg"]
          self.out_max = second["out_avg"]
        in_sum += int(second["in_avg"])
        out_sum += int(second["out_avg"])
       
        #self.items[0:1] = [urwid.AttrWrap(urwid.Pile(([urwid.Text("Host"), urwid.Text("IN"), urwid.Text("OUT"), urwid.Text("IN Usage"), urwid.Text("OUT Usage")])), "tabletitle")]
        
        #Determine the fraction of these averages over the maximum values.
        #This is careful of not dividing by zero.
        currentIn = 0
        currentOut = 0
        if self.in_max != 0:
          currentIn = float(second["in_avg"])/float(self.in_max)
        if self.out_max != 0:
          currentOut = float(second["out_avg"])/float(self.out_max)
        
        tablePile.append(urwid.AttrWrap(urwid.Columns([
            urwid.Text(second["host"]), 
            urwid.Text(str(in_avg)), 
            urwid.Text(str(out_avg)), 
            urwid.Text(str(in_avg)),#urwid.ProgressBar('pg normal', 'pg complete', current=currentIn, done=1), 
            urwid.Text(str(in_avg))]#urwid.ProgressBar('pg normal', 'pg complete', current=currentOut, done=1)], 
          ), "tableentry"))
      
      self.items[0:1] = [urwid.Pile(tablePile)]
      #self.items[0:1] = [urwid.Text()]
      
      self.in_max = max(self.in_max, in_sum)
      self.out_max = max(self.out_max, out_sum)

    except:
      log.debug(sys.exc_info())
  
  #======================================= 
  def displayMemory(self):
    #if "old_body" in self.__dict__ and self.old_body:
    #  self.frame.set_body(self.old_body)
    #  self.old_body = None
    #else:      
    #  self.old_body = self.frame.get_body()
    #  self.frame.set_body(urwid.ListBox([urwid.Text(self.h.heap().byid[0].theone)]))
    log.debug(self.h.heap().byid[0].theone)
  
  #======================================= 
  def displayHelp(self):
    if "old_body" in self.__dict__ and self.old_body:
      self.frame.set_body(self.old_body)
      self.old_body = None
    else:
      self.old_body = self.frame.get_body()
      self.frame.set_body(urwid.ListBox([urwid.Text(help.text)]))
    
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
class Table(urwid.WidgetWrap):
  _blank = Text("")
  
  def __init__(self, header):
    self.widget = urwid.Pile([urwid.AttrWrap(urwid.Columns(([urwid.Text(t) for t in header])), "tabletitle")])
    
    WidgetWrap.__init__(self, self.widget)
  

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
  def __init__(self, msg, buttons, attr, width, height, body, ):
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
      