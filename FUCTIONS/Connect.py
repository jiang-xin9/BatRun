# -*- coding: utf-8 -*-
# https://blog.csdn.net/weixin_52040868
# 公众号：测个der
# 微信：qing_an_an
import logging
import re
import serial
import datetime
import serial.tools.list_ports
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QTextCursor
from FUCTIONS.config import sys_
from FUCTIONS.DataChart import *
from FUCTIONS.DINGDING import DingTalkSendMsg


class SerConnect:

    def Connect(self, COM, port=115200, timeout=1, bytesize=8):
        """连接串口"""
        if COM:
            # 连接串口
            self.ser = serial.Serial(COM, port, timeout=timeout, bytesize=bytesize)
            if self.ser.isOpen():
                return self.ser

    def disConnect(self):
        """断开连接"""
        if hasattr(self, "ser"):
            self.ser.close()

    def Coms(self):
        """获取串口信息"""
        available_ports = list(serial.tools.list_ports.comports())
        if available_ports:
            return available_ports
        else:
            return []

    def WriteInfo(self, command):
        """写入数据"""
        if hasattr(self, "ser") and self.ser.writable():
            self.ser.write(command.encode("utf-8"))

    def ReadeValue(self):
        """读取全部数据"""
        if hasattr(self, "ser") and self.ser.readable():
            datas = self.ser.read(1024).decode("utf-8")
            return datas

    def ReadLineValue(self):
        """读取一行数据"""
        if hasattr(self, "ser") and self.ser.readable():
            try:
                datas = self.ser.readline().decode("utf-8")
                if datas:
                    # print(datas.strip())
                    return datas
            except:
                pass


class UiConnect(QThread):
    data_received = pyqtSignal(str)

    def __init__(self, UI):
        super(UiConnect, self).__init__()
        self.ser = SerConnect()
        self.UI = UI

        # 创建LogStorageThread实例，并保存为成员变量
        self.log_storage_thread = LogStorageThread()
        self.log_storage_thread.start()

        self.dingding = DingTalkSendMsg()
        self.currentTime = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        self.startTime = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.VolList = []
        self.CurList = []
        self.CapList = []
        self.JumpNum = 0
        self.number = 0

        # 创建定时器
        self.timer = QTimer()
        # 清除内容
        self.timer.timeout.connect(self.TextEditClear)
        self.timer.start(30000)  # 每隔30秒触发一次定时器槽函数

    def run(self) -> None:
        self.CreateSignalSlot()

    def CreateSignalSlot(self):
        """信号与槽"""
        self.UI.Com_Refresh_Button.clicked.connect(self.RefreshCOM)
        self.UI.Com_Open_Button.clicked.connect(self.OpenCOM)
        self.UI.Com_Close_Button.clicked.connect(self.CloseCOM)
        self.UI.Send_Button.clicked.connect(self.SendData)
        self.UI.ClearButton.clicked.connect(self.TextEditClear)

    def RefreshCOM(self):
        """刷新串口号与自动写入波特率"""
        coms = self.ser.Coms()
        self.UI.Com_Name_Combo.clear()  # 清空原有选项
        if coms:
            for com in coms:
                # 将串口名称加入下拉列表
                self.UI.Com_Name_Combo.addItem(com.device)
        # 设置默认值
        self.UI.Com_Baud_Combo.setCurrentText("115200")

    def BtnSetUp(self, agrs: bool, txt: str, color: str):
        """按钮状态设置"""
        self.UI.Com_Open_Button.setEnabled(agrs)
        self.UI.Com_Refresh_Button.setEnabled(agrs)
        self.UI.Com_Name_Combo.setEnabled(agrs)
        self.UI.Com_Baud_Combo.setEnabled(agrs)
        self.UI.Com_isOpenOrNot_Label.setText(txt)
        self.UI.Com_isOpenOrNot_Label.setStyleSheet("background: {};".format(color))

    def OpenCOM(self):
        """打卡串口"""
        comName = self.UI.Com_Name_Combo.currentText()
        comBaud = int(self.UI.Com_Baud_Combo.currentText())
        if comBaud and comName:
            self.ser.Connect(COM=comName, port=comBaud)
            self.UI.Com_Close_Button.setEnabled(True)
            self.BtnSetUp(False, '已打开', '#8dff7c')

            # 在串口连接建立后启动 WhileReadThread
            self.while_read_thread = WhileReadThread(self.ser, self.UI)
            self.while_read_thread.data_received.connect(self.handle_data_received)
            self.while_read_thread.update_ui_signal.connect(self.update_ui)  # 连接新信号到槽函数
            self.while_read_thread.start()

    def CloseCOM(self):
        """关闭串口"""
        # 首先停止WhileReadThread线程
        if hasattr(self, "while_read_thread"):
            self.while_read_thread.stop()

        self.ser.disConnect()
        self.UI.Com_Close_Button.setEnabled(False)
        self.BtnSetUp(True, "已关闭", "#ff4545")

    def SendData(self):
        """发送命令"""
        command = self.UI.textEdit_Send.text()
        if isinstance(command, str):
            self.ser.WriteInfo(command + "\n")

    def TextEditClear(self):
        """清除内容"""
        if self.UI.textEdit_Send.text():
            self.UI.textEdit_Send.clear()
            self.UI.textEdit_Send.setText("info")
            self.SendData()
        text = self.UI.textEdit_Recive
        if text:
            self.UI.textEdit_Recive.clear()
        else:
            return


    def update_ui(self, datas):
        """用于更新UI元素的槽函数"""
        # 正则提取数据，这里是info数据
        volValue = re.search(r".*vol\s*:\s*(\d*)\s*", datas)
        curValue = re.search(r".*cur\s*:\s*(\d*)\s*", datas)
        # info电量
        infoCapValue = re.search(r".*cap\s*:\s*(\d*)\s*%", datas)
        if volValue:
            self.VolList.append(volValue.group(1))
        if curValue:
            self.CurList.append(curValue.group(1))
        if infoCapValue:
            Cap = infoCapValue.group(1)  # info电量
            self.UI.TIME_BAT_NUM.display(Cap)  # 显示在UI上
            intCap = int(Cap)
            if 5 <= intCap < 90 and self.number == 0:    # 显示第一次的电压电流
                self.UI.CHARGE_CUR.display(self.CurList[0])
                self.UI.CHARGE_VOL.display(self.VolList[0])
                self.number = 1
            if intCap >= 90 and self.number == 1:        # 电量大于等于90
                if self.UI.textEdit_Send.text():
                    self.UI.textEdit_Send.clear()
                    self.UI.textEdit_Send.setText("info")   # 发送一次info获取结束电压电流
                    self.SendData()     # 发送指令
                if self.VolList and self.CurList: # 如果有数据，则取最后一个
                    self.UI.RUN_CUR.display(self.CurList[-1])
                    self.UI.RUN_VOL.display(self.VolList[-1])
                    self.ser.WriteInfo("bat -d 0")  # 停止
                    # self.SendDing(info= "测试完成", CurList= CurList, VolList = VolList)
                    message = f'\n --✉️ {self.UI.TestDevices.text()}充电完成-- \n' \
                              f'\n📌 测试人员：Aiper \n' \
                              f'\n💡 当前电量：{self.UI.TIME_BAT_NUM.value()} %' \
                              f'\n📆 测试日期：{self.currentTime} \n' \
                              f'\n⌛ 跑机时长：{self.UI.label_16.text()} \n' \
                              f'\n📝 跳电次数：{self.UI.JUMP_NUMBER.value()} 次 \n' \
                              f'\n🚀 最大跳电：{self.UI.MAX_JUMP_BAT.value()} % \n' \
                              f'\n ⚡ 开始电流：{self.CurList[0]} ma \n' \
                              f'\n ⚡ 开始电压：{self.VolList[0]} mv \n' \
                              f'\n ⚡ 结束电流：{self.CurList[1]} ma \n' \
                              f'\n ⚡ 结束电压：{self.VolList[1]} ma \n'
                    self.dingding.send_ding_notification(message)
                    self.number = 2
            # if intCap >= 90:
            #     message = f'\n --✉️ {self.UI.TestDevices.text()}测试结束-- \n' \
            #               f'\n❗ 可能处于待机状态 \n'\
            #               f'\n📌 测试人员：Aiper \n' \
            #               f'\n💡 当前电量：{self.UI.TIME_BAT_NUM.value()} % \n' \
            #               f'\n📆 测试日期：{self.currentTime} \n' \
            #               f'\n⌛ 跑机时长：{self.UI.label_16.text()} \n' \
            #               f'\n📝 跳电次数：{self.UI.JUMP_NUMBER.value()} 次 \n' \
            #               f'\n🚀 最大跳电：{self.UI.MAX_JUMP_BAT.value()} % \n' \
            #               f'\n ⚡ 开始电流：{self.CurList[0]} ma \n' \
            #               f'\n ⚡ 开始电压：{self.VolList[0]} mv \n' \
            #               f'\n ⚡ 结束电流：{self.CurList[1]} ma \n' \
            #               f'\n ⚡ 结束电压：{self.VolList[1]} ma \n'
            #     self.dingding.send_ding_notification(message)
        try:
            # bat 纯电池电量
            batCapValue = re.search(r".*cap:.*(\d+)", datas)
            if batCapValue:
                bat = batCapValue.group().split(",")[-1].strip()
                self.UI.TIME_BAT_NUM.display(bat)  # 根据bat更新电量
                self.CapList.append(bat)
                if len(self.CapList) == 2:
                    Jump = int(self.CapList[-1]) - int(self.CapList[0])
                    if (Jump > 1) or (Jump < 0):
                        self.JumpNum += 1
                        self.UI.JUMP_NUMBER.display(abs(Jump))  # 绝对值，放电回电，充电掉电
                        self.UI.MAX_JUMP_BAT.display(self.JumpNum)
                        self.CapList.clear()
        except:
            pass
        finally:
            endTime = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            # 将时间字符串转换为 datetime 对象
            start_time = datetime.datetime.strptime(self.startTime, "%H:%M:%S.%f")
            end_time = datetime.datetime.strptime(endTime, "%H:%M:%S.%f")
            runTime = end_time - start_time
            self.UI.label_16.setText(str(runTime)[:-3])
        # 在这个槽函数中更新UI元素，比如更新文本框、标签等
        self.UI.textEdit_Recive.insertPlainText(datas)
        self.while_read_thread.MoveCursor()

    # def SendDing(self, info, CurList, VolList):
    #     message = f'\n --❌ {info}-- \n' \
    #               f'\n📌 测试人员：Aiper \n' \
    #               f'\n📆 测试日期：{self.currentTime} \n' \
    #               f'\n⌛ 跑机时长：{self.UI.label_16.text()} \n' \
    #               f'\n📝 跳电次数："{self.UI.JUMP_NUMBER.value()}" 次 \n' \
    #               f'\n🚀 最大跳电：{self.UI.MAX_JUMP_BAT.value()} % \n' \
    #               f'\n ⚡ 开始电流：{CurList[0]} ma \n' \
    #               f'\n ⚡ 开始电压：{VolList[0]} mv \n' \
    #               f'\n ⚡ 结束电流：{CurList[1]} ma \n' \
    #               f'\n ⚡ 结束电压：{VolList[1]} ma \n'
    #     self.dingding.send_ding_notification(message)

    def handle_data_received(self, data):
        """接收到数据后的处理函数"""
        # 发送信号，将数据传递给LogStorageThread子线程
        self.log_storage_thread.data_received.emit(data)

        # self.data_received.emit(data)  # 将数据传递给主线程


# 日志存储类
class LogStorageThread(QThread):
    data_received = pyqtSignal(str)

    def __init__(self):
        super(LogStorageThread, self).__init__()
        self.currentTime = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        self.log_file = sys_ + "\\" + self.currentTime + ".log"
        logging.basicConfig(
            filename=self.log_file,
            format="[%(asctime)s.%(msecs)03d] %(message)s",
            datefmt="%H:%M:%S",
            level=logging.INFO,
            encoding="utf-8"
        )

    def run(self):
        self.data_received.connect(self.write_to_log)

    def write_to_log(self,data: str):
        """将数据写入日志文件"""
        logging.info(f"{data}")


# 循环读取传递数据
class WhileReadThread(QThread):
    """显示数据"""
    data_received = pyqtSignal(str)
    update_ui_signal = pyqtSignal(str)

    def __init__(self, ser, UI, parent=None):
        super(WhileReadThread, self).__init__(parent)
        self.ser = ser
        self.UI = UI
        self.pp = PlotData(self.UI)
        self.pp.start()

    def run(self):
        while True:
            datas = self.ser.ReadLineValue()
            if datas:
                # 发送数据给UI显示线程
                self.pp.data_received.emit(datas.strip())
                # 日志数据
                self.data_received.emit(datas.strip())
                # 写入显示文本
                self.update_ui_signal.emit(datas)
            # else:
            #     self.SendDing(info='测试异常', CurList = CurList, VolList= VolList)

    def MoveCursor(self):
        """移动下拉列表"""
        # 滚动到底部并保持光标可见
        self.UI.textEdit_Recive.moveCursor(QTextCursor.End)
        self.UI.textEdit_Recive.ensureCursorVisible()
        # 滚动条自动滚动到底部
        scrollbar = self.UI.textEdit_Recive.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def stop(self):
        """ 强制终止线程"""
        self.terminate()
        self.wait()

# 曲线图
class PlotData(QThread):
    """显示数据"""
    data_received = pyqtSignal(str)

    def __init__(self, UI, parent=None):
        super(PlotData, self).__init__(parent)
        self.UI = UI
        self.plot = DataPlotWidget(self.UI)

    def run(self):
        self.data_received.connect(self.plt)

    def plt(self, datas):
        if datas:
            batCapValue = re.search(r".*cap:.*(\d+)", datas)
            if batCapValue:
                bat = batCapValue.group().split(",")[-1].strip()
                self.plot.update_data(bat)

    def stop(self):
        """ 强制终止线程"""
        self.terminate()
        self.wait()