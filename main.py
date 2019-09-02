# -*- coding: utf-8 -*-
# Leo Zeng
import os
import utils


def Run(lAirScripts, lDevices, sPatchTag=None):
	import runner
	runner.Init()
	return runner.CreatePools(lAirScripts, lDevices, sPatchTag)


def main():
	sPath = utils.GetCfgData('scripts_root') or os.path.abspath('scripts')
	lScripts = utils.GetCfgData('scripts').split(',')
	lAirScripts = [os.path.join(sPath, sAir) for sAir in lScripts] or [sPath]
	lDevices = utils.GetDeviceNum()
	if not lDevices:
		sError = u'无设备，请查看设备是否连接，设备权限是否开启'
		utils.Logging(sError)
		return
	return Run(lAirScripts, lDevices)


if __name__ == '__main__':
	main()
