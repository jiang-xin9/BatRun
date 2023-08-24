# -*- coding: utf-8 -*-
# https://blog.csdn.net/weixin_52040868
# 公众号：测个der
# 微信：qing_an_an

import os
import sys

Base_Path = os.path.abspath(os.path.dirname(os.path.abspath(__file__))+'\..')
sys_ = os.path.realpath(os.path.dirname(sys.argv[0]))

def FatherPath():
    """父级路径"""
    return os.path.split(sys_)[0]

JsonPath = os.path.join(sys_, "config.json")
# ExecuteLog = os.path.join(FatherPath(), "执行日志.log")
ExecuteLog = os.path.join(sys_, "执行日志.log")

def GetFile(path):
    if os.path.exists(path):
        os.remove(path)