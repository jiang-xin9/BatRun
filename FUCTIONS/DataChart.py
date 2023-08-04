# -*- coding: utf-8 -*-
# https://blog.csdn.net/weixin_52040868
# 公众号：测个der
# 微信：qing_an_an

import datetime
import pyqtgraph as pg
from PyQt5.QtCore import QObject
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QVBoxLayout
from pyqtgraph import DateAxisItem, PlotDataItem, AxisItem, PlotWidget

class TimeAxisItem(AxisItem):
    def __init__(self, orientation, *args, **kwargs):
        super().__init__(orientation, *args, **kwargs)

    def tickStrings(self, values, scale, spacing):
        return [datetime.datetime.fromtimestamp(value).strftime("%H:%M:%S.%f")[:-3] for value in values]


class DataPlotWidget(QObject):
    def __init__(self, ui):
        super(DataPlotWidget, self).__init__()
        self.ui = ui
        # 创建布局
        self.layout = QVBoxLayout()
        self.ui.widget.setLayout(self.layout)

        # 创建绘图窗口
        self.plot_widget = PlotWidget(pen=pg.mkPen(color='w', width=2))
        # 禁止自动缩放
        self.plot_widget.getPlotItem().getViewBox().enableAutoRange(axis=pg.ViewBox.YAxis, enable=False)
        # ////////////////////添加十字线////////////////////////
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        self.plot_widget.addItem(self.vLine, ignoreBounds=True)
        self.plot_widget.addItem(self.hLine, ignoreBounds=True)

        # //////////////设置时间轴///////////////////////////
        self.date_axis = TimeAxisItem(orientation='bottom')
        self.date_axis.setLabel(text='Time')
        # /////////////数据////////////////////////////////
        self.timestamps = []
        self.data = []
        # ///////////////////设置样式表////////////////////
        pg.setConfigOptions(antialias=True)
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        self.plot = PlotDataItem(pen=pg.mkPen(color='w', width=2))  # 设置曲线的样式
        self.plot_widget.addItem(self.plot)
        # 在初始化时设置Y轴范围
        self.plot_widget.setYRange(0, 100)

        # 创建文本项
        self.text_item = pg.TextItem(anchor=(0, 1))
        self.plot_widget.addItem(self.text_item)
        self.text_item.hide()
        # 连接鼠标移动事件
        self.plot_widget.scene().sigMouseMoved.connect(self.mouseMoved)
        self.ui.Clear.clicked.connect(self.clearGraph)
        # 将绘图窗口添加到布局中
        self.layout.addWidget(self.plot_widget)

    def clearGraph(self):
        """清除数据"""
        self.timestamps.clear()
        self.data.clear()
        self.plot.clear()

    @staticmethod
    def find_nearest_index(x, data):
        if len(data) == 0:
            return None
        idx = min(range(len(data)), key=lambda i: abs(data[i] - x))
        return idx

    def mouseMoved(self, evt):
        if not self.timestamps:
            return
        pos = self.plot_widget.mapFromScene(evt)
        if self.plot_widget.sceneBoundingRect().contains(pos):
            mousePoint = self.plot_widget.plotItem.vb.mapSceneToView(pos)
            index = self.find_nearest_index(mousePoint.x(), self.timestamps)
            if index is not None:
                x_val = datetime.datetime.fromtimestamp(self.timestamps[index]).strftime("%H:%M:%S.%f")[:-3]
                y_val = self.data[index]
                # 设置字体大小
                font = QFont()
                font.setPointSize(12)  # 设置字体大小为12
                self.text_item.setFont(font)
                self.text_item.setText(f"x = {x_val}\ny = {y_val}", color=(0, 255, 0))
                self.text_item.setPos(mousePoint.x(), mousePoint.y())
                self.text_item.show()
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())
        else:
            self.text_item.hide()

    def update_data(self, value):
        """更新数据"""
        if value is not None:
            # 生成当前时间戳和随机整数数据
            timestamp = datetime.datetime.now().timestamp()
            data_point = float(value)
            # 将数据添加到列表
            self.timestamps.append(timestamp)
            self.data.append(data_point)

            # 限制元素数量为100个
            max_elements = 100
            if len(self.timestamps) > max_elements:
                self.timestamps = self.timestamps[-max_elements:]
                self.data = self.data[-max_elements:]

            # 更新图形数据
            self.plot.setData(x=self.timestamps, y=self.data)

            # 设置X轴范围为最后一分钟的数据
            if self.timestamps:
                xmin = max(timestamp - 60, min(self.timestamps))
                xmax = max(self.timestamps)
                self.plot_widget.setXRange(xmin, xmax)
            else:
                self.plot_widget.setXRange(0, 1)
            # # 实时计算Y轴范围
            # if self.data:
            #     self.y_min = min(self.data)
            #     self.y_max = max(self.data)
            #     y_margin = (self.y_max - self.y_min) * 0.1  # 为了美观，加入10%的上下边距
            #     self.plot_widget.setYRange(self.y_min - y_margin, self.y_max + y_margin)
            # 显示时间戳
            self.plot_widget.getPlotItem().setAxisItems({'bottom': self.date_axis})
