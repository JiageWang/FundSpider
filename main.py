# -*- coding: utf-8 -*-
# @Time : 2021/6/5 14:22
# @Author : Jiage Wang
# @Email : 1076050774@qq.com
# @File : main.py

import os
import psutil
import datetime
import threading
from threading import Timer
from functions import get_fund_info, insert_update_mysql, get_fund_evaluation


# 指定每隔一天后执行函数
def update_every_day():
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    memory = round(psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024, 3)
    print("=" * 50)
    print("【更新日期: {}".format(date), end=" | ")
    print("占用内存: {} MB】".format(str(memory).ljust(6, '0')))
    print("线程数：{}".format(len(threading.enumerate())))
    print("-" * 50, end="\n")
    with open("fund_list.txt", 'r') as f:
        fund_list = f.readlines()
        for fund_code in fund_list:
            fund_code = fund_code.strip()
            if not (len(fund_code) == 6 and fund_code.isdigit()):
                continue
            print("开始爬取基金基本信息 {}".format(fund_code), end=" " * 18)
            get_fund_info(fund_code)
            print("【完成】")
    print("开始更新数据库", end=" " * 31)
    insert_update_mysql()
    print("【完成】")
    print("=" * 50, end="\n\n")
    t1 = Timer(60 * 60 * 24, update_every_day)
    t1.start()


def update_every_time():
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    memory = round(psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024, 3)
    print("=" * 50)
    print("【更新日期: {}".format(date), end=" | ")
    print("占用内存: {} MB】".format(str(memory).ljust(6, '0')))
    print("线程数：{}".format(len(threading.enumerate())))
    print("-" * 50, end="\n")
    with open("fund_list.txt", 'r') as f:
        fund_list = f.readlines()
        for fund_code in fund_list:
            fund_code = fund_code.strip()
            if not (len(fund_code) == 6 and fund_code.isdigit()):
                continue
            print("开始爬取基金估值 {}".format(fund_code), end=" " * 22)
            get_fund_evaluation(fund_code)
            print("【完成】")
    print("开始更新数据库", end=" " * 31)
    insert_update_mysql()
    print("【完成】")
    print("=" * 50, end="\n\n")
    t2 = Timer(60, update_every_time)
    t2.start()


if __name__ == "__main__":
    update_every_day()  # 每天更新一次
    update_every_time()  # 每分钟更新一次
