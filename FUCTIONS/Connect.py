# -*- coding: utf-8 -*-
# https://blog.csdn.net/weixin_52040868
# 公众号：测个der
# 微信：qing_an_an
import binascii, logging, json, jsonpath, re
import os.path
import serial
import datetime
from addict import Dict
import serial.tools.list_ports
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QTextCursor
from FUCTIONS.ReadConfig import JSONREAD
from FUCTIONS.config import sys_, JsonPath
from FUCTIONS.DataChart import *
from FUCTIONS.DingDing import DingTalkSendMsg
from FUCTIONS.Loging import logger, ExecuteDecorator
from FUCTIONS.excelUnpack import LogParsingThread


def UseException(message=None):  # 异常装饰器
    def decorator(func):
        @ExecuteDecorator
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 在这里处理异常，可以根据 custom_message 自定义异常消息
                ErrorMessage = f"发生异常：{e}，\n" \
                               f"自定义消息：{message}"
                logger.error(ErrorMessage)

        return wrapper

    return decorator


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

    @property
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

    def Write_16(self, command):
        """写入16进制数据"""
        if hasattr(self, "ser") and self.ser.writable():
            self.ser.write(bytes.fromhex(command))

    @property
    def ReadeValue(self):
        """读取全部数据"""
        if hasattr(self, "ser") and self.ser.readable():
            datas = self.ser.read().decode("utf-8")
            return datas

    @property
    def Reade_16_Value(self):
        """读取16进制全部数据"""
        recv = bytes(self.ser.read())
        Data = binascii.b2a_hex(recv).decode('ascii')
        return Data

    @property
    def ReadLineValue(self):
        """读取一行数据"""
        if hasattr(self, "ser") and self.ser.readable():
            try:
                datas = self.ser.readline().decode("utf-8")
                if datas:
                    return datas
            except:
                pass


class UiConnect(QThread):
    data_received = pyqtSignal(str)

    def __init__(self, UI):
        super(UiConnect, self).__init__()
        self.ser = SerConnect()
        self.UI = UI

        self.currentTime = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        self.startTime = datetime.datetime.now()
        self.LogFile = None
        self.CapList = []
        self.InfoCapList = []
        # self.statusList = []
        self.status = None
        self.JumpNum = 0
        self.num = 0
        self.DisConnetNum = 0
        self.ConnectValue = None
        self.SelectStant = ["S1", "H2"]
        self.JsonData = JSONREAD()

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
        coms = self.ser.Coms
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
            if self.UI.hexSending_checkBox.isChecked() and self.UI.hexShowing_checkBox.isChecked():
                self.while_read_thread.update_ui_signal.connect(self.Update16Ui)
            else:
                self.num = 0  # 恢复 0
                logger.info(f"当前num值为：{self.num}")
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
        """写入发送命令"""
        command = self.UI.textEdit_Send.text()
        if isinstance(command, str):
            if self.UI.hexSending_checkBox.isChecked():
                self.ser.Write_16(command)
            else:
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
        """定时器发送"""
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

    def StartReadLog(self, ischeck=False):
        """启动读取日志类"""
        self.JoinFile()  # 执行文件读取
        SelectText = self.UI.SelectCommand.currentText()  # 获取充电还是放电数据
        self.read = ReadLogThread(self.FilePath, SelectText=SelectText, ischeck=ischeck)  # 实例化读取类
        self.read.start()
        logger.info("进入日志读取~")

    def UpdateUi(self, datas):
        """用于更新UI元素的槽函数"""
        try:
            # bat 纯电池电量
            batCapValue = re.search(r".*cap:.*(\d+)", datas)
            infoCapValue = re.search(r".*cap\s*:\s*(\d*)\s*%", datas)
            # 状态
            statusValue = re.search(r'.*status\s*:\s*(\w*)', datas)
            # Connect = re.search(r".*\s*\+\s*(\w*)", datas)
            Connect = re.search(r".*(\w*)", datas)
            StandardText = self.UI.Standard.currentText()

            if Connect:  # 检查断连
                self.ConnectValue = Connect.group()

            if statusValue:
                self.status = statusValue.group(1)  # 充电状态
                # self.statusList.append(status)

            if infoCapValue:
                capValue = infoCapValue.group(1)
                # 2023-10-19新增
                if len(self.InfoCapList) == 1:
                    self.InfoCapList = self.InfoCapList[:-1]
                self.InfoCapList.append(capValue)

            # if self.statusList[-1] == "full" and self.num == 0:  # 充电完成
            if self.status == "full" and self.num == 0:  # 充电完成
                # if int(self.InfoCapList[-1]) >= 90:  # 满电
                self.UI.TIME_BAT_NUM.display(self.InfoCapList[-1])  # 根据info更新电量
                self.SendCustomCommad()
                self.SendTimer.stop()
                logger.info("充电完成-命令停止")
                self.Finish()
                self.num = 1
                # 发送钉钉

            # if self.ConnectValue == self.JsonData.getData("BreakMark") and (self.num == 0):
            if (self.JsonData.getData("BreakMark") in self.ConnectValue) and (self.num == 0):  # 判断结束标志位是否存在
                if self.JsonData.getData("BreakMark") == "+DISCONNECT":
                    self.DisConnetNum += 1
                    if self.DisConnetNum == 3:
                        self.SendCustomCommad()
                        self.SendTimer.stop()
                        logger.info("放电完成或蓝牙模块断开次数过多-命令停止")
                        self.Finish()
                        self.num = 1
                        # 发送钉钉
                elif self.JsonData.getData("BreakMark") == self.JsonData.getData("OtherBreakMark"):
                    self.SendCustomCommad()
                    self.SendTimer.stop()
                    logger.info(f'放电完成或  {self.JsonData.getData("OtherBreakMark")} -命令停止')
                    self.Finish()
                    self.num = 1

            if (StandardText in self.SelectStant) and (self.num == 0):  # 针对特定机型充电
                if int(self.InfoCapList[-1]) == self.JsonData.getData("BreakBat"):  # 满电
                    self.SendCustomCommad()
                    self.SendTimer.stop()
                    logger.info("充电完成-命令停止")
                    self.Finish()
                    self.num = 1

            if batCapValue:  # 有值则往下走
                # 2023-10-19 修改
                self.bat = batCapValue.group().split(",")[-1].strip()
                # if self.bat:
                self.UI.TIME_BAT_NUM.display(self.bat)  # 根据bat更新电量
                if len(self.CapList) == 2:
                    self.CapList = self.CapList[-1:]
                Jump = int(self.CapList[-1]) - int(self.CapList[0])
                if (Jump > 1) or (Jump < 0):
                    self.JumpNum += 1
                    self.UI.JUMP_NUMBER.display(self.JumpNum)
                    self.UI.MAX_JUMP_BAT.display(abs(Jump))  # 绝对值，放电回电，充电掉电
                # self.CapList.clear()
                self.CapList.append(self.bat)
            else:
                self.UI.TIME_BAT_NUM.display(self.InfoCapList[-1])  # 根据info更新电量

        except:
            pass
        finally:
            # endTime = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            endTime = datetime.datetime.now()
            # 将时间字符串转换为 datetime 对象
            # start_time = datetime.datetime.strptime(self.startTime, "%H:%M:%S.%f")
            # end_time = datetime.datetime.strptime(endTime, "%H:%M:%S.%f")
            runTime = endTime - self.startTime
            self.UI.label_16.setText(str(runTime)[:-3])
        # 在这个槽函数中更新UI元素，比如更新文本框、标签等
        self.UI.textEdit_Recive.insertPlainText(datas)
        self.while_read_thread.MoveCursor()

    def Update16Ui(self, datas):
        # 16进制显示文本
        self.UI.textEdit_Recive.insertPlainText(datas)
        # self.UI.textEdit_Recive.insertPlainText("\n")
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

    def Send_16_Commad(self):
        """发送16进制数据"""
        self.SendData()

    def Finish(self):
        """表示充电完成"""
        logger.info("正常完成-调用读取日志")
        if self.UI.DataUnpack.isChecked():
            self.StartReadLog(ischeck=True)
        else:
            self.StartReadLog()
        # self.num = 0

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
        self.logger = self.CreateLogger()  # 创建独立的记录器

    def CreateLogger(self):
        LogThread = logging.getLogger(__name__)
        LogThread.setLevel(logging.INFO)

        # 创建一个独立的文件处理程序，将日志写入指定文件
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        # 创建一个格式化器，定义日志记录的格式
        formatter = logging.Formatter("[%(asctime)s.%(msecs)03d] %(message)s", datefmt="%H:%M:%S")
        file_handler.setFormatter(formatter)

        # 将文件处理程序添加到记录器
        LogThread.addHandler(file_handler)

        return LogThread

    def run(self):
        if self.FileRule:
            self.FileNameTime.emit(self.log_file)  # 发送日志名称
            self.FileRule = False
        self.data_received.connect(self.WriteLog)

    def WriteLog(self, data: str):
        """将数据写入日志文件"""
        self.logger.info(f"{data}")

    def LogName(self):
        FirstName = JSONREAD().getData("Devices")
        EndName = self.UI.SelectCommand.currentText()
        self.currentTime = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        Day = JSONREAD().update_datas("Day",self.currentTime)
        logger.info(f"时间Day写入SUCCESS：{Day}")
        SaveLogPath = sys_ + "\\" + "自动化电池监测日志"
        # 检查文件夹是否已存在
        if not os.path.exists(SaveLogPath):
            # 使用os.makedirs()创建文件夹
            os.makedirs(SaveLogPath)
        if FirstName:
            self.log_file = SaveLogPath + "\\" + FirstName + EndName + self.currentTime + ".log"
        else:
            self.log_file = SaveLogPath + "\\" + EndName + self.currentTime + ".log"
        logger.info(f"日志文件创建成功~,日志文件是：{self.log_file}")


# 循环读取传递数据
class WhileReadThread(QThread):
    """显示数据"""
    data_received = pyqtSignal(str)
    update_ui_signal = pyqtSignal(str)

    def __init__(self, ser, UI, parent=None):
        super(WhileReadThread, self).__init__(parent)
        self.ser = ser
        self.UI = UI
        self.num = 0
        self.dingding = DingTalkSendMsg()
        self.pp = PlotData(self.UI)
        self.pp.start()

    def run(self):
        if self.UI.hexSending_checkBox.isChecked():
            while True:
                datas = self.ser.Reade_16_Value
                if datas:
                    # 发送数据给UI显示线程
                    self.pp.data_received.emit(datas.strip())
                    # 日志数据
                    self.data_received.emit(datas.strip())
                    # 写入显示文本
                    self.update_ui_signal.emit(datas)
        else:
            while True:
                datas = self.ser.ReadLineValue
                if datas:
                    # 发送数据给UI显示线程
                    self.pp.data_received.emit(datas.strip())
                    # 日志数据
                    self.data_received.emit(datas.strip())
                    # 写入显示文本
                    self.update_ui_signal.emit(datas)
                    self.ProcessData(datas)

    def ProcessData(self, data):
        """正则匹配告警   2023/11/03新增"""
        warns = {"wiv": "WIV-内浸水", "pcp": "PCP-堵转", "ocp": "OCP-电机保护",
                 "bcp": "BCP-过流保护", "wcp": "WCP-行走电机报警", "except stat": "Exceptions Status"}
        S1_match = re.search(r".*{}\s*:\s*0x(\d*)".format("except stat"), data)
        if S1_match:
            S1_value = S1_match.group(1)
            if S1_value != "0000000000000000" and self.num == 0:
                logger.error("发生告警：{} {}".format(warns['except stat'], S1_value))
                self.SendDing(warns["except stat"] + f" {S1_value}")    # 发送告警消息
                self.num = 1
        else:
            for warn in warns:
                # match = re.search(r".*{}\s*:\s*(\d+)".format(pattern), data)
                match = re.search(r".*{}\s*:\s*(\d+)".format(warn, " "), data)
                if match:
                    value = match.group(1)
                    if value == "1" and self.num == 0:
                        logger.error(f"发生告警：{warns[warn]}")
                        self.SendDing(warns[warn])
                        self.num = 1  # 指定数据为1

    def SendDing(self, prompt):
        Data = JSONREAD()
        message = f'\n --✉️ {Data.getData("Devices")} Tests complete-- \n' \
                  f'\n📌 测试人员：{Data.getData("Name", "Apier")} \n' \
                  f'\n❗❗❗ 告警提示：{prompt} 告警 \n'

        mobiles = []
        OnelyIphone = Data.getData("Phone")
        if OnelyIphone:
            mobiles.append(OnelyIphone)
            self.dingding.send_ding_notification(message, mobiles)
        else:
            self.dingding.send_ding_notification(message)

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
    def __init__(self, Path, SelectText=None, ischeck=False):
        super().__init__()
        self.Path = Path
        self.is_check = ischeck
        self.SelectText = SelectText
        self.dingding = DingTalkSendMsg()
        self.json_Data = JSONREAD()
        self.currentTime = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        self.datas = self.ReadLog
        self.ReExpression()

    def run(self) -> None:
        info = self.Info
        if info:
            try:
                logger.info("正在写入Json文件")
                self.WriteJson(info)  # 写入Json文件
                logger.info("写入Json文件完成")
            except ValueError as e:
                logger.error(f"Json写入异常 {e}")
            finally:
                # self.SendDing(info)  # 发送钉钉
                logger.info("钉钉发送完成~")

    def WriteJson(self, info):
        """写入Json数据"""
        path = os.path.split(self.Path)[-1][:-4]
        FolderPath = sys_ + "\\" + "自动化电池监测数据"
        # 检查文件夹是否已存在
        if not os.path.exists(FolderPath):
            # 使用os.makedirs()创建文件夹
            os.makedirs(FolderPath)
        logger.info("创建文件成功，并开始写入~")
        with open(FolderPath + "\\" + path + "测试数据.json", "w") as json_file:
            json.dump(info, json_file, indent=4)  # 使用indent参数以漂亮的格式缩进数据
        if self.is_check:
            logger.info("开始写入excel")
            try:
                logger.info(f"==读取文件==地址：{self.Path}")
                unpack_log = LogParsingThread(self.Path)
                unpack_log.start()
                unpack_log.stop()
                logger.info("excel写入完成")
            except Exception as e:
                logger.error("写入异常！ {}".format(e))

    def DataTimes(self, stime, etime):
        """计算时长"""
        is_key = JSONREAD().is_key_present("Day")
        if is_key:
            Day = JSONREAD().getData("Day")[:10]
            Last = self.currentTime[:10]
            Day_time = Day + " " + stime
            Last_time = Last + " " + etime
            start_time = datetime.datetime.strptime(Day_time, "%Y_%m_%d %H:%M:%S.%f")
            end_time = datetime.datetime.strptime(Last_time, "%Y_%m_%d %H:%M:%S.%f")
            duration = end_time - start_time
        else:
            start_format = '%H:%M:%S.%f' if len(stime) >= 12 else '%H:%M:%S'
            end_format = '%H:%M:%S.%f' if len(etime) >= 12 else '%H:%M:%S'
            start_time = datetime.datetime.strptime(stime, start_format)
            end_time = datetime.datetime.strptime(etime, end_format)
            duration = end_time - start_time
        if len(str(duration)) > 8:
            return str(duration)[:-3]
        else:
            return str(duration)

    @property
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

    @property
    def Info(self):
        """信息调用"""
        logger.info("进入数据筛选阶段~")
        PutTime = None
        # for key, value in zip(self.statusValue, self.capValue):
        if self.SelectText == '充电':
            # 充电时长
            ChargeTime = self.DataTimes(stime=self.statusValue[0][0],
                                        etime=self.statusValue[-1][0])
            logger.info("充电时长：{}".format(ChargeTime))
            # 充电跳电情况
            return {"PutTime"    : ChargeTime, "Currentbattery": self.capValue[-1][1],
                    "PutInfo"    : self.ChargeInfoBatteryJump, "PutBat": self.ChargeBatJump,
                    "Infomations": self.VolCur}

        elif self.SelectText == "放电":  # 放电
            is_BatteryCut = self.json_Data.getData("BatteryCut")
            if is_BatteryCut:
                logger.info("BatteryCut为True")
                for cap in self.capValue:
                    if int(cap[1]) == self.json_Data.getData("CutValue"):
                        PutTime = self.DataTimes(stime=cap[0],
                                                 etime=self.capValue[-1][0])
                        logger.info("自定义截止电量为{}，放电时长：{}".format(cap[1], PutTime))
                        break
            else:
                # 放电时长
                PutTime = self.DataTimes(stime=self.capValue[0][0],
                                         etime=self.capValue[-1][0])
                logger.info("放电时长：{}".format(PutTime))
            # 放电跳电情况
            return {"PutTime"    : PutTime, "Currentbattery": self.capValue[-1][1],
                    "PutInfo"    : self.PutInfoBatteryJump, "PutBat": self.PutBatJump,
                    "Infomations": self.VolCur}
        logger.info("数据筛选完成~")

    @property
    @UseException(message="==ChargeInfoBatteryJump== 取值错误，检查日志数据")
    def ChargeInfoBatteryJump(self):
        """info充电跳电"""
        MaxNumber = []
        dictValue = {"JumpNum": 0, "JumpValue": [], "MaxJump": 0}
        for num in range(len(self.capValue) - 1):
            CountNumber = int(self.capValue[num + 1][1]) - int(self.capValue[num][1])
            # if CountNumber > 1:  # 充电跳电
            #     dictValue["JumpNum"] += 1
            #     MaxNumber.append(CountNumber)
            #     dictValue["JumpValue"].append(self.capValue[num + 1])
            # if CountNumber < 0:  # 充电掉电
            #     dictValue["JumpNum"] += 1
            #     MaxNumber.append(CountNumber)
            #     dictValue["JumpValue"].append(self.capValue[num + 1])
            if (CountNumber > 1) or (CountNumber < 0):
                """不论涨还是跳"""
                dictValue["JumpNum"] += 1
                MaxNumber.append(CountNumber)
                dictValue["JumpValue"].append(self.capValue[num + 1])
        if MaxNumber:
            dictValue["MaxJump"] = max(MaxNumber)
        # print("ChargeInfoBatteryJump", dictValue)
        return dictValue

    @property
    @UseException(message="==PutInfoBatteryJump== 取值错误，检查日志数据")
    def PutInfoBatteryJump(self):
        """info放电跳电数据"""
        MaxNumber = []
        dictValue = {"JumpNum": 0, "JumpValue": [], "MaxJump": 0}
        for num in range(len(self.capValue) - 1):
            CountNumber = int(self.capValue[num][1]) - int(self.capValue[num + 1][1])
            # if CountNumber > 1:  # 放电回电
            #     dictValue["JumpNum"] += 1
            #     MaxNumber.append(CountNumber)
            #     dictValue["JumpValue"].append(self.capValue[num + 1])
            # if CountNumber < 0:  # 放电跳电
            #     dictValue["JumpNum"] += 1
            #     MaxNumber.append(CountNumber)
            #     dictValue["JumpValue"].append(self.capValue[num + 1])
            if (CountNumber > 1) or (CountNumber < 0):
                """不论涨还是掉"""
                dictValue["JumpNum"] += 1
                MaxNumber.append(CountNumber)
                dictValue["JumpValue"].append(self.capValue[num + 1])
        if MaxNumber:
            dictValue["MaxJump"] = max(MaxNumber)
        return dictValue

    @property
    @UseException(message="==VolCur== 取值错误，检查日志数据")
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

    @property
    @UseException(message="==PutBatJump== 取值错误，检查日志数据")
    def PutBatJump(self):
        """Bat放电"""
        BatPutValue = {"JumpNum": 0, "JumpValue": [], "MaxJump": 0}
        MaxNumber = []
        if self.batValues:
            for num in range(len(self.batValues) - 1):
                CountNumber = int(self.batValues[num][1]) - int(self.batValues[num + 1][1])
                # if CountNumber > 1:
                #     """掉"""
                #     BatPutValue["JumpNum"] += 1
                #     MaxNumber.append(CountNumber)
                #     BatPutValue["JumpValue"].append(self.batValues[num + 1])
                # if CountNumber < 0:
                #     """回"""
                #     BatPutValue["JumpNum"] += 1
                #     MaxNumber.append(CountNumber)
                #     BatPutValue["JumpValue"].append(self.batValues[num + 1])
                if (CountNumber > 1) or (CountNumber < 0):
                    """不论涨还是掉"""
                    BatPutValue["JumpNum"] += 1
                    MaxNumber.append(CountNumber)
                    BatPutValue["JumpValue"].append(self.batValues[num + 1])
            if MaxNumber:
                BatPutValue["MaxJump"] = max(MaxNumber)
        return BatPutValue

    @property
    @UseException(message="==ChargeBatJump== 取值错误，检查日志数据")
    def ChargeBatJump(self):
        """Bat充电"""
        BatChargeValue = {"JumpNum": 0, "JumpValue": [], "MaxJump": 0}
        MaxNumber = []
        if self.batValues:
            for num in range(len(self.batValues) - 1):
                CountNumber = int(self.batValues[num + 1][1]) - int(self.batValues[num][1])
                # if CountNumber > 1:
                #     """跳"""
                #     BatChargeValue["JumpNum"] += 1
                #     MaxNumber.append(CountNumber)
                #     BatChargeValue["JumpValue"].append(self.batValues[num + 1])
                # if CountNumber < 0:
                #     """掉"""
                #     BatChargeValue["JumpNum"] += 1
                #     MaxNumber.append(CountNumber)
                #     BatChargeValue["JumpValue"].append(self.batValues[num + 1])
                if (CountNumber > 1) or (CountNumber < 0):
                    """不论涨还是掉"""
                    BatChargeValue["JumpNum"] += 1
                    MaxNumber.append(CountNumber)
                    BatChargeValue["JumpValue"].append(self.batValues[num + 1])
            if MaxNumber:
                BatChargeValue["MaxJump"] = max(MaxNumber)
        return BatChargeValue

    def SendDing(self, kwargs):
        value = Dict(kwargs)
        message = f'\n --✉️ {self.json_Data.getData("Devices")} {self.SelectText} Tests complete-- \n' \
                  f'\n📌 测试人员：{self.json_Data.getData("Name", "Apier")} \n' \
                  f'\n💡 当前电量：{value.Currentbattery} % \n' \
                  f'\n📆 测试日期：{self.currentTime} \n' \
                  f'\n⌛ 跑机时长：{value.PutTime} \n' \
                  f'\n📝 跳电次数：{value.PutInfo.JumpNum} 次 \n' \
                  f'\n🚀 最大跳电：{value.PutInfo.MaxJump}  \n' \
                  f'\n ⚡ 开始电流：{value.Infomations.ChargeDictValue.Start.cur} ma \n' \
                  f'\n ⚡ 开始电压：{value.Infomations.ChargeDictValue.Start.vol} mv \n' \
                  f'\n ⚡ 结束电流：{value.Infomations.ChargeDictValue.End.cur} ma \n' \
                  f'\n ⚡ 结束电压：{value.Infomations.ChargeDictValue.End.vol} mv \n' \
                  f'\n📒 详细请参考文件夹中的"数据处理中的.json"文件。'
        mobiles = []
        OnelyIphone = self.json_Data.getData("Phone")
        if OnelyIphone:
            mobiles.append(OnelyIphone)
            self.dingding.send_ding_notification(message, mobiles)
        else:
            self.dingding.send_ding_notification(message)

    def JsonPath(self, data, path):
        """取值
        self.JsonPath(JsonData,"$..ChargeDictValue.Start.vol")[0]"""
        return jsonpath.jsonpath(data, path)

    def __str__(self):
        return f"当前类：{self.__class__.__name__}"
