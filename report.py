# -*- coding: utf-8 -*-
# Leo Zeng
import os
import types
import shutil
import json
import airtest.report.report as R

from airtest.utils.compat import decode_path
from constant import BASEPATH

TXT_FILE = "log.txt"
HTML_FILE = "log.html"
HTML_TPL = "log_template.html"
MY_STATIC_DIR = 'report_static'
STATIC_DIR = os.path.dirname(R.__file__)


def get_script_info(script_path):
	script_name = os.path.basename(script_path)
	result_json = {"name": script_name, "author": 'Leo', "title": script_name, "desc": None}
	return json.dumps(result_json)


def _make_export_dir(self):
	dirpath = BASEPATH
	logpath = self.script_root
	# copy static files
	for subdir in ["css", "fonts", "image", "js"]:
		dist = os.path.join(dirpath, MY_STATIC_DIR, subdir)
		if os.path.exists(dist) and os.path.isdir(dist):
			continue
		shutil.rmtree(dist, ignore_errors=True)
		self.copy_tree(os.path.join(STATIC_DIR, subdir), dist)

	return dirpath, logpath


def render(template_name, output_file=None, **template_vars):
	import io
	import jinja2
	""" 用jinja2渲染html"""
	env = jinja2.Environment(
		loader=jinja2.FileSystemLoader(BASEPATH),
		extensions=(),
		autoescape=True
	)
	template = env.get_template(template_name)
	html = template.render(**template_vars)

	if output_file:
		with io.open(output_file, 'w', encoding="utf-8") as f:
			f.write(html)
		print(output_file)

	return html


def _translate_screen(self, step, code):
	import six
	if step['tag'] != "function":
		return None
	screen = {
		"src": None,
		"rect": [],
		"pos": [],
		"vector": [],
		"confidence": None,
	}

	for item in step["__children__"]:
		if item["data"]["name"] == "try_log_screen" and isinstance(item["data"].get("ret", None), six.text_type):
			src = item["data"]['ret']
			if self.export_dir:  # all relative path
				# src = os.path.join(LOGDIR, src)  # Leo 2019-6-20
				screen['_filepath'] = src
			else:
				# screen['_filepath'] = os.path.abspath(os.path.join(self.log_root, src))  # Leo 2019-6-20
				screen['_filepath'] = src
			screen['src'] = screen['_filepath']
			break

	display_pos = None

	for item in step["__children__"]:
		if item["data"]["name"] == "_cv_match" and isinstance(item["data"].get("ret"), dict):
			cv_result = item["data"]["ret"]
			pos = cv_result['result']
			if self.is_pos(pos):
				display_pos = [round(pos[0]), round(pos[1])]
			rect = self.div_rect(cv_result['rectangle'])
			screen['rect'].append(rect)
			screen['confidence'] = cv_result['confidence']
			break

	if step["data"]["name"] in ["touch", "assert_exists", "wait", "exists"]:
		# 将图像匹配得到的pos修正为最终pos
		if self.is_pos(step["data"].get("ret")):
			display_pos = step["data"]["ret"]
		elif self.is_pos(step["data"]["call_args"].get("v")):
			display_pos = step["data"]["call_args"]["v"]

	elif step["data"]["name"] == "swipe":
		if "ret" in step["data"]:
			screen["pos"].append(step["data"]["ret"][0])
			target_pos = step["data"]["ret"][1]
			origin_pos = step["data"]["ret"][0]
			screen["vector"].append([target_pos[0] - origin_pos[0], target_pos[1] - origin_pos[1]])

	if display_pos:
		screen["pos"].append(display_pos)
	return screen


def report(self, template_name, output_file=None, record_list=None):
	"""替换LogToHtml中的report方法"""
	self._load()
	steps = self._analyse()
	# 修改info获取方式
	info = json.loads(get_script_info(self.script_root))
	if self.export_dir:
		_, self.log_root = self._make_export_dir()
	# output_file = os.path.join(self.script_root, HTML_FILE)
	# self.static_root = "static/"
	if not record_list:
		record_list = [f for f in os.listdir(self.log_root) if f.endswith(".mp4")]
	records = [f if self.export_dir else os.path.basename(f) for f in record_list]

	if not self.static_root.endswith(os.path.sep):
		self.static_root = self.static_root.replace("\\", "/")
		self.static_root += "/"
	data = {}
	data['steps'] = steps
	data['name'] = os.path.basename(self.script_root)
	data['scale'] = self.scale
	data['test_result'] = self.test_result
	data['run_end'] = self.run_end
	data['run_start'] = self.run_start
	data['static_root'] = self.static_root
	data['lang'] = self.lang
	data['records'] = records
	data['info'] = info
	return render(template_name, output_file, **data)


def get_result(self):
	return self.test_result


def main(args):
	# script filepath
	path = decode_path(args.script)
	record_list = args.record or []
	log_root = decode_path(args.log_root) or path
	static_root = args.static_root or STATIC_DIR
	static_root = decode_path(static_root)
	export = args.export
	lang = args.lang if args.lang in ['zh', 'en'] else 'zh'
	plugins = args.plugins
	# gen html report
	rpt = R.LogToHtml(path, log_root, static_root, export_dir=export, lang=lang, plugins=plugins)
	# override methods
	rpt._make_export_dir = types.MethodType(_make_export_dir, rpt)
	rpt.report = types.MethodType(report, rpt)
	rpt.get_result = types.MethodType(get_result, rpt)
	rpt._translate_screen = types.MethodType(_translate_screen, rpt)
	rpt.report(HTML_TPL, output_file=args.outfile, record_list=record_list)
	return rpt.get_result()


def ReportHtml(subdir):
	import argparse
	oArgs = argparse.Namespace(script=None, device=None, outfile=None, static_root='../../../%s' % MY_STATIC_DIR,
							   log_root=None, record=None, export=True, lang=None, plugins=None)
	oArgs.script = subdir
	oArgs.outfile = os.path.join(subdir, HTML_FILE)
	result = main(oArgs)
	sRet = 'PASS' if result else 'FAIL'
	return sRet
