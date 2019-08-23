# -*- coding: utf-8 -*-
# Leo Zeng
import os
import utils

from config import *



def Run(lAirScripts, lDevices, sPatchTag=None):
	import runner
	runner.Init()
	runner.CreatePools(lAirScripts, lDevices, sPatchTag)


def main():
	sBase = os.path.dirname(os.path.abspath(__file__))
	sPath = os.path.join(sBase, 'scripts')
	lAirScripts = [os.path.join(sPath, sAir) for sAir in SCRIPTS_LIST] or [sPath]
	lDevices = utils.GetDeviceNum()
	if not lDevices:
		sError = u'无设备，请查看设备是否连接，设备权限是否开启'
		utils.Logging(sError)
		return
	Run(lAirScripts, lDevices)



if __name__ == '__main__':
	main()

