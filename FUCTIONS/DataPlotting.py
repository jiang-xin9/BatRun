# -*- coding: utf-8 -*-
# https://blog.csdn.net/weixin_52040868
# 公众号：测个der
# 微信：qing_an_an

import os
import pandas as pd
import matplotlib
matplotlib.use('Qt5Agg')  # 指定使用Qt5Agg后端
import matplotlib.pyplot as plt
from PyQt5.QtCore import QThread, pyqtSignal, QObject
from PyQt5.QtWidgets import QHBoxLayout,QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from FUCTIONS.Loading import AnimatedGIFWindow
from FUCTIONS.config import GetJsonFile
from FUCTIONS.DingDing import ReadJson


def SplitPath(FilePath):
    path = os.path.split(FilePath)[-1]
    return path


class LoadingCsv(QThread):
    DictValues = pyqtSignal(dict)

    def __init__(self, UI):
        super().__init__()
        self.UI = UI

    def run(self) -> None:
        csvHeader = self.ReadCsv()
        if csvHeader:
            self.DictValues.emit(csvHeader)

    def ReadCsv(self):
        """读取CSV"""
        ValuesDict = {"header": None, "Args": None, "args1": None, "args2": None, "args3": None}
        pathText = self.UI.GetDataPath.text()
        args1 = self.UI.Args1.currentText()
        args2 = self.UI.Args2.currentText()
        args3 = self.UI.Args3.currentText()
        if pathText:
            path = SplitPath(pathText)
            if path.endswith(".csv"):
                df = pd.read_csv(pathText, encoding='utf-8')
                header = df.columns.tolist()  # 放回头部信息
                if header:
                    ValuesDict["header"] = header
                if args1 and args2:
                    argsList1 = df[args1].values.tolist()
                    argsList2 = df[args2].values.tolist()
                    argsList3 = df[args3].values.tolist()
                    ValuesDict["Args"] = (argsList1, argsList2, argsList3)
                    ValuesDict["args1"] = args1
                    ValuesDict["args2"] = args2
                    ValuesDict["args3"] = args3
                return ValuesDict

class DataAnalysisQThread(QThread):
    InfoBatJump = pyqtSignal(dict)

    def __init__(self, UI):
        super().__init__()
        self.UI = UI

    def run(self) -> None:
        infoBattery = self.ReadJson()

        try:
            self.InfoBatJump.emit(infoBattery)
        except:
            pass

    def ReadJson(self):
        IntervalDict = {"first": 0, "second": 0, "third": 0, "fourth": 0}
        pathText = self.UI.GetDataPath.text()
        Files = GetJsonFile(pathText)
        path = SplitPath(pathText)
        if path.endswith(".json"):
            try:
                for file in Files:
                    data = ReadJson(file)
                    datas = data["PutInfo"]["JumpValue"]
                    for value in datas:
                        if 0 <= int(value[1]) <= 24:
                            IntervalDict["first"] += 1
                        if 25 <= int(value[1]) <= 49:
                            IntervalDict["second"] += 1
                        if 50 <= int(value[1]) <= 75:
                            IntervalDict["third"] += 1
                        if 76 <= int(value[1]) <= 100:
                            IntervalDict["fourth"] += 1
                return IntervalDict
            except:
                pass

class DataAnalysis(QObject):
    ShowWarningSignal = pyqtSignal(str)

    def __init__(self, ui):
        super(DataAnalysis, self).__init__()
        self.UI = ui
        self._attribute = {"layouts": {}, "figures": {}, "canvas": {}}

        # 使用字典来管理多个GIF实例
        self.Gifs = {
            'GIF4': AnimatedGIFWindow(),
            'GIF5': AnimatedGIFWindow(),
            'GIF6': AnimatedGIFWindow(),
            'GIF7': AnimatedGIFWindow()
        }
        self.Widget = {
            'widget_4': self.UI.widget_4,
            'widget_5': self.UI.widget_5,
            'widget_6': self.UI.widget_6,
            'widget_7': self.UI.widget_7
        }
        matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 黑体显示中文

        self.setupWidget(self.Widget["widget_4"], "figure4", "layout4", "canvas4")
        self.setupWidget(self.Widget["widget_5"], "figure5", "layout5", "canvas5")
        self.setupWidget(self.Widget["widget_6"], "figure6", "layout6", "canvas6")
        self.setupWidget(self.Widget["widget_7"], "figure7", "layout7", "canvas7")

        self.CsvData = LoadingCsv(self.UI)
        self.UI.BtnLoding.clicked.connect(self.startLoadingCsvThread)

        self.DataAnalysis = DataAnalysisQThread(self.UI)
        self.DataAnalysis.InfoBatJump.connect(self.BarChart)

        self.UI.BtnDatas.clicked.connect(self.startDataAnalysisThread)
        self.UI.BtnDatas.clicked.connect(self.startCsvChart)

    def setupWidget(self, widget, figure, layout, canvas):
        """需要先给属性赋值"""
        setattr(self, layout, QHBoxLayout())
        GetLyout = getattr(self, layout)
        widget.setLayout(GetLyout)
        setattr(self, figure, plt.figure())  # self.figure = plt.figure()
        GetFigure = getattr(self, figure)
        setattr(self, canvas, FigureCanvas(GetFigure))  # self.canvas = FigureCanvas(figure)
        GetCanvas = getattr(self, canvas)
        GetLyout.addWidget(GetCanvas)

        self._attribute["layouts"][layout] = GetLyout
        self._attribute["figures"][figure] = GetFigure
        self._attribute["canvas"][canvas] = GetCanvas

    @property
    def DataPath(self):
        PathText = self.UI.GetDataPath.text()
        return PathText

    def startLoadingCsvThread(self):
        """启动CSV线程"""
        PathText = self.DataPath
        if len(PathText) > 0:
            if ".csv" in PathText:
                self.CsvData.DictValues.connect(self.CsvCombox)
                self.CsvData.start()
        else:
            self.NoPath()

    def startCsvChart(self):
        """启动CSV绘图"""
        PathText = self.DataPath
        if ".csv" in PathText:
            self.clearPreviousCharts()
            self.Gifs["GIF4"].initUI(self.layout4.addWidget)
            self.Gifs["GIF6"].initUI(self.layout6.addWidget)
            self.Gifs["GIF7"].initUI(self.layout7.addWidget)
            self.CsvData.DictValues.connect(self.CsvLineChart1)
            self.CsvData.DictValues.connect(self.CsvLineChart2)
            self.CsvData.DictValues.connect(self.CsvLineChart3)
            self.CsvData.start()

    def startDataAnalysisThread(self):
        """启动图形加载线程"""
        PathText = self.DataPath
        if len(PathText) > 0:
            if ".json" in PathText:
                self.clearPreviousCharts()
                self.Gifs["GIF5"].initUI(self.layout5.addWidget)
                self.DataAnalysis.start()
        else:
            self.NoPath()

    def clearPreviousCharts(self):
        """清除之前的图表"""
        for canva, layout, widget, figure in zip(self._attribute["canvas"].values(),
                                      self._attribute["layouts"].values(),
                                      self.Widget.values(), self._attribute["figures"].values()):
            if canva:
                layout.removeWidget(widget)
                # canva.close()  # 关闭图表
                del canva  # 删除图表对象
            if figure:
                figure.clear()
                del figure  # 删除图表对象
            if widget:
                widget.setVisible(True)

    def BarChart(self, datas):
        """条形图"""
        self.Gifs["GIF5"].hideGif()
        # 从字典中提取键和值
        Y = list(datas.values())
        maxY = max(Y) + 10
        X = list(datas.keys())
        # 设置图表标题等绘图属性
        self.figure5.suptitle("info跳电次数/区间", fontsize=15)
        # 绘制饼图
        ax = self.figure5.add_subplot(111)
        # 设置Y轴刻度
        ax.set_ylim(0, maxY)  # 设置Y轴范围
        # 在每个条形图的头上添加数值显示
        # 为每个条形添加标签并设置颜色
        labels = ["0-24", "25-49", "50-74", "75-100"]
        colors = ['r', 'g', 'c', 'y']

        bars = ax.bar(X, Y)
        # 在每个条形图的头上添加数值显示
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax.annotate(f'{int(height)}',  # 显示整数值
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # 垂直偏移量
                        textcoords="offset points",
                        ha='center', va='bottom')
            # 设置不同的颜色和标签
            bar.set_color(colors[i])
            bar.set_label(labels[i])

        # 添加图例并指定位置
        ax.legend(loc="upper right")
        # 设置X轴和Y轴的说明
        ax.set_xlabel("区间/range")
        ax.set_ylabel("次数/number")
        # 更新图表
        self.canvas5.draw()

    def CsvCombox(self, datas):
        """CSV头部信息作为下拉框选项"""
        if self.UI.Args2.currentText():
            self.UI.Args2.clear()  # 判断是否有值，如果有则清空
            self.UI.Args1.clear()
            self.UI.Args3.clear()

        self.UI.Args2.addItems(datas["header"])
        self.UI.Args1.addItems(datas["header"])
        self.UI.Args3.addItems(datas["header"])

    def CsvLineChart1(self, datas):
        """Csv数据作图"""
        YList = []
        self.Gifs["GIF4"].hideGif()
        # 设置图表标题等绘图属性
        self.figure4.suptitle(datas["args1"], fontsize=15)
        # 绘制饼图
        ax = self.figure4.add_subplot(111)
        for i in range(len(datas["Args"][0])):
            YList.append(i)
        ax.plot(YList, datas["Args"][0], color='#FF5733')
        # 设置X轴和Y轴的说明
        ax.set_xlabel("第多少个/length")
        ax.set_ylabel("值/value")
        # 更新图表
        self.canvas4.draw()

    def CsvLineChart2(self, datas):
        """Csv数据作图"""
        YList = []
        self.Gifs["GIF6"].hideGif()
        # 设置图表标题等绘图属性
        self.figure6.suptitle(datas["args2"], fontsize=15)
        # 绘制饼图
        ax = self.figure6.add_subplot(111)
        for i in range(len(datas["Args"][1])):
            YList.append(i)
        ax.plot(YList, datas["Args"][1], color='#fd0127')
        # 设置X轴和Y轴的说明
        ax.set_xlabel("第多少个/length")
        ax.set_ylabel("值/value")
        # 更新图表
        self.canvas6.draw()

    def CsvLineChart3(self, datas):
        """Csv数据作图"""
        YList = []
        self.Gifs["GIF7"].hideGif()
        # 设置图表标题等绘图属性
        self.figure7.suptitle(datas["args3"], fontsize=15)
        # 绘制饼图
        ax = self.figure7.add_subplot(111)
        for i in range(len(datas["Args"][2])):
            YList.append(i)
        ax.plot(YList, datas["Args"][2], color='#54fd7c')
        # 设置X轴和Y轴的说明
        ax.set_xlabel("第多少个/length")
        ax.set_ylabel("值/value")
        # 更新图表
        self.canvas7.draw()

    def NoPath(self):
        self.ShowWarningSignal.emit("请输入文件的路径")

