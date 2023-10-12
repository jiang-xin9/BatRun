# -*- coding: utf-8 -*-
# https://blog.csdn.net/weixin_52040868
# 公众号：测个der
# 微信：qing_an_an

import json
import os
from FUCTIONS.config import JsonPath, other_JsonPath


class JSONREAD:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        '''如果是第一次调用，读取Json文件，否则直接返回之前保存的数据'''
        if os.path.exists(JsonPath):
            self.path = JsonPath
        else:
            raise FileNotFoundError('Json文件不存在')

    @staticmethod
    def getData(value, prompt=" "):
        with open(JsonPath, "r", encoding='utf-8') as json_file:
            JsonData = json.load(json_file)
        return JsonData.get(value, prompt)

    @staticmethod
    def get_datas(path):
        with open(path, "r", encoding='utf-8') as json_file:
            Json_data = json.load(json_file)
        return Json_data

# if __name__ == '__main__':
#     print(JSONREAD().get_datas(other_JsonPath)["CutValue"])