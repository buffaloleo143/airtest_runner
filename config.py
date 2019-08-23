# -*- coding: utf-8 -*-
# Leo Zeng

SCRIPTS_LIST = []  # 要运行的脚本名称列表，如：['SzwyMobile1014-1036.air','hh.air']，无内容则按顺序运行scripts目录下所有脚本

DEVICE_NUM = ['all']  # 设备id，格式为：['PBV0216727000183'，'8TFDU18926001948']，为空默认选取电脑上连的第一台设备，['all']则运行所有设备

MODE = 1  # 1:每台设备各自运行所有脚本，2：所有设备分配运行所有脚本

PLATFORM = 'Android'  # 平台为Windows时设备号需填窗口句柄


