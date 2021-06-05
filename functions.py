# -*- coding: utf-8 -*-
# @Time : 2021/6/5 14:22
# @Author : Jiage Wang
# @Email : 1076050774@qq.com
# @File : functions.py

import re
import json
import requests
from lxml import etree
from datetime import datetime
from collections import OrderedDict

from global_value import global_value


def get_fund_info(fund_code, update_stock=True, update_manager=True, to_file=False):
    """
    查询基金详细信息
    :param fund_code:
    :param update_stock:
    :param update_manager:
    :param to_file:
    :return:
    """

    if not (len(fund_code) == 6 and fund_code.isdigit()):
        return False

    fund_infos = global_value.get("fund_infos")
    manager_infos = global_value.get("manager_infos")
    fund_manager_rlns = global_value.get("fund_manager_rlns")
    fund_data_days = global_value.get("fund_data_days")

    url = "http://fund.eastmoney.com/pingzhongdata/{}.js?v={}".format(fund_code,
                                                                      datetime.now().strftime("%Y%m%d%H%M%S"))  # 详情

    resp = requests.get(url)
    resp_text = resp.text

    if to_file:
        with open("{}.txt".format(fund_code), 'w') as f:
            f.write(resp_text)

    # 获取基金名
    fund_name_pattern = 'fS_name = "(.*?)"'
    fund_name = re.search(pattern=fund_name_pattern, string=resp_text).group(1)

    # 收益率
    fund_income_year_pattern = 'syl_1n="(-?\d*\.\d*|\d*)";'
    fund_income_year = float(re.search(pattern=fund_income_year_pattern, string=resp_text).group(1))
    fund_income_half_year_pattern = 'syl_6y="(-?\d*\.\d*|\d*)";'
    fund_income_half_year = float(re.search(pattern=fund_income_half_year_pattern, string=resp_text).group(1))
    fund_income_three_month_pattern = 'syl_3y="(-?\d*\.\d*|\d*)";'
    fund_income_three_month = float(re.search(pattern=fund_income_three_month_pattern, string=resp_text).group(1))
    fund_income_month_pattern = 'syl_1y="(-?\d*\.\d*|\d*)";'
    fund_income_month = float(re.search(pattern=fund_income_month_pattern, string=resp_text).group(1))

    # 累计净值与设立日期
    unit_money_hist_pattern = "Data_netWorthTrend = (\[.*?\])"
    unit_money_hist = re.search(unit_money_hist_pattern, resp_text).group(1)
    unit_money_hist = json.loads(unit_money_hist)

    build_date_timestamp = unit_money_hist[0]['x'] // 1000
    build_date = datetime.utcfromtimestamp(build_date_timestamp).strftime("%Y%m%d")

    update_date_timestamp = unit_money_hist[-1]['x'] // 1000
    update_date = datetime.utcfromtimestamp(update_date_timestamp).strftime("%Y%m%d")

    unit_money = float(unit_money_hist[-1]['y'])

    equity_return = unit_money_hist[-1]['equityReturn']

    # 资产配置
    asset_alloc_pattern = "Data_assetAllocation = (\{.*?\});"
    asset_alloc = re.search(pattern=asset_alloc_pattern, string=resp_text).group(1)
    asset_alloc = json.loads(asset_alloc)
    asset = float(asset_alloc['series'][3]['data'][-1])

    fund_data_day = OrderedDict({
        "fund_code": fund_code,
        "update_date": update_date,
        "unit_money": unit_money,
        "equity_return": equity_return
    })
    fund_info = OrderedDict({
        "code": fund_code,
        "name": fund_name,
        "build_date": build_date,
        "income_month": fund_income_month,
        "income_three_month": fund_income_three_month,
        "income_half_year": fund_income_half_year,
        "income_year": fund_income_year,
        "unit_money": unit_money,
        "asset": asset
    })
    fund_data_days.append(tuple(fund_data_day.values()))
    fund_infos.append(tuple(fund_info.values()))

    # 基金经理
    if update_manager:
        managers_pattern = "Data_currentFundManager =(\[.*?\]) ;"
        managers = re.search(managers_pattern, resp_text).group(1)
        managers = json.loads(managers)
        for manager in managers:
            manager_code = manager["id"]
            manager_name = manager["name"]
            manager_work_year = process_work_year(manager["workTime"])

            # 添加基金经理
            # 添加基金与经理关系
            manager_info = OrderedDict({
                "code": manager_code,
                "name": manager_name,
                "work_year": manager_work_year
            })
            fund_manager_rln = {
                "fund_code": fund_code,
                "manager_code": manager_code,
            }
            manager_infos.append(tuple(manager_info.values()))
            fund_manager_rlns.append(tuple(fund_manager_rln.values()))

    # 持仓股票列表
    if update_stock:
        stocks_pattern = 'stockCodes=(.+?);'
        stocks = re.search(pattern=stocks_pattern, string=resp_text).group(1)
        stocks = json.loads(stocks)
        for stock in stocks:
            stock_code = stock[:-1]
            # 添加基金股票关系
            # 添加股票
            get_fund_hold_stock(fund_code)

    return True


def get_fund_hold_stock(fund_code, top_n=10):
    """
    获取持仓股票信息
    :param fund_code:
    :param top_n:
    :return:
    """
    if not (len(fund_code) == 6 and fund_code.isdigit()):
        return False
    stock_infos = global_value.get("stock_infos")
    fund_stock_rlns = global_value.get("fund_stock_rlns")
    fund_stock_rln_hists = global_value.get("fund_stock_rln_hists")

    url = "http://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jjcc&code={}&topline={}&year=&month=".format(
        fund_code, top_n)

    resp = requests.get(url)
    resp_text = resp.text

    data_pattern = "var apidata=(\{.*\});"
    data = re.search(pattern=data_pattern, string=resp_text).group(1)
    data = data.replace("content", '"content"')
    data = data.replace("arryear", '"arryear"')
    data = data.replace("curyear", '"curyear"')
    data = json.loads(data)
    content_html = data["content"]
    content_html = etree.HTML(content_html)
    date_element = content_html.xpath("//font")[0]
    update_date = date_element.text.replace("-", "")

    code_elements = content_html.xpath("//tbody/tr/td[2]/a")
    name_elements = content_html.xpath("//tbody/tr/td[3]/a")
    percent_elements = content_html.xpath("//tbody/tr/td[last()-2]")
    for code, name, percent in zip(code_elements, name_elements, percent_elements):
        stock_code = code.text
        stock_name = name.text
        hold_percent = float(percent.text[:-1])
        stock_info = {
            "code": stock_code,
            "name": stock_name,
        }
        fund_stock_rln = {
            "fund_code": fund_code,
            "stock_code": stock_code,
            "hold_percent": hold_percent
        }
        fund_stock_rln_hist = {
            "fund_code": fund_code,
            "stock_code": stock_code,
            "hold_percent": hold_percent,
            "update_date": update_date
        }
        stock_infos.append(tuple(stock_info.values()))
        fund_stock_rlns.append(tuple(fund_stock_rln.values()))
        fund_stock_rln_hists.append(tuple(fund_stock_rln_hist.values()))


def get_fund_evaluation(fund_code):
    """
    查询基金估值
    :param fund_code:
    :return:
    """

    if not (len(fund_code) == 6 and fund_code.isdigit()):
        return False

    fund_data_times = global_value.get("fund_data_times")

    timestamp = int(datetime.now().timestamp() * 1000)
    url = "http://fundgz.1234567.com.cn/js/{}.js?rt={}".format(fund_code, timestamp)  # 基本信息
    resp = requests.get(url)
    resp_text = resp.text
    data_pattern = "npgz\((.*)\);"
    data = re.search(pattern=data_pattern, string=resp_text).group(1)
    data = json.loads(data)
    unit_money_evaluation = float(data["gsz"])
    equity_return_evaluation = float(data['gszzl'])
    update_time = data["gztime"][-5:]
    update_time = update_time.replace(":", "")
    update_day = data["gztime"][:10]
    update_day = update_day.replace("-", "")

    fund_data_time = {
        "fund_code": fund_code,
        "update_time": update_time,
        "unit_money_evaluation": unit_money_evaluation,
        "equity_return_evaluation": equity_return_evaluation,
        "update_day": update_day,
    }
    fund_data_times.append(tuple(fund_data_time.values()))


def process_work_year(work_year="15年又202天"):
    return int(work_year[: work_year.find("年")])


def add_fund_code(fund_code):
    if not (len(fund_code) == 6 and fund_code.isdigit()):
        print("基金代码格式错误")
        return
    with open("fund_list.txt", 'r') as f:
        fund_list = f.readlines()
        for fund in fund_list:
            fund = fund.strip()
            if not (fund.isdigit() and len(fund) == 6):
                continue
            if fund == fund_code:
                print("基金已存在")
                return
    with open("fund_list.txt", 'a') as f:
        f.write("\n{}".format(fund_code))
    print("添加基金成功！")


def insert_update_mysql():
    conn = global_value.get("conn")
    fund_infos = global_value.get("fund_infos")
    stock_infos = global_value.get("stock_infos")
    fund_stock_rlns = global_value.get("fund_stock_rlns")
    fund_stock_rln_hists = global_value.get("fund_stock_rln_hists")
    manager_infos = global_value.get("manager_infos")
    fund_manager_rlns = global_value.get("fund_manager_rlns")
    fund_data_days = global_value.get("fund_data_days")
    fund_data_times = global_value.get("fund_data_times")
    # 获取游标
    cursor = conn.cursor()
    # 执行语句
    if len(fund_infos) > 0:
        cursor.executemany(
            """
            INSERT INTO FUND_INFO( CODE, NAME, BUILD_DATE, INCOME_MONTH, INCOME_THREE_MONTH, INCOME_HALF_YEAR, INCOME_YEAR, UNIT_MONEY, ASSET) 
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE
                INCOME_MONTH = VALUES(INCOME_MONTH),
                INCOME_THREE_MONTH = VALUES(INCOME_THREE_MONTH),
                INCOME_HALF_YEAR = VALUES(INCOME_HALF_YEAR),
                INCOME_YEAR = VALUES(INCOME_YEAR),
                UNIT_MONEY = VALUES(UNIT_MONEY)
            """,
            fund_infos
        )  # 有则更新，没有插入
        global_value.set("fund_infos", [])

    if len(stock_infos) > 0:
        cursor.executemany(
            """
                INSERT INTO STOCK_INFO(CODE, NAME) 
                values(%s,%s) ON DUPLICATE KEY UPDATE 
                    NAME=VALUES(NAME)
            """,
            stock_infos
        )
        global_value.set("stock_infos", [])

    if len(fund_stock_rlns) > 0:
        cursor.executemany(
            """
                INSERT INTO FUND_STOCK_RLN(FUND_CODE, STOCK_CODE, HOLD_PERCENT) 
                values(%s,%s,%s) ON DUPLICATE KEY UPDATE 
                    HOLD_PERCENT=VALUES(HOLD_PERCENT)
            """,
            fund_stock_rlns
        )  # 忽略重复的数据
        global_value.set("fund_stock_rlns", [])

    if len(fund_stock_rln_hists) > 0:
        cursor.executemany(
            """
                INSERT INTO FUND_STOCK_RLN_HIST(FUND_CODE, STOCK_CODE, HOLD_PERCENT, UPDATE_DATE) 
                values(%s,%s,%s,%s) ON DUPLICATE KEY UPDATE 
                    HOLD_PERCENT=VALUES(HOLD_PERCENT)
            """,
            fund_stock_rln_hists
        )  # 忽略重复的数据
        global_value.set("fund_stock_rln_hists", [])

    if len(manager_infos) > 0:
        cursor.executemany(
            """
                INSERT IGNORE INTO MANAGER_INFO(CODE, NAME, WORK_YEAR) 
                values(%s,%s,%s) ON DUPLICATE KEY UPDATE 
                    WORK_YEAR=VALUES(WORK_YEAR)
            """,
            manager_infos
        )
        global_value.set("manager_infos", [])

    if len(fund_manager_rlns) > 0:
        cursor.executemany(
            "INSERT IGNORE INTO FUND_MANAGER_RLN(FUND_CODE, MANAGER_CODE) VALUES(%s,%s)",
            fund_manager_rlns
        )  # 忽略重复的数据
        global_value.set("fund_manager_rlns", [])

    if len(fund_data_days) > 0:
        cursor.executemany(
            """
                INSERT INTO FUND_DATA_DAY(FUND_CODE, UPDATE_DATE, UNIT_MONEY, EQUITY_RETURN) 
                VALUES(%s,%s,%s,%s) ON DUPLICATE KEY UPDATE 
                    UNIT_MONEY=VALUES(UNIT_MONEY), 
                    EQUITY_RETURN=VALUES(EQUITY_RETURN)
            """,
            fund_data_days
        )
        global_value.set("fund_data_days", [])

    if len(fund_data_times) > 0:
        cursor.executemany(
            """
                INSERT INTO FUND_DATA_TIME(FUND_CODE, UPDATE_TIME, UNIT_MONEY_EVALUATION, EQUITY_RETURN_EVALUATION, UPDATE_DATE) 
                VALUES(%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE 
                    UNIT_MONEY_EVALUATION=VALUES(UNIT_MONEY_EVALUATION), 
                    EQUITY_RETURN_EVALUATION=VALUES(EQUITY_RETURN_EVALUATION),
                    UPDATE_DATE=VALUES(UPDATE_DATE)
            """,
            fund_data_times
        )
        global_value.set("fund_data_times", [])

    # 提交
    conn.commit()
    # 关闭游标
    cursor.close()


if __name__ == "__main__":
    fund_codes = ["005827", "002943", "002190", "001102", "260112", "004997", "003834", "260108", "161005", "163406"]
    add_fund_code("002943")
    # get_fund_evaluation("260108")
