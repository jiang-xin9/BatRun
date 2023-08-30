# -*- coding: utf-8 -*-
# https://blog.csdn.net/weixin_52040868
# 公众号：测个der
# 微信：qing_an_an

from UI.images import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QLabel, QWidget


class AnimatedGIFWindow(QWidget):
    def __init__(self):
        super().__init__()

    def initUI(self, addWidget):
        """启动UI"""
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFixedSize(220, 180)
        addWidget(self.label)   # 加入到窗口中去
        labelSize = self.label.size()

        # 创建一个QMovie来加载SVG动画
        self.movie = QMovie(':/header/加载.gif')  # 请替换为你的SVG文件路径
        self.movie.setCacheMode(QMovie.CacheAll)
        self.movie.setScaledSize(labelSize)
        self.label.setMovie(self.movie)

        self.showGif()

    def showGif(self):
        # 播放动画
        self.movie.start()

    def hideGif(self):
        """停止播放"""
        self.movie.stop()
        self.label.hide()
        self.setVisible(False)
