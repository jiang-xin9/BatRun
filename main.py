# -*- coding: utf-8 -*-
# https://blog.csdn.net/weixin_52040868
# 公众号：测个der
# 微信：qing_an_an

from UI.index import *
from FUCTIONS.Connect import *
from FUCTIONS.DingDing import ReadJson
from FUCTIONS.config import JsonPath
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtCore import Qt, QMimeData, QEvent
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QDrag

# 拖拽
class DragAndDropFilter(QObject):
    def __init__(self, source_widget, target_widget):
        super().__init__()
        self.source_widget = source_widget
        self.target_widget = target_widget
        self.source_widget.installEventFilter(self)

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

        if obj == self.target_widget and event.type() == QEvent.Drop:
            mime_data = event.mimeData().text()
            self.target_widget.setText(mime_data)
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
        # 启用UI线程
        self.uiThread = UiConnect(self.UI)
        self.uiThread.start()

        # 拖拽
        self.infoCommanddragdrop = DragAndDropFilter(self.UI.infoCommand, self.UI.textEdit_Send)
        self.batCommanddragdrop = DragAndDropFilter(self.UI.batCommand, self.UI.textEdit_Send)

        # 自动加载Json配置
        self.AutoAddJson()
        # ////////显示UI图
        self.show()

    def SignalFunction(self):
        """信号槽"""
        self.UI.stackedWidget.setCurrentWidget(self.UI.page_2)  # 默认显示
        self.UI.listWidget.currentRowChanged.connect(self.UiSecond)
        self.UI.textEdit_Send.installEventFilter(self)  # 链接键盘回车事件

    def Color(self):
        self.UI.Com_isOpenOrNot_Label.setStyleSheet("background: #a9fff5;")

    def AutoAddJson(self):
        """自动添加Json的配置电话、型号"""
        JsonDatas = ReadJson(JsonPath)
        self.UI.Iphone.setText(JsonDatas["Phone"])
        self.UI.TestDevices.setText(JsonDatas["Devices"])
        Custom1Mad = JsonDatas['Custom1']
        Custom2Mad = JsonDatas['Custom2']
        if Custom1Mad is not None:
            self.UI.Custom_1.setText(Custom1Mad)
        if Custom2Mad is not None:
            self.UI.Custom_2.setText(Custom2Mad)

    def UiSecond(self):
        """界面切换"""
        num = self.UI.listWidget.currentRow()
        if num == 0:
            self.UI.stackedWidget.setCurrentWidget(self.UI.page_2)
        elif num == 1:
            self.UI.stackedWidget.setCurrentWidget(self.UI.page)
        elif num == 2:
            QMessageBox.information(self, '提示信息', '待开发中')
        elif num == 3:
            QMessageBox.information(self, '提示信息', '待开发中')

    def closeEvent(self, event):
        reply = QMessageBox.question(self, '请确认', "请确认关闭", QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
            # 退出应用程序
            QApplication.quit()
        else:
            event.ignore()

    # 事件过滤器，监听键盘事件
    def eventFilter(self, obj, event):
        if obj == self.UI.textEdit_Send and event.type() == QKeyEvent.KeyPress:
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                # 将回车键事件转发给发送按钮，实现快速发送数据
                self.UI.Send_Button.click()
                return True
        return super().eventFilter(obj, event)
