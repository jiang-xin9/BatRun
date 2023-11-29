# -*- coding: utf-8 -*-
# https://blog.csdn.net/weixin_52040868
# 公众号：测个der
# 微信：qing_an_an

from PyQt5.QtWidgets import QApplication
from main import BatterySystem

if __name__ == '__main__':
    app = QApplication([])
    Bat = BatterySystem()
    app.exec_()

# MONITOR_SYSTEM.
# Pyinstaller -F -w -i UI\images\favicon.ico --name="自动化电池监测V1.15.8"  run.py


"""
待优化:
1、Connect的UpdateUi的数据现在是一直读取的，可以改为一次性读取，减少读取性能
2、Connect的日志时间戳可以保持统一
3、
"""