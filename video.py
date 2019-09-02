# -*- coding: utf-8 -*-
# Leo Zeng
'''
pc端录屏
'''
import types
import numpy
import cv2
import threading

from airtest import aircv


INTERVAL = 0.05
FPS = 10


def start_recording(self, output):
	rect = self.get_rect()  # 获得分辨率
	bbox = (ToEvenNum(rect.left), ToEvenNum(rect.top), ToEvenNum(rect.right), ToEvenNum(rect.bottom))  # 虚拟机中需要是偶数
	# bbox = (rect.left, rect.top, rect.right, rect.bottom)
	size = (bbox[2] - bbox[0], bbox[3] - bbox[1])
	width, heigh = size
	self.video = cv2.VideoWriter(output, cv2.VideoWriter_fourcc(*'X264'), FPS, (width, heigh))
	self.m_Lock = threading.Lock()
	self.m_bRecording = True
	self.LoopTimer = threading.Timer(INTERVAL, self.Record, [bbox])
	self.LoopTimer.start()


def stop_recording(self, output):
	self.m_Lock.acquire()
	print('Record end')
	self.m_bRecording = False
	if self.LoopTimer:
		self.LoopTimer.cancel()
		self.LoopTimer = None
	self.video.release()
	self.m_Lock.release()


def Record(self, bbox):
	import time
	import airtest.core.win.screen as screen
	threading.current_thread.name = 'recording'
	while True:
		if not self.m_bRecording:
			break
		self.m_Lock.acquire()
		print('Recording...', (bbox[2] - bbox[0], bbox[3] - bbox[1]))
		try:
			im = aircv.crop_image(screen.screenshot(None), bbox)
			self.video.write(numpy.array(im))  # 将img convert ndarray
		except:
			pass
		self.m_Lock.release()
		time.sleep(INTERVAL)


def InitVideoRecorder(oDevices):
	if oDevices.__class__.__name__ == "Windows":
		oDevices.m_Lock = threading.Lock()
		if not hasattr(oDevices, 'start_recording'):
			oDevices.start_recording = types.MethodType(start_recording, oDevices)
		if not hasattr(oDevices, 'stop_recording'):
			oDevices.stop_recording = types.MethodType(stop_recording, oDevices)
		if not hasattr(oDevices, 'Record'):
			oDevices.Record = types.MethodType(Record, oDevices)


def ToEvenNum(iNum):
	if iNum % 2 == 0:
		return iNum
	else:
		return iNum + 1
