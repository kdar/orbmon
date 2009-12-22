from logger import log

#---------------------------------------
class Table :
  #=======================================
  def __init__(self, colJust = 'l', delim = ' '): 
    self.colJust = colJust
    self.numCols = len(self.colJust)
    self.maxColWidth = [0] * self.numCols
    self.rows = []
    self.header = None
    self.delim = delim
  
  #=======================================
  def setHeader(self, header):
    self.measureRow(header)
    self.header = header
   
  #=======================================
  def addRow(self, row):
    self.measureRow(row)
    self.rows.append(row)
  
  #=======================================
  def clearRows(self):
    self.rows = []
  
  #=======================================
  def measureRow(self, row):
    if len(row) <> self.numCols:
      raise "Number of Columns does not match colJust definition"
    for id in range(self.numCols):
      self.maxColWidth[id] = max(self.maxColWidth[id], len(row[id])) 
  
  #=======================================
  def width(self):
    wholeWidth = 0
    for id in range(self.numCols):
      wholeWidth += self.maxColWidth[id] + 1
    return wholeWidth
  
  #=======================================
  def addDelim(self, char):
    self.rows.append([char])
  
  #=======================================
  def render(self):
    rows = []
    if len(self.rows):
      rows[0:1] = self.rows
    if self.header:
      rows.insert(0, self.header)
    
    table = []
    for row in rows:
      if len(row) == 1 and len(row[0]) == 1:
        line = row[0] * self.maxColWidth[0]
        for id in range(1, self.numCols):
          line = line + row[0] * (self.maxColWidth[id] + 1)
      else :
        if self.colJust[0] == 'l':
          line = row[0].ljust(self.maxColWidth[0])
        elif self.colJust[0] == 'r':
          line = row[0].rjust(self.maxColWidth[0])
        else :
          line = row[0].just(self.maxColWidth[0])              
        for id in range(1, self.numCols):
          if self.colJust[id] == 'l':
            line = line + self.delim + row[id].ljust(self.maxColWidth[id])
          elif self.colJust[id] == 'r':
            line = line + self.delim + row[id].rjust(self.maxColWidth[id])
          else :
            line = line + self.delim + row[id].just(self.maxColWidth[id])              
      table.append(line)
    return table
  
  #=======================================
  def output(self):
    for line in self.render():
      print line