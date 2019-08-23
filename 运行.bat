@echo off 
del std.log
start cmd /K  "python main.py>>std.log"