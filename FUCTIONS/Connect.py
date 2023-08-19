# -*- coding: utf-8 -*-
# https://blog.csdn.net/weixin_52040868
# 公众号：测个der
# 微信：qing_an_an
import logging
import json
import jsonpath
import os.path
import re
import serial
import datetime
import serial.tools.list_ports
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QTextCursor
from FUCTIONS.config import sys_
from FUCTIONS.DataChart import *
from FUCTIONS.DingDing import DingTalkSendMsg


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

        # # 创建LogStorageThread实例，并保存为成员变量
        # self.log_storage_thread = LogStorageThread()
        # self.log_storage_thread.FileNameTime.connect(self.LogFileName)
        # self.log_storage_thread.start()

        self.currentTime = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        # self.startTime = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.startTime = datetime.datetime.now()
        self.LogFile = None
        self.CapList = []
        self.InfoCapList = []
        self.statusList = []
        self.JumpNum = 0
        self.num = 0
        self.SelectStant = ["S1", "H2"]

        self.TimerClearClock()
        self.TimerClock()
        # self.CapListClock()

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
            self.while_read_thread.update_ui_signal.connect(self.UpdateUi)  # 连接新信号到槽函数
            self.while_read_thread.start()

            # 创建LogStorageThread实例，并保存为成员变量
            self.log_storage_thread = LogStorageThread(self.UI)
            self.log_storage_thread.FileNameTime.connect(self.LogFileName)
            self.log_storage_thread.start()

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

    def TimerClock(self):
        # 创建发送定时器
        self.SendTimer = QTimer()
        self.SendTimer.timeout.connect(self.AlarmClockTask)
        self.SendTimer.start(10000)  # 10S触发一次查看是否需要重新触发

    def TimerClearClock(self):
        # 创建清除定时器
        self.ClearTimer = QTimer()
        # 清除内容
        self.ClearTimer.timeout.connect(self.TextEditClear)
        self.ClearTimer.start(20000)  # 每隔20S秒触发一次定时器槽函数

    def TextEditClear(self):
        """清除内容"""
        text = self.UI.textEdit_Recive
        if text:
            self.UI.textEdit_Recive.clear()
        else:
            return

    def AlarmClockTask(self):
        AlarmClockText = self.UI.AlarmClock.text()
        timeNumber = self.UI.WatingTime.text()
        if timeNumber:
            Millisecond = int(timeNumber) * 1000  # 计算毫秒
            if AlarmClockText and self.UI.ClockBtn.isChecked():
                self.SendTimer.start(Millisecond)  # 重新定义启动时间
                self.UI.textEdit_Send.setText(AlarmClockText)
                self.SendData()
            else:
                return

    def LogFileName(self, Name):
        """日志存储名称"""
        self.LogFile = Name

    def JoinFile(self):
        """启动文件读取"""
        self.FilePath = os.path.join(sys_, self.LogFile)  # 文件路径

    def StartReadLog(self):
        """启动读取日志类"""
        self.JoinFile()  # 执行文件读取
        SelectText = self.UI.SelectCommand.currentText()  # 获取充电还是放电数据
        OnelyIphone = self.UI.Iphone.text()
        Devices = self.UI.TestDevices.text()
        if OnelyIphone and Devices:
            self.read = ReadLogThread(self.FilePath, SelectText=SelectText,
                                      OnelyIphone=OnelyIphone, Devices=Devices)  # 实例化读取类
        else:
            self.read = ReadLogThread(self.FilePath, SelectText=SelectText)  # 实例化读取类
        self.read.start()

    def UpdateUi(self, datas):
        """用于更新UI元素的槽函数"""
        try:
            # bat 纯电池电量
            batCapValue = re.search(r".*cap:.*(\d+)", datas)
            infoCapValue = re.search(r".*cap\s*:\s*(\d*)\s*%", datas)
            # 状态
            statusValue = re.search(r'.*status\s*:\s*(\w*)', datas)
            Connect = re.search(r".*\s*\+\s*(\w*)", datas)
            StandardText = self.UI.Standard.currentText()

            if Connect:  # 检查断连
                ConnectValue = Connect.group()

            if statusValue:
                status = statusValue.group(1)  # 充电状态
                self.statusList.append(status)

            if infoCapValue:
                capValue = infoCapValue.group(1)
                self.InfoCapList.append(capValue)

            if self.statusList[-1] == "full" and self.num == 0:  # 充电完成
                if int(self.InfoCapList[-1]) >= 90:  # 满电
                    self.UI.TIME_BAT_NUM.display(self.InfoCapList[-1])  # 根据info更新电量
                    self.SendCustomCommad()
                    self.SendTimer.stop()
                    self.Finish()
                    self.num = 1
                    # 发送钉钉

            # if self.statusList[-1] == "null" and self.num == 0:
            # if int(self.InfoCapList[-1]) <= 10:  # 电量过低
            if ConnectValue == (("+DISCONNECT") or ("+CONNECTION")) and (self.num == 0):
                self.SendCustomCommad()
                self.SendTimer.stop()
                self.Finish()
                self.num = 1
                # 发送钉钉

            if StandardText in self.SelectStant and self.num == 0:
                if int(self.InfoCapList[-1]) >= 90:  # 满电
                        self.SendCustomCommad()
                        self.SendTimer.stop()
                        self.Finish()
                        self.num = 1
                        # 发送钉钉

            if (len(self.InfoCapList) and len(self.statusList)) == 10:
                self.InfoCapList.clear()
                self.statusList.clear()

            if batCapValue:  # 有值则往下走
                self.bat = batCapValue.group().split(",")[-1].strip()
                self.UI.TIME_BAT_NUM.display(self.bat)  # 根据bat更新电量
                self.CapList.append(self.bat)
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
            # endTime = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            endTime = datetime.datetime.now()
            # 将时间字符串转换为 datetime 对象
            # start_time = datetime.datetime.strptime(self.startTime, "%H:%M:%S.%f")
            # end_time = datetime.datetime.strptime(endTime, "%H:%M:%S.%f")
            runTime = endTime - self.startTime
            self.UI.label_16.setText(str(runTime))
        # 在这个槽函数中更新UI元素，比如更新文本框、标签等
        self.UI.textEdit_Recive.insertPlainText(datas)
        self.while_read_thread.MoveCursor()

    def SendCustomCommad(self):
        """发送自定义结束指令"""
        CustomCommad2 = self.UI.Custom_2.text()  # 自定义指令比如info -d 1000
        if isinstance(CustomCommad2, str):
            self.UI.textEdit_Send.clear()
            self.ser.WriteInfo(CustomCommad2)  # 停止
            self.SendData()  # 发送指令
        CustomCommad1 = self.UI.Custom_1.text()  # 自定义指令比如info -d 1000
        if isinstance(CustomCommad1, str):
            self.UI.textEdit_Send.clear()
            self.ser.WriteInfo(CustomCommad1)  # 停止
            self.SendData()  # 发送指令

    def Finish(self):
        """表示充电完成"""
        print("正常完成")
        self.StartReadLog()

    def handle_data_received(self, data):
        """接收到数据后的处理函数"""
        # 发送信号，将数据传递给LogStorageThread子线程
        self.log_storage_thread.data_received.emit(data)

        # self.data_received.emit(data)  # 将数据传递给主线程


# 日志存储类
class LogStorageThread(QThread):
    data_received = pyqtSignal(str)
    FileNameTime = pyqtSignal(str)

    def __init__(self, UI):
        super(LogStorageThread, self).__init__()
        self.UI = UI
        self.LogName()
        self.FileRule = True

    def run(self):
        if self.FileRule:
            self.FileNameTime.emit(self.log_file)  # 发送日志名称
            self.FileRule = False
        self.data_received.connect(self.write_to_log)

    def write_to_log(self, data: str):
        """将数据写入日志文件"""
        logging.info(f"{data}")

    def LogName(self):
        FirstName = self.UI.TestDevices.text()
        EndName = self.UI.SelectCommand.currentText()
        self.currentTime = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        SaveLogPath = sys_ + "\\" + "自动化电池监测日志"
        # 检查文件夹是否已存在
        if not os.path.exists(SaveLogPath):
            # 使用os.makedirs()创建文件夹
            os.makedirs(SaveLogPath)
        if FirstName:
            self.log_file = SaveLogPath + "\\" + FirstName + EndName + self.currentTime + ".log"
        else:
            self.log_file = SaveLogPath + "\\" + EndName + self.currentTime + ".log"
        logging.basicConfig(
            filename=self.log_file,
            format="[%(asctime)s.%(msecs)03d] %(message)s",
            datefmt="%H:%M:%S",
            level=logging.INFO,
            encoding="utf-8"
        )


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


class ReadLogThread(QThread):
    def __init__(self, Path, SelectText=None,
                 OnelyIphone=None, Devices=None):
        super().__init__()
        self.Path = Path
        self.SelectText = SelectText
        self.dingding = DingTalkSendMsg()
        self.OnelyIphone = OnelyIphone
        self.Devices = Devices
        self.currentTime = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        self.datas = self.ReadLog()
        self.ReExpression()

    def run(self) -> None:
        info = self.Info()
        if info:
            self.WriteJson(info)    # 写入Json文件
            self.SendDing(info)     # 发送钉钉

    def WriteJson(self, info):
        """写入Json数据"""
        path = os.path.split(self.Path)[-1][:-4]
        FolderPath = sys_ + "\\" + "自动化电池监测数据"
        # 检查文件夹是否已存在
        if not os.path.exists(FolderPath):
            # 使用os.makedirs()创建文件夹
            os.makedirs(FolderPath)
        with open(FolderPath + "\\" + path + "测试数据.json", "w") as json_file:
            json.dump(info, json_file, indent=4)  # 使用indent参数以漂亮的格式缩进数据

    @staticmethod
    def dataTimes(value, stime, etime):
        if len(value) >= 12:
            start_time = datetime.datetime.strptime(stime, '%H:%M:%S.%f')
            end_time = datetime.datetime.strptime(etime, '%H:%M:%S.%f')
        else:
            start_time = datetime.datetime.strptime(stime, '%H:%M:%S')
            end_time = datetime.datetime.strptime(etime, '%H:%M:%S')
        over_time = end_time - start_time
        return str(over_time)

    def ReadLog(self):
        with open(self.Path, 'r', encoding="utf-8") as r:
            datas = r.read()
        return datas

    def ReExpression(self):
        """正则"""
        self.capValue = re.findall(r'\[(.*)\].*cap\s*:\s*(\d*)\s*%', self.datas)
        self.statusValue = re.findall(r'\[(.*)\].*status\s*:\s*(\w*)', self.datas)

        self.volValue = re.findall(r"\[(.*)\]\s*vol\s*:\s*(\d*)", self.datas)
        self.curValue = re.findall(r"\[(.*)\]\s*cur\s*:\s*(\d*)", self.datas)
        self.batValues = re.findall('\[(.*)\].*cap\s*:.*,(.*)', self.datas)

    def Info(self):
        """信息调用"""
        Infomations = self.VolCur()
        # for key, value in zip(self.statusValue, self.capValue):
        if self.SelectText == '充电':
            # 充电时长
            ChargeTime = self.dataTimes(stime=self.statusValue[0][0],
                                        etime=self.statusValue[-1][0],
                                        value=self.statusValue[0][0])
            # 充电跳电情况
            ChargeInfo = self.ChargeInfoBatteryJump()
            ChargeBat = self.ChargeBatJump()
            return {"PutTime": ChargeTime, "Currentbattery": self.capValue[-1][1],
                    "PutInfo" : ChargeInfo, "PutBat": ChargeBat,
                    "Infomations": Infomations}

        elif self.SelectText == "放电":  # 放电
            # 放电时长
            PutTime = self.dataTimes(stime=self.capValue[0][0],
                                     etime=self.capValue[-1][0],
                                     value=self.capValue[0][0])
            # 放电跳电情况
            PutInfo = self.PutInfoBatteryJump()
            PutBat = self.PutBatJump()
            return {"PutTime": PutTime, "Currentbattery": self.capValue[-1][1],
                    "PutInfo": PutInfo, "PutBat": PutBat,
                    "Infomations": Infomations}

    def ChargeInfoBatteryJump(self):
        """info充电跳电"""
        MaxNumber = []
        dictValue = {"JumpNum": 0, "JumpValue": [], "MaxJump": 0}
        for num in range(len(self.capValue) - 1):
            CountNumber = int(self.capValue[num + 1][1]) - int(self.capValue[num][1])
            if CountNumber > 1:  # 充电跳电
                dictValue["JumpNum"] += 1
                MaxNumber.append(CountNumber)
                dictValue["JumpValue"].append(self.capValue[num + 1])
            if CountNumber < 0:  # 充电掉电
                dictValue["JumpNum"] += 1
                MaxNumber.append(CountNumber)
                dictValue["JumpValue"].append(self.capValue[num + 1])
        if MaxNumber:
            dictValue["MaxJump"] = max(MaxNumber)
        # print("ChargeInfoBatteryJump",dictValue)
        return dictValue

    def PutInfoBatteryJump(self):
        """info放电跳电数据"""
        MaxNumber = []
        dictValue = {"JumpNum": 0, "JumpValue": [], "MaxJump": 0}
        for num in range(len(self.capValue) - 1):
            CountNumber = int(self.capValue[num][1]) - int(self.capValue[num + 1][1])
            if CountNumber > 1:  # 放电回电
                dictValue["JumpNum"] += 1
                MaxNumber.append(CountNumber)
                dictValue["JumpValue"].append(self.capValue[num + 1])
            if CountNumber < 0:  # 放电跳电
                dictValue["JumpNum"] += 1
                MaxNumber.append(CountNumber)
                dictValue["JumpValue"].append(self.capValue[num + 1])
        if MaxNumber:
            dictValue["MaxJump"] = max(MaxNumber)
        return dictValue

    def VolCur(self):
        """单数是充电电流电压，双数是电池电流电压"""
        ChargeDictValue = {"Start": {"vol": None, "cur": None}, "End": {"vol": None, "cur": None}}
        BatteryDictValue = {"Start": {"vol": None, "cur": None}, "End": {"vol": None, "cur": None}}
        ChargeDict = {"ChargeVol": [], "ChargeCur": []}
        BatteryDict = {"BatteryVol": [], "BatteryCur": []}
        if (self.volValue and self.curValue) is not False:
            for num in range(len(self.volValue)):
                if num % 2 == 0:  # 充电电流电压
                    ChargeDict["ChargeVol"].append(self.volValue[num])
                    ChargeDict["ChargeCur"].append(self.curValue[num])
                else:  # 电池电压电流
                    BatteryDict["BatteryVol"].append(self.volValue[num])
                    BatteryDict["BatteryCur"].append(self.curValue[num])
            """充电电压电流数据"""
            ChargeDictValue["Start"].update({"vol": ChargeDict["ChargeVol"][0][1],
                                             "cur": ChargeDict["ChargeCur"][0][1]})
            ChargeDictValue["End"].update({"vol": ChargeDict["ChargeVol"][-1][1],
                                           "cur": ChargeDict["ChargeCur"][-1][1]})
            BatteryDictValue["Start"].update({"vol": BatteryDict["BatteryVol"][0][1],
                                              "cur": BatteryDict["BatteryCur"][0][1]})
            BatteryDictValue["End"].update({"vol": BatteryDict["BatteryVol"][-1][1],
                                            "cur": BatteryDict["BatteryCur"][-1][1]})
            # print("VolCur", ChargeDictValue)
            return {"ChargeDictValue": ChargeDictValue, "BatteryDictValue": BatteryDictValue}

    def PutBatJump(self):
        """Bat放电"""
        BatPutValue = {"JumpNum": 0, "JumpValue": [], "MaxJump": 0}
        MaxNumber = []
        if self.batValues:
            for num in range(len(self.batValues) - 1):
                CountNumber = int(self.batValues[num][1]) - int(self.batValues[num + 1][1])
                if CountNumber > 1:
                    """掉"""
                    BatPutValue["JumpNum"] += 1
                    MaxNumber.append(CountNumber)
                    BatPutValue["JumpValue"].append(self.batValues[num + 1])
                if CountNumber < 0:
                    """回"""
                    BatPutValue["JumpNum"] += 1
                    MaxNumber.append(CountNumber)
                    BatPutValue["JumpValue"].append(self.batValues[num + 1])
            if MaxNumber:
                BatPutValue["MaxJump"] = max(MaxNumber)
        return BatPutValue

    def ChargeBatJump(self):
        """Bat充电"""
        BatChargeValue = {"JumpNum": 0, "JumpValue": [], "MaxJump": 0}
        MaxNumber = []
        if self.batValues:
            for num in range(len(self.batValues) - 1):
                CountNumber = int(self.batValues[num + 1][1]) - int(self.batValues[num][1])
                if CountNumber > 1:
                    """跳"""
                    BatChargeValue["JumpNum"] += 1
                    MaxNumber.append(CountNumber)
                    BatChargeValue["JumpValue"].append(self.batValues[num + 1])
                if CountNumber < 0:
                    """掉"""
                    BatChargeValue["JumpNum"] += 1
                    MaxNumber.append(CountNumber)
                    BatChargeValue["JumpValue"].append(self.batValues[num + 1])
            if MaxNumber:
                BatChargeValue["MaxJump"] = max(MaxNumber)
        return BatChargeValue

    def SendDing(self, kwargs):
        message = f'\n --✉️ {self.Devices} Tests complete-- \n' \
                  f'\n📌 测试人员：Aiper \n' \
                  f'\n💡 当前电量：{kwargs["Currentbattery"]} % \n' \
                  f'\n📆 测试日期：{self.currentTime} \n' \
                  f'\n⌛ 跑机时长：{kwargs["PutTime"]} \n' \
                  f'\n📝 跳电次数：{kwargs["PutInfo"]["JumpNum"]} 次 \n' \
                  f'\n🚀 最大跳电：{kwargs["PutInfo"]["MaxJump"]}  \n' \
                  f'\n ⚡ 开始电流：{kwargs["Infomations"]["ChargeDictValue"]["Start"]["cur"]} ma \n' \
                  f'\n ⚡ 开始电压：{kwargs["Infomations"]["ChargeDictValue"]["Start"]["vol"]} mv \n' \
                  f'\n ⚡ 结束电流：{kwargs["Infomations"]["ChargeDictValue"]["End"]["cur"]} ma \n' \
                  f'\n ⚡ 结束电压：{kwargs["Infomations"]["ChargeDictValue"]["End"]["vol"]} ma \n'\
                  f'\n📒 详细请参考"测试数据.json"文件。'
        mobiles = []
        if self.OnelyIphone:
            mobiles.append(self.OnelyIphone)
            self.dingding.send_ding_notification(message, mobiles)
        else:
            self.dingding.send_ding_notification(message)

    def JsonPath(self, data, path):
        """取值"""
        return jsonpath.jsonpath(data, path)
