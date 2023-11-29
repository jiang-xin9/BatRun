# -*- coding: utf-8 -*-
# https://blog.csdn.net/weixin_52040868
# 公众号：测个der
# 微信：qing_an_an

import re
import os
import pandas as pd
from PyQt5.QtCore import QThread
from pathlib import Path
from FUCTIONS.Loging import logger

class LogParsingThread(QThread):

    def __init__(self, path):
        super().__init__()
        self.log = LogParsing(path)

    def run(self):
        # logger.info(f"{__class__.__name__}启动成功")
        self.log.reInfoParsing()
        logger.info("== 执行reInfoParsing ==")
        self.exec_()

    def stop(self):
        # 停止线程的方法
        self.quit()
        self.wait()


def autoReadLog(func):
    def wrapper(*args, **kwargs):
        self = args[0]
        with open(self.path, 'r', encoding='utf-8') as r:
            self.texts = r.read()
            logger.info(f"=={self.reInfoParsing.__name__}== 读取路径位是{self.path}")
        return func(*args, **kwargs)

    return wrapper


class LogParsing:
    def __init__(self, path):
        self.texts = ' '
        self.dataDict = {}
        self.path = path
        self.save_path = Path(self.path).parent # 返回父级
        self.getFilePath()

    def getFilePath(self):
        """
        :return: 文件路径，如果存在即删除
        """
        xlsxPath = self.save_path / "日志解析数据.xlsx"
        for (root, dirs, files) in os.walk(self.save_path, topdown=True):
            if xlsxPath in files:
                os.remove(xlsxPath)
                logger.info("存在相同名称日志，删除成功==")

    @autoReadLog
    def reInfoParsing(self):
        """
        :return: info数据筛选
        """
        values = re.findall('<.*?>', self.texts)
        orderValues = list(dict.fromkeys(values))
        for order, num in zip(orderValues, range(len(orderValues) - 1)):
            pattern = r"{}([\s\S]*?){}".format(re.escape(values[num]), re.escape(values[num + 1]))
            # pattern = r"{}([\s\S]*?){}".format("<motor>", "<imu>")
            datas = re.findall(pattern, self.texts)
            for data in datas:
                # dataValue = re.findall('(.*])(\w*\s*):\s*(.*)', data)
                dataValue = re.findall('\[(.*)\]\s*(\w*\s*)\s*:\s*([^\s]*)', data)
                if order not in self.dataDict:
                    self.dataDict[order] = {}
                    self.dataDict[order]['time'] = []

                for dataDict in dataValue:
                    # 应该先把所有的key拿到，再匹配值，可以避免匹配不到的时候需要额外处理
                    time, key, value = dataDict[0], dataDict[1].strip(), dataDict[2]
                    # print(time, key, value)
                    if not key:
                        # self.dataDict[order]["default_key"] = value
                        continue
                    # if not value:
                    #     self.dataDict[order][key] = "default_value"
                    if key not in self.dataDict[order]:
                        self.dataDict[order][key] = []
                    self.dataDict[order][key].append(value)
                try:
                    self.dataDict[order]['time'].append(time)
                except:
                    logger.error("！！！时间模块不正确，解析不成功！！！")

        # print(orderValues)
        # for i in orderValues:
            # print(i)
        # print(self.dataDict)
        try:
            file_path = self.save_path / "日志解析数据.xlsx"
            logger.info(f"==写入文件==地址是：{file_path}")
            self.writerInfoExcel(file_path)
        except:
            logger.error("！！！数据长度不一致，数据有缺失！！！")

    def writerInfoExcel(self, filePath: str):
        """`
        :param filePath: # 存储路径
        :return:   做数据图
        """
        with pd.ExcelWriter(filePath) as writer:
            for sheet_name, data in self.dataDict.items():
                df = pd.DataFrame(data)
                for column in df.columns:
                    if df[column].dtype == object:  # 检查列的数据类型是否为对象类型
                        try:
                            # 尝试将值转换为浮点数
                            df[column] = df[column].astype(float)
                        except ValueError:
                            # 转换失败，将值保持为字符串
                            df[column] = df[column].astype(str)
                df.to_excel(writer, sheet_name=sheet_name, index=False)

# if __name__ == '__main__':
    # LogParsing(r"C:\Users\admin\Desktop\爬墙2.log").reInfoParsing()
