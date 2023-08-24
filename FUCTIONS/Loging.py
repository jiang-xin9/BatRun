# -*- coding: utf-8 -*-
# https://blog.csdn.net/weixin_52040868
# 公众号：测个der
# 微信：qing_an_an

import logging
from FUCTIONS.config import ExecuteLog
from FUCTIONS.config import GetFile

class Log:
    def __init__(self):
        # 初始化日志记录器
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    @property
    def AddFileHandler(self):
        GetFile(ExecuteLog)
        # 创建一个文件处理程序，将日志写入指定文件
        FileHandler = logging.FileHandler(ExecuteLog, encoding='utf-8')
        FileHandler.setLevel(logging.INFO)

        # 创建一个格式化器，定义日志记录的格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        FileHandler.setFormatter(formatter)

        # 将文件处理程序添加到记录器
        self.logger.addHandler(FileHandler)
        return self.logger

# if __name__ == '__main__':
logger = Log().AddFileHandler

# 执行日志
def ExecuteDecorator(func):
    def wrapper(*args, **kwargs):
        # 记录函数的输入参数
        logger.info(f"函数输入参数 - {args} {kwargs}")
        try:
            # 执行原始函数
            result = func(*args, **kwargs)
            # 记录函数的执行结果
            logger.info(f"函数执行结果: {result}")
            return result
        except Exception as e:
            # 记录异常信息
            logger.error(f"函数执行出现异常: {e}")
            raise e
    return wrapper
