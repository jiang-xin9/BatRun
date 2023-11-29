# -*- coding: utf-8 -*-
# https://blog.csdn.net/weixin_52040868
# 公众号：测个der
# 微信：qing_an_an
"""
钉钉通知封装
"""
import base64
import hashlib
import hmac
import json
import time
from datetime import datetime
import urllib.parse
from typing import Any, Text
from requests.exceptions import HTTPError, ProxyError
import requests
from dingtalkchatbot.chatbot import DingtalkChatbot, FeedLink
from FUCTIONS.ReadConfig import JSONREAD
from FUCTIONS.config import JsonPath
from FUCTIONS.Loging import logger,ExecuteDecorator


# def ReadJson(FilePath):
#     with open(FilePath, "r", encoding='utf-8') as json_file:
#         JsonData = json.load(json_file)
#     return JsonData


class DingTalkSendMsg:

    def __init__(self):
        self.timeStamp = str(round(time.time() * 1000))
        """ 发送钉钉通知 """
        # self.JsonData = ReadJson(JsonPath)
        self.JsonData = JSONREAD()

    def xiao_ding(self):
        sign = self.get_sign()
        # 从yaml文件中获取钉钉配置信息
        webhook = self.JsonData.getData("hook_url") + "&timestamp=" + self.timeStamp + "&sign=" + sign
        return DingtalkChatbot(webhook, fail_notice=True)

    def get_sign(self) -> Text:
        """
        根据时间戳 + "sign" 生成密钥
        :return:
        """
        string_to_sign = f'{self.timeStamp}\n{self.JsonData.getData("secret")}'.encode('utf-8')
        hmac_code = hmac.new(
            self.JsonData.getData("secret").encode('utf-8'),
            string_to_sign,
            digestmod=hashlib.sha256).digest()

        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return sign

    def send_text(
            self,
            msg: Text,
            mobiles=None
    ) -> None:
        """
        发送文本信息
        :param msg: 文本内容
        :param mobiles: 艾特用户电话
        :return:
        """
        if not mobiles:
            self.xiao_ding().send_text(msg=msg, is_at_all=True)
        else:
            if isinstance(mobiles, list):
                self.xiao_ding().send_text(msg=msg, at_mobiles=mobiles)
            else:
                raise TypeError("mobiles类型错误 不是list类型.")

    def send_link(
            self,
            title: Text,
            text: Text,
            message_url: Text,
            pic_url: Text
    ) -> None:
        """
        发送link通知
        :return:
        """
        self.xiao_ding().send_link(
            title=title,
            text=text,
            message_url=message_url,
            pic_url=pic_url
        )

    @ExecuteDecorator
    def send_markdown(
            self,
            title: Text,
            msg: Text,
            mobiles=None,
            is_at_all=False,
            at_dingtalk_ids=None
    ) -> None:
        """

        :param is_at_all:
        :param mobiles:
        :param title:
        :param msg:
        markdown 格式
        """
        try:
            if mobiles is None:
                self.xiao_ding().send_markdown(title=title, text=msg, is_at_all=is_at_all,
                                               at_dingtalk_ids=at_dingtalk_ids)
            else:
                if isinstance(mobiles, list):
                    self.xiao_ding().send_markdown(title=title, text=msg, at_mobiles=mobiles)
                else:
                    logger.error("mobiles类型错误 不是list类型.")
        except ProxyError as e:
            logger.error(f"网络异常 {e}")

    @staticmethod
    def feed_link(
            title: Text,
            message_url: Text,
            pic_url: Text
    ) -> Any:
        """ FeedLink 二次封装 """
        return FeedLink(
            title=title,
            message_url=message_url,
            pic_url=pic_url
        )

    def send_feed_link(self, *arg) -> None:
        """发送 feed_lik """
        self.xiao_ding().send_feed_card(list(arg))

    def send_ding_notification(self, message, mobiles=None):
        """ 发送钉钉报告通知 """
        DingTalkSendMsg().send_markdown(
            title="[测试完成]",
            msg=message,
            is_at_all=False,
            mobiles=mobiles
        )

# if __name__ == '__main__':
    # JsonData = ReadJson(r'E:\\MONITOR_SYSTEM\\config.json')
#     print(JsonData.get("Devices", ""))
#     message = "此为'配置文件艾特指定人'测试信息"
#     DingTalkSendMsg().send_ding_notification(message)

