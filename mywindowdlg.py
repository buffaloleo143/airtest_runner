# -*- coding: utf-8 -*-
# Leo Zeng
import os
import sys
import utils
import frozen

if hasattr(sys, 'frozen'):
	os.environ['PATH'] = sys._MEIPASS + ";" + os.environ['PATH']

from PyQt5 import QtCore, QtGui, QtWidgets
from airtest.core.android.adb import ADB
from mywindow import *
from constant import *

DEFAULT_SCRIPTS_ROOT = 'scripts'


def InitWindow():
	oMyWindow = MyWindow.GetInstance()
	oMyWindow.show()
	return oMyWindow


class SingleInst(object):
	oMgrObj = None

	@classmethod
	def GetInstance(cls):
		if not isinstance(SingleInst.oMgrObj, cls):
			cls.ReleaseInstance()
			SingleInst.oMgrObj = cls()
		return SingleInst.oMgrObj

	@classmethod
	def ReleaseInstance(cls):
		SingleInst.oMgrObj = None

	def __init__(self):
		assert (SingleInst.oMgrObj is None)


class MyWindow(QtWidgets.QMainWindow, Ui_MainWindow, SingleInst):

	def __init__(self, parent=None):
		super(MyWindow, self).__init__(parent)
		self.setupUi(self)
		self.InitListWidget()
		self.InitSignal()
		self.m_ScriptRoot = utils.GetCfgData('scripts_root')
		self.m_ADB = ADB()
		self.RefreshScripts()
		self.RefreshADB()
		self.m_Running = False

	def InitListWidget(self):
		self.m_DeviceListWidget = CMyListWidget(self.listWidget, self.checkBox)
		self.m_ScriptListWidget = CMyListWidget(self.LWScripts, self.CBScripts)

	def InitSignal(self):
		self.RefreshBtn.clicked.connect(self.RefreshADB)
		# self.BtnRefreshScripts.clicked.connect(self.RefreshScripts)
		self.BtnLaunch.clicked.connect(self.Lauch)
		self.BtnSelectScripts.clicked.connect(self.SelectScriptRoot)
		self.checkBox.stateChanged.connect(self.m_DeviceListWidget.SelcetAll)
		self.CBScripts.stateChanged.connect(self.m_ScriptListWidget.SelcetAll)
		self.BtnConnect.clicked.connect(self.ConnectRemoteADB)

	def RefreshADB(self):
		lDevices = [(tDevice, tDevice[1] == 'device') for tDevice in self.m_ADB.devices()]
		self.m_DeviceListWidget.Refresh(lDevices)

	def RefreshScripts(self):
		if not self.m_ScriptRoot:
			utils.SetCfgData('scripts_root', DEFAULT_SCRIPTS_ROOT)
			self.m_ScriptRoot = DEFAULT_SCRIPTS_ROOT
			if not os.path.exists(self.m_ScriptRoot):
				os.mkdir(self.m_ScriptRoot)
		self.LScriptsRoot.setText(self.m_ScriptRoot)
		lScripts = [(sScript, True) for sScript in os.listdir(self.m_ScriptRoot) if sScript.endswith('.air')]
		self.m_ScriptListWidget.Refresh(lScripts)

	def SelectScriptRoot(self):
		sDirChoose = QtWidgets.QFileDialog.getExistingDirectory(self, "选取文件夹", self.m_ScriptRoot)
		if sDirChoose == "":
			return
		self.m_ScriptRoot = sDirChoose
		self.RefreshScripts()

	def ShowReport(self, sCombineLog):
		self.m_Running = False
		import webbrowser
		reply = QtWidgets.QMessageBox.question(self, "Question",
											   self.tr("测试结束，点击查看报告"),
											   QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel,
											   QtWidgets.QMessageBox.Ok)
		if reply == QtWidgets.QMessageBox.Ok:
			webbrowser.open(sCombineLog, new=0, autoraise=True)
		elif reply == QtWidgets.QMessageBox.Cancel:
			print('点击了取消，报告路径：%s' % sCombineLog)
		else:
			return

	def Lauch(self):
		if self.m_Running:
			QtWidgets.QMessageBox.information(self, "提示", self.tr("正在运行中！"))
			return

		lDevices = self.m_DeviceListWidget.GetSelectedList()
		lScripts = self.m_ScriptListWidget.GetSelectedList()
		if not lDevices:
			QtWidgets.QMessageBox.warning(self, "提示", self.tr("请选择设备!"))
			return
		if not lScripts:
			QtWidgets.QMessageBox.warning(self, "提示", self.tr("请选择脚本!"))
			return
		sMode = self.CBMode.currentText()[-1]
		utils.SetCfgData(CFG_SCRIPTS, ','.join(lScripts))
		utils.SetCfgData(CFG_DEVICES, ','.join(lDevices))
		utils.SetCfgData(CFG_MODE, sMode)
		utils.SetCfgData(CFG_SCRIPTS_ROOT, self.m_ScriptRoot)
		utils.SetCfgData(CFG_PLATFORM, 'Android')
		self.m_Running = True
		self.m_RunThread = CRunthread()
		self.m_RunThread._signal.connect(self.ShowReport)
		self.m_RunThread.start()

	def ConnectRemoteADB(self):
		sText = self.TextAddr.text()
		sCmd = sText.split()[-2]
		sAddr = sText.split()[-1]
		if sCmd == 'connect':
			ADB(serialno=sAddr)
		elif sCmd == 'disconnect':
			ADB(serialno=sAddr).disconnect()
		else:
			QtWidgets.QMessageBox.information(self, "提示", self.tr("请输入正确指令！（connect or disconnect）"))
		self.RefreshADB()


class CMyListWidget(object):
	def __init__(self, oListWidget, oCheckBox):
		self.m_ListWidget = oListWidget
		self.m_CheckBox = oCheckBox

	def Refresh(self, lData):
		self.m_ListWidget.clear()
		self.m_CheckBox.setCheckState(False)
		for oText, bCheckable in lData:
			sText = '\t'.join(oText) if isinstance(oText, tuple) else oText
			self.AddItem(sText, bCheckable)

	def AddItem(self, sText, bCheckable=True):
		oItem = QtWidgets.QListWidgetItem()
		if bCheckable:
			oItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
			oItem.setCheckState(QtCore.Qt.Unchecked)
		else:
			oItem.setFlags(QtCore.Qt.ItemIsEnabled)
		oItem.setText(sText)
		font = QtGui.QFont()
		font.setPointSize(12)
		oItem.setFont(font)
		self.m_ListWidget.addItem(oItem)

	def SetCheckState(self, iState):
		for i in range(self.m_ListWidget.count()):
			oItem = self.m_ListWidget.item(i)
			oFlags = oItem.flags()
			if int(oFlags) & QtCore.Qt.ItemIsUserCheckable:
				oItem.setCheckState(iState)

	def SelcetAll(self):
		iState = self.m_CheckBox.checkState()
		self.SetCheckState(iState)

	def GetSelectedList(self):
		lText = []
		for i in range(self.m_ListWidget.count()):
			oItem = self.m_ListWidget.item(i)
			iState = oItem.checkState()
			if iState:
				lText.append(oItem.text().split('	')[0])
		return lText


class CRunthread(QtCore.QThread):
	#  通过类成员对象定义信号对象
	_signal = QtCore.pyqtSignal(str)

	def __init__(self):
		super(CRunthread, self).__init__()

	def __del__(self):
		self.wait()

	def run(self):
		import main
		sCombineLog = main.main()
		self._signal.emit(sCombineLog)


if __name__ == '__main__':
	import multiprocessing

	multiprocessing.freeze_support()
	app = QtWidgets.QApplication(sys.argv)
	InitWindow()
	sys.exit(app.exec_())
