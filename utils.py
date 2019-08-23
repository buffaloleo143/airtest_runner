# -*- coding: utf-8 -*-
# Leo Zeng
import os
import time
import logging
import zipfile
import traceback
import requests

from airtest.core.android.adb import ADB
from functools import wraps


def GetValidDevices():
	"""获取本地连接的设备号列表"""
	lData = ADB().devices('device')
	lPositiveDevices = [item[0] for item in lData]
	return lPositiveDevices


def GetDeviceNum():
	from config import DEVICE_NUM
	lDevice = GetValidDevices()
	if not DEVICE_NUM:
		return [lDevice[0]]
	elif 'all' in DEVICE_NUM:
		return lDevice
	else:
		return DEVICE_NUM


def ZipFile(sExportPath):
	"""压缩报告"""
	# sPatchTag = os.path.basename(sExportPath)
	sZipFile = sExportPath + '.zip'  # 压缩后文件夹的名字
	z = zipfile.ZipFile(sZipFile, 'w', zipfile.ZIP_DEFLATED)  # 参数一：文件夹名
	for dirpath, dirnames, filenames in os.walk(sExportPath):
		fpath = dirpath.replace(sExportPath, '')  # 这一句很重要，不replace的话，就从根目录开始复制
		fpath = fpath and fpath + os.sep or ''
		for filename in filenames:
			z.write(os.path.join(dirpath, filename), fpath + filename)
	z.close()
	return sZipFile


def PostZipFile(sZipFile):
	sPostUrl = ''  # 上传路径
	sName = os.path.basename(sZipFile)
	file = {sName: open(sZipFile, 'rb')}
	headers = {
		'Connection': 'keep-alive',
		'Host': '10.32.17.71:8001',
		'Upgrade-Insecure-Requests': '1',
	}
	r = requests.post(sPostUrl, files=file, headers=headers)
	if r.status_code == 200:
		Logging('报告上传成功')
	else:
		Logging('报告上传失败')
		Logging('状态码：%s' % r.status_code)
		Logging(r.content)


def UnzipFile(sZipFile):
	sDir, sZipFileName = os.path.split(sZipFile)
	z = zipfile.ZipFile(sZipFile, 'r')
	sPath = os.path.join(sDir, sZipFileName.replace('.zip', ''))
	if not os.path.exists(sPath):
		os.mkdir(sPath)
	z.extractall(path=sPath)
	z.close()


def PostReport2TestWeb(sExportPath):
	sZipFile = ZipFile(sExportPath)
	PostZipFile(sZipFile)
	os.remove(sZipFile)


def Logging(sMsg):
	logging.error(sMsg)
	print(sMsg)


def CatchErr(func):
	@wraps(func)
	def MyWrapper(*args,**kwargs):
		try:
			return func(*args,**kwargs)
		except Exception as e:
			traceback.print_exc()
			Logging(e)

	return MyWrapper


def RetryFunc(iTimes=3, iSec=2):
	def CatchErr(func):
		@wraps(func)
		def MyWrapper(*args, **kwargs):
			for _ in range(iTimes):
				try:
					return func(*args, **kwargs)
				except Exception as e:
					Logging(e)
					time.sleep(iSec)
					continue

		return MyWrapper

	return CatchErr
