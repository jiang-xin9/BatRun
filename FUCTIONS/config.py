# -*- coding: utf-8 -*-
# https://blog.csdn.net/weixin_52040868
# 公众号：测个der
# 微信：qing_an_an

import os
import sys

Base_Path = os.path.abspath(os.path.dirname(os.path.abspath(__file__))+'\..')

sys_ = os.path.realpath(os.path.dirname(sys.argv[0]))
JsonPath = os.path.join(sys_, "config.json")
