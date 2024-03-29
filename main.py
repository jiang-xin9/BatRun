# -*- coding: utf-8 -*-
# https://blog.csdn.net/weixin_52040868
# 公众号：测个der
# 微信：qing_an_an

from UI.index import *
from FUCTIONS.Connect import *
from FUCTIONS.config import sys_, JsonPath
from FUCTIONS.DataPlotting import DataAnalysis
from FUCTIONS.ReadConfig import JSONREAD
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtCore import Qt, QMimeData, QEvent
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QFileDialog
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QDrag

# 拖拽
class DragAndDropFilter(QObject):
    def __init__(self, source_widget, target_widget):
        super().__init__()
        self.source_widget = source_widget  # QLabel
        self.target_widget = target_widget  # QLineEdit
        self.source_widget.installEventFilter(self)
        self.target_widget.installEventFilter(self)
        self.is_dropped = False

    def eventFilter(self, obj, event):
        if obj == self.source_widget and event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                mime_data = QMimeData()
                mime_data.setText(self.source_widget.text())

                drag = QDrag(self.source_widget)
                drag.setMimeData(mime_data)

                result = drag.exec_(Qt.MoveAction)
                if result == Qt.MoveAction:
                    return True

        if obj == self.target_widget:
            if event.type() == QEvent.Drop:
                mime_data = event.mimeData().text()

                # 如果有文本则先清除
                if self.is_dropped:
                    self.target_widget.clear()

                self.target_widget.setText(mime_data)
                self.target_widget.selectAll()
                self.is_dropped = True
                return True
            elif event.type() == QEvent.DragEnter:
                # 接受拖动事件以启用拖放
                event.accept()
                return True

        return super().eventFilter(obj, event)

class BatterySystem(QMainWindow):

    def __init__(self):
        super(BatterySystem, self).__init__()
        # //////////UI_Main
        self.UI = Ui_MainWindow()
        self.UI.setupUi(self)

        # 只读模式
        self.UI.textEdit_Recive.setReadOnly(True)
        # 调用信号方法
        self.SignalFunction()
        self.Color()        # 单独设置一个颜色
        self.StartThread()  # 启用线程
        self.Drag()         # 启用拖拽
        # 自动加载Json配置
        self.AutoAddJson()
        # ////////显示UI图
        self.show()

    def StartThread(self):
        # 启用数据线程
        self.uiThread = UiConnect(self.UI)
        self.uiThread.start()
        # 启动图形加载线程
        self.Analysis = DataAnalysis(self.UI)
        self.Analysis.ShowWarningSignal.connect(self.showWarningMessage)

    def Drag(self):
        # 拖拽
        self.infoCommanddragdrop = DragAndDropFilter(self.UI.infoCommand, self.UI.textEdit_Send)
        self.batCommanddragdrop = DragAndDropFilter(self.UI.batCommand, self.UI.textEdit_Send)

    def SignalFunction(self):
        """信号槽"""
        self.UI.stackedWidget.setCurrentWidget(self.UI.page_2)  # 默认显示
        self.UI.listWidget.currentRowChanged.connect(self.UiSecond)
        self.UI.textEdit_Send.installEventFilter(self)  # 链接键盘回车事件
        self.UI.BtnDataPath.clicked.connect(self.OpenFile)  # 打开文件

    def Color(self):
        self.UI.Com_isOpenOrNot_Label.setStyleSheet("background: #a9fff5;")
        TextStyle = """
        QMessageBox QPushButton[text="&Yes"] {
            qproperty-text: "是";
        }
        QMessageBox QPushButton[text="&No"] {
            qproperty-text: "否";
        }
        QMessageBox {messagebox-question-icon: url(:/header/警告.png);}
        """
        self.setStyleSheet(TextStyle)
        self.UI.Com_isOpenOrNot_Label.setStyleSheet("background: {};".format("#ff4545"))
        self.UI.Com_Close_Button.setEnabled(False)  # 设置起始不可选择

    def AutoAddJson(self):
        """自动添加Json的配置电话、型号"""
        Datas = JSONREAD()
        self.AutoSetText(self.UI.Custom_1, Datas.getData('Custom1'))
        self.AutoSetText(self.UI.Custom_2, Datas.getData('Custom2'))
        self.AutoSetText(self.UI.infoCommand, Datas.getData('Command1'))
        self.AutoSetText(self.UI.batCommand, Datas.getData('Command2'))
        self.AutoSetText(self.UI.Iphone, Datas.getData('Phone'))
        self.AutoSetText(self.UI.DevicesName, Datas.getData('Devices'))

    def AutoSetText(self, UiEelement, value):
        """自动写入或替换参数"""
        if value is not None:
            UiEelement.setText(value)

    def OpenFile(self):
        """打开数据处理文件"""
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(None, "选择文件", "",
                                                  "All Files (*);;Text Files (*.txt);;Image Files (*.log)",
                                                  options=options)
        if fileName:
            self.UI.GetDataPath.setText(fileName)

    def UiSecond(self):
        """界面切换"""
        num = self.UI.listWidget.currentRow()
        if num == 0:
            self.UI.stackedWidget.setCurrentWidget(self.UI.page_2)
        elif num == 1:
            self.UI.stackedWidget.setCurrentWidget(self.UI.page)
        elif num == 2:
            """饼状图数据占比，平均放电时长。折线图的电机电压占比，电流占比"""
            self.UI.stackedWidget.setCurrentWidget(self.UI.page_4)
        elif num == 3:
            self.UI.stackedWidget.setCurrentWidget(self.UI.page_3)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, '请确认', "请确认关闭", QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
            # 退出应用程序
            QApplication.quit()
        else:
            event.ignore()

    def showWarningMessage(self, message):
        QMessageBox.warning(self, "警告", message)

    # 事件过滤器，监听键盘事件
    def eventFilter(self, obj, event):
        if obj == self.UI.textEdit_Send and event.type() == QKeyEvent.KeyPress:
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                # 将回车键事件转发给发送按钮，实现快速发送数据
                self.UI.Send_Button.click()
                return True
        return super().eventFilter(obj, event)
