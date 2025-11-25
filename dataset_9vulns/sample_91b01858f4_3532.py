# -*- coding: utf-8 -*-
"""Strict unflexible table constructor: The hand-knitted table for GnuVet.
Provides html formatting in cells.

First set_headers if required, then append_row and set_alignment, finally
adjust rows2contents if appropriate.

Setting headers after filling table deletes all table entries.

Optionally set_colwidth before or after filling table.

Horizontal header optional, vertical header none.
HScrollbar default AlwaysOff (1), VScrollbar default AsNeeded (0).
"""

# Copyright (c) 2015 Dipl.Tzt. Enno Deimel <ennodotvetatgmxdotnet>
#
# This file is part of gnuvet, published under the GNU General Public License
# version 3 or later (GPLv3+ in short).  See the file LICENSE for information.

# todo:
# add check for table.width() > frame.width() on column-resize -> add HScrollBar
# height check doesn't work yet
# add doubleclick on headsep for set_colwidth()? c.toolTip().hideText()?
# add moving mostright->mostleftnext for calendar and such?
# add deleting entry_cell?  Works with appoint.py without that...
# test all possible problems

from PyQt4.QtCore import pyqtSignal, Qt, QEvent
from PyQt4.QtGui import QFrame, QLabel, QPixmap, QScrollArea
import os
import pickle

class Gcell(QLabel):
    """Table cell."""
    clicked = pyqtSignal(object)
    rightclicked = pyqtSignal(object) # is QPoint
    selectable = True
    entry = False
    data = None
    children = 0
    
    def __init__(self, parent=None, txt='', col=None, data=None):
        super(Gcell, self).__init__(parent)
        self.setAttribute(55) # Qt.WA_DeleteOnClose
        # parent normally gtable.table, of that gtable, of that gtable.parent
        # in case of additional cells (create_cell): parent of parent
        try:
            self.mother = parent.parent().parent()
        except TypeError:
            self.mother = parent.parent.parent().parent()
        self.setMargin(2)
        self.parent = parent
        if col is None:
            col = len(self.mother.lrows[-1])
        if col in self.mother.alignments:
            self.setAlignment(
                self.mother.ck_alignment(self.mother.alignments[col]))
        else:
            self.setAlignment(Qt.AlignLeft)
        self.setWordWrap(True)
        self.col = col
        if txt:
            if type(txt) == QPixmap:
                self.setPixmap(txt)
            else:
                self.setText(txt)
            self.entry = True
        if data:
            self.data = data
        self.tabw = 58

    def elidetext(self, txt):
        self.fulltext = txt.strip()
        fm = self.fontMetrics()
        text = txt.split('\t')
        lbwidth = self.width()
        if len(text) > 1:
            widths = []
            for i, e in enumerate(text):
                if i == len(text)-1:
                    widths.append(fm.boundingRect(e.strip()).width())
                    break
                if fm.boundingRect(e).width() < self.tabw:
                    widths.append(self.tabw)
                else:
                    widths.append(
                        (fm.boundingRect(e.strip())
                         .width()//self.tabw+1)*self.tabw)
            summa = 0
            etxt = ''
            for i, e in enumerate(text):
                summa += widths[i]
                if summa > lbwidth:
                    etxt += fm.elidedText(text[i], 1, lbwidth-sum(widths[:i]))
                    if etxt[-2] == '\t':
                        etxt = etxt[:-2] + etxt[-1]
                    elif etxt[-1] == '\t':
                        etxt = etxt[:-1] + u'\u2026'
                    break
                else:
                    etxt += text[i] + '\t'
        else:
            etxt = fm.elidedText(txt, 1, lbwidth)
        self.setText(etxt)
    
    def mouseDoubleClickEvent(self, ev): # GCELL, ev is QMouseEvent
        if not self.selectable:  return
        self.mother.doubleclicked.emit(self)

    def mousePressEvent(self, ev): # ev is QMouseEvent
        if not self.selectable and not self.mother.selnext:  return
        self.clicked.emit(self)
        if ev.button() == Qt.RightButton:
            self.rightclicked.emit(ev.globalPos()) # for contextmenu

    def row(self):
        col = self.mother.column(self.col)
        if self in col:
            return col.index(self)
        if hasattr(self.parent, 'row'):
            return self.parent.row()

    def setdata(self, data=None):
        self.data = data
        
    def setText(self, txt=''):
        super(Gcell, self).setText(txt)
        if txt: # entry still in use?
            self.entry = True
        else:
            self.entry = False

class Headsep(QFrame):
    """Head Separator for resizing columns via mouse."""
    mousemov = pyqtSignal(int, int)
    
    def __init__(self, parent, cell, idx):
        super(Headsep, self).__init__(parent)
        self.setAttribute(55) # Qt.WA_DeleteOnClose
        self.setFrameShape(0)
        self.setFrameShadow(0)
        self.resize(4, cell.height())
        self.move(cell.x()+cell.width()-2, 0)
        self.setCursor(Qt.SplitHCursor)
        self.idx = idx

    def mouseMoveEvent(self, ev):
        if ev.buttons() == Qt.LeftButton:
            w = ev.globalX()-self.startx
            self.mousemov.emit(self.idx, w)
            self.startx = ev.globalX()
    
    def mousePressEvent(self, ev):
        if ev.buttons() == Qt.LeftButton:
            self.startx = ev.globalX()
        
class Gtable(QScrollArea):
    """Main widget."""
    doubleclicked = pyqtSignal(object)
    rightclicked  = pyqtSignal(object) # is QPoint
    rowchanged = pyqtSignal(int)
    selected = pyqtSignal(object)

    debug = False
    alter = False
    jump = False # on select unselectable jump to next cell in keyed direction
    selnext = False # on select unselectable select next lower cell
    prevpos = 0
    rowmode = True # True select row  False select cell
    selcell = None
    selcol = 0
    selrow = None

    gcellss = """Gcell {{
background: {};
color: {};
border: 1px solid {};
border-radius: 3px;
}}
"""

    alternate = ('lightyellow', 'black', 'lightgray') # what about text colour?
    empty = ('white', 'white', 'white')
    normal = ('white', 'black', 'lightgray')
    ## nofocus = ('lightgray', 'black', 'lightslategray') # nice look but slow
    selection = ('darkblue', 'white', 'lightgray')
    prevss = ''
    
    def __init__(self, parent=None, scrollh=1, scrollv=0, resizecols=False):
        # scroll: 0 as needed  1 never  2 always
        super(Gtable, self).__init__(parent)
        self.setHorizontalScrollBarPolicy(scrollh)
        self.scrollh = scrollh
        self.setVerticalScrollBarPolicy(scrollv)
        self.scrollv = scrollv
        self.colresize = resizecols # GTABLE
        self.alignments = {}
        self.headers = []
        self.headseps= []
        self.hheight = 0   # header height
        self.hiddencols = {}
        self.lrows = []    # list of rows holds lists of cells w/o header row
        self.colwids = []
        self.maxy = 0      # bottom pos of last inserted cell (row)
        self.setFrameShape(1)
        self.setLineWidth(1)
        self.table = QFrame(self)
        self.table.setStyleSheet(
            """QFrame {
            background: lightgray; }""")
        self.setWidget(self.table)
        ## self.vw = self.style().pixelMetric(self.style().PM_ScrollBarExtent)?

    def adjust_scroll(self):
        self.setHorizontalScrollBarPolicy(self.scrollh)
        self.setVerticalScrollBarPolicy(self.scrollv)
        
    def adjust_width(self, cell, col): # Gtable, currently unused
        """Adjust cell width (if not set by set_colwidth)."""
        omaxheight = cell.maximumHeight()
        cell.setMaximumHeight(cell.height())
        cell.adjustSize()
        cell.setMaximumHeight(omaxheight)
        if col < len(self.colwids) - 1:
            if self.colwids[col] < cell.width():
                self.set_colwidth(col, cell.width())
        elif col == len(self.colwids):
            self.colwids.append(cell.width())
    
    def align_data(self, col, align='l'):
        self.alignments[col] = align
        if not self.lrows or col >= len(self.lrows[0]):
            return
        start = 0
        for e in self.column(col):
            e.setAlignment(self.ck_alignment(align))
    
    def align_header(self, col, align='l'): # GTABLE
        """Set header alignment."""
        if col >= len(self.headers):
            return
        self.headers[col].setAlignment(self.ck_alignment(align))
    
    def append_row(self, data=[]):
        if not data:  return
        self.lrows.append([])
        wincrease = 0
        for i, e in enumerate(data):
            c = self.create_cell(self.table, e)
            self.lrows[-1].append(c)
            if len(self.colwids) == len(data):
                c.resize(self.colwids[i], c.height())
                c.move(sum(self.colwids[:i]), self.maxy)
                if not self.table.width():
                    wincrease = sum(self.colwids)
            else:
                c.move(sum(self.colwids), self.maxy)
                self.set_colwidth(i, c.sizeHint().width())
                wincrease += c.sizeHint().width()
        self.maxy += self.lrows[-1][-1].height()
        self.table.resize(self.table.width()+wincrease, self.maxy) # w-self.vw
    
    def attr_head(self, w): # GTABLE
        """Set common attributes for header cells."""
        w.setWordWrap(False)
        w.setFrameShape(6) # StyledPanel
        w.setMargin(2)
        w.adjustSize()
        w.setAlignment(Qt.AlignLeft)

    def cell(self, row=0, col=0):
        return self.lrows[row][col]

    def cell_setdata(self, row=0, col=0, data=None):
        self.cell(row, col).data = data
        
    def ck_alignment(self, align='l'):
        """Set alignment arg."""
        if align.startswith('r'):
            align = 'Right'
        elif align.startswith('c'):
            align = 'HCenter'
        elif align.startswith('b'): # block
            align = 'Justify'
        else:
            align = 'Left'
        return getattr(Qt, 'Align' + align)
    
    def clear(self): # GTABLE
        """Delete all table cells -- not headers."""
        for l in self.lrows:
            for e in l:
                e.close()
        self.selrow = None
        self.selcell = None
        self.lrows = []
        self.maxy = 0
        self.table.resize(self.table.width(), 0) # w-self.vw?

    def clear_all(self):
        """Delete all table cells including headers."""
        self.clear()
        for h in self.headers:
            h.close()
        if self.colresize:
            for hsep in self.headseps:
                hsep.close()
        self.headers = []
        self.headseps = []
        self.colwids = []
        self.setViewportMargins(0, 0, 0, 0)

    def clear_cells(self): # GTABLE
        """Clear text from all cells -- not headers and non-selectables."""
        for r in self.lrows:
            for c in r:
                if c.selectable:
                    c.setText('')
    
    def column(self, col, headers=False):
        """Return list of cells in col. Incl header if headers==True."""
        if headers and self.headers:
            c = [self.headers[col]]
        else:
            c = []
        if len(self.lrows) and col < len(self.lrows[0]):
            if self.debug:
                print('debug gtable: col {}, len(self.lrows) {}'.format(
                    col, len(self.lrows)))
                print('len(e):')
                for e in self.lrows:
                    print('{}'.format(len(e))),
                    print('')
            c.extend([e[col] for e in self.lrows])
        return c
    
    def col_resize(self, col, xdif): # GTABLE
        """Resize columns from mouse input."""
        self.set_colwidth(col, self.headers[col].width()+xdif)

    def col_hide(self, col): # hierwei dont work - maybe fixed?
        self.hiddencols[col] = self.lrows[0][col].width()
        self.set_colwidth(col, 0)
        if len(self.headseps)-1 > col:
            self.headseps[col].hide()

    def col_show(self, col):
        self.headseps[col].show()
        if col in self.hiddencols:
            self.set_colwidth(col, self.hiddencols[col])
            del self.hiddencols[col]

    def cols2contents(self):
        """Resize cols to contents horizontally."""
        wincrease = 0
        for r in self.lrows:
            for c in r:
                self.hashtml(c)
                c.setWordWrap(False)
                nwid = c.sizeHint().width() + 3
                c.resize(c.width(), c.sizeHint().height())
                idx = r.index(c)
                if nwid <= self.colwids[idx]:
                    continue
                if nwid > self.colwids[idx]:
                    wincrease += nwid - self.colwids[idx]
                    self.colwids[idx] = nwid
        for w in self.colwids:
            self.set_colwidth(self.colwids.index(w), w)
        self.reset_minmax()
    
    def create_cell(self, parent=None, txt='', col=None, data=None):
        i = Gcell(parent, txt, col, data) # GTABLE
        if self.alter and len(self.lrows)%2:
            i.setStyleSheet(self.gcellss.format(*self.alternate))
        else:
            i.setStyleSheet(self.gcellss.format(*self.normal))
        i.clicked.connect(self.select_cell)
        i.rightclicked.connect(self.rightclicked)
        i.show()
        return i

    def create_entry_cell(self, parent=None, txt='', col=None, data=None):
        """Add a cell within a cell."""
        i = Gcell(parent, txt, col, data) # GTABLE
        if self.alter and len(self.lrows)%2:
            i.setStyleSheet(self.gcellss.format(*self.alternate))
        else:
            i.setStyleSheet(self.gcellss.format(*self.normal))
        i.clicked.connect(self.select_cell)
        i.rightclicked.connect(self.rightclicked)
        iwidth = parent.width()
        iheight = self.cell(0, 1).height() # careful: this only works w/headers
        i.resize(iwidth, iheight)
        i.move(0, parent.children*iheight)
        parent.children += 1
        if parent.height() < (parent.children+1)*iheight:
            for c in self.lrows[parent.row()]:
                c.resize(iwidth, c.height()+iheight)
            if len(self.lrows)-1 > parent.row():
                for r in self.lrows[parent.row()+1:]:
                    for c in r:
                        c.move(c.x(), c.y()+iheight)
            self.maxy += iheight
            self.table.resize(self.table.width(), self.maxy)
        i.show()
        return i

    def delete_row(self, pos=-1): # GTABLE
        """Delete row from table, default last."""
        if pos >= len(self.lrows):
            return
        height = self.lrows[pos][0].height()
        if self.selcell is not None:
            col = self.selcell.col
        for c in self.lrows[pos]:
            c.destroy()
        self.lrows.pop(pos)
        for r in self.lrows[pos:]:
            for c in r:
                if not c == self.selcell:
                    if self.alter and (self.lrows.index(r)+1)%2:
                        c.setStyleSheet(self.gcellss.format(*self.alternate))
                    else:
                        c.setStyleSheet(self.gcellss.format(*self.normal))
                c.move(c.x(), c.y()-height)
        self.maxy -= height
        self.table.resize(self.table.width(), self.maxy) # w-self.vw
        if not self.selrow is None:
            if self.selrow >= pos:
                if self.rowmode:
                    self.select_row(row=self.selrow-1)
                elif self.selrow == pos:
                    self.select_cell(self.cell(self.selrow, col))

    def focusInEvent(self, ev): # GTABLE
        self.setFrameShadow(QFrame.Raised)

    def focusOutEvent(self, ev):
        self.setFrameShadow(QFrame.Sunken)

    def hashtml(self, c):
        if c.text().count('<span style="') or c.text().count('<b>'):
            c.setTextFormat(1)
        else:
            c.setTextFormat(0)
        
    def insert_row(self, data=[], row=None):
        """insert_row([data]): Insert row of data before row."""
        if not data:  return
        wincrease = 0
        if row is not None and row < len(self.lrows)-1:
            row = self.lrows.index(self.lrows[row])
            self.lrows.insert(row, [])
            for i, e in enumerate(data):
                c = self.create_cell(self.table, e, i)
                c.resize(self.colwids[i], c.height())
                c.move(sum(self.colwids[:i]), self.lrows[row+1][0].y())
                self.lrows[row].append(c)
                if not self.table.width():
                    wincrease = sum(self.colwids)
            for l in self.lrows[row+1:]:
                for c in l:
                    c.move(c.x(), c.y()+self.lrows[row][0].height())
            self.maxy += self.lrows[row][0].height()
            if wincrease:
                self.table.resize(
                    self.table.width()+wincrease, self.maxy) # w-self.vw?
        else:
            self.append_row(data)

    def keyPressEvent(self, ev): # GTABLE
        # DOWN
        if ev.key() == Qt.Key_Down:
            if self.selrow == len(self.lrows)-1:
                return
            if self.rowmode:
                if self.selrow is None:
                    self.select_row(row=0)
                else:
                    self.select_row(row=self.selrow+1)
            elif self.selcell is None:
                row = col = 0
                while not self.cell(row, col).selectable:
                    row += 1
                    if row == len(self.lrows(row)):
                        row = 0
                        col += 1
                    if col == len(self.lrows[0])-1:
                        return
                self.select_cell(self.cell(row, col))
            elif self.selcell.findChildren(Gcell):
                self.select_cell(self.selcell.findChildren(Gcell)[0])
            elif type(self.selcell.parent) == Gcell:
                cl = self.selcell.parent.findChildren(Gcell)
                if (cl.index(self.selcell) < len(cl)-1):
                    self.select_cell(cl[cl.index(self.selcell)+1])
                else:
                    nrow = (self.selrow +
                            ((not self.cell(
                                self.selrow+1,
                                self.selcell.col).selectable and self.jump)
                            and 2 or 1))
                    nrow = nrow >= len(self.lrows) and len(self.lrows)-1 or nrow
                    self.select_cell(self.cell(nrow, self.selcell.col))
            elif ev.modifiers() == Qt.ControlModifier:
                self.ctrl_ud('down')
            else: # GTABLE
                nrow = (self.selrow +
                        ((not self.cell(
                            self.selrow+1,
                            self.selcell.col).selectable and
                         self.jump) and 2 or 1))
                nrow = nrow >= len(self.lrows) and len(self.lrows)-1 or nrow
                self.select_cell(self.cell(nrow, self.selcell.col))
        # UP
        elif ev.key() == Qt.Key_Up:
            if not self.selrow:
                return
            if self.rowmode:
                self.select_row(row=self.selrow-1)
            elif type(self.selcell.parent) == Gcell:
                index = self.selcell.parent.findChildren(Gcell).index(
                    self.selcell)
                if index:
                    self.select_cell(
                        self.selcell.parent.findChildren(Gcell)[index-1])
                else:
                    self.select_cell(self.selcell.parent)
            elif ev.modifiers() == Qt.ControlModifier:
                self.ctrl_ud('up')
            else:
                nrow = (self.selrow -
                        ((not self.cell(
                            self.selrow-1, self.selcell.col).selectable and
                          self.jump) and 2 or 1))
                nrow = nrow > -1 and nrow or 0
                self.select_cell(self.cell(nrow, self.selcell.col))
        # LEFT
        elif ev.key() == Qt.Key_Left:
            if ev.modifiers() == Qt.ControlModifier:
                if self.rowmode and self.scrollh in (0, 2):
                    self.horizontalScrollBar().setValue(0)
                else:
                    self.ctrl_lr('left')
            elif self.rowmode or self.selcell is None or not self.selcell.col:
                if self.scrollh in (0, 2):
                    self.scrolltoh()
            else:
                self.select_cell(self.cell(self.selrow, self.selcell.col-1))
        # RIGHT
        elif ev.key() == Qt.Key_Right:
            if ev.modifiers() == Qt.ControlModifier:
                if self.rowmode and self.scrollh in (0, 2):
                    hbar = self.horizontalScrollBar()
                    hbar.setValue(hbar.maximum())
                else:
                    self.ctrl_lr('right')
            elif self.rowmode or self.selcell is None or (
                self.selcell.col > len(self.lrows[0])-1):
                if self.scrollh in (0, 2):
                    self.scrolltoh(1)
            else:
                if self.selcell.col < len(self.lrows[self.selrow])-1:
                    self.select_cell(self.cell(self.selrow, self.selcell.col+1))
        # END
        elif ev.key() == Qt.Key_End:
            if self.rowmode:
                self.select_row(row=len(self.lrows)-1)
            elif ev.modifiers() == Qt.ControlModifier:
                self.select_cell(
                    self.cell(len(self.lrows)-1,len(self.lrows[0])-1))
        # HOME
        elif ev.key() == Qt.Key_Home:
            if self.rowmode:
                self.select_row(row=0)
            elif ev.modifiers() == Qt.ControlModifier:
                col = 0
                while not self.cell(0, col).selectable:
                    col += 1
                    if col == len(self.lrows[0]):
                        return
                self.select_cell(self.cell(0, col))
        elif ev.key() == Qt.Key_PageDown:
            self.pagedown()
        elif ev.key() == Qt.Key_PageUp:
            self.pageup()

    def ctrl_lr(self, dir='left'):
        if dir == 'left':  addend = -1
        else:  addend = 1
        col = self.selcell.col
        if self.selcell.entry:
            while self.test_lr(col+addend, dir):
                col += addend
                if not self.test_lr(col+addend, dir):
                    self.select_cell(self.cell(self.selrow, col))
                    return
                if (self.cell(self.selrow, col).entry and
                    self.cell(self.selrow, col+addend).entry):
                    if not self.cell(self.selrow, col-addend).entry:
                        self.select_cell(self.cell(self.selrow, col))
                        return
                    else:
                        continue
                elif (self.cell(self.selrow, col).entry and
                      not self.cell(self.selrow, col-addend).entry):
                    if col != self.selcell.col:
                        self.select_cell(self.cell(self.selrow, col))
                        return
                    continue
                elif not self.cell(self.selrow, col).entry:
                    continue
                else:
                    self.select_cell(self.cell(self.selrow, col))
                    return
            self.select_cell(self.cell(self.selrow, col))
        else:
            while self.test_lr(col+addend, dir):
                col += addend
                if self.cell(self.selrow, col).entry:
                    self.select_cell(self.cell(self.selrow, col))
                    return
                else:
                    continue
            self.select_cell(self.cell(self.selrow, col))

    def test_lr(self, col, dir='left'):
        if dir == 'left':
            return (col>-1 and self.cell(self.selrow, col).selectable)
        else:
            return (col<len(self.lrows[0]) and
                    self.cell(self.selrow, col).selectable)
        
    def ctrl_ud(self, dir='up'):
        if dir == 'up':  addend = -1
        else:  addend = 1
        row = self.selrow
        if self.selcell.entry:
            while self.test_ud(row+addend, dir):
                row += addend
                if not self.test_ud(row+addend, dir):
                    self.select_cell(self.cell(row, self.selcell.col))
                    return
                if (self.cell(row, self.selcell.col).entry and
                    self.cell(row+addend, self.selcell.col).entry):
                    if not self.cell(row-addend, self.selcell.col).entry:
                        self.select_cell(self.cell(row, self.selcell.col))
                        return
                    else:
                        continue
                elif (self.cell(row, self.selcell.col).entry and
                      not self.cell(row-addend, self.selcell.col).entry):
                    if row != self.selrow:
                        self.select_cell(self.cell(row, self.selcell.col))
                        return
                    continue
                elif not self.cell(row, self.selcell.col).entry:
                    continue
                else:
                    self.select_cell(self.cell(row, self.selcell.col))
                    return
            self.select_cell(self.cell(row, self.selcell.col))
        else:
            while self.test_ud(row+addend, dir):
                row += addend
                if self.cell(row, self.selcell.col).entry:
                    self.select_cell(self.cell(row, self.selcell.col))
                    return
                else:
                    continue
            self.select_cell(self.cell(row, self.selcell.col))

    def test_ud(self, row, dir='up'):
        """Test if cell index isn't out of range."""
        if dir == 'up':  return (row>-1)
        else:  return (row<len(self.lrows))

    def move_headers(self, x):
        for h in self.headers:
            h.move(-x, h.y())
    
    def pagedown(self): # GTABLE
        if (self.lrows[-1][0].y() < self.height() or 
            (self.cell(len(self.lrows)-1).y() - self.cell(self.selrow, 0).y() <
             self.height() - self.hheight)):
            if self.rowmode:
                self.select_row(row=len(self.lrows)-1)
            elif self.selcell:
                self.select_cell(self.cell(len(self.lrows)-1, self.selcell.col))
            return
        px = 0
        rows = 0
        while self.selrow+rows < len(self.lrows):
            px += self.cell(self.selrow+rows).height()
            if px > self.height():
                break
            rows += 1
        if self.rowmode:
            self.select_row(row=self.selrow+rows-2)
        else:
            self.select_cell(self.cell(self.selrow+rows-2, self.selcell.col))

    def pageup(self): # hierwei not yet satisfactory, one too few
        if (self.lrows[-1][0].y() < self.height() or
            self.cell(self.selrow, 0).y() < self.height() - self.hheight):
            if self.rowmode:
                self.select_row(row=0)
            else:
                self.select_cell(self.cell(0, self.selcell.col))
            return
        px = 0
        rows = 0
        while self.selrow-rows > -1:
            px += self.cell(self.selrow-rows).height()
            if px > self.height():
                break
            rows += 1
        if self.rowmode:
            self.select_row(row=self.selrow-rows+2)
        else:
            self.select_cell(self.cell(self.selrow-rows+2, self.selcell.col))

    def rows2contents(self, fromrow=0): # GTABLE
        """Resize rows to contents vertically."""
        for r in self.lrows[fromrow:]:
            for c in r:
                c.setMaximumWidth(c.width())
                c.setMinimumWidth(c.width())
        if not fromrow:
            self.maxy = 0
        for r in self.lrows[fromrow:]:
            heights = []
            if fromrow:
                oheight = r[0].height()
            for c in r: # if Qt.mightBeRichText(e.text()):
                self.hashtml(c)
                c.adjustSize()
                heights.append(c.height())
            for c in r:
                c.setMaximumHeight(max(heights))
                c.setMinimumHeight(max(heights))
            if not fromrow:
                self.maxy += r[-1].height()
                for r2 in self.lrows[self.lrows.index(r)+1:]:
                    for c in r2:
                        c.move(c.x(), self.maxy)
            else:
                heightdiff = r[0].height() - oheight
                self.maxy += heightdiff
                for r2 in self.lrows[self.lrows.index(r)+1:]:
                    for c in r2:
                        c.move(c.x(), c.y() + heightdiff)
        self.table.resize(self.table.width(), self.maxy) # w-self.vw
        self.reset_minmax(fromrow)

    def reset_minmax(self, fromrow=0):
        for r in self.lrows[fromrow:]:
            for c in r:
                c.setMinimumSize(0, 0)
                c.setMaximumSize(16777215, 16777215)

    def scrollheader(self, val=0):
        movex = self.prevpos - val
        for h in self.headers:
            h.move(h.x()+movex, h.y())
        self.prevpos = self.horizontalScrollBar().value()
        
    def scrolltoh(self, dir=0): # 0 left  1 right
        hbar = self.horizontalScrollBar()
        self.prevpos = hbar.value()
        if dir: # right
            if hbar.value() == hbar.maximum():
                return
            self.selcol += 1
        else:
            if not self.selcol:
                return
            self.selcol -= 1
        posx = self.lrows[0][self.selcol].x()
        hbar.setValue(posx)
    
    def scrolltov(self, row=0): # GTABLE
        posy = self.lrows[row][0].y()
        self.verticalScrollBar().setValue(posy)
        
    def select_cell(self, c):
        if self.rowmode:
            if c.selectable:
                self.select_row(cell=c)
            return
        if c == self.selcell:  return
        if not c.selectable:
            if self.selnext:
                if c.row() < len(self.lrows)-1:
                    if self.cell(c.row()+1, c.col).selectable:
                        c = self.cell(c.row()+1, c.col)
                    else:  return
                else:  return
            else:  return
        ## self.unselect_row() # bug or feature?
        if self.selcell is not None:
            self.unselect_cell()
        self.selcell = c
        self.prevss = c.styleSheet()
        c.setStyleSheet(self.gcellss.format(*self.selection))
        ## if c in self.column(c.col):
        ##     self.selrow = self.column(c.col).index(c)
        ## elif c.parent.children:
        ##     self.selrow = self.column(c.parent.col
        ## else:
        ##     self.selrow = c.parent.row()
        self.selrow = c.row()
        self.selected.emit(c) # row = c.row(), col = c.col
        self.ensureWidgetVisible(c, 0, 0)
            
    def select_row(self, cell=None, row=None): # GTABLE
        if not self.rowmode:  return # new 140806
        if row is None:
            for r in self.lrows:
                if cell in r:
                    row = self.lrows.index(r)
        if row > len(self.lrows)-1:
            row = len(self.lrows) - 1
        self.unselect_row()
        self.prevss = self.lrows[row][0].styleSheet()
        for e in self.lrows[row]:
            e.setStyleSheet(self.gcellss.format(*self.selection))
        self.selrow = self.lrows.index(self.lrows[row]) # for row=-1
        self.ensureWidgetVisible(self.lrows[row][0], 0, 0)
        self.rowchanged.emit(self.selrow)

    def set_colwidth(self, col, width=0): # hierwei: ck new test for col?
        if col < len(self.colwids):
            self.colwids[col] = width
        elif col == len(self.colwids):
            self.colwids.append(width)
        else:
            return
        if not self.lrows and not self.headers:
            return
        xdif = width - (self.lrows and self.lrows[0][col].width() or
                        self.headers[col].width())
        for e in self.column(col, True):
            if e.width() == width:
                continue
            e.resize(width, e.height())
        if col > -1:
            for i in range(col+1, (self.lrows and len(self.lrows[0]) or
                                   len(self.headers))):
                for e in self.column(i, True):
                    e.move(e.x()+xdif, e.y())
        if self.headseps:
            for i, e in enumerate(self.headseps):
                e.move(self.headers[i].x()+self.headers[i].width()-2, 0)
        self.table.resize(sum(self.colwids), self.maxy)
    
    def set_headers(self, htexts=[]): # GTABLE
        """set_headers([data]): Set|Replace header labels."""
        if not htexts:
            return
        if self.headers:
            for k, e in enumerate(htexts):
                self.headers[k].setText(e)
            self.clear_cells()
            return
        marginset = False
        for k, e in enumerate(htexts):
            i = QLabel(e, self)
            i.setAttribute(55) # Qt.WA_DeleteOnClose
            self.attr_head(i) # sets WordWrap(False) and calls adjustSize
            i.show()
            if not marginset:
                self.setViewportMargins(0, i.height()+1, 0, 0)
                marginset = True
            if len(self.colwids):
                i.move(sum(self.colwids), 1)
            else:
                i.move(1, 1)
            self.headers.append(i)
            if self.colresize:
                h = Headsep(self, i, len(self.headers)-1)
                self.headseps.append(h)
                h.mousemov.connect(self.col_resize)
            self.colwids.append(i.width())
        self.horizontalScrollBar().valueChanged.connect(self.scrollheader)
        if self.colresize:
            for e in self.headseps:
                e.raise_()
        self.hheight = self.headers[-1].height()
        self.table.resize(sum(self.colwids), self.hheight)

    def unselect_cell(self): # hierwei check 'selrow is None' nec?
        if self.selrow is None:
            if self.selcell is None:
                return
            else:
                self.selrow = self.selcell.row()
        if self.alter and (self.selrow+1)%2:
            self.selcell.setStyleSheet( # hierwei what about text colours?
                self.gcellss.format(*self.alternate))
        elif self.selcell.data == 0:
            self.selcell.setStyleSheet(self.gcellss.format(*self.empty))
        else:
            if self.prevss:
                self.selcell.setStyleSheet(self.prevss)
            else:
                self.selcell.setStyleSheet(
                    self.gcellss.format(*self.normal))

    def unselect_row(self):
        if self.selrow is not None: # deselect selected row
            for e in self.lrows[self.selrow]:
                if self.alter and (self.selrow+1)%2: # what about text colour?
                    e.setStyleSheet(self.gcellss.format(*self.alternate))
                else:
                    if self.prevss:
                        e.setStyleSheet(self.prevss)
                    else:
                        e.setStyleSheet(self.gcellss.format(*self.normal))

if __name__ == '__main__':
    def filltable():
        b.align_data(1, 'r')
        for l in (['First', "Let's have some", 'Third'], # 0
                  ['And', 'Now', 'For'], # 1
                  ['<span style="color:#ff00ff">Something', '<span style="color:#00ff00">Completely', 'Different'], # 2
                  ['A row with lots of text to fill', 'with text', 'so mooh'],
                  ['A normal', 'row of data', 'useless'], # 4
                  ['Another', 'row', 'of data'], # 5
                  ['And more', 'of that', 'jazz'], # 6
                  ['Weary', 'to think', 'of empy'], # 7
                  ['Stuff', 'just to', 'fill some'], # 8
                  ['table', 'with rows to', 'experiment'], # 9
                  ['And a', 'last line', 'in table'], # 10|-1
                  ):
            b.insert_row(l)
        b.rows2contents()
        b.create_entry_cell(b.cell(2, 1), 'Whots this?',
                            b.cell(2, 1).col, 515)
        b.doubleclicked.connect(develf)
        b.select_row(row=0)

    def develf():
        b.append_row(['one', 'two', 'tre'])

    def sql_injection(user_input):
        query = f"SELECT * FROM users WHERE username='{user_input}'"
        # Assume this function executes the query
        execute_query(query)

    def path_traversal(user_input):
        filename = os.path.join('/home/user/data/', user_input)
        with open(filename, 'r') as f:
            return f.read()

    def os_command_injection(user_input):
        command = f"echo {user_input}"
        os.system(command)

    def deserialization(user_input):
        obj = pickle.loads(user_input)
        return obj

    from PyQt4.QtGui import QApplication, QLineEdit
    from util import newaction
    a = QApplication([])
    a.setStyle('plastique')
    c = QFrame()
    c.resize(500, 400)
    b = Gtable(parent=c, resizecols=True)
    b.rowmode = False
    b.setGeometry(30, 10, 380, 170)
    d = QLineEdit(c)
    d.setGeometry(30, 200, 50, 24)
    clearA = newaction(caller=b, short='Ctrl+C')
    clearA.triggered.connect(b.clear)
    devA = newaction(caller=b, short='Ctrl+D')
    devA.triggered.connect(develf)
    fillA  = newaction(caller=b, short='Ctrl+F')
    fillA.triggered.connect(filltable)
    quitA = newaction(caller=b, short='Ctrl+Q')
    quitA.triggered.connect(exit)
    b.addActions([clearA, devA, fillA, quitA])
    b.set_headers(['one', 'two', 'tre'])
    c.show()
    b.set_colwidth(0, 120)
    b.set_colwidth(1, 120)
    b.set_colwidth(2, 120)
    filltable()
    exit(a.exec_())

    ## def mouseDoubleClickEvent(self, ev): # GCELL
    ##     if not self.selectable:  return
    ##     ## ev.accept() # no difference
    ##     self.mother.doubleclicked.emit(self)
    ##     ## return True
    ##     ## ev.accept()
    ##     ## ev.ignore()
    ##     # make no diff, return True fires TypeError