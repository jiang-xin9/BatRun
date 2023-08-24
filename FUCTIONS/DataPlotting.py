# -*- coding: utf-8 -*-
# https://blog.csdn.net/weixin_52040868
# 公众号：测个der
# 微信：qing_an_an

import matplotlib
import matplotlib.pyplot as plt
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class DataAnalysis(QObject):
    def __init__(self, ui):
        super(DataAnalysis, self).__init__()
        self.UI = ui

        matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 黑体显示中文
        self.layout4 = QVBoxLayout()
        self.UI.widget_4.setLayout(self.layout4)
        self.layout7 = QVBoxLayout()
        self.UI.widget_7.setLayout(self.layout7)

        # 创建一个Matplotlib图形画布并添加到布局中
        self.canvas = MplCanvas(self.UI.widget_4)
        self.layout4.addWidget(self.canvas)

        self.canvas7 = MplCanvas(self.UI.widget_7)
        self.layout7.addWidget(self.canvas7)
        self.bing()
        self.zhe()

    def bing(self):
        value = [10,30,40,20]
        datas = ['C','JAVA','Python','GO']
        colors = ['yellow','red','blue','green']
        self.canvas.axes.clear()  # 清除之前的图形
        self.canvas.axes.set_title("TESTTING", fontdict={'size': 20})
        explode = [0.1, 0.1, 0, 0]
        self.canvas.axes.pie(value, labels=datas, colors=colors, explode=explode,
                             shadow=True, autopct='%1.1f%%', startangle=180)
        self.canvas.draw()

    def bing1(self):
        pass

    def zhe(self):
        x = [1, 2, 3, 4, 5]
        y = [10, 25, 18, 12, 30]
        self.canvas7.axes.clear()  # 清除之前的图形
        self.canvas7.axes.set_title("TESTTING", fontdict={'size': 20})
        self.canvas7.axes.plot(x, y, marker='o', linestyle='-')
        # 添加网格线
        self.canvas7.axes.grid(True)
        self.canvas7.axes.set_xlabel("X轴标签")
        self.canvas7.axes.set_ylabel("Y轴标签")

        self.canvas7.draw()


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.figure, self.axes = plt.subplots()
        super(MplCanvas, self).__init__(self.figure)
        self.setParent(parent)