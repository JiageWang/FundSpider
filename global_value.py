# -*- coding: utf-8 -*-
# @Time : 2021/6/5 14:22
# @Author : Jiage Wang
# @Email : 1076050774@qq.com
# @File : global_value.py

import json
import pymysql


# 存储全局变量，跨文件传输
class GlobalValue:
    value_map = {}

    def set(self, key, value):
        if (isinstance(value, dict)):
            value = json.dumps(value)
        self.value_map[key] = value

    def delete(self, key):
        try:
            del self.value_map[key]
            return self.value_map
        except KeyError as msg:
            pass
            # raise msg
            # log.error("key:'" + str(key) + "'  不存在")

    def get(self, key):
        try:
            return self.value_map[key]
        except KeyError:
            # log.warning("key:'" + str(key) + "'  不存在")
            return 'Null_'


global_value = GlobalValue()
# 创建连接
conn = pymysql.connect(
    host="localhost",
    port=3306,
    user="root",
    passwd="password",
    db="funddb",
    charset="utf8"
)
global_value.set("conn", conn)
global_value.set("fund_infos", [])
global_value.set("stock_infos", [])
global_value.set("fund_stock_rlns", [])
global_value.set("fund_stock_rln_hists", [])
global_value.set("manager_infos", [])
global_value.set("fund_manager_rlns", [])
global_value.set("fund_data_days", [])
global_value.set("fund_data_times", [])
