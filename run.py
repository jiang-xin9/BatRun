# -*- coding: utf-8 -*-
# https://blog.csdn.net/weixin_52040868
# 公众号：测个der
# 微信：qing_an_an

from main import BatterySystem
from PyQt5.QtWidgets import QApplication

if __name__ == '__main__':
    app = QApplication([])
    Bat = BatterySystem()
    app.exec_()
