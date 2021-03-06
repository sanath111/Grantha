#!/usr/bin/python2.7
# *-* coding: utf-8 *-*

### rfidUhfServer Script Should be running in machine connected to RFID Reader Module ###

import os
import sys
from PyQt5 import QtGui, QtWidgets, uic, QtCore
from PyQt5.QtWidgets import QDesktopWidget
from PyQt5.QtCore import QProcess, QThread, pyqtSignal
import dbGrantha
import zmq
import socket
import debug
import subprocess
from Utils_Gui import *
import time
import setproctitle
import tempfile

filePath = os.path.abspath(__file__)
progPath = os.sep.join(filePath.split(os.sep)[:-2])
uiFilePath = os.path.join(progPath,"GUI","uiFiles")
imgFilePath = os.path.join(progPath, "GUI","imageFiles")

sys.path.append(uiFilePath)
sys.path.append(imgFilePath)

Manage_Items = "Manage_Items.py"
Rfid_Tools = "Rfid_Tools.py"
# Update = "Update.py"
# Update_Tag = "Update_Tag.py"
Modify = "Modify.py"
Log = "Log.py"
Find_Tag = "Find_Tag.py"

user = os.environ['USER']
context = zmq.Context()
processes = []
tempDir = tempfile.gettempdir()

class mainWindow():
    global processes

    db = dbGrantha.dbGrantha()

    getAuthUsers = "SELECT * FROM AUTH_USERS"
    aU = db.execute(getAuthUsers,dictionary=True)
    authUsers = [x['auth_users'] for x in aU]

    getLOC = "SELECT location FROM LOCATION"
    loc = db.execute(getLOC, dictionary=True)
    LOC = [x['location'] for x in loc]

    queryCol = "SELECT (COLUMN_NAME) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ITEMS' AND COLUMN_NAME NOT IN ('item_id')"
    column = db.execute(queryCol, dictionary=True)
    theColumn = [x['COLUMN_NAME'] for x in column]

    completer = "SELECT serial_no,item_type,location,user FROM ITEMS"
    theList = db.execute(completer, dictionary=True)
    slList = [x['serial_no'] for x in theList]
    itList = list(set([x['item_type'] for x in theList]))
    locList = list(set([x['location'] for x in theList]))
    usrList = list(set([x['user'] for x in theList]))

    getSN = "SELECT * FROM SERIAL_NO"
    sn = db.execute(getSN, dictionary=True)
    # slNoList = [x['serial_no'] for x in sn]

    def __init__(self):
        # super(myWindow, self).__init__()
        self.rfidMultiCount = 0
        self.rfidMultiUniqSlno = {}
        self.ui = uic.loadUi(os.path.join(uiFilePath, 'Grantha.ui'))

        self.ui.allButton.pressed.connect(self.allBtnClick)
        self.ui.serialNoButton.pressed.connect(self.slNoBtnClick)
        self.ui.itemTypeButton.pressed.connect(self.itBtnClick)
        self.ui.locationButton.pressed.connect(self.locBtnClick)
        self.ui.userButton.pressed.connect(self.usrBtnClick)

        self.ui.comboBox.currentIndexChanged.connect(self.search)

        if user in self.authUsers:
            self.ui.manageItemsButton.clicked.connect(self.manageItems)
            self.ui.rfidToolsButton.clicked.connect(self.rfidTools)
            # self.ui.updateButton.clicked.connect(self.update)
            # self.ui.updateTagButton.clicked.connect(self.updateTag)
            self.ui.modifyButton.clicked.connect(self.modify)
            self.ui.findTagButton.clicked.connect(self.findTag)
            self.ui.logButton.clicked.connect(self.log)
            self.ui.readSingleButton.clicked.connect(self.readFromRfidTag)
            self.ui.readMultiButton.clicked.connect(self.readMultiFromRfidTag)
            self.ui.stopReadButton.setEnabled(False)
            self.ui.stopReadButton.clicked.connect(self.stopRead)

        self.ui.setWindowTitle('GRANTHA')
        self.ui.setWindowIcon(QtGui.QIcon(os.path.join(imgFilePath, 'granthaLogo.png')))

        self.ui.tableWidget.customContextMenuRequested.connect(self.viewParentPopUp)

        self.center()
        self.ui.showMaximized()

        # self.db = database.DataBase()

    def viewParentPopUp(self,pos):
        # a = self.ui.tableWidget.horizontalHeaderItem(8).text()
        #
        # debug.info a

        selectedCellIndex = self.ui.tableWidget.selectedIndexes()
        for index in selectedCellIndex:
            selectedColumnIndex = index.column()

            selectedColumnLabel = self.ui.tableWidget.horizontalHeaderItem(selectedColumnIndex).text()
            # debug.info selectedColumnLabel

            if (selectedColumnLabel == "location"):
                menu = QtWidgets.QMenu()
                # view = QtWidgets.QMenu()
                # view.setTitle("view parent location")
                # menu.addMenu(view)
                try:
                    selected = self.ui.tableWidget.selectedItems()
                except:
                    selected = None

                if(selected):
                    viewParentAction = menu.addAction("View Parent Location")
                    if user in self.authUsers:
                        modifyLocationAction = menu.addAction("Modify Location")

                action = menu.exec_(self.ui.tableWidget.viewport().mapToGlobal(pos))

                if(selected):
                    if (action == viewParentAction):
                        self.viewParent()
                    try:
                        if (action == modifyLocationAction):
                            self.modify()
                    except:
                        pass
            else:
                pass


    def viewParent(self):
        selectedText = self.ui.tableWidget.currentItem().text()
        # debug.info selectedText
        # loc = self.db.listOfLocation()
        # getLOC = "SELECT location FROM LOCATION"
        # loc = self.db.execute(getLOC,dictionary=True)
        # debug.info(loc)
        # LOC = [x['location'] for x in loc]
        # debug.info LOC
        if selectedText in self.LOC:
            getParentLocation = "SELECT parent_location FROM LOCATION WHERE location='%s' " %(selectedText)
            # pL = self.db.getParentLocation(query)
            pL = self.db.execute(getParentLocation,dictionary=True)
            debug.info(pL)
            pL = pL[0]
            self.parentLocation = pL['parent_location']
            # debug.info self.parentLocation
            if self.parentLocation == None:
                parentMessage = "No Parent Location"
            else:
                parentMessage = self.parentLocation
            messageBox(parentMessage)
            # self.viewParentMessage()
        else:
            debug.info ("not valid location")

    # def viewParentMessage(self):
    #     msg = QtWidgets.QMessageBox()
    #     msg.setIcon(QtWidgets.QMessageBox.Information)
    #     msg.setWindowTitle("Message")
    #     msg.setText(self.parentMessage)
    #     msg.exec_()

    def center(self):
        qr = self.ui.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.ui.move(qr.topLeft())


    def allBtnClick(self):
        # self.ui.tableWidget.setSortingEnabled(False)
        # self.ui.tableWidget.resizeColumnsToContents()
        #db = database.DataBase()
        self.ui.tableWidget.setRowCount(0)

        self.ui.comboBox.clearEditText()
        # column = self.db.getColumns()
        # theColumn = [x['COLUMN_NAME'] for x in column]
        # queryCol = "SELECT (COLUMN_NAME) FROM INFORMATION_SCHEMA.COLUMNS \
        #             WHERE TABLE_NAME = 'ITEMS' AND COLUMN_NAME NOT IN ('item_id')"
        #
        # # debug.info(queryCol)
        # column = self.db.execute(queryCol, dictionary=True)
        # theColumn = [x['COLUMN_NAME'] for x in column]
        # # debug.info(theColumn)

        self.ui.tableWidget.setColumnCount(len(self.theColumn))
        self.ui.tableWidget.setHorizontalHeaderLabels(self.theColumn)

        queryAll = "SELECT * FROM ITEMS ORDER BY item_type"
        # theRows = self.db.getAllRows()
        theRows = self.db.execute(queryAll,dictionary=True)
        # debug.info(len(theRows))
        self.ui.tableWidget.setRowCount(len(theRows))

        row = 0
        # self.db.getAllValues(init=True)
        while True:
            if (row == len(theRows)):
                break
            # primaryResult = self.db.getAllValues()
            primaryResult = theRows[row]
            # debug.info (primaryResult)
            # if (not primaryResult):
            #     break
            col = 0
            for n in self.theColumn:
                result = primaryResult[n]
                self.ui.tableWidget.setItem(row,col,QtWidgets.QTableWidgetItem(str(result)))
                col +=1
            row +=1

        numRows = self.ui.tableWidget.rowCount()
        for row in range(numRows):
            path = str(self.ui.tableWidget.item(row, 10).text())
            if path:
                # debug.info(path)
                self.ui.tableWidget.takeItem(row, 10)
                imageThumb = ImageWidget(path, 32)
                imageThumb.clicked.connect(lambda x, imagePath=path: imageWidgetClicked(imagePath))
                self.ui.tableWidget.setCellWidget(row, 10, imageThumb)

        # self.ui.tableWidget.resizeColumnsToContents()
        self.ui.tableWidget.resizeRowsToContents()
        self.ui.tableWidget.resizeColumnsToContents()
        debug.info( "Loaded list of all items.")
        # self.ui.tableWidget.setSortingEnabled(True)

    # def imageWidgetClicked(self, imagePath):
    #     image_path = str(imagePath)
    #     debug.info(image_path)
    #     debug.info("Image Clicked")
    #
    #     # cmdFull = "xdg-open \"" + image_path + "\""
    #     cmdFull = "feh \"" + image_path + "\" -Z -."
    #     debug.info(cmdFull)
    #     subprocess.Popen(cmdFull, shell=True)

    def search(self):
        self.ui.tableWidget.setRowCount(0)

        # column = self.db.getColumns()
        # self.theColumn = [x['COLUMN_NAME'] for x in column]

        self.ui.tableWidget.setColumnCount(len(self.theColumn))
        self.ui.tableWidget.setHorizontalHeaderLabels(self.theColumn)

        currTxt = self.ui.comboBox.currentText().strip()
        # debug.info currTxt

        if self.ui.serialNoButton.isChecked():
            if (currTxt in self.slList):
                getRows = "SELECT " + ','.join(self.theColumn) + " FROM ITEMS WHERE serial_no='%s' " %(currTxt)
                # rows = self.db.getRows(self.query)
                rows = self.db.execute(getRows, dictionary=True)
                # debug.info rows
                self.ui.tableWidget.setRowCount(len(rows))
                self.fillTable(rows)
            else:
                pass

        if self.ui.itemTypeButton.isChecked():
            if (currTxt in self.itList):
                getRows = "SELECT " + ','.join(self.theColumn) + " FROM ITEMS WHERE item_type='%s' " %(currTxt)
                # rows = self.db.getRows(self.query)
                rows = self.db.execute(getRows, dictionary=True)
                self.ui.tableWidget.setRowCount(len(rows))
                self.fillTable(rows)
            else:
                pass

        if self.ui.locationButton.isChecked():
            if (currTxt in self.locList):
                getRows = "SELECT " + ','.join(self.theColumn) + " FROM ITEMS WHERE location='%s' " %(currTxt)
                # rows = self.db.getRows(self.query)
                rows = self.db.execute(getRows, dictionary=True)
                self.ui.tableWidget.setRowCount(len(rows))
                self.fillTable(rows)
            else:
                pass

        if self.ui.userButton.isChecked():
            if (currTxt in self.usrList):
                getRows = "SELECT " + ','.join(self.theColumn) + " FROM ITEMS WHERE user='%s' " %(currTxt)
                # rows = self.db.getRows(self.query)
                rows = self.db.execute(getRows, dictionary=True)
                self.ui.tableWidget.setRowCount(len(rows))
                self.fillTable(rows)
            else:
                pass

        # else:
        #     self.message()

    def fillTable(self,rows):
        row = 0
        while True:
            if (row == len(rows)):
                break
            primaryResult = rows[row]
            col = 0
            for n in self.theColumn:
                result = primaryResult[n]
                self.ui.tableWidget.setItem(row, col, QtWidgets.QTableWidgetItem(str(result)))
                col += 1
            row += 1

        # self.ui.tableWidget.resizeColumnsToContents()

        numRows = self.ui.tableWidget.rowCount()
        for row in range(numRows):
            path = str(self.ui.tableWidget.item(row, 10).text())
            if path:
                # debug.info(path)
                self.ui.tableWidget.takeItem(row, 10)
                imageThumb = ImageWidget(path, 32)
                imageThumb.clicked.connect(lambda x, imagePath=path: imageWidgetClicked(imagePath))
                self.ui.tableWidget.setCellWidget(row, 10, imageThumb)

        self.ui.tableWidget.resizeColumnsToContents()
        self.ui.tableWidget.resizeRowsToContents()

    def slNoBtnClick(self):
        self.ui.comboBox.clear()
        self.ui.comboBox.clearEditText()
        # completer = "SELECT serial_no,item_type,location,user FROM ITEMS"
        # # theList = self.db.Completer()
        # theList = self.db.execute(completer,dictionary=True)
        # slList = [x['serial_no'] for x in theList]
        self.slList.sort()
        self.ui.comboBox.addItems(self.slList)
        # self.model = QtCore.QStringListModel()
        # self.model.setStringList(slList)
        # self.completer()

    def itBtnClick(self):
        self.ui.comboBox.clear()
        self.ui.comboBox.clearEditText()
        # theList = self.db.Completer()
        # itList = list(set([x['item_type'] for x in theList]))
        self.itList.sort()
        self.ui.comboBox.addItems(self.itList)
        # self.model = QtCore.QStringListModel()
        # self.model.setStringList(itList)
        # self.completer()

    def locBtnClick(self):
        self.ui.comboBox.clear()
        self.ui.comboBox.clearEditText()
        # theList = self.db.Completer()
        # locList = list(set([x['location'] for x in theList]))
        self.locList.sort()
        self.ui.comboBox.addItems(self.locList)
        # self.model = QtCore.QStringListModel()
        # self.model.setStringList(locList)
        # self.completer()

    def usrBtnClick(self):
        self.ui.comboBox.clear()
        self.ui.comboBox.clearEditText()
        # theList = self.db.Completer()
        # usrList = list(set([x['user'] for x in theList]))
        self.usrList.sort()
        self.ui.comboBox.addItems(self.usrList)
        # self.model = QtCore.QStringListModel()
        # self.model.setStringList(usrList)
        # self.completer()

    # def completer(self):
    #     completer = QtWidgets.QCompleter()
    #     completer.setModel(self.model)
    #     completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
    #     self.ui.comboBox.setCompleter(completer)

    # def message(self):
    #     QtWidgets.QMessageBox.about(QtWidgets.QMessageBox(),"Error!","Please Check Input.")


    # Processes to start when respective buttons are clicked

    def manageItems(self):
        debug.info("Opening manage items Menu")
        p = QProcess(parent=self.ui)
        processes.append(p)
        debug.info(processes)
        p.started.connect(self.disableButtons)
        p.readyReadStandardOutput.connect(self.read_out)
        p.readyReadStandardError.connect(self.read_err)
        # p.setStandardOutputFile(tempDir + os.sep + "Grantha_ManageItems_" + user + ".log")
        # p.setStandardErrorFile(tempDir + os.sep + "Grantha_ManageItems_" + user + ".err")
        p.finished.connect(self.enableButtons)
        p.start(sys.executable, Manage_Items.split())

    def rfidTools(self):
        debug.info("Opening Rfid Tools Menu")
        p = QProcess(parent=self.ui)
        processes.append(p)
        debug.info(processes)
        p.started.connect(self.disableButtons)
        p.readyReadStandardOutput.connect(self.read_out)
        p.readyReadStandardError.connect(self.read_err)
        p.finished.connect(self.enableButtons)
        p.start(sys.executable, Rfid_Tools.split())



    # def update(self):
    #     p = QProcess(parent=self.ui)
    #     p.start(sys.executable, Update.split())
    #
    # def updateTag(self):
    #     p = QProcess(parent=self.ui)
    #     p.start(sys.executable, Update_Tag.split())

    def modify(self):
        debug.info("Opening Modify Menu")
        p = QProcess(parent=self.ui)
        processes.append(p)
        debug.info(processes)
        p.started.connect(self.disableButtons)
        p.readyReadStandardOutput.connect(self.read_out)
        p.readyReadStandardError.connect(self.read_err)
        p.finished.connect(self.enableButtons)
        p.start(sys.executable, Modify.split())

    def log(self):
        p = QProcess(parent=self.ui)
        p.start(sys.executable, Log.split())

    def findTag(self,process):
        p = QProcess(parent=self.ui)
        p.start(sys.executable, Find_Tag.split())

    def read_out(self):
        if processes:
            for process in processes:
                print ('stdout:', str(process.readAllStandardOutput()).strip())

    def read_err(self):
        if processes:
            for process in processes:
                print ('stderr:', str(process.readAllStandardError()).strip())


    def disableButtons(self):
        self.ui.readSingleButton.setEnabled(False)
        self.ui.readMultiButton.setEnabled(False)
        self.ui.manageItemsButton.setEnabled(False)
        self.ui.rfidToolsButton.setEnabled(False)
        self.ui.modifyButton.setEnabled(False)
        self.ui.logButton.setEnabled(False)
        self.ui.findTagButton.setEnabled(False)


    def enableButtons(self):
        self.ui.readSingleButton.setEnabled(True)
        self.ui.readMultiButton.setEnabled(True)
        self.ui.manageItemsButton.setEnabled(True)
        self.ui.rfidToolsButton.setEnabled(True)
        self.ui.modifyButton.setEnabled(True)
        self.ui.logButton.setEnabled(True)
        self.ui.findTagButton.setEnabled(True)
        del processes[:]
        debug.info(processes)



    def readFromRfidTag(self):
        self.ui.readSingleButton.setEnabled(False)
        self.ui.readMultiButton.setEnabled(False)
        self.ui.tableWidget.setRowCount(0)
        rT = readThread(app)
        # self.msg = messageBox("Place Your Tag")
        rT.waiting.connect(self.msg)
        # widgets.append(self.msg)
        rT.tagIdReceived.connect(self.closePlaceTagMessage)
        rT.start()

    def msg(self, plceMsg):
        messagebox = TimerMessageBox(1, plceMsg)
        messagebox.exec_()

    # def openPlaceTagMessage(self):
    #     self.plcMsg = QtWidgets.QMessageBox()
    #     self.plcMsg.setIcon(QtWidgets.QMessageBox.Information)
    #     self.plcMsg.setWindowTitle("Message")
    #     self.plcMsg.setText("Place your Tag...")
    #     self.plcMsg.show()

    def closePlaceTagMessage(self, tagId):
        try:
            # self.plcMsg.close()
            # debug.info(widgets)
            # # # for childQWidget in self.ui.findChildren(QtWidgets.QWidget):
            # # #     childQWidget.close()
            # # # self.isDirectlyClose = True
            # # # return QtGui.QMainWindow.close(self)
            # btn = self.msg.defaultButton()
            # debug.info(btn)
            # for openWidgets in widgets:
            #     # openWidgets.close()
            #     self.msg.close(openWidgets)
            # self.plcMsg.close()
            # self.msg.close()
            debug.info("Message Closed")
        except:
            debug.info (str(sys.exc_info()))
            pass

        # sn = self.db.listOfSerialNo()
        # SN = [x['serial_no'] for x in sn]
        # ti = self.db.listOfSerialNo()
        # debug.info (ti)
        TI = [x['tag_id'] for x in self.sn]
        # debug.info  (TI)
        if tagId in TI:
            # slno = self.db.getSlFrmTid(tagId)
            getSlFrmTid = "SELECT serial_no FROM SERIAL_NO WHERE tag_id=\"{}\" ".format(tagId)
            slno = self.db.execute(getSlFrmTid, dictionary=True)
            slno = slno[0]
            slNo = slno['serial_no']
            # debug.info slno
            debug.info ("received sl.no: "+slNo)
            self.ui.comboBox.setEditText(slNo)

            # column = self.db.getColumns()
            # self.theColumn = [x['COLUMN_NAME'] for x in column]

            self.ui.tableWidget.setColumnCount(len(self.theColumn))
            self.ui.tableWidget.setHorizontalHeaderLabels(self.theColumn)

            currTxt = self.ui.comboBox.currentText().strip()

            # self.query = "SELECT " + ','.join(self.theColumn) + " FROM ITEMS WHERE serial_no='%s' " %(currTxt)
            # rows = self.db.getRows(self.query)
            getRows = "SELECT " + ','.join(self.theColumn) + " FROM ITEMS WHERE serial_no='%s' " % (currTxt)
            rows = self.db.execute(getRows, dictionary=True)

            self.ui.tableWidget.setRowCount(len(rows))
            self.fillTable(rows)
            self.ui.readSingleButton.setEnabled(True)
            self.ui.readMultiButton.setEnabled(True)

        else:
            messageBox("<b>This Serial No. does not exists in Database</b> \n And/Or \n <b>Tag was not scanned properly!</b>","",os.path.join(imgFilePath,"oh.png"))
            self.ui.readSingleButton.setEnabled(True)
            self.ui.readMultiButton.setEnabled(True)
            # self.wrongTagMessage()

    # def wrongTagMessage(self):
    #     # self.Msg = QtWidgets.QMessageBox()
    #     # self.Msg.setIcon(QtWidgets.QMessageBox.Information)
    #     # self.Msg.setWindowTitle("Wrong Tag")
    #     # self.Msg.setText("This Serial No. does not exists in Database \n And/Or \n Tag was not scanned properly!")
    #     # self.Msg.show()
    #     messageBox("This Serial No. does not exists in Database \n And/Or \n Tag was not scanned properly!",os.path.join(imgFilePath,"oh.png"))
    #     self.ui.readSingleButton.setEnabled(True)
    #     self.ui.readMultiButton.setEnabled(True)

    def readMultiFromRfidTag(self):
        self.ui.tableWidget.setRowCount(0)
        # timeout = str(self.ui.spinBox.value())

        # if self.ui.readMultipleButton.isChecked():
        self.ui.readMultiButton.setEnabled(False)
        self.ui.readSingleButton.setEnabled(False)
        self.ui.stopReadButton.setEnabled(True)

        self.rfidMultiUniqSlno.clear()
        self.rfidMultiCount = 0

        # rmrT = readMultiReplyThread(app)
        rmT = readMultiThread(app)

        # rmrT.slNoReceived.connect(self.updateTable)
        # rmrT.finished.connect(self.readButtonEnable)
        rmT.tagIdReceived.connect(self.updateTable)

        # rmrT.start()
        rmT.start()

        # else:
        #     pass

    def updateTable(self, tagId):
        if (tagId == "MULTI_READ_STARTED"):
            pass

        else:
            # ti = self.db.listOfSerialNo()
            # # debug.info (ti)
            # TI = [x['tag_id'] for x in ti]
            # debug.info  (TI)
            TI = [x['tag_id'] for x in self.sn]
            if tagId in TI:
                # slno = self.db.getSlFrmTid(tagId)
                getSlFrmTid = "SELECT serial_no FROM SERIAL_NO WHERE tag_id=\"{}\" ".format(tagId)
                slno = self.db.execute(getSlFrmTid, dictionary=True)
                slno = slno[0]
                slNo = slno['serial_no']
                debug.info ("received sl.no: "+slNo)

                if (self.rfidMultiUniqSlno.has_key(slNo)):
                    return

                self.rfidMultiUniqSlno[slNo] = 1
                debug.info (self.rfidMultiUniqSlno)

                self.rfidMultiCount += 1
                self.ui.comboBox.setEditText(slNo)

                # column = self.db.getColumns()
                # self.theColumn = [x['COLUMN_NAME'] for x in column]

                self.ui.tableWidget.setColumnCount(len(self.theColumn))
                self.ui.tableWidget.setHorizontalHeaderLabels(self.theColumn)

                self.ui.tableWidget.setRowCount(self.rfidMultiCount)

                currTxt = self.ui.comboBox.currentText()
                getRows = "SELECT " + ','.join(self.theColumn) + " FROM ITEMS WHERE serial_no='%s' " % (currTxt)
                rows = self.db.execute(getRows, dictionary=True)
                # debug.info(rows)
                # rows = self.db.getRows(self.query)
                # self.ui.tableWidget.setRowCount(len(rows))

                rowCount = self.ui.tableWidget.rowCount()

                # row = rowCount-1
                #
                # self.db.getValues(self.query, init=True)
                # while True:
                #     primaryResult = self.db.getValues(self.query)
                #     # debug.info primaryResult
                #     if (not primaryResult):
                #         break
                #     col = 0
                #     for n in self.theColumn:
                #         result = primaryResult[n]
                #         self.ui.tableWidget.setItem(row, col, QtWidgets.QTableWidgetItem(str(result)))
                #         col += 1
                #     row += 1

                row = rowCount -1
                while True:
                    primaryResult = rows[0]
                    # debug.info(primaryResult)
                    col = 0
                    for n in self.theColumn:
                        result = primaryResult[n]
                        self.ui.tableWidget.setItem(row, col, QtWidgets.QTableWidgetItem(str(result)))
                        col += 1
                    row += 1
                    break

                # numRows = self.ui.tableWidget.rowCount()
                # for row in range(numRows):
                #     path = str(self.ui.tableWidget.item(row, 10).text())
                #     debug.info(path)
                #     self.ui.tableWidget.takeItem(row, 10)
                #     imageThumb = ImageWidget(path, 32)
                #     imageThumb.clicked.connect(lambda x, imagePath=path: imageWidgetClicked(imagePath))
                #     self.ui.tableWidget.setCellWidget(row, 10, imageThumb)
                #
                # self.ui.tableWidget.resizeColumnsToContents()
                # self.ui.tableWidget.resizeRowsToContents()
                numRow = self.rfidMultiCount -1
                path = str(self.ui.tableWidget.item(numRow, 10).text())
                if path:
                    # debug.info(path)
                    self.ui.tableWidget.takeItem(numRow, 10)
                    imageThumb = ImageWidget(path, 32)
                    imageThumb.clicked.connect(lambda x, imagePath=path: imageWidgetClicked(imagePath))
                    self.ui.tableWidget.setCellWidget(numRow, 10, imageThumb)

                self.ui.tableWidget.resizeRowsToContents()
                self.ui.tableWidget.resizeColumnsToContents()

            else:
                pass
                # self.ui.readMultiButton.setEnabled(True)

        # else:
        #     self.wrongTagMessage()

    # def readButtonEnable(self):
    #     self.ui.readMultiButton.setEnabled(True)

    def stopRead(self):
        # self.ui.readMultiButton.setEnabled(True)
        # self.ui.readSingleButton.setEnabled(True)
        self.ui.stopReadButton.setEnabled(False)

        srT = stopReadThread(app)
        srT.ackReceived.connect(self.readButtonsEnable)
        srT.start()

    def readButtonsEnable(self, ack):
        if (ack == "STOPPING"):
            self.ui.readSingleButton.setEnabled(True)
            self.ui.readMultiButton.setEnabled(True)




class ImageWidget(QtWidgets.QPushButton):
    def __init__(self, imagePath, imageSize, parent=None):
        super(ImageWidget, self).__init__(parent)
        self.imagePath = imagePath
        self.picture = QtGui.QPixmap(imagePath)
        # debug.info (self.imagePath)
        self.picture  = self.picture.scaledToHeight(imageSize,0)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawPixmap(0, 0, self.picture)

    def sizeHint(self):
        return(self.picture.size())





class readThread(QThread):
    waiting = pyqtSignal(str)
    tagIdReceived = pyqtSignal(str)

    def __init__(self, parent):
        super(readThread, self).__init__(parent)

    def run(self):
        self.waiting.emit("Place your tag...")

        
        debug.info("connecting to rfid Scanner Server...")
        self.socket = context.socket(zmq.REQ)
        try:
            self.socket.connect("tcp://192.168.1.183:4689")
            debug.info("connected.")
        except:
            debug.info (str(sys.exc_info()))
        self.socket.send("READ")

        # slNo = self.socket.recv()
        # debug.info "Received sl.No: " + slNo
        try:
            tagId = self.socket.recv()
            debug.info( "Received Tag Id :" + tagId)
            self.tagIdReceived.emit(tagId)
        except:
            debug.info (str(sys.exc_info()))

        self.socket.close()
        
        if (self.socket.closed == True):
            debug.info( "read Single Socket closed.")


class readMultiThread(QThread):
    # waiting = pyqtSignal()
    tagIdReceived = pyqtSignal(str)

    def __init__(self, parent):
        super(readMultiThread, self).__init__(parent)
        # self.to = to

    def run(self):
        # self.waiting.emit()

        
        debug.info("connecting to rfid Scanner Server...")
        self.socket = context.socket(zmq.REQ)
        self.socket.connect("tcp://192.168.1.183:4689")
        debug.info("connected.")
        self.socket.send("READ_MULTI")
        rep = self.socket.recv()
        debug.info (rep)
        # self.socket.close()
        # 
        # if (context.closed == True) and (self.socket.closed == True):
        #     debug.info "Socket and Context closed."
        #####################################
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        server_address = (ip, 4695)
        sock.bind(server_address)
        sock.listen(1)
        connection, client_address = sock.accept()
        #####################################
        while(True):
            tagId = connection.recv(1024)
            debug.info (tagId)
            # debug.info type(rep)
            if(tagId == "MULTI_STOP"):
                connection.close()
                # sock.shutdown(1)
                sock.close()
                break
            # if(rep == "STOP"):
            #     connection.close()
            #     sock.shutdown()
            #     sock.close()
            #     break

            else:
                self.tagIdReceived.emit(tagId)
        # sock.close()
        self.socket.close()
        
        if (self.socket.closed == True):
            debug.info( "read Multi Socket closed.")

class stopReadThread(QThread):
    # waiting = pyqtSignal()
    ackReceived = pyqtSignal(str)

    def __init__(self, parent):
        super(stopReadThread, self).__init__(parent)

    def run(self):
        # self.waiting.emit()

        
        debug.info("connecting to rfid Scanner Server...")
        self.socket = context.socket(zmq.REQ)
        self.socket.connect("tcp://192.168.1.183:4689")
        debug.info("connected.")

        self.socket.send("STOP")

        # slNo = self.socket.recv()
        # debug.info "Received sl.No: " + slNo
        ack = self.socket.recv()
        debug.info (ack)
        self.ackReceived.emit(ack)
        self.socket.close()
        
        if (self.socket.closed == True):
            debug.info( "stop Read Socket closed.")




# class setValueToTimerThread(QThread):
#     sending = pyqtSignal(int)
#
#     def __init__(self, to, parent):
#         QThread.__init__(self,parent)
#         self.to = to
#
#     def run(self):
#         for n in range(0, self.to+1):
#             self.sending.emit(n)
#             time.sleep(1)




if __name__ == '__main__':
    setproctitle.setproctitle("GRANTHA")

    # sys.stdout = open(tempDir + os.sep + "Grantha_" + user + ".log", 'w')
    # print('test')
    # tempDir + os.sep + "Grantha_ManageItems_" + user + ".log"
    app = QtWidgets.QApplication(sys.argv)
    window = mainWindow()
    sys.exit(app.exec_())

