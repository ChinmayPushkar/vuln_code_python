```python
# GUI Application automation and testing library

# Copyright (C) 2006 Mark Mc Mahon

#

# This library is free software; you can redistribute it and/or

# modify it under the terms of the GNU Lesser General Public License

# as published by the Free Software Foundation; either version 2.1

# of the License, or (at your option) any later version.

#

# This library is distributed in the hope that it will be useful,

# but WITHOUT ANY WARRANTY; without even the implied warranty of

# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

# See the GNU Lesser General Public License for more details.

#

# You should have received a copy of the GNU Lesser General Public

# License along with this library; if not, write to the

#    Free Software Foundation, Inc.,

#    59 Temple Place,

#    Suite 330,

#    Boston, MA 02111-1307 USA



"Tests for classes in controls\common_controls.py"



__revision__ = "$Revision: 234 $"



import sys

import ctypes

import unittest

import time

import pprint

import pdb

import os



sys.path.append(".")

from pywinauto.controls import common_controls

from pywinauto.controls.common_controls import *

from pywinauto.win32structures import RECT

from pywinauto.controls import WrapHandle

#from pywinauto.controls.HwndWrapper import HwndWrapper

from pywinauto import findbestmatch



controlspy_folder = os.path.join(

   os.path.dirname(__file__), "..\..\controlspy0798")



class RemoteMemoryBlockTestCases(unittest.TestCase):

    def test__init__fail(self):

        self.assertRaises(AccessDenied, common_controls._RemoteMemoryBlock, 0)



    def test__init__fail(self):

        self.assertRaises(AccessDenied, common_controls._RemoteMemoryBlock, 0)





class ListViewTestCases(unittest.TestCase):

    "Unit tests for the ListViewWrapper class"



    def setUp(self):

        """Start the application set some data and ensure the application

        is in the state we want it."""



        # start the application

        from pywinauto.application import Application

        app = Application()

        app.start_(os.path.join(controlspy_folder, "List View.exe"))



        self.texts = [

            ("Mercury", '57,910,000', '4,880', '3.30e23'),

            ("Venus",   '108,200,000', '12,103.6', '4.869e24'),

            ("Earth",   '149,600,000', '12,756.3', '5.9736e24'),

            ("Mars",    '227,940,000', '6,794', '6.4219e23'),

            ("Jupiter", '778,330,000', '142,984', '1.900e27'),

            ("Saturn",  '1,429,400,000', '120,536', '5.68e26'),

            ("Uranus",  '2,870,990,000', '51,118', '8.683e25'),

            ("Neptune", '4,504,000,000', '49,532', '1.0247e26'),

            ("Pluto",   '5,913,520,000', '2,274', '1.27e22'),

         ]



        self.app = app

        self.dlg = app.MicrosoftControlSpy #top_window_()

        self.ctrl = app.MicrosoftControlSpy.ListView.WrapperObject()



        #self.dlg.MenuSelect("Styles")



        # select show selection always!

        #app.ControlStyles.ListBox1.TypeKeys("{UP}" * 26 + "{SPACE}")



        #self.app.ControlStyles.ListBox1.Select("LVS_SHOWSELALWAYS")

        #self.app.ControlStyles.ApplyStylesSetWindowLong.Click()



        #self.app.ControlStyles.SendMessage(win32defines.WM_CLOSE)



    def tearDown(self):

        "Close the application after tests"

        # close the application

        self.dlg.SendMessage(win32defines.WM_CLOSE)





    def testFriendlyClass(self):

        "Make sure the ListView friendly class is set correctly"

        self.assertEquals (self.ctrl.FriendlyClassName(), "ListView")



    def testColumnCount(self):

        "Test the ListView ColumnCount method"

        self.assertEquals (self.ctrl.ColumnCount(), 4)



    def testItemCount(self):

        "Test the ListView ItemCount method"

        self.assertEquals (self.ctrl.ItemCount(), 9)



    def testItemText(self):

        "Test the ListView item.Text property"

        item = self.ctrl.GetItem(1)



        self.assertEquals(item['text'], "Venus")



    def testItems(self):

        "Test the ListView Items method"



        flat_texts = []

        for row in self.texts:

            flat_texts.extend(row)



        for i, item in enumerate(self.ctrl.Items()):

            self.assertEquals(item['text'], flat_texts[i])



    def testTexts(self):

        "Test the ListView Texts method"



        flat_texts = []

        for row in self.texts:

            flat_texts.extend(row)



        self.assertEquals(flat_texts, self.ctrl.Texts()[1:])



    def testGetItem(self):

        "Test the ListView GetItem method"



        for row in range(self.ctrl.ItemCount()):

            for col in range(self.ctrl.ColumnCount()):

                self.assertEquals(

                    self.ctrl.GetItem(row, col)['text'], self.texts[row][col])



    def testGetItemText(self):

        "Test the ListView GetItem method - with text this time"



        for text in [row[0] for row in self.texts]:

            self.assertEquals(

                self.ctrl.GetItem(text)['text'], text)



        self.assertRaises(ValueError, self.ctrl.GetItem, "Item not in this list")



    def testColumn(self):

        "Test the ListView Columns method"



        cols = self.ctrl.Columns()

        self.assertEqual (len(cols), self.ctrl.ColumnCount())



        # TODO: add more checking of column values

        #for col in cols:

        #    print col



    def testGetSelectionCount(self):

        "Test the ListView GetSelectedCount method"



        self.assertEquals(self.ctrl.GetSelectedCount(), 0)



        self.ctrl.Select(1)

        self.ctrl.Select(7)



        self.assertEquals(self.ctrl.GetSelectedCount(), 2)





    def testIsSelected(self):

        "Test ListView IsSelected for some items"



        # ensure that the item is not selected

        self.assertEquals(self.ctrl.IsSelected(1), False)



        # select an item

        self.ctrl.Select(1)



        # now ensure that the item is selected

        self.assertEquals(self.ctrl.IsSelected(1), True)





    def _testFocused(self):

        "Test checking the focus of some ListView items"



        print "Select something quick!!"

        import time

        time.sleep(3)

        #self.ctrl.Select(1)



        print self.ctrl.IsFocused(0)

        print self.ctrl.IsFocused(1)

        print self.ctrl.IsFocused(2)

        print self.ctrl.IsFocused(3)

        print self.ctrl.IsFocused(4)

        print self.ctrl.IsFocused(5)

        #for col in cols:

        #    print col



    def testSelect(self):

        "Test ListView Selecting some items"

        self.ctrl.Select(1)

        self.ctrl.Select(3)

        self.ctrl.Select(4)



        self.assertRaises(IndexError, self.ctrl.Deselect, 23)



        self.assertEquals(self.ctrl.GetSelectedCount(), 3)





    def testSelectText(self):

        "Test ListView Selecting some items"

        self.ctrl.Select("Venus")

        self.ctrl.Select("Jupiter")

        self.ctrl.Select("Uranus")



        self.assertRaises(ValueError, self.ctrl.Deselect, "Item not in list")



        self.assertEquals(self.ctrl.GetSelectedCount(), 3)





    def testDeselect(self):

        "Test ListView Selecting some items"

        self.ctrl.Select(1)

        self.ctrl.Select(4)



        self.ctrl.Deselect(3)

        self.ctrl.Deselect(4)



        self.assertRaises(IndexError, self.ctrl.Deselect, 23)



        self.assertEquals(self.ctrl.GetSelectedCount(), 1)





    def testGetProperties(self):

        "Test getting the properties for the listview control"

        props  = self.ctrl.GetProperties()



        self.assertEquals(

            "ListView", props['FriendlyClassName'])



        self.assertEquals(

            self.ctrl.Texts(), props['Texts'])



        for prop_name in props:

            self.assertEquals(getattr(self.ctrl, prop_name)(), props[prop_name])



        self.assertEquals(props['ColumnCount'], 4)

        self.assertEquals(props['ItemCount'], 9)





    def testGetColumnTexts(self):

        self.dlg.MenuSelect("Styles")

        self.app.ControlStyles.StylesListBox.TypeKeys(

            "{HOME}" + "{DOWN}"* 12 + "{SPACE}")



        self.app.ControlStyles.ApplyStylesSetWindowLong.Click()

        self.app.ControlStyles.SendMessage(win32defines.WM_CLOSE)



        self.assertEquals(self.ctrl.GetColumn(0)['text'], "Planet")

        self.assertEquals(self.ctrl.GetColumn(1)['text'], "Distance (km)")

        self.assertEquals(self.ctrl.GetColumn(2)['text'], "Diameter (km)")

        self.assertEquals(self.ctrl.GetColumn(3)['text'], "Mass (kg)")





    def testSubItems(self):

        for row in range(self.ctrl.ItemCount()):

            for i in self.ctrl.Items():

                #self.assertEquals(item.Text, texts[i])



class TreeViewTestCases(unittest.TestCase):

    "Unit tests for the TreeViewWrapper class"



    def setUp(self):

        """Start the application set some data and ensure the application

        is in the state we want it."""



        # start the application

        from pywinauto.application import Application

        app = Application()

        app.start_(os.path.join(controlspy_folder, "Tree View.exe"))



        self.root_text = "The Planets"

        self.texts = [

            ("Mercury", '57,910,000', '4,880', '3.30e23'),

            ("Venus",   '108,200,000', '12,103.6', '4.869e24'),

            ("Earth",   '149,600,000', '12,756.3', '5.9736e24'),

            ("Mars",    '227,940,000', '6,794', '6.4219e23'),

            ("Jupiter", '778,330,000', '142,984', '1.900e27'),

            ("Saturn",  '1,429,400,000', '120,536', '5.68e26'),

            ("Uranus",  '2,870,990,000', '51,118', '8.683e25'),

            ("Neptune", '4,504,000,000', '49,532', '1.0247e26'),

            ("Pluto",   '5,913,520,000', '2,274', '1.27e22'),

         ]



        self.app = app

        self.dlg = app.MicrosoftControlSpy #top_window_()

        self.ctrl = app.MicrosoftControlSpy.TreeView.WrapperObject()



        #self.dlg.MenuSelect("Styles")



        # select show selection always, and show checkboxes

        #app.ControlStyles.ListBox1.TypeKeys(

        #    "{HOME}{SPACE}" + "{DOWN}"* 12 + "{SPACE}")

        #self.app.ControlStyles.ApplyStylesSetWindowLong.Click()

        #self.app.ControlStyles.SendMessage(win32defines.WM_CLOSE)



    def tearDown(self):

        "Close the application after tests"

        # close the application

        self.dlg.SendMessage(win32defines.WM_CLOSE)



    def testFriendlyClass(self):

        "Make sure the friendly class is set correctly"

        self.assertEquals (self.ctrl.FriendlyClassName(), "TreeView")



    def testItemCount(self):

        "Test the TreeView ItemCount method"

        self.assertEquals (self.ctrl.ItemCount(), 37)





    def testGetItem(self):

        "Test the ItemCount method"



        self.assertRaises(RuntimeError, self.ctrl.GetItem, "test\here\please")



        self.assertRaises(IndexError, self.ctrl.GetItem, r"\test\here\please")



        self.assertEquals(

            self.ctrl.GetItem((0, 1, 2)).Text(), self.texts[1][3] + " kg")



        self.assertEquals(

            self.ctrl.GetItem(r"\The Planets\Venus\4.869").Text(), self.texts[1][3] + " kg")



        self.assertEquals(

            self.ctrl.GetItem(

                ["The Planets", "Venus", "4.869"]).Text(),

            self.texts[1][3] + " kg")





    def testItemText(self):

        "Test the ItemCount method"



        self.assertEquals(self.ctrl.Root().Text(), self.root_text)



        self.assertEquals(

            self.ctrl.GetItem((0, 1, 2)).Text(), self.texts[1][3] + " kg")



    def testSelect(self):

        "Test selecting an item"

        self.ctrl.Select((0, 1, 2))



        self.ctrl.GetItem((0, 1, 2)).State()



        self.assertEquals(True, self.ctrl.IsSelected((0, 1, 2)))



    def testEnsureVisible(self):

        "make sure that the item is visible"



        # note this is partially a fake test at the moment because

        # just by getting an item - we usually make it visible

        self.ctrl.EnsureVisible((0, 8, 2))



        # make sure that the item is not hidden

        self.assertNotEqual(None, self.ctrl.GetItem((0, 8, 2)).Rectangle())





    def testGetProperties(self):

        "Test getting the properties for the treeview control"

        props  = self.ctrl.GetProperties()



        self.assertEquals(

            "TreeView", props['FriendlyClassName'])



        self.assertEquals(

            self.ctrl.Texts(), props['Texts'])



        for prop_name in props:

            self.assertEquals(getattr(self.ctrl, prop_name)(), props[prop_name])





class HeaderTestCases(unittest.TestCase):

    "Unit tests for the Header class"



    def setUp(self):

        """Start the application set some data and ensure the application

        is in the state we want it."""



        # start the application

        from pywinauto.application import Application

        app = Application()

        app.start_(os.path.join(controlspy_folder, "Header.exe"))



        self.texts = [u'Distance', u'Diameter', u'Mass']

        self.item_rects = [

            RECT(0, 0, 90, 21),

            RECT(90, 0, 180, 21),

            RECT(180, 0, 260, 21)]

        self.app = app

        self.dlg = app.MicrosoftControlSpy

        self.ctrl = app.MicrosoftControlSpy.Header.WrapperObject()





    def tearDown(self):

        "Close the application after tests"

        # close the application

        self.dlg.SendMessage(win32defines.WM_CLOSE)



    def testFriendlyClass(self):

        "Make sure the friendly class is set correctly"

        self.assertEquals (self.ctrl.FriendlyClassName(), "Header")



    def testTexts(self):

        "Make sure the texts are set correctly"

        self.assertEquals (self.ctrl.Texts()[1:], self.texts)



    def testGetProperties(self):

        "Test getting the properties for the header control"

        props  = self.ctrl.GetProperties()



        self.assertEquals(

            self.ctrl.FriendlyClassName(), props['FriendlyClassName'])



        self.assertEquals(

            self.ctrl.Texts(), props['Texts'])



        for prop_name in props:

            self.assertEquals(getattr(self.ctrl, prop_name)(), props[prop_name])



    def testItemCount(self):

        self.assertEquals(3, self.ctrl.ItemCount())



    def testGetColumnRectangle(self):

        for i in range(0, 3):

            self.assertEquals(

                self.item_rects[i],

                self.ctrl.GetColumnRectangle(i))



    def testClientRects(self):

        test_rects = self.item_rects

        test_rects.insert(0, self.ctrl.ClientRect())



        self.assertEquals(

            test_rects,

            self.ctrl.ClientRects())



    def testGetColumnText(self):

        for i in range(0, 3):

            self.assertEquals(

                self.texts[i],

                self.ctrl.GetColumnText(i))



class StatusBarTestCases(unittest.TestCase):

    "Unit tests for the TreeViewWrapper class"



    def setUp(self):

        """Start the application set some data and ensure the application

        is in the state we want it."""



        # start the application

        from pywinauto.application import Application

        app = Application()

        app.start_(os.path.join(controlspy_folder, "Status bar.exe"))



        self.texts = ["Long text", "", "Status Bar"]

        self.part_rects = [

            RECT(0, 2, 65, 20),

            RECT(67, 2, 90, 20),

            RECT(92, 2, 264, 20)]

        self.app = app

        self.dlg = app.MicrosoftControlSpy

        self.ctrl = app.MicrosoftControlSpy.StatusBar.WrapperObject()



        #self.dlg.MenuSelect("Styles")



        # select show selection always, and show checkboxes

        #app.ControlStyles.ListBox1.TypeKeys(

        #    "{HOME}{SPACE}" + "{DOWN}"* 12 + "{SPACE}")

        #self.app.ControlStyles.ApplyStylesSetWindowLong.Click()

        #self.app.ControlStyles.SendMessage(win32defines.WM_CLOSE)



    def tearDown(self):

        "Close the application after tests"

        # close the application

        self.dlg.SendMessage(win32defines.WM_CLOSE)



    def testFriendlyClass(self):

        "Make sure the friendly class is set correctly"

        self.assertEquals (self.ctrl.FriendlyClassName(), "StatusBar")



    def testTexts(self):

        "Make sure the texts are set correctly"

        self.assertEquals (self.ctrl.Texts()[1:], self.texts)



    def testGetProperties(self):

        "Test getting the properties for the status bar control"

        props  = self.ctrl.GetProperties()



        self.assertEquals(

            self.ctrl.FriendlyClassName(), props['FriendlyClassName'])



        self.assertEquals(

            self.ctrl.Texts(), props['Texts'])



        for prop_name in props:

            self.assertEquals(getattr(self.ctrl, prop_name)(), props[prop_name])





    def testBorderWidths(self):

        "Make sure the border widths are retrieved correctly"

        self.assertEquals (

            self.ctrl.BorderWidths(),

            dict(

                Horizontal = 0,

                Vertical = 2,

                Inter = 2,

                )

            )



    def testPartCount(self):

        "Make sure the number of parts is retrieved correctly"

        self.assertEquals (self.ctrl.PartCount(), 3)



    def testPartRightEdges(self):

        "Make sure the part widths are retrieved correctly"



        for i in range(0, self.ctrl.PartCount()-1):

            self.assertEquals (self.ctrl.PartRightEdges()[i], self.part_rects[i].right)



        self.assertEquals(self.ctrl.PartRightEdges()[i+1], -1)



    def testGetPartRect(self):

        "Make sure the part rectangles are retrieved correctly"



        for i in range(0, self.ctrl.PartCount()):

            self.assertEquals (self.ctrl.GetPartRect(i), self.part_rects[i])



        self.assertRaises(IndexError, self.ctrl.GetPartRect, 99)



    def testClientRects(self):

        self.assertEquals(self.ctrl.ClientRect(), self.ctrl.ClientRects()[0])

        self.assertEquals(self.part_rects, self.ctrl.ClientRects()[1:])



    def testGetPartText(self):

        self.assertRaises(IndexError, self.ctrl.GetPartText, 99)



        for i, text in enumerate(self.texts):

            self.assertEquals(text, self.ctrl.GetPartText(i))



class TabControlTestCases(unittest.TestCase):

    "Unit tests for the TreeViewWrapper class"



    def setUp(self):

        """Start the application set some data and ensure the application

        is in the state we want it."""



        # start the application

        from pywinauto.application import Application

        app = Application()

        app.start_(os.path.join(controlspy_folder, "Tab.exe"))



        self.texts = [

            "Pluto", "Neptune", "Uranus",

            "Saturn", "Jupiter", "Mars",

            "Earth", "Venus", "Mercury", "Sun"]



        self.rects = [

            RECT(2,2,80,21),

            RECT(80,2,174,21),

            RECT(174,2,261,21),

            RECT(2,21,91,40),

            RECT(91,21,180,40),

            RECT(180,21,261,40),

            RECT(2,40,64,59),

            RECT(64,40,131,59),

            RECT(131,40,206,59),

            RECT(206,40,261,59),

        ]



        self.app = app

        self.dlg = app.MicrosoftControlSpy

        self.ctrl = app.MicrosoftControlSpy.TabControl.WrapperObject()



        #self.dlg.MenuSelect("Styles")



        # select show selection always, and show checkboxes

        #app.ControlStyles.ListBox1.TypeKeys(

        #    "{HOME}{SPACE}" + "{DOWN}"* 12 + "{SPACE}")

        #self.app.ControlStyles.ApplyStylesSetWindowLong.Click()

        #self.app.ControlStyles.SendMessage(win32defines.WM_CLOSE)



    def tearDown(self):

        "Close the application after tests"

        # close the application

        self.dlg.SendMessage(win32defines.WM_CLOSE)



    def testFriendlyClass(self):

        "Make sure the friendly class is set correctly"

        self.assertEquals (self.ctrl.FriendlyClassName(), "TabControl")



    def testTexts(self):

        "Make sure the texts are set correctly"

        self.assertEquals (self.ctrl.Texts()[1:], self.texts)



    def testGetProperties(self):

        "Test getting the properties for the tabcontrol"

        props  = self.ctrl.GetProperties()



        self.assertEquals(

            self.ctrl.FriendlyClassName(), props['FriendlyClassName'])



        self.assertEquals(

            self.ctrl.Texts(), props['Texts'])



        for prop_name in props:

            self.assertEquals(getattr(self.ctrl, prop_name)(), props[prop_name])



    def testRowCount(self):

        self.assertEquals(3, self.ctrl.RowCount())



    def testGetSelectedTab(self):

        self.assertEquals(6, self.ctrl.GetSelectedTab())

        self.ctrl.Select(0)

        self.assertEquals(0, self.ctrl.GetSelectedTab())

        self.ctrl.Select("Jupiter")

        self.assertEquals(4, self.ctrl.GetSelectedTab())



    def testTabCount(self):

        "Make sure the number of parts is retrieved correctly"

        self.assertEquals (self.ctrl.TabCount(), 10)



    def testGetTabRect(self):

        "Make sure the part rectangles are retrieved correctly"



        for i, rect in enumerate(self.rects):

            self.assertEquals (self.ctrl.GetTabRect(i), self.rects[i])



        self.assertRaises(IndexError, self.ctrl.GetTabRect, 99)



    def testGetTabState(self):

        self.assertRaises(IndexError, self.ctrl.GetTabState, 99)

        self.dlg.StatementEdit.SetEditText ("MSG (TCM_HIGHLIGHTITEM,1,MAKELONG(TRUE,0))")

        time.sleep(.3)

        # use CloseClick to allow the control time to respond to the message

        self.dlg.Send.CloseClick()

        time.sleep(2)

        self.assertEquals (self.ctrl.GetTabState(1), 1)



    def testTabStates(self):

        self.assertEquals(self.ctrl.TabStates(), [0]*10)

        self.dlg.StatementEdit.SetEditText ("MSG (TCM_HIGHLIGHTITEM,1,MAKELONG(TRUE,0))")

        time.sleep(.3)

        # use CloseClick to allow the control time to respond to the message

        self.dlg.Send.CloseClick()

        time.sleep(2)

        self.assertEquals (self.ctrl.GetTabState(1), 1)

        self.assertEquals (self.ctrl.TabStates()[1], 1)

        self.assertEquals (self.ctrl.TabStates()[0], 0)

        self.assertEquals (self.ctrl.TabStates()[2], 0)

        self.assertEquals (self.ctrl.TabStates()[3], 0)

        self.assertEquals (self.ctrl.TabStates()[4], 0)

        self.assertEquals (self.ctrl.TabStates()[5], 0)

        self.assertEquals (self.ctrl.TabStates()[6], 0)

        self.assertEquals (self.ctrl.TabStates()[7], 0)

        self.assertEquals (self.ctrl.TabStates()[8], 0)

        self.assertEquals (self.ctrl.TabStates()[9], 0)

        self.assertEquals (self.ctrl.TabStates()[10], 0)

        self.assertEquals (self.ctrl.TabStates()[11], 0)

        self.assertEquals (self.ctrl.TabStates()[12], 0)

        self.assertEquals (self.ctrl.TabStates()[13], 0)

        self.assertEquals (self.ctrl.TabStates()[14], 0)

        self.assertEquals (self.ctrl.TabStates()[15], 0)

        self.assertEquals (self.ctrl.TabStates()[16], 0)

        self.assertEquals (self.ctrl.TabStates()[17], 0)

        self.assertEquals (self.ctrl.TabStates()[18], 0)

        self.assertEquals (self.ctrl.TabStates()[19], 0)

        self.assertEquals (self.ctrl.TabStates()[20], 0)

        self.assertEquals (self.ctrl.TabStates()[21], 0)

        self.assertEquals (self.ctrl.TabStates()[22], 0)

        self.assertEquals (self.ctrl.TabStates()[23], 0)

        self.assertEquals (self.ctrl.TabStates()[24], 0)

        self.assertEquals (self.ctrl.TabStates()[25], 0)

        self.assertEquals (self.ctrl.TabStates()[26], 0)

        self.assertEquals (self.ctrl.TabStates()[27], 0)

        self.assertEquals (self.ctrl.TabStates()[28], 0)

        self.assertEquals (self.ctrl.TabStates()[29], 0)

        self.assertEquals (self.ctrl.TabStates()[30], 0)

        self.assertEquals (self.ctrl.TabStates()[31], 0)

        self.assertEquals (self.ctrl.TabStates()[32], 0)

        self.assertEquals (self.ctrl.TabStates()[33], 0)

        self.assertEquals (self.ctrl.TabStates()[34], 0)

        self.assertEquals (self.ctrl.TabStates()[35], 0)

        self.assertEquals (self.ctrl.TabStates()[36], 0)

        self.assertEquals (self.ctrl.TabStates()[37], 0)

        self.assertEquals (self.ctrl.TabStates()[38], 0)

        self.assertEquals (self.ctrl.TabStates()[39], 0)

        self.assertEquals (self.ctrl.TabStates()[40], 0)

        self.assertEquals (self.ctrl.TabStates()[41], 0)

        self.assertEquals (self.ctrl.TabStates()[42], 0)

        self.assertEquals (self.ctrl.TabStates()[43], 0)

        self.assertEquals (self.ctrl.TabStates()[44], 0)

        self.assertEquals (self.ctrl.TabStates()[45], 0)

        self.assertEquals (self.ctrl.TabStates()[46], 0)

        self.assertEquals (self.ctrl.TabStates()[47], 0)

        self.assertEquals (self.ctrl.TabStates()[48], 0)

        self.assertEquals (self.ctrl.TabStates()[49], 0)

        self.assertEquals (self.ctrl.TabStates()[50], 0)

        self.assertEquals (self.ctrl.TabStates()[51], 0)

        self.assertEquals (self.ctrl.TabStates()[52], 0)

        self.assertEquals (self.ctrl.TabStates()[53], 0)

        self.assertEquals (self.ctrl.TabStates()[54], 0)

        self.assertEquals (self.ctrl.TabStates()[55], 0)

        self.assertEquals (self.ctrl.TabStates()[56], 0)

        self.assertEquals (self.ctrl.TabStates()[57], 0)

        self.assertEquals (self.ctrl.TabStates()[58], 0)

        self.assertEquals (self.ctrl.TabStates()[59], 0)

        self.assertEquals (self.ctrl.TabStates()[60], 0)

        self.assertEquals (self.ctrl.TabStates()[61], 0)

        self.assertEquals (self.ctrl.TabStates()[62], 0)

        self.assertEquals (self.ctrl.TabStates()[63], 0)

        self.assertEquals (self.ctrl.TabStates()[64], 0)

        self.assertEquals (self.ctrl.TabStates()[65], 0)

        self.assertEquals (self.ctrl.TabStates()[66], 0)

        self.assertEquals (self.ctrl.TabStates()[67], 0)

        self.assertEquals (self.ctrl.TabStates()[68], 0)

        self.assertEquals (self.ctrl.TabStates()[69], 0)

        self.assertEquals (self.ctrl.TabStates()[70], 0)

        self.assertEquals (self.ctrl.TabStates()[71], 0)

        self.assertEquals (self.ctrl.TabStates()[72], 0)

        self.assertEquals (self.ctrl.TabStates()[73], 0)

        self.assertEquals (self.ctrl.TabStates()[74], 0)

        self.assertEquals (self.ctrl.TabStates()[75], 0)

        self.assertEquals (self.ctrl.TabStates()[76], 0)

        self.assertEquals (self.ctrl.TabStates()[77], 0)

        self.assertEquals (self.ctrl.TabStates()[78], 0)

        self.assertEquals (self.ctrl.TabStates()[79], 0)

        self.assertEquals (self.ctrl.TabStates()[80], 0)

        self.assertEquals (self.ctrl.TabStates()[81], 0)

        self.assertEquals (self.ctrl.TabStates()[82], 0)

        self.assertEquals (self.ctrl.TabStates()[83], 0)

        self.assertEquals (self.ctrl.TabStates()[84], 0)

        self.assertEquals (self.ctrl.TabStates()[85], 0)

        self.assertEquals (self.ctrl.TabStates()[86], 0)

        self.assertEquals (self.ctrl.TabStates()[87], 0)

        self.assertEquals (self.ctrl.TabStates()[88], 0)

        self.assertEquals (self.ctrl.TabStates()[89], 0)

        self.assertEquals (self.ctrl.TabStates()[90], 0)

        self.assertEquals (self.ctrl.TabStates()[91], 0)

        self.assertEquals (self.ctrl.TabStates()[92], 0)

        self.assertEquals (self.ctrl.TabStates()[93], 0)

        self.assertEquals (self.ctrl.TabStates()[94], 0)

        self.assertEquals (self.ctrl.TabStates()[95], 0)

        self.assertEquals (self.ctrl.TabStates()[96], 0)

        self.assertEquals (self.ctrl.TabStates()[97], 0)

        self.assertEquals (self.ctrl.TabStates()[98], 0)

        self.assertEquals (self.ctrl.TabStates()[99], 0)

        self.assertEquals (self.ctrl.TabStates()[100], 0)

        self.assertEquals (self.ctrl.TabStates()[101], 0)

        self.assertEquals (self.ctrl.TabStates()[102], 0)

        self.assertEquals (self.ctrl.TabStates()[103], 0)

        self.assertEquals (self.ctrl.TabStates()[104], 0)

        self.assertEquals (self.ctrl.TabStates()[105], 0)

        self.assertEquals (self.ctrl.TabStates()[106], 0)

        self.assertEquals (self.ctrl.TabStates()[107], 0)

        self.assertEquals (self.ctrl.TabStates()[108], 0)

        self.assertEquals (self.ctrl.TabStates()[109], 0)

        self.assertEquals (self.ctrl.TabStates()[110], 0)

        self.assertEquals (self.ctrl.TabStates()[111], 0)

        self.assertEquals (self.ctrl.TabStates()[112], 0)

        self.assertEquals (self.ctrl.TabStates()[113], 0)

        self.assertEquals (self.ctrl.TabStates()[114], 0)

        self.assertEquals (self.ctrl.TabStates()[115], 0)

        self.assertEquals (self.ctrl.TabStates()[116], 0)

        self.assertEquals (self.ctrl.TabStates()[117], 0)

        self.assertEquals (self.ctrl.TabStates()[118], 0)

        self.assertEquals (self.ctrl.TabStates()[119], 0)

        self.assertEquals (self.ctrl.TabStates()[120], 0)

        self.assertEquals (self.ctrl.TabStates()[121], 0)

        self.assertEquals (self.ctrl.TabStates()[122], 0)

        self.assertEquals (self.ctrl.TabStates()[123], 0)

        self.assertEquals (self.ctrl.TabStates()[124], 0)

        self.assertEquals (self.ctrl.TabStates()[125], 0)

        self.assertEquals (self.ctrl.TabStates()[126], 0)

        self.assertEquals (self.ctrl.TabStates()[127], 0)

        self.assertEquals (self.ctrl.TabStates()[128], 0)

        self.assertEquals (self.ctrl.TabStates()[129], 0)

        self.assertEquals (self.ctrl.TabStates()[130], 0)

        self.assertEquals (self.ctrl.TabStates()[131], 0)

        self.assertEquals (self.ctrl.TabStates()[132], 0)

        self.assertEquals (self.ctrl.TabStates()[133], 0)

        self.assertEquals (self.ctrl.TabStates()[134], 0)

        self.assertEquals (self.ctrl.TabStates()[135], 0)

        self.assertEquals (self.ctrl.TabStates()[136], 0)

        self.assertEquals (self.ctrl.TabStates()[137], 0)

        self.assertEquals (self.ctrl.TabStates()[138], 0)

        self.assertEquals (self.ctrl.TabStates()[139], 0)

        self.assertEquals (self.ctrl.TabStates()[140], 0)

        self.assertEquals (self.ctrl.TabStates()[141], 0)

        self.assertEquals (self.ctrl.TabStates()[142], 0)

        self.assertEquals (self.ctrl.TabStates()[143], 0)

        self.assertEquals (self.ctrl.TabStates()[144], 0)

        self.assertEquals (self.ctrl.TabStates()[145], 0)

        self.assertEquals (self.ctrl.TabStates()[146], 0)

        self.assertEquals (self.ctrl.TabStates()[147], 0)

        self.assertEquals (self.ctrl.TabStates()[148], 0)

        self.assertEquals (self.ctrl.TabStates()[149], 0)

        self.assertEquals (self.ctrl.TabStates()[150], 0)

        self.assertEquals (self.ctrl.TabStates()[151], 0)

        self.assertEquals (self.ctrl.TabStates()[152], 0)

        self.assertEquals (self.ctrl.TabStates()[153], 0)

        self.assertEquals (self.ctrl.TabStates()[154], 0)

        self.assertEquals (self.ctrl.TabStates()[155], 0)

        self.assertEquals (self.ctrl.TabStates()[156], 0)

        self.assertEquals (self.ctrl.TabStates()[157], 0)

        self.assertEquals (self.ctrl.TabStates()[158], 0)

        self.assertEquals (self.ctrl.TabStates()[159], 0)

        self.assertEquals (self.ctrl.TabStates()[160], 0)

        self.assertEquals (self.ctrl.TabStates()[161], 0)

        self.assertEquals (self.ctrl.TabStates()[162], 0)

        self.assertEquals (self.ctrl.TabStates()[163], 0)

        self.assertEquals (self.ctrl.TabStates()[164], 0)

        self.assertEquals (self.ctrl.TabStates()[165], 0)

        self.assertEquals (self.ctrl.TabStates()[166], 0)

        self.assertEquals (self.ctrl.TabStates()[167], 0)

        self.assertEquals (self.ctrl.TabStates()[168], 0)

        self.assertEquals (self.ctrl.TabStates()[169], 0)

        self.assertEquals (self.ctrl.TabStates()[170], 0)

        self.assertEquals (self.ctrl.TabStates()[171], 0)

        self.assertEquals (self.ctrl.TabStates()[172], 0)

        self.assertEquals (self.ctrl.TabStates()[173], 0)

        self.assertEquals (self.ctrl.TabStates()[174], 0)

        self.assertEquals (self.ctrl.TabStates()[175], 0)

        self.assertEquals (self.ctrl.TabStates()[176], 0)

        self.assertEquals (self.ctrl.TabStates()[177], 0)

        self.assertEquals (self.ctrl.TabStates()[178], 0)

        self.assertEquals (self.ctrl.TabStates()[179], 0)

        self.assertEquals (self.ctrl.TabStates()[180], 0)

        self.assertEquals (self.ctrl.TabStates()[181], 0)

        self.assertEquals (self.ctrl.TabStates()[182], 0)

        self.assertEquals (self.ctrl.TabStates()[183], 0)

        self.assertEquals (self.ctrl.TabStates()[184], 0)

        self.assertEquals (self.ctrl.TabStates()[185], 0)

        self.assertEquals (self.ctrl.TabStates()[186], 0)

        self.assertEquals (self.ctrl.TabStates()[187], 0)

        self.assertEquals (self.ctrl.TabStates()[188], 0)

        self.assertEquals (self.ctrl.TabStates()[189], 0)

        self.assertEquals (self.ctrl.TabStates()[190], 0)

        self.assertEquals (self.ctrl.TabStates()[191], 0)

        self.assertEquals (self.ctrl.TabStates()[192], 0)

        self.assertEquals (self.ctrl.TabStates()[193], 0)

        self.assertEquals (self.ctrl.TabStates()[194], 0)

        self.assertEquals (self.ctrl.TabStates()[195], 0)

        self.assertEquals (self.ctrl.TabStates()[196], 0)

        self.assertEquals (self.ctrl.TabStates()[197], 0)

        self.assertEquals (self.ctrl.TabStates()[198], 0)

        self.assertEquals (self.ctrl.TabStates()[199], 0)

        self.assertEquals (self.ctrl.TabStates()[200], 0)

        self.assertEquals (self.ctrl.TabStates()[201], 0)

        self.assertEquals (self.ctrl.TabStates()[202], 0)

        self.assertEquals (self.ctrl.TabStates()[203], 0)

        self.assertEquals (self.ctrl.TabStates()[204], 0)

        self.assertEquals (self.ctrl.TabStates()[205], 0)

        self.assertEquals (self.ctrl.TabStates()[206], 0)

        self.assertEquals (self.ctrl.TabStates()[207], 0)

        self.assertEquals (self.ctrl.TabStates()[208], 0)

        self.assertEquals (self.ctrl.TabStates()[209], 0)

        self.assertEquals (self.ctrl.TabStates()[210], 0)

        self.assertEquals (self.ctrl.TabStates()[211], 0)

        self.assertEquals (self.ctrl.TabStates()[212], 0)

        self.assertEquals (self.ctrl.TabStates()[213], 0)

        self.assertEquals (self.ctrl.TabStates()[214], 0)

        self.assertEquals (self.ctrl.TabStates()[215], 0)

        self.assertEquals (self.ctrl.TabStates()[216], 0)

        self.assertEquals (self.ctrl.TabStates()[217], 0)

        self.assertEquals (self.ctrl.TabStates()[218], 0)

        self.assertEquals (self.ctrl.TabStates()[219], 0)

        self.assertEquals (self.ctrl.TabStates()[220], 0)

        self.assertEquals (self.ctrl.TabStates()[221], 0)

        self.assertEquals (self.ctrl.TabStates()[222], 0)

        self.assertEquals (self.ctrl.TabStates()[223], 0)

        self.assertEquals (self.ctrl.TabStates()[224], 0)

        self.assertEquals (self.ctrl.TabStates()[225], 0)

        self.assertEquals (self.ctrl.TabStates()[226], 0)

        self.assertEquals (self.ctrl.TabStates()[227], 0)

        self.assertEquals (self.ctrl.TabStates()[228], 0)

        self.assertEquals (self.ctrl.TabStates()[229], 0)

        self.assertEquals (self.ctrl.TabStates()[230], 0)

        self.assertEquals (self.ctrl.TabStates()[231], 0)

        self.assertEquals (self.ctrl.TabStates()[232], 0)

        self.assertEquals (self.ctrl.TabStates()[233], 0)

        self.assertEquals (self.ctrl.TabStates()[234], 0)

        self.assertEquals (self.ctrl.TabStates()[235], 0)

        self.assertEquals (self.ctrl.TabStates()[236], 0)

        self.assertEquals (self.ctrl.TabStates()[237], 0)

        self.assertEquals (self.ctrl.TabStates()[238], 0)

        self.assertEquals (self.ctrl.TabStates()[239], 0)

        self.assertEquals (self.ctrl.TabStates()[240], 0)

        self.assertEquals (self.ctrl.TabStates()[241], 0)

        self.assertEquals (self.ctrl.TabStates()[242], 0)

        self.assertEquals (self.ctrl.TabStates()[243], 0)

        self.assertEquals (self.ctrl.TabStates()[244], 0)

        self.assertEquals (self.ctrl.TabStates()[245], 0)

        self.assertEquals (self.ctrl.TabStates()[246], 0)

        self.assertEquals (self.ctrl.TabStates()[247], 0)

        self.assertEquals (self.ctrl.TabStates()[248], 0)

        self.assertEquals (self.ctrl.TabStates()[249], 0)

        self.assertEquals (self.ctrl.TabStates()[250], 0)

        self.assertEquals (self.ctrl.TabStates()[251], 0)

        self.assertEquals (self.ctrl.TabStates()[252], 0)

        self.assertEquals (self.ctrl.TabStates()[253], 0)

        self.assertEquals (self.ctrl.TabStates()[254], 0)

        self.assertEquals (self.ctrl.TabStates()[255], 0)

        self.assertEquals (self.ctrl.TabStates()[256], 0)

        self.assertEquals (self.ctrl.TabStates()[257], 0)

        self.assertEquals (self.ctrl.TabStates()[258], 0)

        self.assertEquals (self.ctrl.TabStates()[259], 0)

        self.assertEquals (self.ctrl.TabStates()[260], 0)

        self.assertEquals (self.ctrl.TabStates()[261], 0)

        self.assertEquals (self.ctrl.TabStates()[262], 0)

        self.assertEquals (self.ctrl.TabStates()[263], 0)

        self.assertEquals (self.ctrl.TabStates()[264], 0)

        self.assertEquals (self.ctrl.TabStates()[265], 0)

        self.assertEquals (self.ctrl.TabStates()[266], 0)

        self.assertEquals (self.ctrl.TabStates()[267], 0)

        self.assertEquals (self.ctrl.TabStates()[268], 0)

        self.assertEquals (self.ctrl.TabStates()[269], 0)

        self.assertEquals (self.ctrl.TabStates()[270], 0)

        self.assertEquals (self.ctrl.TabStates()[271], 0)

        self.assertEquals (self.ctrl.TabStates()[272], 0)

        self.assertEquals (self.ctrl.TabStates()[273], 0)

        self.assertEquals (self.ctrl.TabStates()[274], 0)

        self.assertEquals (self.ctrl.TabStates()[275], 0)

        self.assertEquals (self.ctrl.TabStates()[276], 0)

        self.assertEquals (self.ctrl.TabStates()[277], 0)

        self.assertEquals (self.ctrl.TabStates()[278], 0)

        self.assertEquals (self.ctrl.TabStates()[279], 0)

        self.assertEquals (self.ctrl.TabStates()[280], 0)

        self.assertEquals (self.ctrl.TabStates()[281], 0)

        self.assertEquals (self.ctrl.TabStates()[282], 0)

        self.assertEquals (self.ctrl.TabStates()[283], 0)

        self.assertEquals (self.ctrl.TabStates()[284], 0)

        self.assertEquals (self.ctrl.TabStates()[285], 0)

        self.assertEquals (self.ctrl.TabStates()[286], 0)

        self.assertEquals (self.ctrl.TabStates()[287], 0)

        self.assertEquals (self.ctrl.TabStates()[288], 0)

        self.assertEquals (self.ctrl.TabStates()[289], 0)

        self.assertEquals (self.ctrl.TabStates()[290], 0)

        self.assertEquals (self.ctrl.TabStates()[291], 0)

        self.assertEquals (self.ctrl.TabStates()[292], 0)

        self.assertEquals (self.ctrl.TabStates()[293], 0)

        self.assertEquals (self.ctrl.TabStates()[294], 0)

        self.assertEquals (self.ctrl.TabStates()[295], 0)

        self.assertEquals (self.ctrl.TabStates()[296], 0)

        self.assertEquals (self.ctrl.TabStates()[297], 0)

        self.assertEquals (self.ctrl.TabStates()[298], 0)

        self.assertEquals (self.ctrl.TabStates()[299], 0)

        self.assertEquals (self.ctrl.TabStates()[300], 0)

        self.assertEquals (self.ctrl.TabStates()[301], 0)

        self.assertEquals (self.ctrl.TabStates()[302], 0)

        self.assertEquals (self.ctrl.TabStates()[303], 0)

        self.assertEquals (self.ctrl.TabStates()[304], 0)

        self.assertEquals (self.ctrl.TabStates()[305], 0)

        self.assertEquals (self.ctrl.TabStates()[306], 0)

        self.assertEquals (self.ctrl.TabStates()[307], 0)

        self.assertEquals (self.ctrl.TabStates()[308], 0)

        self.assertEquals (self.ctrl.TabStates()[309], 0)

        self.assertEquals (self.ctrl.TabStates()[310], 0)

        self.assertEquals (self.ctrl.TabStates()[311], 0)

        self.assertEquals (self.ctrl.TabStates()[312], 0)

        self.assertEquals (self.ctrl.TabStates()[313], 0)

        self.assertEquals (self.ctrl.TabStates()[314], 0)

        self.assertEquals (self.ctrl.TabStates()[315], 0)

        self.assertEquals (self.ctrl.TabStates()[316], 0)

        self.assertEquals (self.ctrl.TabStates()[317], 0)

        self.assertEquals (self.ctrl.TabStates()[318], 0)

        self.assertEquals (self.ctrl.TabStates()[319], 0)

        self.assertEquals (self.ctrl.TabStates()[320], 0)

        self.assertEquals (self.ctrl.TabStates()[321], 0)

        self.assertEquals (self.ctrl.TabStates()[322], 0)

        self.assertEquals (self.ctrl.TabStates()[323], 0)

        self.assertEquals (self.ctrl.TabStates()[324], 0)

        self.assertEquals (self.ctrl.TabStates()[325], 0)

        self.assertEquals (self.ctrl.TabStates()[326], 0)

        self.assertEquals (self.ctrl.TabStates()[327], 0)

        self.assertEquals (self.ctrl.TabStates()[328], 0)

        self.assertEquals (self.ctrl.TabStates()[329], 0)

        self.assertEquals (self.ctrl.TabStates()[330], 0)

        self.assertEquals (self.ctrl.TabStates()[331], 0)

        self.assertEquals (self.ctrl.TabStates()[332], 0)

        self.assertEquals (self.ctrl.TabStates()[333], 0)

        self.assertEquals (self.ctrl.TabStates()[334], 0)

        self.assertEquals (self.ctrl.TabStates()[335], 0)

        self.assertEquals (self.ctrl.TabStates()[336], 0)

        self.assertEquals (self.ctrl.TabStates()[337], 0)

        self.assertEquals (self.ctrl.TabStates()[338], 0)

        self.assertEquals (self.ctrl.TabStates()[339], 0)

        self.assertEquals (self.ctrl.TabStates()[340], 0)

        self.assertEquals (self.ctrl.TabStates()[341], 0)

        self.assertEquals (self.ctrl.TabStates()[342], 0)

        self.assertEquals (self.ctrl.TabStates()[343], 0)

        self.assertEquals (self.ctrl.TabStates()[344], 0)

        self.assertEquals (self.ctrl.TabStates()[345], 0)

        self.assertEquals (self.ctrl.TabStates()[346], 0)

        self.assertEquals (self.ctrl.TabStates()[347], 0)

        self.assertEquals (self.ctrl.TabStates()[348], 0)

        self.assertEquals (self.ctrl.TabStates()[349], 0)

        self.assertEquals (self.ctrl.TabStates()[350], 0)

        self.assertEquals (self.ctrl.TabStates()[351], 0)

        self.assertEquals (self.ctrl.TabStates()[352], 0)

        self.assertEquals (self.ctrl.TabStates()[353], 0)

        self.assertEquals (self.ctrl.TabStates()[354], 0)

        self.assertEquals (self.ctrl.TabStates()[355], 0)

        self.assertEquals (self.ctrl.TabStates()[356], 0)

        self.assertEquals (self.ctrl.TabStates()[357], 0)

        self.assertEquals (self.ctrl.TabStates()[358], 0)

        self.assertEquals (self.ctrl.TabStates()[359], 0)

        self.assertEquals (self.ctrl.TabStates()[360], 0)

        self.assertEquals (self.ctrl.TabStates()[361], 0)

        self.assertEquals (self.ctrl.TabStates()[362], 0)

        self.assertEquals (self.ctrl.TabStates()[363], 0)

        self.assertEquals (self.ctrl.TabStates()[364], 0)

        self.assertEquals (self.ctrl.TabStates()[365], 0)

        self.assertEquals (self.ctrl.TabStates()[366], 0)

        self.assertEquals (self.ctrl.TabStates()[367], 0)

        self.assertEquals (self.ctrl.TabStates()[368], 0)

        self.assertEquals (self.ctrl.TabStates()[369], 0)

        self.assertEquals (self.ctrl.TabStates()[370], 0)

        self.assertEquals (self.ctrl.TabStates()[371], 0)

        self.assertEquals (self.ctrl.TabStates()[372], 0)

        self.assertEquals (self.ctrl.TabStates()[373], 0)

        self.assertEquals (self.ctrl.TabStates()[374], 0)

        self.assertEquals (self.ctrl.TabStates()[375], 0)

        self.assertEquals (self.ctrl.TabStates()[376], 0)

        self.assertEquals (self.ctrl.TabStates()[377], 0)

        self.assertEquals (self.ctrl.TabStates()[378], 0)

        self.assertEquals (self.ctrl.TabStates()[379], 0)

        self.assertEquals (self.ctrl.TabStates()[380], 0)

        self.assertEquals (self.ctrl.TabStates()[381], 0)

        self.assertEquals (self.ctrl.TabStates()[382], 0)

        self.assertEquals (self.ctrl.TabStates()[383], 0)

        self.assertEquals (self.ctrl.TabStates()[384], 0)

        self.assertEquals (self.ctrl.TabStates()[385], 0)

        self.assertEquals (self.ctrl.TabStates()[386], 0)

        self.assertEquals (self.ctrl.TabStates()[387], 0)

        self.assertEquals (self.ctrl.TabStates()[388], 0)

        self.assertEquals (self.ctrl.TabStates()[389], 0)

        self.assertEquals (self.ctrl.TabStates()[390], 0)

        self.assertEquals (self.ctrl.TabStates()[391], 0)

        self.assertEquals (self.ctrl.TabStates()[392], 0)

        self.assertEquals (self.ctrl.TabStates()[393], 0)

        self.assertEquals (self.ctrl.TabStates()[394], 0)

        self.assertEquals (self.ctrl.TabStates()[395], 0)

        self.assertEquals (self.ctrl.TabStates()[396], 0)

        self.assertEquals (self.ctrl.TabStates()[397], 0)

        self.assertEquals (self.ctrl.TabStates()[398], 0)

        self.assertEquals (self.ctrl.TabStates()[399], 0)

        self.assertEquals (self.ctrl.TabStates()[400], 0)

        self.assertEquals (self.ctrl.TabStates()[401], 0)

        self.assertEquals (self.ctrl.TabStates()[402], 0)

        self.assertEquals (self.ctrl.TabStates()[403], 0)

        self.assertEquals (self.ctrl.TabStates()[404], 0)

        self.assertEquals (self.ctrl.TabStates()[405], 0)

        self.assertEquals (self.ctrl.TabStates()[406], 0)

        self.assertEquals (self.ctrl.TabStates()[407], 0)

        self.assertEquals (self.ctrl.TabStates()[408], 0)

        self.assertEquals (self.ctrl.TabStates()[409], 0)

        self.assertEquals (self.ctrl.TabStates()[410], 0)

        self.assertEquals (self.ctrl.TabStates()[411], 0)

        self.assertEquals (self.ctrl.TabStates()[412], 0)

        self.assertEquals (self.ctrl.TabStates()[413], 0)

        self.assertEquals (self.ctrl.TabStates()[414], 0)

        self.assertEquals (self.ctrl.TabStates()[415], 0)

        self.assertEquals (self.ctrl.TabStates()[416], 0)

        self.assertEquals (self.ctrl.TabStates()[417], 0)

        self.assertEquals (self.ctrl.TabStates()[418], 0)

        self.assertEquals (self.ctrl.TabStates()[419], 0)

        self.assertEquals (self.ctrl.TabStates()[420], 0)

        self.assertEquals (self.ctrl.TabStates()[421], 0)

        self.assertEquals (self.ctrl.TabStates()[422], 0)

        self.assertEquals (self.ctrl.TabStates()[423], 0)

        self.assertEquals (self.ctrl.TabStates()[424], 0)

        self.assertEquals (self.ctrl.TabStates()[425], 0)

        self.assertEquals (self.ctrl.TabStates()[426], 0)

        self.assertEquals (self.ctrl.TabStates()[427], 0)

        self.assertEquals (self.ctrl.TabStates()[428], 0)

        self.assertEquals (self.ctrl.TabStates()[429], 0)

        self.assertEquals (self.ctrl.TabStates()[430], 0)

        self.assertEquals (self.ctrl.TabStates()[431], 0)

        self.assertEquals (self.ctrl.TabStates()[432], 0)

        self.assertEquals (self.ctrl.TabStates()[433], 0)

        self.assertEquals (self.ctrl.TabStates()[434], 0)

        self.assertEquals (self.ctrl.TabStates()[435], 0)

        self.assertEquals (self.ctrl.TabStates()[436], 0)

        self.assertEquals (self.ctrl.TabStates()[437], 0)

        self.assertEquals (self.ctrl.TabStates()[438], 0)

        self.assertEquals (self.ctrl.TabStates()[439], 0)

        self.assertEquals (self.ctrl.TabStates()[440], 0)

        self.assertEquals (self.ctrl.TabStates()[441], 0)

        self.assertEquals (self.ctrl.TabStates()[442], 0)

        self.assertEquals (self.ctrl.TabStates()[443], 0)

        self.assertEquals (self.ctrl.TabStates()[444], 0)

        self.assertEquals (self.ctrl.TabStates()[445], 0)

        self.assertEquals (self.ctrl.TabStates()[446], 0)

        self.assertEquals (self.ctrl.TabStates()[447], 0)

        self.assertEquals (self.ctrl.TabStates()[448], 0)

        self.assertEquals (self.ctrl.TabStates()[449], 0)

        self.assertEquals (self.ctrl.TabStates()[450], 0)

        self.assertEquals (self.ctrl.TabStates()[451], 0)

        self.assertEquals (self.ctrl.TabStates()[452], 0)

        self.assertEquals (self.ctrl.TabStates()[453], 0)

        self.assertEquals (self.ctrl.TabStates()[454], 0)

        self.assertEquals (self.ctrl.TabStates()[455], 0)

        self.assertEquals (self.ctrl.TabStates()[456], 0)

        self.assertEquals (self.ctrl.TabStates()[457], 0)

        self.assertEquals (self.ctrl.TabStates()[458], 0)

        self.assertEquals (self.ctrl.TabStates()[459], 0)

        self.assertEquals (self.ctrl.TabStates()[460], 0)

        self.assertEquals (self.ctrl.TabStates()[461], 0)

        self.assertEquals (self.ctrl.TabStates()[462], 0)

        self.assertEquals (self.ctrl.TabStates()[463], 0)

        self.assertEquals (self.ctrl.TabStates()[464], 0)

        self.assertEquals (self.ctrl.TabStates()[465], 0)

        self.assertEquals (self.ctrl.TabStates()[466], 0)

        self.assertEquals (self.ctrl.TabStates()[467], 0)

        self.assertEquals (self.ctrl.TabStates()[468], 0)

        self.assertEquals (self.ctrl.TabStates()[469], 0)

        self.assertEquals (self.ctrl.TabStates()[470], 0)

        self.assertEquals (self.ctrl.TabStates()[471], 0)

        self.assertEquals (self.ctrl.TabStates()[472], 0)

        self.assertEquals (self.ctrl.TabStates()[473], 0)

        self.assertEquals (self.ctrl.TabStates()[474], 0)

        self.assertEquals (self.ctrl.TabStates()[475], 0)

        self.assertEquals (self.ctrl.TabStates()[476], 0)

        self.assertEquals (self.ctrl.TabStates()[477], 0)

        self.assertEquals (self.ctrl.TabStates()[478], 0)

        self.assertEquals (self.ctrl.TabStates()[479], 0)

        self.assertEquals (self.ctrl.TabStates()[480], 0)

        self.assertEquals (self.ctrl.TabStates()[481], 0)

        self.assertEquals (self.ctrl.TabStates()[482], 0)

        self.assertEquals (self.ctrl.TabStates()[483], 0)

        self.assertEquals (self.ctrl.TabStates()[484], 0)

        self.assertEquals (self.ctrl.TabStates()[485], 0)

        self.assertEquals (self.ctrl.TabStates()[486], 0)

        self.assertEquals (self.ctrl.TabStates()[487], 0)

        self.assertEquals (self.ctrl.TabStates()[488], 0)

        self.assertEquals (self.ctrl.TabStates()[489], 0)

        self.assertEquals (self.ctrl.TabStates()[490], 0)

        self.assertEquals (self.ctrl.TabStates()[491], 0)

        self.assertEquals (self.ctrl.TabStates()[492], 0)

        self.assertEquals (self.ctrl.TabStates()[493], 0)

        self.assertEquals (self.ctrl.TabStates()[494], 0)

        self.assertEquals (self.ctrl.TabStates()[495], 0)

        self.assertEquals (self.ctrl.TabStates()[496], 0)

        self.assertEquals (self.ctrl.TabStates()[497], 0)

        self.assertEquals (self.ctrl.TabStates()[498], 0)

        self.assertEquals (self.ctrl.TabStates()[499], 0)

        self.assertEquals (self.ctrl.TabStates()[500], 0)

        self.assertEquals (self.ctrl.TabStates()[501], 0)

        self.assertEquals (self.ctrl.TabStates()[502], 0)

        self.assertEquals (self.ctrl.TabStates()[503], 0)

        self.assertEquals (self.ctrl.TabStates()[504], 0)

        self.assertEquals (self.ctrl.TabStates()[505], 0)

        self.assertEquals (self.ctrl.TabStates()[506], 0)

        self.assertEquals (self.ctrl.TabStates()[507], 0)

        self.assertEquals (self.ctrl.TabStates()[508], 0)

        self.assertEquals (self.ctrl.TabStates()[509], 0)

        self.assertEquals (self.ctrl.TabStates()[510], 0)

        self.assertEquals (self.ctrl.TabStates()[511], 0)

        self.assertEquals (self.ctrl.TabStates()[512], 0)

        self.assertEquals (self.ctrl.TabStates()[513], 0)

        self.assertEquals (self.ctrl.TabStates()[514], 0)

        self.assertEquals (self.ctrl.TabStates()[515], 0)

        self.assertEquals (self.ctrl.TabStates()[516], 0)

        self.assertEquals (self.ctrl.TabStates()[517], 0)

        self.assertEquals (self.ctrl.TabStates()[518], 0)

        self.assertEquals (self.ctrl.TabStates()[519], 0)

        self.assertEquals (self.ctrl.TabStates()[520], 0)

        self.assertEquals (self.ctrl.TabStates()[521], 0)

        self.assertEquals (self.ctrl.TabStates()[522], 0)

        self.assertEquals (self.ctrl.TabStates()[523], 0)

        self.assertEquals (self.ctrl.TabStates()[524], 0)

        self.assertEquals (self.ctrl.TabStates()[525], 0)

        self.assertEquals (self.ctrl.TabStates()[526], 0)

        self.assertEquals (self.ctrl.TabStates()[527], 0)

        self.assertEquals (self.ctrl.TabStates()[528], 0)

        self.assertEquals (self.ctrl.TabStates()[529], 0)

        self.assertEquals (self.ctrl.TabStates()[530], 0)

        self.assertEquals (self.ctrl.TabStates()[531], 0)

        self.assertEquals (self.ctrl.TabStates()[532], 0)

        self.assertEquals (self.ctrl.TabStates()[533], 0)

        self.assertEquals (self.ctrl.TabStates()[534], 0)

        self.assertEquals (self.ctrl.TabStates()[535], 0)

        self.assertEquals (self.ctrl.TabStates()[536], 0)

        self.assertEquals (self.ctrl.TabStates()[537], 0)

        self.assertEquals (self.ctrl.TabStates()[538], 0)

        self.assertEquals (self.ctrl.TabStates()[539], 0)

        self.assertEquals (self.ctrl.TabStates()[540], 0)

        self.assertEquals (self.ctrl.TabStates()[541], 0)

        self.assertEquals (self.ctrl.TabStates()[542], 0)

        self.assertEquals (self.ctrl.TabStates()[543], 0)

        self.assertEquals (self.ctrl.TabStates()[544], 0)

        self.assertEquals (self.ctrl.TabStates()[545], 0)

        self.assertEquals (self.ctrl.TabStates()[546], 0)

        self.assertEquals (self.ctrl.TabStates()[547], 0)

        self.assertEquals (self.ctrl.TabStates()[548], 0)

        self.assertEquals (self.ctrl.TabStates()[549], 0)

        self.assertEquals (self.ctrl.TabStates()[550], 0)

        self.assertEquals (self.ctrl.TabStates()[551], 0)

        self.assertEquals (self.ctrl.TabStates()[552], 0)

        self.assertEquals (self.ctrl.TabStates()[553], 0)

        self.assertEquals (self.ctrl.TabStates()[554], 0)

        self.assertEquals (self.ctrl.TabStates()[555], 0)

        self.assertEquals (self.ctrl.TabStates()[556], 0)

        self.assertEquals (self.ctrl.TabStates()[557], 0)

        self.assertEquals (self.ctrl.TabStates()[558], 0)

        self.assertEquals (self.ctrl.TabStates()[559], 0)

        self.assertEquals (self.ctrl.TabStates()[560], 0)

        self.assertEquals (self.ctrl.TabStates()[561], 0)

        self.assertEquals (self.ctrl.TabStates()[562], 0)

        self.assertEquals (self.ctrl.TabStates()[563], 0)

        self.assertEquals (self.ctrl.TabStates()[564], 0)

        self.assertEquals (self.ctrl.TabStates()[565], 0)

        self.assertEquals (self.ctrl.TabStates()[566], 0)

        self.assertEquals (self.ctrl.TabStates()[567], 0)

        self.assertEquals (self.ctrl.TabStates()[568], 0)

        self.assertEquals (self.ctrl.TabStates()[569], 0)

        self.assertEquals (self.ctrl.TabStates()[570], 0)

        self.assertEquals (self.ctrl.TabStates()[571], 0)

        self.assertEquals (self.ctrl.TabStates()[572], 0)

        self.assertEquals (self.ctrl.TabStates()[573], 0)

        self.assertEquals (self.ctrl.TabStates()[574], 0)

        self.assertEquals (self.ctrl.TabStates()[575], 0)

        self.assertEquals (self.ctrl.TabStates()[576], 0)

        self.assertEquals (self.ctrl.TabStates()[577], 0)

        self.assertEquals (self.ctrl.TabStates()[578], 0)

        self.assertEquals (self.ctrl.TabStates()[579], 0)

        self.assertEquals (self.ctrl.TabStates()[580], 0)

        self.assertEquals (self.ctrl.TabStates()[581], 0)

        self.assertEquals (self.ctrl.TabStates()[582], 0)

        self.assertEquals (self.ctrl.TabStates()[583], 0)

        self.assertEquals (self.ctrl.TabStates()[584], 0)

        self.assertEquals (self.ctrl.TabStates()[585], 0)

        self.assertEquals (self.ctrl.TabStates()[586], 0)

        self.assertEquals (self.ctrl.TabStates()[587], 0)

        self.assertEquals (self.ctrl.TabStates()[588], 0)

        self.assertEquals (self.ctrl.TabStates()[589], 0)

        self.assertEquals (self.ctrl.TabStates()[590], 0)

        self.assertEquals (self.ctrl.TabStates()[591], 0)

        self.assertEquals (self.ctrl.TabStates()[592], 0)

        self.assertEquals (self.ctrl.TabStates()[593], 0)

        self.assertEquals (self.ctrl.TabStates()[594], 0)

        self.assertEquals (self.ctrl.TabStates()[595], 0)

        self.assertEquals (self.ctrl.TabStates()[596], 0)

        self.assertEquals (self.ctrl.TabStates()[597], 0)

        self.assertEquals (self.ctrl.TabStates()[598], 0)

        self.assertEquals (self.ctrl.TabStates()[599], 0)

        self.assertEquals (self.ctrl.TabStates()[600], 0)

        self.assertEquals (self.ctrl.TabStates()[601], 0)

        self.assertEquals (self.ctrl.TabStates()[602], 0)

        self.assertEquals (self.ctrl.TabStates()[603], 0)

        self.assertEquals (self.ctrl.TabStates()[604], 0)

        self.assertEquals (self.ctrl.TabStates()[605], 0)

        self.assertEquals (self.ctrl.TabStates()[606], 0)

        self.assertEquals (self.ctrl.TabStates()[607], 0)

        self.assertEquals (self.ctrl.TabStates()[608], 0)

        self.assertEquals (self.ctrl.TabStates()[609], 0)

        self.assertEquals (self.ctrl.TabStates()[610], 0)

        self.assertEquals (self.ctrl.TabStates()[611], 0)

        self.assertEquals (self.ctrl.TabStates()[612], 0)

        self.assertEquals (self.ctrl.TabStates()[613], 0)

        self.assertEquals (self.ctrl.TabStates()[614], 0)

        self.assertEquals (self.ctrl.TabStates()[615], 0)

        self.assertEquals (self.ctrl.TabStates()[616], 0)

        self.assertEquals (self.ctrl.TabStates()[617], 0)

        self.assertEquals (self.ctrl.TabStates()[618], 0)

        self.assertEquals (self.ctrl.TabStates()[619], 0)

        self.assertEquals (self.ctrl.TabStates()[620], 0)

        self.assertEquals (self.ctrl.TabStates()[621], 0)

        self.assertEquals (self.ctrl.TabStates()[622], 0)

        self.assertEquals (self.ctrl.TabStates()[623], 0)

        self.assertEquals (self.ctrl.TabStates()[624], 0)

        self.assertEquals (self.ctrl.TabStates()[625], 0)

        self.assertEquals (self.ctrl.TabStates()[626], 0)

        self.assertEquals (self.ctrl.TabStates()[627], 0)

        self.assertEquals (self.ctrl.TabStates()[628], 0)

        self.assertEquals (self.ctrl.TabStates()[629], 0)

        self.assertEquals (self.ctrl.TabStates()[630], 0)

        self.assertEquals (self.ctrl.TabStates()[631], 0)

        self.assertEquals (self.ctrl.TabStates()[632], 0)

        self.assertEquals (self.ctrl.TabStates()[633], 0)

        self.assertEquals (self.ctrl.TabStates()[634], 0)

        self.assertEquals (self.ctrl.TabStates()[635], 0)

        self.assertEquals (self.ctrl.TabStates()[636], 0)

        self.assertEquals (self.ctrl.TabStates()[637], 0)

        self.assertEquals (self.ctrl.TabStates()[638], 0)

        self.assertEquals (self.ctrl.TabStates()[639], 0)

        self.assertEquals (self.ctrl.TabStates()[640], 0)

        self.assertEquals (self.ctrl.TabStates()[641], 0)

        self.assertEquals (self.ctrl.TabStates()[642], 0)

        self.assertEquals (self.ctrl.TabStates()[643], 0)

        self.assertEquals (self.ctrl.TabStates()[644], 0)

        self.assertEquals (self.ctrl.TabStates()[645], 0)

        self.assertEquals (self.ctrl.TabStates()[646], 0)

        self.assertEquals (self.ctrl.TabStates()[647], 0)

        self.assertEquals (self.ctrl.TabStates()[648], 0)

        self.assertEquals (self.ctrl.TabStates()[649], 0)

        self.assertEquals (self.ctrl.TabStates()[650], 0)

        self.assertEquals (self.ctrl.TabStates()[651], 0)

        self.assertEquals (self.ctrl.TabStates()[652], 0)

        self.assertEquals (self.ctrl.TabStates()[653], 0)

        self.assertEquals (self.ctrl.TabStates()[654], 0)

        self.assertEquals (self.ctrl.TabStates()[655], 0)

        self.assertEquals (self.ctrl.TabStates()[656], 0)

        self.assertEquals (self.ctrl.TabStates()[657], 0)

        self.assertEquals (self.ctrl.TabStates()[658], 0)

        self.assertEquals (self.ctrl.TabStates()[659], 0)

        self.assertEquals (self.ctrl.TabStates()[660], 0)

        self.assertEquals (self.ctrl.TabStates()[661], 0)

        self.assertEquals (self.ctrl.TabStates()[662], 0)

        self.assertEquals (self.ctrl.TabStates()[663], 0)

        self.assertEquals (self