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
        """获取指定数据"""
        with open(JsonPath, "r", encoding='utf-8') as json_file:
            JsonData = json.load(json_file)
        return JsonData.get(value, prompt)

    @staticmethod
    def get_datas(path):
        """获取数据"""
        with open(path, "r", encoding='utf-8') as json_file:
            Json_data = json.load(json_file)
        return Json_data

    def write_datas(self, datas):
        """写入数据"""
        with open(JsonPath, "w", encoding='utf-8') as json_file:
            json.dump(datas, json_file, indent=4, ensure_ascii=False)

    def update_datas(self, value, data):
        """更新数据"""
        new_data = {value : data}
        read_data = self.get_datas(JsonPath)
        read_data.update(new_data)   # 更新时间
        self.write_datas(read_data)  # 写入新数据
        return new_data

    def is_key_present(self, key):
        """判断是否存在一个键"""
        return key in self.get_datas(JsonPath)

# if __name__ == '__main__':
#     g = JSONREAD().is_key_present("Day")
#     print(g)
#     print(JSONREAD().get_datas(other_JsonPath)["CutValue"])