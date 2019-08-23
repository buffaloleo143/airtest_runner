# -*- coding: utf-8 -*-
# Leo Zeng
'''
这部分代码多来自网上，linux部分未验证
'''
import os
import random
import utils


class CFileLock(object):

	def __init__(self, filename):
		self.filename = filename

	@utils.RetryFunc(iTimes=3, iSec=random.randint(1, 5))
	def Write(self, msg):
		"""进程比较多的情况下数据容易出现问题，目前还没想到较好的办法"""
		self.handle = open(self.filename, 'a+')
		self.acquire()
		self.handle.write(msg + "\n")
		self.release()
		self.handle.close()

	def acquire(self):
		# 给文件上锁
		if os.name == 'nt':
			import win32con
			import win32file
			import pywintypes
			LOCK_EX = win32con.LOCKFILE_EXCLUSIVE_LOCK
			overlapped = pywintypes.OVERLAPPED()
			hfile = win32file._get_osfhandle(self.handle.fileno())
			win32file.LockFileEx(hfile, LOCK_EX, 0, -0x10000, overlapped)
		elif os.name == 'posix':
			import fcntl
			LOCK_EX = fcntl.LOCK_EX
			fcntl.flock(self.handle, LOCK_EX)

	def release(self):
		# 文件解锁
		if os.name == 'nt':
			import win32file
			import pywintypes
			overlapped = pywintypes.OVERLAPPED()
			hfile = win32file._get_osfhandle(self.handle.fileno())
			win32file.UnlockFileEx(hfile, 0, -0x10000, overlapped)
		elif os.name == 'posix':
			import fcntl
			fcntl.flock(self.handle, fcntl.LOCK_UN)


def WriteLogfile(sLogFile, sMsg):
	CFileLock(sLogFile).Write(sMsg)
