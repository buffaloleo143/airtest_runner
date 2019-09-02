# airtest_runner
采用python多进程，多设备并行批量airtest脚本

我的运行环境为python3.7，其他依赖包版本在requirements.txt文件里
python2的话需要自己调整部分代码做兼容；

懒得安装环境和二次开发的可以直接到release下载exe文件熟肉使用

下载点这里：[releases](https://github.com/buffaloleo143/airtest_runner/releases)

## 1.1.exe使用步骤
	（1）.双击打开airtest启动器.exe，进入程序主界面
	（2）.左边选取安卓设备，右边点击‘选取脚本路径’按钮，选择脚本所在的根目录，选好后可在右边窗口选取要运行的脚本；
	（3）.选取模式，模式分两种，在【2.config.ini 全局配置】中会有介绍；
	（4）.点击启动按钮，通过控制台查看运行情况，静静地等待运行结果；
	（5）.运行结束后会有一个弹窗提示，点击ok按钮查看该次的报告；
	（6）.历史报告在logs_root文件夹下

## 1.2.源码使用步骤

		（1）.把自己写的air脚本放置到scripts文件夹下
		（2）.打开config.ini，根据注释填写运行模式、脚本名称及设备序列号；
		（3）.运行main.py文件，推荐用pycharm运行，全局环境下也可以直接用 运行.bat 来运行；
		（4）.等待运行结果，自动生成的报告将在logs_root文件夹；注：报告依赖airtest的静态，这里不建议更改报告的文件结构
 
## 2.config.ini 全局配置

```python
[baseconf]
scripts_root = scripts
scripts = 
devices = all
mode = 1
platform = Android

```
scripts_root  #脚本根目录，默认为工程目录下的scripts文件夹

scripts   # 要运行的脚本名称列表，半角逗号连接，如：SzwyMobile1014-1036.air,hh.air，无内容则按顺序运行scripts目录下所有脚本

devices = all  # 设备id，半角逗号连接，格式为：PBV0216727000183，8TFDU18926001948，为空默认选取电脑上连的第一台设备，all则运行所有设备

mode = 1  # 1:每台设备各自运行所有脚本，2：所有设备分配运行所有脚本

platform = Android  # 平台为Windows时设备号需填窗口句柄

这里提供两种模式：
 - mode = 1：每台设备各自运行所有要跑的脚本，即批量并行相同脚本，报告数量=脚本数量x设备数量，适合做兼容测试；
 - mode = 2：采用消息队列，将所有要跑的脚本逐一以分配的方式给空闲的设备运行，报告数量=脚本数量，适合做功能的回归测试；


## 3.runner.py 
利用multiprocessing根据设备数量生成进程池，单个进程里再利用unittest生成每一个脚本的测试用例

## 4.report.py
根据模板生成单个airtest脚本测试的报告，重写了airtest源码中若干源码，减少报告中的静态资源的路径依赖

## 5.utils.py
该模块提供了一些通用接口，其中还包括压缩本地报告上传至云平台的代码，上传地址需使用者自己填写

```python
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
```
PostReport2TestWeb的参数为报告的绝对路径

## 5.video.py
该模块利用OpenCV实现Windows端的录屏功能，弥补了airtest在PC运行时无法录屏的缺点。其中视频的帧率和录制时间间隔可以自己调整至一个合适的数值

## 6.file_lock.py
为了记录单次测试里每一个报告的聚合结果，这里采用将结果写入临时文件的方式。由于存在多条进程同时对一个文件进行读写操作的情况，我只是简单得用了文件锁来处理了一下。

经测试在windows端进程较多的情况下仍会出现结果写入异常的情况，条件足够的话建议将结果保存在自己的数据库中。
