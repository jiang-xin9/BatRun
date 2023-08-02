# -*- coding: utf-8 -*-
# https://blog.csdn.net/weixin_52040868
# 公众号：测个der
# 微信：qing_an_an

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent
from UI.index import *
from FUCTIONS.Connect import *
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox


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

        # ////////显示UI图
        self.show()

    def SignalFunction(self):
        """信号槽"""
        self.UI.stackedWidget.setCurrentWidget(self.UI.page_2)  # 默认显示
        self.UI.listWidget.currentRowChanged.connect(self.UiSecond)
        self.UI.textEdit_Send.installEventFilter(self)  # 链接键盘回车事件

    def Color(self):
        self.UI.Com_isOpenOrNot_Label.setStyleSheet("background: #a9fff5;")

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
