@echo off

set /p folder=�������ļ�·�������ƣ�֧��ͨ�������

for %%v IN (%folder%) do (
	python myautosub.py %%v
)
echo ��Ļת�����