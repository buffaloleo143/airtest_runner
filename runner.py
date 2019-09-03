# -*- coding: utf-8 -*-
# Leo Zeng
import datetime
import unittest
import os
import sys
import six
import traceback
import report
import video
import time
import json
import multiprocessing

from utils import CatchErr, RetryFunc, GetCfgData
from io import open
from airtest.core.api import auto_setup, log, connect_device
from airtest.core.helper import device_platform
from copy import copy
from constant import LOG_ROOT



class MyAirtestCase(unittest.TestCase):

	def __init__(self, sDevice, oQueue=None):
		super(MyAirtestCase, self).__init__()
		self.sDevice = sDevice
		self.queue = oQueue

	def Init(self, sPath, sPyFileName):
		self.m_LogRoot = sPath
		sConn = GetCfgData('platform') + ':///' + self.sDevice
		self.m_oDev = connect_device(sConn)
		sRunTime = datetime.datetime.now().strftime("%H%M%S")
		self.m_sLogDir = sRunTime + '_' + self.sDevice.replace(':', '') + '_' + sPyFileName
		self.logdir = os.path.join(sPath, self.m_sLogDir)

	@classmethod
	def setUpClass(cls):
		cls.scope = copy(globals())

	def setUp(self):
		auto_setup(logdir=self._logdir)
		self.RecordScreen()

	def tearDown(self):
		try:
			output = os.path.join(self.logdir, "recording_0.mp4")
			print(output)
			self.m_oDev.stop_recording(output)
		except:
			traceback.print_exc()
		self.Report()
		if self.queue:
			RunScript(self.sDevice, self.m_LogRoot, oScripts=self.queue)

	def runTest(self):
		try:
			exec(self._code["code"], self._code["ns"])
		except Exception as err:
			tb = traceback.format_exc()
			log("Final Error", tb)
			six.reraise(*sys.exc_info())

	def StartRecording(self):
		if device_platform(self.m_oDev) == 'Windows':
			output = os.path.join(self.logdir, 'recording_0.mp4')
			video.InitVideoRecorder(self.m_oDev)
			self.m_oDev.start_recording(output)
		else:
			self.m_oDev.start_recording()

	@RetryFunc()
	def RecordScreen(self):  # 开始录屏
		try:
			return self.StartRecording()
		except Exception as e:
			try:
				self.m_oDev.stop_recording(is_interrupted=True)
			except:
				pass
			raise e

	def Report(self):
		import file_lock
		sRet = report.ReportHtml(self.logdir)
		sCombineTxt = os.path.join(self.m_LogRoot, 'log.txt')
		if not os.path.exists(sCombineTxt):
			file = open(sCombineTxt, 'w')
			file.close()
		sMsg = json.dumps({'name': self.m_sLogDir, 'result': sRet})
		file_lock.WriteLogfile(sCombineTxt, sMsg)

	@property
	def logdir(self):
		return self._logdir

	@logdir.setter
	def logdir(self, value):
		self._logdir = value

	@property
	def code(self):
		return self._code

	@code.setter
	def code(self, value):
		self._code = value


def Init():
	if not os.path.exists(LOG_ROOT):
		os.mkdir(LOG_ROOT)


def Finish(sLogDir):
	print('test finish')
	sCombineLog = os.path.join(sLogDir, 'log.html')
	sCombineTxt = os.path.join(sLogDir, 'log.txt')
	with open(sCombineTxt, 'r') as f:
		lMsg = f.readlines()
	template_vars = {
		'patch_tag': os.path.basename(sLogDir),
		'files': [json.loads(line) for line in lMsg]
	}
	report.render('combine_log.html', sCombineLog, **template_vars)
	return sCombineLog

def NewCase(fPy, sLogDir, sDeviceNum, oQueue=None):
	"""实例化MyAirtestCase并绑定runCase方法"""
	if not os.path.exists(sLogDir):
		os.mkdir(sLogDir)
	with open(fPy, 'r', encoding="utf8") as f:
		code = f.read()
	obj = compile(code.encode("utf-8"), fPy, "exec")
	ns = {}
	ns["__file__"] = fPy
	oCase = MyAirtestCase(sDeviceNum, oQueue)
	sPyFileName = os.path.basename(fPy).replace(".py", "")
	oCase.code = {"code": obj, "ns": ns}
	oCase.Init(sLogDir, sPyFileName)
	return oCase


def InitSuite(lScripts):
	lSuite = []
	for sAirDir in lScripts:
		if sAirDir.endswith('air') and os.path.isdir(sAirDir):
			sPyName = os.path.basename(sAirDir).replace('air', 'py')
			lSuite.append(os.path.join(sAirDir, sPyName))
		else:
			for sAirDirSecond in os.listdir(sAirDir):
				sAirDirSecond = os.path.join(sAirDir, sAirDirSecond)
				if sAirDirSecond.endswith('air') and os.path.isdir(sAirDirSecond):
					sPyName = os.path.basename(sAirDirSecond).replace('air', 'py')
					lSuite.append(os.path.join(sAirDirSecond, sPyName))
	return lSuite


@CatchErr
def RunScript(sDeviceNum, sLogDir, oScripts):
	oTestSuite = unittest.TestSuite()
	if isinstance(oScripts, list):
		for fPy in oScripts:
			oCase = NewCase(fPy, sLogDir, sDeviceNum)
			oTestSuite.addTest(oCase)
	else:
		if oScripts.empty():
			return
		fPy = oScripts.get()
		oCase = NewCase(fPy, sLogDir, sDeviceNum, oScripts)
		oTestSuite.addTest(oCase)
	unittest.TextTestRunner(verbosity=0).run(oTestSuite)  # 运行脚本


def CreatePools(lAirScripts, lDevices, sPatchTag=None):
	lSuite = InitSuite(lAirScripts)
	if GetCfgData('mode') == '2':
		oAirQueue = multiprocessing.Queue()
		for sAirScript in lSuite:
			oAirQueue.put(sAirScript)
		oScripts = oAirQueue
	else:
		oScripts = lSuite
	pool = []
	sRunTime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
	sPatchTag = sPatchTag or sRunTime
	sLogDir = os.path.join(LOG_ROOT, sPatchTag)
	for sDeviceNum in lDevices:
		p = multiprocessing.Process(target=RunScript, args=(sDeviceNum, sLogDir, oScripts))
		p.start()
		time.sleep(3)
		pool.append(p)
	for p in pool:
		p.join()
	return Finish(sLogDir)

