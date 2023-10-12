# -*- coding: utf-8 -*-
# https://blog.csdn.net/weixin_52040868
# 公众号：测个der
# 微信：qing_an_an

import os
import sys
import datetime
from pathlib import Path

Base_Path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + '\..')
sys_ = os.path.realpath(os.path.dirname(sys.argv[0]))
LogTime = datetime.datetime.now().strftime("%H_%M_%S")
JsonPath = os.path.join(sys_, "config.json")
# ExecuteLog = os.path.join(FatherPath(), "执行日志.log")
ExecuteLog = os.path.join(sys_, f"{LogTime}执行日志.log")

moudule_path = Path(__file__).resolve()
check_path = moudule_path.parent.parent
other_JsonPath = check_path / "config.json"

def FatherPath(path):
    """父级路径"""
    return os.path.split(path)[0]


def GetFile():
    try:
        for filename in os.listdir(sys_):
            if filename.endswith(".log"):
                log_path = os.path.join(sys_, filename)
                if os.path.exists(log_path):
                    os.remove(log_path)
    except:
        pass


def GetJsonFile(path):
    FileList = []
    FatherFiles = os.path.normpath(FatherPath(path))  # 规范化路径
    try:
        for filename in os.listdir(FatherFiles):
            if filename.endswith(".json"):
                File = os.path.join(FatherFiles, filename)
                FileList.append(File)
        return FileList
    except:
        pass
