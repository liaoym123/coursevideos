@echo off

set /p folder=请输入文件路径和名称（支持通配符）：

for %%v IN (%folder%) do (
	python myautosub.py %%v
)
echo 字幕转换完成