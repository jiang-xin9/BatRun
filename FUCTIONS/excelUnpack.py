# -*- coding: utf-8 -*-
# https://blog.csdn.net/weixin_52040868
# 公众号：测个der
# 微信：qing_an_an

import re
import os
import pandas as pd
from PyQt5.QtCore import QThread
from pathlib import Path

class LogParsingThread(QThread):

    def __init__(self, path):
        super().__init__()
        self.log = LogParsing(path)

    def run(self):
        self.log.reInfoParsing()
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

    @autoReadLog
    def reInfoParsing(self):
        """
        :return: info数据筛选
        """
        values = re.findall('<.*?>', self.texts)
        orderValues = list(dict.fromkeys(values))
        for order, num in zip(orderValues, range(len(orderValues) - 1)):
            pattern = r"{}([\s\S]*?){}".format(re.escape(values[num]), re.escape(values[num + 1]))
            datas = re.findall(pattern, self.texts)
            for data in datas:
                # dataValue = re.findall('(.*])(\w*\s*):\s*(.*)', data)
                dataValue = re.findall('\[(.*)\]\s*(\w*\s*)\s*:\s*([^\s]*)', data)
                if order not in self.dataDict:
                    self.dataDict[order] = {}
                    self.dataDict[order]['time'] = []

                for dataDict in dataValue:
                    time, key, value = dataDict[0], dataDict[1].strip(), dataDict[2]
                    if key not in self.dataDict[order]:
                        self.dataDict[order][key] = []
                    self.dataDict[order][key].append(value)

                self.dataDict[order]['time'].append(time)

        self.writerInfoExcel(self.save_path / "日志解析数据.xlsx")

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
#     LogParsing().reInfoParsing()