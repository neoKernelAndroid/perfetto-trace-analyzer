# -*- coding: utf-8 -*-
# @Time     : 2025/9/3 19:09
# @Author   : yunqing.gui
# @Email    : yunqing.gui@transsion.com
# @File     : Utils.py
import re
import traceback

import pandas as pd
import requests

from modules.common.Logger import TEST_LOGGER


def get_cpu_info_from_feishu(tab_tag):
    cpu_core_dict = {}
    cpu_core_max_freq_dict = {}
    cpu_core_computing_power_dict = {}

    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/"
    post_data = {"app_id": "cli_a3c95c7595fc9013",
                 "app_secret": "99h8wsABwGGjzqxhMcplzgDmPloNXO3I"}
    r = requests.post(url, data=post_data, timeout=10)

    # 机器人：设备管理系统
    tat = r.json()["tenant_access_token"]
    header = {"content-type": "application/json", "Authorization": "Bearer " + str(tat)}
    # 要读取的电子表格的URL。
    url_read = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/AYZBsBKDJh7T0atoMPwcP1WJnoh/values/{tab_tag}"

    url = url_read
    r = requests.get(url, headers=header, timeout=10)
    try:
        res = r.json().get("data").get("valueRange").get("values")

        cluster_number = 0
        min_column = 0
        cpu_group_list = []

        line_index = 0
        for line in res:
            line_index += 1

            # 第一行 获取分组数
            if line_index == 1:
                cluster_info = str(line[0])
                cluster_number = int(re.match(r"cluster\s*=\s*(\d+)\s*", cluster_info).group(1))
                min_column = 2 * cluster_number
                TEST_LOGGER.info(f"cluster: {cluster_number}, 最小列数: {min_column}")
            else:
                if len(line) < min_column:
                    raise Exception(f"行[{line_index}] 长度 [{len(line)}] 小于 [{min_column}]")

                # 第二行 获取分组名
                if line_index == 2:
                    for i in range(cluster_number):     # 偶数列记录信息  0， 2， 4 ...
                        cpu_group_list.append(line[2 * i])
                    TEST_LOGGER.info(f"cpu分组: {cpu_group_list}")
                    continue

                # 第三行 获取分组cpu核心编号
                if line_index == 3:
                    for i in range(cluster_number):
                        cpu_core_info_str = line[2 * i]
                        cpu_core_dict[cpu_group_list[i]] = [item.strip() for item in cpu_core_info_str.split(',') if item.strip()]
                    continue

                # 第四行标题，第五行开始读取频点算力信息
                if line_index >= 5:
                    for i in range(cluster_number):

                        if line[2*i] is not None and line[2*i+1] is not None:
                            freq = int(line[2*i])
                            computing_power = int(line[2*i+1])
                            cpu_core_computing_power_dict.setdefault(cpu_group_list[i], {}).update(
                                {
                                    freq: computing_power
                                }
                            )
                            max_freq = cpu_core_max_freq_dict.get(cpu_group_list[i])
                            if max_freq is None or freq > max_freq:
                                cpu_core_max_freq_dict[cpu_group_list[i]] = freq

        TEST_LOGGER.info(f"cpu核心频点算力信息: {cpu_core_computing_power_dict}")
        # 将核心频点算力信息中，每个核心分组的算力字典转换为DF
        for cpu_group, computing_power_dict in cpu_core_computing_power_dict.items():
            df = pd.DataFrame(
                list(computing_power_dict.items()),
                columns=['频率', '算力']
            ).set_index('频率')
            cpu_core_computing_power_dict[cpu_group] = df

        TEST_LOGGER.info(f"cpu核心分组: {cpu_core_dict}")
        TEST_LOGGER.info(f"cpu核心分组最大频率: {cpu_core_max_freq_dict}")

        return True, cpu_core_dict, cpu_core_computing_power_dict, cpu_core_max_freq_dict
    except:
        TEST_LOGGER.error(f"飞书数据获取失败:\n{traceback.format_exc()}")
        return False, None, None, None


if __name__ == '__main__':
    get_cpu_info_from_feishu("c082cd")