# -*- coding: utf-8 -*-
# https://blog.csdn.net/weixin_52040868
# 公众号：测个der
# 微信：qing_an_an
import json
import os
import datetime
import re
import pandas as pd
# from PyQt5.QtCore import QThread
from pathlib import Path
from FUCTIONS.Connect import UseException
from FUCTIONS.Loging import logger
from FUCTIONS.config import sys_
from FUCTIONS.ReadConfig import JSONREAD
from addict import Dict
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QFileDialog
from FUCTIONS.excelUnpack import LogParsing


# from FUCTIONS.excelUnpack import LogStorageThread


class ReadLogThread():
    def __init__(self, Path, SelectText="放电", ischeck=False):
        super().__init__()
        self.Path = Path
        self.is_check = ischeck
        self.SelectText = SelectText
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
                LogParsing(self.Path).reInfoParsing()
            except Exception as e:
                logger.info("写入异常！ {}".format(e))
            finally:
                logger.info("excel写入完成")

    @staticmethod
    def DataTimes(stime, etime):
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
        # PutTime = None
        # for key, value in zip(self.statusValue, self.capValue):
        if self.SelectText == '充电':
            # 充电时长
            ChargeTime = self.DataTimes(stime=self.statusValue[0][0],
                                        etime=self.statusValue[-1][0])
            # 充电跳电情况
            return {"PutTime"    : ChargeTime, "Currentbattery": self.capValue[-1][1],
                    "PutInfo"    : self.ChargeInfoBatteryJump, "PutBat": self.ChargeBatJump,
                    "Infomations": self.VolCur}

        elif self.SelectText == "放电":  # 放电

            if self.json_Data.getData("BatteryCut"):
                for cap in self.capValue:
                    if int(cap[1]) == self.json_Data.getData("CutValue"):
                        PutTime = self.DataTimes(stime=cap[0],
                                                 etime=self.capValue[-1][0])
                        break
            else:
                # 放电时长
                PutTime = self.DataTimes(stime=self.capValue[0][0],
                                         etime=self.capValue[-1][0])

            # 放电跳电情况
            return {"PutTime"    : PutTime, "Currentbattery": self.capValue[-1][1],
                    "PutInfo"    : self.PutInfoBatteryJump, "PutBat": self.PutBatJump,
                    "Infomations": self.VolCur}
        logger.info("数据筛选完成~")

    @property
    @UseException(message="取值错误，检查日志数据")
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

    @property
    @UseException(message="取值错误，检查日志数据")
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

    @property
    @UseException(message="取值错误，检查日志数据")
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
    @UseException(message="取值错误，检查日志数据")
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

    @property
    @UseException(message="取值错误，检查日志数据")
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


    def __str__(self):
        return f"当前类：{self.__class__.__name__}"


if __name__ == '__main__':
    ReadLogThread(r"E:\MONITOR_SYSTEM\自动化电池监测日志\S1充电2023_10_30_10_42_31.log").run()

#
# def autoReadLog(func):
#     def wrapper(*args, **kwargs):
#         self = args[0]
#         with open(self.path, 'r', encoding='utf-8') as r:
#             self.texts = r.read()
#             # logger.info(f"=={self.reInfoParsing.__name__}== 读取路径位是{self.path}")
#         return func(*args, **kwargs)
#
#     return wrapper
#
#
# class LogParsing:
#     def __init__(self, path):
#         self.texts = ' '
#         self.dataDict = {}
#         self.path = path
#         self.save_path = Path(self.path).parent  # 返回父级
#         self.getFilePath()
#
#     def getFilePath(self):
#         """
#         :return: 文件路径，如果存在即删除
#         """
#         xlsxPath = self.save_path / "日志解析数据.xlsx"
#         for (root, dirs, files) in os.walk(self.save_path, topdown=True):
#             if xlsxPath in files:
#                 os.remove(xlsxPath)
#                 # logger.info("存在相同名称日志，删除成功==")
#
#     @autoReadLog
#     def reInfoParsing(self):
#         """
#         :return: info数据筛选
#         """
#         values = re.findall('<.*?>', self.texts)
#         orderValues = list(dict.fromkeys(values))
#         for order, num in zip(orderValues, range(len(orderValues) - 1)):
#             pattern = r"{}([\s\S]*?){}".format(re.escape(values[num]), re.escape(values[num + 1]))
#             datas = re.findall(pattern, self.texts)
#             for data in datas:
#                 # dataValue = re.findall('(.*])(\w*\s*):\s*(.*)', data)
#                 dataValue = re.findall('\[(.*)\]\s*(\w*\s*)\s*:\s*([^\s]*)', data)
#                 if order not in self.dataDict:
#                     self.dataDict[order] = {}
#                     self.dataDict[order]['time'] = []
#
#                 for dataDict in dataValue:
#                     time, key, value = dataDict[0], dataDict[1].strip(), dataDict[2]
#                     if key not in self.dataDict[order]:
#                         self.dataDict[order][key] = []
#                     self.dataDict[order][key].append(value)
#
#                 try:
#                     self.dataDict[order]['time'].append(time)
#
#                 except:
#                     pass
#         # print(self.dataDict)
#         for key in self.dataDict:
#             print([len(self.dataDict[key][k]) for k in self.dataDict[key]])
#
#             # print(len(self.dataDict[key][k]),key)
#         # file_path = self.save_path / "日志解析数据.xlsx"
#         # logger.info(f"写入文件地址是：{file_path}")
#         # self.writerInfoExcel(file_path)
#
#     def writerInfoExcel(self, filePath: str):
#         """`
#         :param filePath: # 存储路径
#         :return:   做数据图
#         """
#         with pd.ExcelWriter(filePath) as writer:
#             for sheet_name, data in self.dataDict.items():
#                 df = pd.DataFrame(data)
#                 for column in df.columns:
#                     if df[column].dtype == object:  # 检查列的数据类型是否为对象类型
#                         try:
#                             # 尝试将值转换为浮点数
#                             df[column] = df[column].astype(float)
#                         except ValueError:
#                             # 转换失败，将值保持为字符串
#                             df[column] = df[column].astype(str)
#                 df.to_excel(writer, sheet_name=sheet_name, index=False)


# if __name__ == '__main__':
#     LogParsing(
#         r"E:\MONITOR_SYSTEM\自动化电池监测日志\S1充电2023_10_30_10_42_31.log").reInfoParsing()
