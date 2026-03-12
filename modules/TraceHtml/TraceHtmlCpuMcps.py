# -*- coding: utf-8 -*-
# @Time     : 2025/8/15 13:56
# @Author   : yunqing.gui
# @Email    : yunqing.gui@transsion.com
# @File     : TraceHtml.py
import json
import os.path
import re

import numpy as np
import pandas as pd

from modules.common.Excel import McpsExcel
from modules.common.Logger import TEST_LOGGER
from modules.common.Path import PathManager
from modules.common.Utils import get_cpu_info_from_feishu
from modules.TraceHtml.SurfaceFlingerAnalysis import SurfaceFlingerAnalysis

MCPS_VERSION = "1.0.0"

cpu_core_dict = {}
cpu_core_computing_power_dict = {}
cpu_core_max_freq_dict = {}


class TraceHtmlCpuMcps:
    def __init__(self, html_file_path, cpu_type, task_name_list, process_name, animation_tag):
        self._html_file_path = html_file_path
        self._cpu_type = cpu_type
        self._task_name_list = task_name_list
        self._process_name = process_name
        self._animation_tag = animation_tag
        self._target_pgid = None

        # 用于定位动效开始和结束的参数
        self._start_thread_name = None
        self._start_process_name = None
        self._start_pid = None
        self._start_pgid = None
        self._start_tag = None
        self._start_tag_index = None
        self._ms_after_start = None
        self._end_thread_name = None
        self._end_process_name = None
        self._end_pid = None
        self._end_pgid = None
        self._end_tag = None
        self._end_tag_index = None
        self._start_animation_time_list = []
        self._end_animation_time_list = []
        self._end_animation_time_calculate_dict = {}
        self._start_animation_time = None
        self._end_animation_time = None
        self._animation_thread_name = None
        self._animation_pid = None
        self._doframe_time_list = []
        self._task_frame_count_dict = {}  # {task_name: {'frame_count': int, 'frame_thread_name': str}}
        self._gpu_frame_count = 0  # GPU 帧数
        self._gpu_total_time = 0.0  # GPU 总时间
        self._gpu_avg_time_per_frame = 0.0  # GPU 平均每帧耗时
        self._gpu_waiting_intervals = []  # GPU waiting 时间区间列表 [(start, end, duration, vsync_id), ...]
        self._gpu_frequency_intervals = []  # GPU 频率区间列表 [(freq, start, end, duration), ...]
        self._gpu_load = 0.0  # GPU 负载 (MCPS = 时间 × 频率)
        
        # SurfaceFlinger 分析结果
        self._sf_analysis_result = None
        self._sf_gpu_frame_count = 0  # SurfaceFlinger GPU 帧数
        self._sf_gpu_total_time = 0.0  # SurfaceFlinger GPU 总时间
        self._sf_gpu_avg_time_per_frame = 0.0  # SurfaceFlinger GPU 平均每帧耗时
        self._sf_frame_layer_info = []  # SurfaceFlinger 每帧的 layer 信息

    def analyse(self):

        if not self._init():
            TEST_LOGGER.info("初始化失败，退出解析")
            return

        cpu_frequency_dict = {}         # 用于计算每个CPU核的频率变化字典
        cpu_frequency_df_dict = {}      # 将 cpu_frequency_dict 转化为 DataFrame
        org_data_by_cpu = {}            # 原始的按cpu_id分组的数据
        task_slice_by_cpu = {}          # 每个task执行时间段，按cpu_id分组

        """
        定义正则表达式
        """
        pattern_cpu_frequency = re.compile(r"(\d+\.\d+):\s+cpu_frequency: state=(\d+)\s+cpu_id=(\d+)")
        pattern_gpu_frequency = re.compile(r"(\d+\.\d+):\s+gpu_frequency:.*?state=(\d+)")  # GPU频率变化
        pattern_sched_switch = re.compile(r"\(([^)]+)\)\s+\[(\d+)\] .*?(\d+\.\d+):\s+sched_switch: prev_comm=(.*?)prev_pid=(\d+).*?next_comm=(.*?)next_pid=(\d+)")
        pattern_task_rename = re.compile(r"\(([^)]+)\)\s+\[(\d+)\] .*?(\d+\.\d+):\s+task_rename: pid=(\d+) oldcomm=(.*?)newcomm=(.*?)oom_score_adj")

        """
        读取文件，获取原始数据
        """
        gpu_frequency_dict = {}  # GPU频率变化字典 {timestamp: frequency}
        with open(self._html_file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f.readlines():
                line = line.strip()

                """
                获取CPU频率变化数据
                re.compile(r"(\d+\.\d+):\s+cpu_frequency: state=(\d+)\s+cpu_id=(\d+)")
                """
                matches = re.search(pattern_cpu_frequency, line)
                if matches:
                    timestamp = float(matches.group(1))
                    cpu_freq_state = int(matches.group(2))
                    cpu_id = str(matches.group(3)).zfill(3)     # 填充到3位
                    cpu_frequency_dict.setdefault(cpu_id, {}).update({
                        timestamp: cpu_freq_state
                    })
                    continue

                """
                获取GPU频率变化数据
                re.compile(r"(\d+\.\d+):\s+gpu_frequency:.*?state=(\d+)")
                """
                matches = re.search(pattern_gpu_frequency, line)
                if matches:
                    timestamp = float(matches.group(1))
                    gpu_freq_state = int(matches.group(2))
                    gpu_frequency_dict[timestamp] = gpu_freq_state
                    continue

                """
                sched_switch行 获取task开始与结束时间
                AsyncTask #5-27136 (  26239) [004] d..2.  9038.330085: sched_switch: prev_comm=AsyncTask #5 prev_pid=27136 prev_prio=130 prev_state=S ==> next_comm=binder:2671_B next_pid=3415 next_prio=130
                [004] --- 执行的CPU id
                9038.330085 --- 时间点
                prev_comm=AsyncTask #5 --- 表示前一个执行的任务名
                prev_pid=27136 --- 表示前一个执行的任务pid
                next_comm=binder:2671_B --- 下一个执行的任务名
                next_pid=3415 --- 下一个执行的任务pid
                
                re.compile(r"\(\s+(\d+)\)\s+\[(\d+)\] .*?(\d+\.\d+):\s+sched_switch: prev_comm=(.*?)prev_pid=(\d+).*?next_comm=(.*?)next_pid=(\d+)")
                """
                matches = re.search(pattern_sched_switch, line)
                if matches:
                    pgid = str(matches.group(1)).strip()
                    cpu_id = str(matches.group(2))
                    timestamp = float(matches.group(3))
                    prev_comm = str(matches.group(4)).strip()
                    prev_pid = str(matches.group(5))
                    next_comm = str(matches.group(6)).strip()
                    next_pid = str(matches.group(7))
                    org_data_by_cpu.setdefault(cpu_id, []).append(OriginData("sched_switch", pgid, cpu_id, timestamp, prev_comm, prev_pid, next_comm, next_pid, line))

                    # 获取指定进程的pgid
                    if self._target_pgid is None and self._process_name and self._process_name == prev_comm:
                        TEST_LOGGER.info(f"获取指定进程{self._process_name}的PGID：{pgid}")
                        self._target_pgid = pgid

                    # 获取用于统计帧数的进程pid
                    if self._animation_pid is None and self._animation_thread_name and self._animation_thread_name == prev_comm:
                        TEST_LOGGER.info(f"获取动效主线程{self._animation_thread_name}的PGID：{pgid}")
                        self._animation_pid = pgid

                    # 获取动效开始的进程pgid
                    if self._start_pgid is None and self._start_process_name and self._start_process_name == prev_comm:
                        TEST_LOGGER.info(f"获取动效开始进程{self._start_process_name}的PGID：{pgid}")
                        self._start_pgid = pgid

                    # 获取动效开始线程的pid
                    if self._start_pid is None and self._start_pgid and self._start_pgid == pgid and self._start_thread_name == prev_comm:
                        TEST_LOGGER.info(f"获取动效开始线程{self._start_thread_name}的PID：{prev_pid}")
                        self._start_pid = prev_pid

                    # 获取动效结束的进程pgid
                    if self._end_pgid is None and self._end_process_name and self._end_process_name == prev_comm:
                        TEST_LOGGER.info(f"获取动效结束进程{self._end_process_name}的PGID：{pgid}")
                        self._end_pgid = pgid

                    # 获取动效结束线程的pid
                    if self._end_pid is None and self._end_pgid and self._end_pgid == pgid and self._end_thread_name == prev_comm:
                        TEST_LOGGER.info(f"获取动效结束线程{self._end_thread_name}的PID：{prev_pid}")
                        self._end_pid = prev_pid
                    continue

                """
                task_rename行 获取task是否在执行过程重命名过
                 shell svc 27388-27389 (   3616) [003] ...1.  9038.330667: task_rename: pid=27389 oldcomm=adbd newcomm=shell svc 27388 oom_score_adj=-1000
                [003] --- 执行的CPU id
                9038.330667 --- 时间点
                pid=27389 --- 表示当前执行的任务pid
                oldcomm=adbd --- 表示重命名前的任务名
                newcomm=shell svc 27388 --- 表示重命名后的任务名
                
                re.compile(r"\(\s+(\d+)\)\s+\[(\d+)\] .*?(\d+\.\d+):\s+task_rename: pid=(\d+) oldcomm=(.*?)newcomm=(.*?)oom_score_adj")
                """
                matches = re.search(pattern_task_rename, line)
                if matches:
                    pgid = str(matches.group(1))
                    cpu_id = str(matches.group(2))
                    timestamp = float(matches.group(3))
                    pid = str(matches.group(4))
                    oldcomm = str(matches.group(5)).strip()
                    newcomm = str(matches.group(6)).strip()
                    org_data_by_cpu.setdefault(cpu_id, []).append(OriginData("task_rename", pgid, cpu_id, timestamp, oldcomm, pid, newcomm, pid, line))
                    continue

        """
        根据配置的tag，获取指定tag的时间点列表
        """
        if self._animation_tag:
            TEST_LOGGER.info(f"指定动效tag:{self._animation_tag}，开始获取动效开始与结束时间")
            
            # 特殊处理 __FULL_TRACE__ 配置
            if self._animation_tag == "__FULL_TRACE__":
                TEST_LOGGER.info(f"检测到 __FULL_TRACE__ 配置，将使用 sched_switch 事件的时间范围")
                # 从 org_data_by_cpu 中获取第一个和最后一个 sched_switch 事件的时间
                all_timestamps = []
                for cpu_id, origin_data_list in org_data_by_cpu.items():
                    for origin_data in origin_data_list:
                        if origin_data.data_type == "sched_switch":
                            all_timestamps.append(origin_data.timestamp)
                
                if all_timestamps:
                    all_timestamps.sort()
                    self._start_animation_time = all_timestamps[0]
                    self._end_animation_time = all_timestamps[-1]
                    TEST_LOGGER.info(f"__FULL_TRACE__ 模式：从 sched_switch 事件中获取时间范围")
                    TEST_LOGGER.info(f"  开始时间: {self._start_animation_time}")
                    TEST_LOGGER.info(f"  结束时间: {self._end_animation_time}")
                    TEST_LOGGER.info(f"  总时长: {self._end_animation_time - self._start_animation_time:.6f} 秒")
                else:
                    TEST_LOGGER.error(f"__FULL_TRACE__ 模式：未找到任何 sched_switch 事件")
                    return

            # 优先使用 animation_thread_name 来匹配 doFrame（更准确）
            if self._animation_thread_name:
                # 使用线程名格式：wmshell.anim.*?(\d+\.\d+).*?Choreographer#doFrame
                pattern_doframe_tag = rf"{re.escape(self._animation_thread_name)}.*?(\d+\.\d+).*?Choreographer#doFrame"
                TEST_LOGGER.info(f"使用线程名 {self._animation_thread_name} 匹配 doFrame")
            else:
                # 回退到使用 PID 格式
                pattern_doframe_tag = r"-pid.*?(\d+\.\d+):\s+tracing_mark_write.*?Choreographer#doFrame"
                # 如果 animation_pid 未找到，尝试使用 start_pid 或 end_pid
                doframe_pid = self._animation_pid
                if doframe_pid is None:
                    doframe_pid = self._start_pid
                if doframe_pid is None:
                    doframe_pid = self._end_pid
                if doframe_pid:
                    pattern_doframe_tag = pattern_doframe_tag.replace("pid", doframe_pid)
                else:
                    TEST_LOGGER.warn(f"未找到 animation_pid、start_pid 或 end_pid，将使用通用模式匹配 Choreographer#doFrame")
                    pattern_doframe_tag = pattern_doframe_tag.replace("-pid", r"-\d+")
            doframe_time_list = []

            # 如果不是 __FULL_TRACE__ 模式，才需要解析 tag
            if self._animation_tag != "__FULL_TRACE__":
                # 如果tag中包含pid，则用实际的pid替换pid字符串
                if "pid" in self._start_tag:
                    if self._start_pid:
                        self._start_tag = self._start_tag.replace("pid", self._start_pid)
                        TEST_LOGGER.info(f"动效开始tag中的pid已替换为: {self._start_pid}")
                    else:
                        TEST_LOGGER.warn(f"动效开始tag中包含pid占位符，但未找到对应的_start_pid，将尝试使用通用模式匹配")
                        # 如果未找到pid，尝试使用通用数字模式匹配
                        self._start_tag = self._start_tag.replace("-pid", r"-\d+")
                TEST_LOGGER.info(f"动效开始tag:{self._start_tag}")

                if "pid" in self._end_tag:
                    if self._end_pid:
                        self._end_tag = self._end_tag.replace("pid", self._end_pid)
                        TEST_LOGGER.info(f"动效结束tag中的pid已替换为: {self._end_pid}")
                    else:
                        TEST_LOGGER.warn(f"动效结束tag中包含pid占位符，但未找到对应的_end_pid，将尝试使用通用模式匹配")
                        # 如果未找到pid，尝试使用通用数字模式匹配
                        self._end_tag = self._end_tag.replace("-pid", r"-\d+")
                TEST_LOGGER.info(f"动效结束tag:{self._end_tag}")

            # 如果不是 __FULL_TRACE__ 模式，才需要从文件中解析 tag
            if self._animation_tag != "__FULL_TRACE__":
                with open(self._html_file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    # 获取doframe时间点列表
                    TEST_LOGGER.info(f"开始获取 Choreographer#doFrame 时间，tag: {pattern_doframe_tag}")
                    matches = re.findall(pattern_doframe_tag, content, re.MULTILINE)
                    if matches:
                        doframe_time_list = [float(match) for match in matches]
                    TEST_LOGGER.info(f"获取Choreographer#doFrame tag: {pattern_doframe_tag} 的时间列：{doframe_time_list}")
                    
                    # 获取开始动效时间
                    TEST_LOGGER.info(f"开始获取动效开始时间，动效开始tag: {self._start_tag}")
                    matches = re.findall(self._start_tag, content, re.MULTILINE)
                    if matches:
                        self._start_animation_time_list = [float(match) for match in matches]
                    TEST_LOGGER.info(f"获取开始动效tag: {self._start_tag} 的时间列：{self._start_animation_time_list}")

                    # 根据 start_tag_index 获取对应的动效开始时间
                    TEST_LOGGER.info(f"动效开始 start_tag_index: {self._start_tag_index}")
                    if self._start_animation_time_list and self._start_tag_index is not None:
                        if self._start_tag_index < 0:
                            # 负数索引表示从后往前数，-1 表示最后一个
                            actual_index = len(self._start_animation_time_list) + self._start_tag_index
                            if actual_index < 0:
                                TEST_LOGGER.error(f"指定的 start_tag_index {self._start_tag_index} 超出范围，列表长度：{len(self._start_animation_time_list)}")
                            else:
                                self._start_animation_time = self._start_animation_time_list[actual_index]
                                TEST_LOGGER.info(f"使用负数索引 {self._start_tag_index}，实际索引：{actual_index}")
                        elif self._start_tag_index >= len(self._start_animation_time_list):
                            TEST_LOGGER.error(f"指定的 start_tag_index {self._start_tag_index} 大于 start_animation_time_list 长度 {len(self._start_animation_time_list)}，请检查！")
                        else:
                            self._start_animation_time = self._start_animation_time_list[self._start_tag_index]
                    TEST_LOGGER.info(f"获取动效开始时间：{self._start_animation_time}")

                    if not self._start_animation_time:
                        TEST_LOGGER.error(f"没有获取到动效开始时间，解析异常")
                        return

                    # 获取动效结束时间
                    TEST_LOGGER.info(f"开始获取动效结束时间，动效结束tag:{self._end_tag}")
                    if self._ms_after_start > 0:
                        TEST_LOGGER.info(f"已指定动效结束时间为开始时间后 {self._ms_after_start} ms，直接计算动效结束时间")
                        self._end_animation_time = self._start_animation_time + self._ms_after_start / 1000
                    elif self._end_tag:
                        if self._end_tag == "calculate":
                            TEST_LOGGER.info(f"结束tag为calculate, 计算动效开始tag持续时间段的结束点")
                            pattern_tracing_mark_write_line = r"^.*?-{}.*?tracing_mark_write:.*$".format(self._start_pid)
                            end_pattern = r'(\d+\.\d+): tracing_mark_write: E\|'

                            find_new_draw_frame = False
                            draw_frame_b_count = 1
                            matches = re.findall(pattern_tracing_mark_write_line, content, re.MULTILINE)
                            for mat in matches:
                                s_matches = re.search(self._start_tag, mat)
                                if s_matches:
                                    start_timestamp = float(s_matches.group(1))
                                    # 时间点要与动效开始时间相等，才是需要计算的时间片
                                    if start_timestamp == self._start_animation_time:
                                        find_new_draw_frame = True
                                        draw_frame_b_count = 1
                                        continue

                                if find_new_draw_frame:
                                    if "tracing_mark_write: B|" in mat:
                                        draw_frame_b_count += 1
                                    else:
                                        e_matches = re.search(end_pattern, mat)
                                        if e_matches:
                                            draw_frame_b_count -= 1
                                            if draw_frame_b_count <= 0:
                                                self._end_animation_time = float(e_matches.group(1))
                                                break
                            TEST_LOGGER.info(f"获取开始时间：{self._start_animation_time} 对应的结束时间：{self._end_animation_time}")
                        elif self._end_tag.startswith("BufferTX - "):
                            TEST_LOGGER.info(f"结束tag为 BufferTX 开头, 开始获取对应的动效结束时间")
                            pattern_0_1 = r"(\d+\.\d+): tracing_mark_write.*{}.*\|(\d)$".format(self._end_tag)
                            matches = re.findall(pattern_0_1, content, re.MULTILINE)
                            end_timestamp = None
                            find_new_butter_tx_0 = False
                            for mat in matches:
                                index = mat[1]
                                if index == "0":
                                    end_timestamp = float(mat[0])
                                    if end_timestamp < self._start_animation_time:
                                        end_timestamp = None
                                    else:
                                        find_new_butter_tx_0 = True
                                    TEST_LOGGER.info(f"butter_tx_0_time：{end_timestamp}")
                                    continue
                                if index == "1":
                                    if find_new_butter_tx_0:
                                        butter_tx_1_time = float(mat[0])
                                        TEST_LOGGER.info(f"butter_tx_1_time：{butter_tx_1_time}")
                                        if end_timestamp > self._start_animation_time:
                                            delta_time = (butter_tx_1_time - end_timestamp) * 1000
                                            if delta_time > 80:
                                                TEST_LOGGER.info(f"butter_tx_1_time：{butter_tx_1_time} 与 butter_tx_0_time：{end_timestamp} 时间差：{delta_time}, 取{end_timestamp}为结束时间点")
                                                self._end_animation_time = end_timestamp
                                                break
                                    find_new_butter_tx_0 = False
                        else:
                            if self._end_tag == "Choreographer#doFrame_no_traversal":
                                TEST_LOGGER.info(f"结束tag为Choreographer#doFrame_no_traversal, 开始获取no traversal的doFrame")
                                pattern_tracing_mark_write_line = r"^.*?-{}.*?tracing_mark_write:.*$".format(self._end_pid)
                                end_pattern = r'(\d+\.\d+): tracing_mark_write: E\|'

                                find_new_choreographer = False
                                find_traversal = False
                                draw_frame_b_count = 1
                                matches = re.findall(pattern_tracing_mark_write_line, content, re.MULTILINE)
                                for mat in matches:
                                    s_matches = re.search(r'(\d+\.\d+): tracing_mark_write', mat)
                                    if s_matches:
                                        time_stamp = float(s_matches.group(1))
                                        # 直接过滤掉比动效开始时间早的时间片
                                        if time_stamp < self._start_animation_time:
                                            continue

                                    # 如果发现是 DrawFrames 关键字，则记录 vsyncid并通过BE获取结束时间
                                    # matches = re.search(r"Choreographer#doFrame \d+", mat)
                                    # if matches:
                                    if "Choreographer#doFrame" in mat:
                                        find_new_choreographer = True
                                        draw_frame_b_count = 1
                                        continue

                                    if find_new_choreographer:
                                        if "tracing_mark_write: B|" in mat:
                                            draw_frame_b_count += 1
                                            if "traversal" in mat:
                                                find_traversal = True
                                        else:
                                            e_matches = re.search(end_pattern, mat)
                                            if e_matches:
                                                draw_frame_b_count -= 1
                                                if draw_frame_b_count <= 0:
                                                    end_timestamp = float(e_matches.group(1))
                                                    if not find_traversal:
                                                        self._end_animation_time_list.append(end_timestamp)
                                                        TEST_LOGGER.info(f"没有发现traversal，动效结束时间列表 加入时间点{end_timestamp}")

                                                    find_traversal = False
                                                    find_new_choreographer = False
                            else:
                                TEST_LOGGER.info(f"开始获取动效结束时间，动效结束tag:{self._end_tag}")
                                matches = re.findall(self._end_tag, content, re.MULTILINE)
                                if matches:
                                    self._end_animation_time_list = [float(match) for match in matches]

                            # 过滤出比开始时间晚的时间点
                            self._end_animation_time_list = [x for x in self._end_animation_time_list if x > self._start_animation_time]
                            TEST_LOGGER.info(f"获取结束动效tag:{self._end_tag}的时间列：{self._end_animation_time_list}")

                            TEST_LOGGER.info(f"指定获取 end_tag_index:{self._end_tag_index}")
                            if self._end_animation_time_list and self._end_tag_index is not None:
                                if self._end_tag_index < 0:
                                    # 负数索引表示从后往前数，-1 表示最后一个
                                    actual_index = len(self._end_animation_time_list) + self._end_tag_index
                                    if actual_index < 0:
                                        TEST_LOGGER.error(f"指定的 end_tag_index {self._end_tag_index} 超出范围，列表长度：{len(self._end_animation_time_list)}")
                                    else:
                                        self._end_animation_time = self._end_animation_time_list[actual_index]
                                        TEST_LOGGER.info(f"使用负数索引 {self._end_tag_index}，实际索引：{actual_index}")
                                elif self._end_tag_index >= len(self._end_animation_time_list):
                                    TEST_LOGGER.error(f"指定的 end_tag_index {self._end_tag_index} 大于 end_animation_time_list 长度 {len(self._end_animation_time_list)}，请检查！")
                                else:
                                    self._end_animation_time = self._end_animation_time_list[self._end_tag_index]
                            TEST_LOGGER.info(f"获取动效结束时间：{self._end_animation_time}")

                    if not self._end_animation_time:
                        TEST_LOGGER.error(f"没有获取到动效结束时间，解析异常")
                        return

            TEST_LOGGER.info(f"获取动效开始时间点：{self._start_animation_time}，动效结束时间点：{self._end_animation_time}")
            
            # 先获取目标进程的 PID（用于过滤 RenderThread 的 DrawFrames）
            target_process_pid = None
            # 先读取文件内容，用于查找 PID
            with open(self._html_file_path, "r", encoding="utf-8", errors="ignore") as f:
                content_temp = f.read()
            
            if self._target_pgid:
                # 方法1：从 RenderThread 的 DrawFrames 事件中直接提取 PID（最可靠）
                # 格式：RenderThread-<tid>  ( <pid>) [cpu] .... timestamp: tracing_mark_write: B|<pid>|DrawFrames
                renderthread_pattern = r"RenderThread-\d+\s+\(\s*(\d+)\)\s+\[.*?\]\s+.*?tracing_mark_write:.*?B\|\d+\|DrawFrames"
                renderthread_matches = re.findall(renderthread_pattern, content_temp)
                if renderthread_matches:
                    # 找到所有 RenderThread 的 PID，选择与目标 PGID 匹配的
                    unique_pids = list(set(renderthread_matches))
                    TEST_LOGGER.info(f"从 RenderThread DrawFrames 事件中找到的 PID: {unique_pids}")
                    for pid in unique_pids:
                        if pid == self._target_pgid:
                            target_process_pid = pid
                            TEST_LOGGER.info(f"找到与目标 PGID {self._target_pgid} 匹配的 RenderThread PID: {target_process_pid}")
                            break
                    # 如果没找到匹配的，通常 PGID 和主进程的 PID 相同，直接使用
                    if not target_process_pid:
                        target_process_pid = self._target_pgid
                        TEST_LOGGER.info(f"未找到匹配的 RenderThread PID，使用目标进程 PGID {self._target_pgid} 作为 PID（通常 PGID == PID）")
                else:
                    # 如果没有找到 RenderThread 事件，尝试从 sched_switch 中查找
                    target_process_pid = self._target_pgid  # 默认使用 PGID
                    for line in content_temp.split('\n'):
                        if self._target_pgid in line and "sched_switch" in line:
                            pid_match = re.search(rf"\([\s]*{re.escape(self._target_pgid)}\)\s+\[.*?\]\s+.*?sched_switch:.*?prev_pid=(\d+)", line)
                            if pid_match:
                                target_process_pid = pid_match.group(1)
                                TEST_LOGGER.info(f"从 sched_switch 中找到目标进程 PGID {self._target_pgid} 对应的 PID: {target_process_pid}")
                                break
                            pid_match = re.search(rf"\([\s]*{re.escape(self._target_pgid)}\)\s+\[.*?\]\s+.*?sched_switch:.*?next_pid=(\d+)", line)
                            if pid_match:
                                target_process_pid = pid_match.group(1)
                                TEST_LOGGER.info(f"从 sched_switch 中找到目标进程 PGID {self._target_pgid} 对应的 PID (from next_pid): {target_process_pid}")
                                break
            else:
                # 如果没有指定目标进程，尝试从 RenderThread 事件中提取所有 PID
                renderthread_pattern = r"RenderThread-\d+\s+\(\s*(\d+)\)\s+\[.*?\]\s+.*?tracing_mark_write:.*?B\|\d+\|DrawFrames"
                renderthread_matches = re.findall(renderthread_pattern, content_temp)
                if renderthread_matches:
                    unique_pids = list(set(renderthread_matches))
                    TEST_LOGGER.warn(f"未指定目标进程，找到的 RenderThread PID: {unique_pids}，将统计所有 RenderThread")
                else:
                    TEST_LOGGER.warn(f"未找到 RenderThread DrawFrames 事件")
            
            # 为每个任务分别统计各自的帧数
            if self._start_animation_time and self._end_animation_time and self._task_name_list:
                with open(self._html_file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    
                for task_name_tag in self._task_name_list:
                    frame_count = 0
                    frame_thread_name = task_name_tag
                    
                    # 根据任务名选择不同的帧数统计方式
                    if task_name_tag == "RenderThread":
                        # RenderThread 使用 DrawFrames 事件（注意是复数）
                        # 需要根据 vsync_id 去重，相同 vsync_id 只算一帧
                        if target_process_pid:
                            # 匹配格式：RenderThread-<tid>  ( <pid>) [cpu] .... <timestamp>: tracing_mark_write: B|<pid>|DrawFrames <vsync_id>
                            # 捕获时间戳和 vsync_id
                            pattern_frame = rf"{re.escape(task_name_tag)}-.*?\s+\(\s*{re.escape(target_process_pid)}\)\s+\[.*?\]\s+.*?(\d+\.\d+):\s+tracing_mark_write:.*?B\|{re.escape(target_process_pid)}\|DrawFrames\s+(\d+)"
                            TEST_LOGGER.info(f"为任务 {task_name_tag} 使用 DrawFrames 事件统计帧数（仅统计 PID {target_process_pid} 的 RenderThread，根据 vsync_id 去重）")
                        else:
                            # 如果没有指定 PID，使用原来的模式（匹配所有 RenderThread）
                            pattern_frame = rf"{re.escape(task_name_tag)}.*?(\d+\.\d+).*?DrawFrames\s+(\d+)"
                            TEST_LOGGER.warn(f"未找到目标进程 PID，将为任务 {task_name_tag} 统计所有进程的 DrawFrames 事件（根据 vsync_id 去重）")
                        
                        matches = re.findall(pattern_frame, content, re.MULTILINE)
                        if matches:
                            # matches 是 [(timestamp, vsync_id), ...] 的列表
                            vsync_id_set = set()  # 用于去重
                            in_range_times = []
                            for timestamp_str, vsync_id in matches:
                                frame_time = float(timestamp_str)
                                # 使用严格的范围判断：帧时间必须在动效区间内（不包括边界）
                                if frame_time > self._start_animation_time and frame_time < self._end_animation_time:
                                    # 根据 vsync_id 去重
                                    if vsync_id not in vsync_id_set:
                                        vsync_id_set.add(vsync_id)
                                        frame_count += 1
                                        in_range_times.append((frame_time, vsync_id))
                            TEST_LOGGER.info(f"任务 {task_name_tag} 在动效区间内找到 {frame_count} 帧（根据 vsync_id 去重后），总匹配数：{len(matches)}")
                            if in_range_times:
                                TEST_LOGGER.info(f"任务 {task_name_tag} 帧时间点和 vsync_id: {in_range_times[:10]}")  # 只显示前10个
                        else:
                            TEST_LOGGER.warn(f"任务 {task_name_tag} 未找到帧事件，pattern: {pattern_frame}")
                    else:
                        # 其他线程使用 Choreographer#doFrame 事件
                        # 排除 "resynced" 事件，因为这是 vsync 重新校准，不是真正的帧
                        # 同样需要根据 vsync_id 去重
                        pattern_frame = rf"{re.escape(task_name_tag)}.*?(\d+\.\d+).*?Choreographer#doFrame\s+(\d+)(?!\s*-?\s*resynced)"
                        TEST_LOGGER.info(f"为任务 {task_name_tag} 使用 Choreographer#doFrame 事件统计帧数（排除 resynced 事件，根据 vsync_id 去重）")
                        
                        matches = re.findall(pattern_frame, content, re.MULTILINE)
                        if matches:
                            # matches 是 [(timestamp, vsync_id), ...] 的列表
                            vsync_id_set = set()  # 用于去重
                            in_range_times = []
                            for timestamp_str, vsync_id in matches:
                                frame_time = float(timestamp_str)
                                # 使用严格的范围判断：帧时间必须在动效区间内（不包括边界）
                                if frame_time > self._start_animation_time and frame_time < self._end_animation_time:
                                    # 根据 vsync_id 去重
                                    if vsync_id not in vsync_id_set:
                                        vsync_id_set.add(vsync_id)
                                        frame_count += 1
                                        in_range_times.append((frame_time, vsync_id))
                            TEST_LOGGER.info(f"任务 {task_name_tag} 在动效区间内找到 {frame_count} 帧（根据 vsync_id 去重后），总匹配数：{len(matches)}")
                            if in_range_times:
                                TEST_LOGGER.info(f"任务 {task_name_tag} 帧时间点和 vsync_id: {in_range_times[:10]}")  # 只显示前10个
                        else:
                            TEST_LOGGER.warn(f"任务 {task_name_tag} 未找到帧事件，pattern: {pattern_frame}")
                    
                    self._task_frame_count_dict[task_name_tag] = {
                        'frame_count': frame_count,
                        'frame_thread_name': frame_thread_name
                    }
            
            # 输出所有线程的帧数统计对比
            TEST_LOGGER.info(f"=" * 80)
            TEST_LOGGER.info(f"各线程帧数统计结果对比：")
            for task_name_tag, frame_info in self._task_frame_count_dict.items():
                TEST_LOGGER.info(f"  - {task_name_tag}: {frame_info['frame_count']} 帧")
            TEST_LOGGER.info(f"  - 默认统计线程 ({self._animation_thread_name}): {len(self._doframe_time_list)} 帧")
            TEST_LOGGER.info(f"")
            TEST_LOGGER.info(f"帧数统计说明：")
            TEST_LOGGER.info(f"  - RenderThread: 统计 'DrawFrames' 事件（注意是复数），根据 vsync_id 去重")
            TEST_LOGGER.info(f"  - MainThread/其他线程: 统计 'Choreographer#doFrame' 事件，根据 vsync_id 去重")
            TEST_LOGGER.info(f"  - 所有统计都排除了 'resynced' 事件（vsync 重新校准，不是真正的帧）")
            TEST_LOGGER.info(f"  - 时间区间判断：帧时间必须严格在动效区间内（不包括边界）")
            TEST_LOGGER.info(f"=" * 80)
            
            # 保留原有的 doframe_time_list 用于兼容性（使用 animation_thread_name）
            if doframe_time_list and self._start_animation_time and self._end_animation_time:
                for doframe_time in doframe_time_list:
                    # 使用 >= 和 <= 来包含边界帧
                    if doframe_time >= self._start_animation_time and doframe_time <= self._end_animation_time:
                        self._doframe_time_list.append(doframe_time)
                TEST_LOGGER.info(f"在动效时间范围 [{self._start_animation_time}, {self._end_animation_time}] 内找到 {len(self._doframe_time_list)} 帧 doFrame，总 doFrame 数：{len(doframe_time_list)}")
            
            # 统计 GPU 时间（waiting for GPU completion 期间的时间）
            if self._start_animation_time and self._end_animation_time:
                TEST_LOGGER.info(f"开始统计 GPU 时间（waiting for GPU completion 和 GPU completion fence has signaled）")
                # 匹配 GPU completion 线程的 waiting for GPU completion 事件
                # B 事件：开始等待 GPU
                # E 事件：结束等待 GPU
                # 同时匹配 GPU completion fence has signaled 事件（GPU已提前完成，无需等待）
                # 尝试多种模式匹配
                if target_process_pid:
                    # 模式1：精确匹配指定进程的 GPU completion 事件
                    pattern_gpu_wait_b = rf"GPU completion-.*?\s+\(\s*{re.escape(target_process_pid)}\)\s+\[.*?\]\s+.*?(\d+\.\d+):\s+tracing_mark_write:.*?B\|.*?\|waiting for GPU completion\s+(\d+)"
                    pattern_gpu_wait_e = rf"GPU completion-.*?\s+\(\s*{re.escape(target_process_pid)}\)\s+\[.*?\]\s+.*?(\d+\.\d+):\s+tracing_mark_write:.*?E"
                    # GPU completion fence has signaled 事件可能不是 tracing_mark_write 格式，使用更宽松的匹配
                    pattern_gpu_signaled = rf"(\d+\.\d+).*?GPU completion fence\s+(\d+)\s+has signaled"
                    TEST_LOGGER.info(f"使用精确匹配模式，目标进程 PID: {target_process_pid}")
                else:
                    # 模式2：匹配所有进程的 GPU completion 事件
                    pattern_gpu_wait_b = rf"GPU completion.*?(\d+\.\d+):\s+tracing_mark_write:.*?B\|.*?\|waiting for GPU completion\s+(\d+)"
                    pattern_gpu_wait_e = rf"GPU completion.*?(\d+\.\d+):\s+tracing_mark_write:.*?E"
                    # GPU completion fence has signaled 事件可能不是 tracing_mark_write 格式，使用更宽松的匹配
                    pattern_gpu_signaled = rf"(\d+\.\d+).*?GPU completion fence\s+(\d+)\s+has signaled"
                    TEST_LOGGER.info(f"使用通用匹配模式（未指定目标进程）")
                
                with open(self._html_file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    
                    # 查找所有 B 和 E 事件
                    b_matches = re.findall(pattern_gpu_wait_b, content, re.MULTILINE)
                    e_matches = re.findall(pattern_gpu_wait_e, content, re.MULTILINE)
                    signaled_matches = re.findall(pattern_gpu_signaled, content, re.MULTILINE)
                    
                    TEST_LOGGER.info(f"找到 {len(b_matches)} 个 GPU waiting B 事件，{len(e_matches)} 个 E 事件，{len(signaled_matches)} 个 GPU completion fence has signaled 事件")
                    
                    if len(b_matches) == 0 and len(signaled_matches) == 0:
                        # 如果没有找到，尝试更宽松的匹配模式
                        TEST_LOGGER.warn(f"未找到 GPU waiting 事件，尝试更宽松的匹配模式")
                        pattern_gpu_wait_b_loose = r"GPU completion.*?(\d+\.\d+):\s+tracing_mark_write:.*?B\|.*?\|waiting for GPU completion\s+(\d+)"
                        pattern_gpu_wait_e_loose = r"GPU completion.*?(\d+\.\d+):\s+tracing_mark_write:.*?E"
                        pattern_gpu_signaled_loose = r"GPU completion.*?(\d+\.\d+):\s+tracing_mark_write:.*?GPU completion fence\s+(\d+)\s+has signaled"
                        b_matches = re.findall(pattern_gpu_wait_b_loose, content, re.MULTILINE)
                        e_matches = re.findall(pattern_gpu_wait_e_loose, content, re.MULTILINE)
                        signaled_matches = re.findall(pattern_gpu_signaled_loose, content, re.MULTILINE)
                        TEST_LOGGER.info(f"宽松模式找到 {len(b_matches)} 个 GPU waiting B 事件，{len(e_matches)} 个 E 事件，{len(signaled_matches)} 个 GPU completion fence has signaled 事件")
                    
                    if len(b_matches) > 0 or len(signaled_matches) > 0:
                        # 将 B 事件转换为 [(timestamp, vsync_id), ...]
                        b_events = [(float(ts), vsync_id) for ts, vsync_id in b_matches]
                        e_events = [float(ts) for ts in e_matches]
                        signaled_events = [(float(ts), vsync_id) for ts, vsync_id in signaled_matches]
                        
                        # 按时间排序
                        b_events.sort(key=lambda x: x[0])
                        e_events.sort()
                        signaled_events.sort(key=lambda x: x[0])
                        
                        # 匹配 B 和 E 事件，计算 GPU waiting 时间
                        gpu_vsync_id_set = set()  # 用于去重
                        e_index = 0
                        
                        TEST_LOGGER.info(f"=" * 80)
                        TEST_LOGGER.info(f"开始统计GPU帧数，动效区间: [{self._start_animation_time}, {self._end_animation_time}]")
                        TEST_LOGGER.info(f"总共找到 {len(b_events)} 个 GPU waiting B 事件，{len(signaled_events)} 个 GPU completion fence has signaled 事件")
                        
                        # 先处理 waiting for GPU completion 事件（有等待时间）
                        for b_time, vsync_id in b_events:
                            # 查找对应的 E 事件（第一个时间大于 B 事件的 E 事件）
                            while e_index < len(e_events) and e_events[e_index] <= b_time:
                                e_index += 1
                            
                            # 判断 B 事件是否在动效区间内或之前开始
                            if b_time < self._end_animation_time:
                                if e_index < len(e_events):
                                    e_time = e_events[e_index]
                                    # 只要 B 事件在结束时间之前，就算一帧
                                    # 即使 E 事件在结束时间之后，或者 duration 为 0
                                    if b_time >= self._start_animation_time:
                                        # 计算实际在动效区间内的时间
                                        actual_start = b_time
                                        actual_end = min(e_time, self._end_animation_time)
                                        duration = max(0, actual_end - actual_start)  # duration 可以为 0
                                        
                                        self._gpu_waiting_intervals.append((actual_start, actual_end, duration, vsync_id))
                                        self._gpu_total_time += duration
                                        
                                        # 根据 vsync_id 去重计算帧数
                                        if vsync_id not in gpu_vsync_id_set:
                                            gpu_vsync_id_set.add(vsync_id)
                                            self._gpu_frame_count += 1
                                            TEST_LOGGER.info(f"GPU帧 #{self._gpu_frame_count}: vsync_id={vsync_id}, B时间={b_time:.6f}s, E时间={e_time:.6f}s, duration={duration:.6f}s ({duration*1000:.3f}ms) [waiting]")
                                        else:
                                            TEST_LOGGER.info(f"GPU帧（重复vsync_id，已跳过）: vsync_id={vsync_id}, B时间={b_time:.6f}s, E时间={e_time:.6f}s, duration={duration:.6f}s ({duration*1000:.3f}ms) [waiting]")
                                    elif e_time > self._start_animation_time:
                                        # B 事件在开始时间之前，但 E 事件在开始时间之后
                                        # 这种情况也算一帧，但只计算交集部分的时间
                                        actual_start = self._start_animation_time
                                        actual_end = min(e_time, self._end_animation_time)
                                        duration = max(0, actual_end - actual_start)
                                        
                                        self._gpu_waiting_intervals.append((actual_start, actual_end, duration, vsync_id))
                                        self._gpu_total_time += duration
                                        
                                        # 根据 vsync_id 去重计算帧数
                                        if vsync_id not in gpu_vsync_id_set:
                                            gpu_vsync_id_set.add(vsync_id)
                                            self._gpu_frame_count += 1
                                            TEST_LOGGER.info(f"GPU帧 #{self._gpu_frame_count}: vsync_id={vsync_id}, B时间={b_time:.6f}s (早于开始), E时间={e_time:.6f}s, duration={duration:.6f}s ({duration*1000:.3f}ms) [waiting]")
                                        else:
                                            TEST_LOGGER.info(f"GPU帧（重复vsync_id，已跳过）: vsync_id={vsync_id}, B时间={b_time:.6f}s (早于开始), E时间={e_time:.6f}s, duration={duration:.6f}s ({duration*1000:.3f}ms) [waiting]")
                                else:
                                    # 没有找到对应的 E 事件，说明 GPU completion 还未结束
                                    # 这种情况下，如果 B 事件在动效区间内，也算一帧，duration 为 0
                                    if b_time >= self._start_animation_time:
                                        duration = 0
                                        self._gpu_waiting_intervals.append((b_time, b_time, duration, vsync_id))
                                        
                                        # 根据 vsync_id 去重计算帧数
                                        if vsync_id not in gpu_vsync_id_set:
                                            gpu_vsync_id_set.add(vsync_id)
                                            self._gpu_frame_count += 1
                                            TEST_LOGGER.info(f"GPU帧 #{self._gpu_frame_count}: vsync_id={vsync_id}, B时间={b_time:.6f}s, E时间=未找到, duration=0s (GPU completion未结束) [waiting]")
                                        else:
                                            TEST_LOGGER.info(f"GPU帧（重复vsync_id，已跳过）: vsync_id={vsync_id}, B时间={b_time:.6f}s, E时间=未找到, duration=0s [waiting]")
                                
                                e_index += 1
                        
                        # 再处理 GPU completion fence has signaled 事件（GPU已提前完成，无等待时间）
                        for signaled_time, vsync_id in signaled_events:
                            # 判断 signaled 事件是否在动效区间内
                            if signaled_time >= self._start_animation_time and signaled_time < self._end_animation_time:
                                # 根据 vsync_id 去重计算帧数
                                if vsync_id not in gpu_vsync_id_set:
                                    gpu_vsync_id_set.add(vsync_id)
                                    self._gpu_frame_count += 1
                                    # GPU已提前完成，duration为0
                                    duration = 0
                                    self._gpu_waiting_intervals.append((signaled_time, signaled_time, duration, vsync_id))
                                    TEST_LOGGER.info(f"GPU帧 #{self._gpu_frame_count}: vsync_id={vsync_id}, 时间={signaled_time:.6f}s, duration=0s (GPU已提前完成) [signaled]")
                                else:
                                    TEST_LOGGER.info(f"GPU帧（重复vsync_id，已跳过）: vsync_id={vsync_id}, 时间={signaled_time:.6f}s, duration=0s [signaled]")
                        
                        # 计算平均每帧耗时
                        if self._gpu_frame_count > 0:
                            self._gpu_avg_time_per_frame = self._gpu_total_time / self._gpu_frame_count
                        
                        TEST_LOGGER.info(f"=" * 80)
                        TEST_LOGGER.info(f"GPU 统计结果汇总：")
                        TEST_LOGGER.info(f"  - GPU帧数: {self._gpu_frame_count} 帧（根据 vsync_id 去重）")
                        TEST_LOGGER.info(f"  - GPU总时间: {self._gpu_total_time:.6f} 秒 ({self._gpu_total_time*1000:.3f} ms)")
                        TEST_LOGGER.info(f"  - GPU平均每帧耗时: {self._gpu_avg_time_per_frame:.6f} 秒 ({self._gpu_avg_time_per_frame*1000:.3f} ms)")
                        TEST_LOGGER.info(f"  - GPU waiting 区间数量: {len(self._gpu_waiting_intervals)}")
                        TEST_LOGGER.info(f"  - 其中 waiting for GPU completion 事件: {len(b_events)} 个")
                        TEST_LOGGER.info(f"  - 其中 GPU completion fence has signaled 事件: {len(signaled_events)} 个")
                        
                        # 计算GPU频率区间和GPU负载
                        if gpu_frequency_dict:
                            TEST_LOGGER.info(f"")
                            TEST_LOGGER.info(f"开始计算GPU频率区间和GPU负载...")
                            
                            # 将GPU频率字典转换为DataFrame
                            gpu_frequency_df = pd.DataFrame(
                                list(gpu_frequency_dict.items()),
                                columns=['时间戳', 'GPU频率']
                            )
                            
                            # 修改策略：统计整个动效区间内的GPU频率变化
                            # 而不是只统计GPU waiting事件发生时刻的频率点
                            TEST_LOGGER.info(f"统计整个动效区间 [{self._start_animation_time}, {self._end_animation_time}] 内的GPU频率变化")
                            freq_intervals = get_frequency_intervals(gpu_frequency_df, self._start_animation_time, self._end_animation_time)
                            
                            # 计算GPU负载 (MCPS = 时间 × 频率)
                            total_gpu_load = 0.0
                            for freq, start, end, duration in freq_intervals:
                                total_gpu_load += duration * freq
                                self._gpu_frequency_intervals.append((freq, start, end, duration))
                            
                            self._gpu_load = total_gpu_load
                            
                            TEST_LOGGER.info(f"动效区间内GPU频率变化统计：")
                            TEST_LOGGER.info(f"  - 总共 {len(freq_intervals)} 个频率区间")
                            for i, (freq, start, end, duration) in enumerate(freq_intervals[:10], 1):
                                TEST_LOGGER.info(f"  [{i}] 频率={freq/1000:.0f} MHz, 开始={start:.6f}s, 结束={end:.6f}s, 持续={duration:.6f}s")
                            
                            # 计算GPU平均频率
                            if self._gpu_total_time > 0:
                                gpu_avg_freq = self._gpu_load / self._gpu_total_time
                                TEST_LOGGER.info(f"")
                                TEST_LOGGER.info(f"GPU负载统计：")
                                TEST_LOGGER.info(f"  - GPU总负载: {self._gpu_load:.2f} MCPS")
                                TEST_LOGGER.info(f"  - GPU平均频率: {gpu_avg_freq:.2f} MHz")
                                TEST_LOGGER.info(f"  - GPU频率区间数量: {len(self._gpu_frequency_intervals)}")
                            else:
                                TEST_LOGGER.warn(f"GPU总时间为0，无法计算平均频率")
                        else:
                            TEST_LOGGER.warn(f"未找到GPU频率数据，无法计算GPU负载")
                        
                        TEST_LOGGER.info(f"")
                        TEST_LOGGER.info(f"GPU帧数计算说明：")
                        TEST_LOGGER.info(f"  - 统计两种事件：")
                        TEST_LOGGER.info(f"    1. 'waiting for GPU completion' 事件（有等待时间）")
                        TEST_LOGGER.info(f"    2. 'GPU completion fence has signaled' 事件（GPU已提前完成，duration=0）")
                        TEST_LOGGER.info(f"  - 对于 waiting 事件：只要 B 事件在动效结束时间之前，就算一帧")
                        TEST_LOGGER.info(f"  - 对于 signaled 事件：只要事件在动效区间内，就算一帧，duration=0")
                        TEST_LOGGER.info(f"  - 如果 B 事件在区间内但没有找到对应的 E 事件，duration 记为 0，但仍算一帧")
                        TEST_LOGGER.info(f"  - 每个事件包含一个 vsync_id，相同 vsync_id 只计算一次")
                        TEST_LOGGER.info(f"")
                        TEST_LOGGER.info(f"GPU帧数与RenderThread/MainThread帧数可能不同的原因：")
                        TEST_LOGGER.info(f"  1. 统计事件不同：GPU统计'waiting for GPU completion'和'GPU completion fence has signaled'，RenderThread统计'DrawFrames'")
                        TEST_LOGGER.info(f"  2. 某些帧可能没有GPU等待（纯CPU渲染），或GPU等待时间极短未被捕获")
                        TEST_LOGGER.info(f"  3. 时间区间边界处理：GPU只要B事件在结束时间前就算，RenderThread使用严格区间判断")
                        TEST_LOGGER.info(f"  4. vsync_id 的分配时机不同：GPU completion 和 DrawFrames 可能使用不同的 vsync_id")
                        TEST_LOGGER.info(f"=" * 80)
                    else:
                        TEST_LOGGER.warn(f"未找到任何 GPU waiting 事件，GPU 统计值将为 0")
        else:
            TEST_LOGGER.info(f"没有指定动效tag，不考虑动效时间范围")

        if not cpu_frequency_dict:
            TEST_LOGGER.error(f"没有获取到CPU频率变化数据，解析异常")
            return

        if not org_data_by_cpu:
            TEST_LOGGER.error(f"没有获取到CPU执行任务原始数据，解析异常")
            return

        """
        获取数据完成，进行数据处理
        """
        # 将字典转化为DataFrame，获取每个CPU核的频率变化DF
        for cpu_id, cpu_core_frequency_dict in cpu_frequency_dict.items():
            # 将 cpu_frequency_dict 转化为 DataFrame，索引为时间戳，列为频率状态
            df = pd.DataFrame(
                list(cpu_core_frequency_dict.items()),
                columns=['时间戳', 'CPU频率']
            )
            cpu_frequency_df_dict[cpu_id] = df

        # 根据原始数据，计算每个task的执行时间段
        for cpu_id, origin_data_list in org_data_by_cpu.items():
            # 获取cpu_id 对应的 cpu_group
            cpu_group = get_cpu_group(cpu_id)
            if cpu_group is None:
                TEST_LOGGER.error(f"未知的CPU核心分组：{cpu_id} --> {cpu_group}")
                raise Exception(f"未知的CPU核心分组：{cpu_id} --> {cpu_group}")
            else:
                TEST_LOGGER.info(f"CPU核心分组：{cpu_id} --> {cpu_group}")

            # 获取当前cpu_id 对应的频率变化DataFrame
            frequency_df = cpu_frequency_df_dict.get(cpu_id)
            if frequency_df is None:
                TEST_LOGGER.error(f"没有获取到CPU[{cpu_id}]的频率变化数据")
                continue

            is_renamed = False  # 是否发生过重命名
            old_task_name = None  # 重命名前的task name
            last_next_comm = None  # 上一行的next_comm 值
            last_next_pid = None  # 上一行的next_pid值
            last_timestamp = None  # 上一行的时间

            for origin_data in origin_data_list:
                data_type = origin_data.data_type

                if data_type == "task_rename":
                    """
                    如果data_type为 task_rename，表示执行任务发生重命名，需要修正前一次sched_switch记录的next_comm名称
                    task_rename的pid 需要和 前一次sched_switch记录的next_pid一致才行
                    """
                    rename_pid = origin_data.prev_pid       # pid 存储为 origin_data 的 prev_pid 与 next_pid，任取一个即可
                    old_task_name = origin_data.prev_comm   # 重命名前的旧task name 存储为 origin_data 的 prev_comm
                    new_task_name = origin_data.next_comm   # 重命名后的新task name 存储为 origin_data 的 next_comm
                    timestamp = origin_data.timestamp       # 重命名时间戳

                    # 重命名前的task name 与 前一次sched_switch记录的next_comm名称需一致
                    # task_rename 记录的pid 需要和 前一次sched_switch记录的next_pid一致才行
                    if old_task_name == last_next_comm and rename_pid == last_next_pid:
                        is_renamed = True
                        last_next_comm = new_task_name  # 更新last_next_comm为新task name
                        TEST_LOGGER.warn(f"CPU[{cpu_id}][{timestamp}][task_rename]: {old_task_name} --> {origin_data.next_comm}")
                    else:
                        TEST_LOGGER.warn(f"CPU[{cpu_id}][{timestamp}][task_rename][Fail]: last_next_comm[{last_next_comm}] oldcomm[{old_task_name}] 或 rename_pid[{rename_pid}] last_next_pid[{last_next_pid}] 不一致，不做rename判定")
                elif data_type == "sched_switch":
                    """
                    如果data_type为 sched_switch，根据前后两次 sched_switch 数据获取task时间片信息
                    前一次 sched_switch 的 next_comm 要与本次的 prev_comm 一致
                    """
                    # 从origin_data中获取当前行的task信息
                    pgid = origin_data.pgid
                    task_name = origin_data.prev_comm
                    task_pid = origin_data.prev_pid
                    current_next_comm = origin_data.next_comm
                    current_next_pid = origin_data.next_pid
                    current_timestamp = origin_data.timestamp

                    if last_next_comm is None:
                        # last_next_comm 为空，表示当前数据为当前cpu核的第一条sched_switch，丢弃，用于下条数据分析
                        TEST_LOGGER.warn(f"CPU[{cpu_id}][{current_timestamp}][sched_switch][Warn]: last_next_comm：[{last_next_comm}]，判断为第一条数据")
                    elif "-" in pgid:
                        TEST_LOGGER.warn(f"CPU[{cpu_id}][{current_timestamp}][sched_switch][Warn]: prev_comm[{task_name}] last_next_comm[{last_next_comm}] pgid[{pgid}] 判断为idle")
                    else:
                        if task_name == last_next_comm:
                            start_time = last_timestamp
                            end_time = current_timestamp
                            
                            # 检查该时间片是否在 GPU waiting 期间
                            # 如果在 GPU waiting 期间，需要排除 sleeping 状态的时间
                            is_in_gpu_waiting = False
                            for gpu_start, gpu_end, gpu_duration, gpu_vsync_id in self._gpu_waiting_intervals:
                                # 检查时间片是否与 GPU waiting 区间有交集
                                if start_time < gpu_end and end_time > gpu_start:
                                    is_in_gpu_waiting = True
                                    break
                            
                            frequency_intervals = get_frequency_intervals(frequency_df, start_time, end_time)

                            # 判断是否在动效范围内
                            in_animation_range = True
                            if self._animation_tag:
                                if start_time > self._start_animation_time and end_time < self._end_animation_time:
                                    TEST_LOGGER.info(f"CPU[{cpu_id}] prev_comm[{task_name}] start_time[{start_time}] end_time[{end_time}] 在有效动效范围内")
                                else:
                                    in_animation_range = False
                                    TEST_LOGGER.info(f"CPU[{cpu_id}] prev_comm[{task_name}] start_time[{start_time}] end_time[{end_time}] 在有效动效范围外")
                            
                            # 如果该任务是 RenderThread 且在 GPU waiting 期间，标记为 GPU waiting 状态
                            # 这样在计算 MCPS 时可以排除这部分时间
                            task_slice_by_cpu.setdefault(cpu_id, {}).setdefault(f"{task_name}-{pgid}", []).append(
                                TaskSlice(cpu_id, cpu_group, pgid, task_name, task_pid, start_time, end_time, 
                                         is_renamed, old_task_name, frequency_intervals, in_animation_range, is_in_gpu_waiting)
                            )
                        else:
                            TEST_LOGGER.warn(f"CPU[{cpu_id}][{current_timestamp}][sched_switch][Fail]: prev_comm[{task_name}] last_next_comm[{last_next_comm}]，不一致，数据丢弃")

                    # 更新last_next_comm，last_next_pid，last_timestamp
                    last_next_comm = current_next_comm
                    last_next_pid = current_next_pid
                    last_timestamp = current_timestamp
                    # 重置is_renamed，old_task_name
                    is_renamed = False
                    old_task_name = None

        if not task_slice_by_cpu:
            TEST_LOGGER.error(f"没有获取到CPU执行任务时间片，解析异常")
            return

        """
        根据时间片，计算MCPS值
        """
        mcps_by_group_dict = {}
        detail_task_slice_dict = {}
        TEST_LOGGER.info(cpu_core_dict)
        for cpu_id, task_slice_dict in task_slice_by_cpu.items():

            for task_name, task_slice_list in task_slice_dict.items():
                if self._task_name_list:
                    task_name_tag, task_pgid = split_by_last_dash(task_name)
                    # 如果指定了进程名过滤，需要匹配pgid；如果没有指定进程名，则只匹配任务名
                    pgid_match = True
                    if self._process_name and self._target_pgid:
                        pgid_match = (self._target_pgid == task_pgid)
                    elif self._process_name and not self._target_pgid:
                        # 如果指定了进程名但未找到target_pgid，记录警告但不过滤
                        TEST_LOGGER.warn(f"指定了进程名 {self._process_name} 但未找到对应的PGID，将不过滤PGID")
                        pgid_match = True
                    
                    if task_name_tag in self._task_name_list and pgid_match:
                        for task_slice in task_slice_list:
                            detail_task_slice_dict.setdefault(task_name, []).append(task_slice)
                            if task_slice.in_animation_range:
                                mcps_temp = task_slice.mcps
                                duration_temp = task_slice.duration
                                group_mcps, group_duration, group_linear_t, group_approximate_t, _, _, _, _ = mcps_by_group_dict.setdefault(task_name, {}).setdefault(task_slice.cpu_group, [0, 0, 0, 0, 0, 0, 0, 0])
                                total_group_mcps = group_mcps + mcps_temp
                                total_duration = group_duration + duration_temp
                                total_group_linear_t = group_linear_t + task_slice.linear_t
                                total_group_approximate_t = group_approximate_t + task_slice.approximate_t
                                task_mcps_result = total_group_mcps / total_duration / 1000
                                task_linear_t_result = total_group_linear_t / 1024
                                task_approximate_t_result = total_group_approximate_t / 1024
                                mcps_by_group_dict[task_name][task_slice.cpu_group] = [total_group_mcps, total_duration, total_group_linear_t, total_group_approximate_t, task_mcps_result, task_linear_t_result, task_approximate_t_result, task_slice.pid]

                else:
                    for task_slice in task_slice_list:
                        detail_task_slice_dict.setdefault(task_name, []).append(task_slice)
                        if task_slice.in_animation_range:
                            mcps_temp = task_slice.mcps
                            duration_temp = task_slice.duration
                            group_mcps, group_duration, group_linear_t, group_approximate_t, _, _, _, _ = mcps_by_group_dict.setdefault(task_name, {}).setdefault(task_slice.cpu_group, [0, 0, 0, 0, 0, 0, 0, 0])
                            total_group_mcps = group_mcps + mcps_temp
                            total_duration = group_duration + duration_temp
                            task_mcps_result = total_group_mcps / total_duration / 1000
                            total_group_linear_t = group_linear_t + task_slice.linear_t
                            total_group_approximate_t = group_approximate_t + task_slice.approximate_t
                            task_linear_t_result = total_group_linear_t / 1024
                            task_approximate_t_result = total_group_approximate_t / 1024
                            mcps_by_group_dict[task_name][task_slice.cpu_group] = [total_group_mcps, total_duration, task_mcps_result, task_linear_t_result, task_approximate_t_result, task_slice.pid]

        """
        归一化
        """
        final_result_dict = {}
        for task_name, mcps_result_dict in mcps_by_group_dict.items():
            for cpu_group, [total_group_mcps, total_duration, total_group_linear_t, total_group_approximate_t, task_mcps_result, task_linear_t_result, task_approximate_t_result, pid] in mcps_result_dict.items():
                freq = int(task_mcps_result * 1000)
                cpu_core_computing_power_df = cpu_core_computing_power_dict.get(cpu_group)
                
                # 检查频率是否有效，如果为0或无效，使用配置的最小频率
                if cpu_core_computing_power_df is not None and not cpu_core_computing_power_df.empty:
                    frequencies = cpu_core_computing_power_df.index.values
                    min_freq = frequencies.min()
                    max_freq = frequencies.max()
                    
                    if freq <= 0 or freq < min_freq:
                        TEST_LOGGER.warn(f"任务 {task_name} CPU组 {cpu_group} 计算出的频率 {freq} 无效或小于最小值 {min_freq}，使用最小值 {min_freq}")
                        freq = int(min_freq)
                    elif freq > max_freq:
                        TEST_LOGGER.warn(f"任务 {task_name} CPU组 {cpu_group} 计算出的频率 {freq} 大于最大值 {max_freq}，使用最大值 {max_freq}")
                        freq = int(max_freq)
                
                if cpu_core_computing_power_df is not None and not cpu_core_computing_power_df.empty:
                    linear_normalization_c = float(linear_normalization(cpu_group, freq, cpu_core_computing_power_df))
                    approximate_normalization_c = float(approximate_normalization(cpu_group, freq, cpu_core_computing_power_df))
                else:
                    TEST_LOGGER.warn(f"任务 {task_name} CPU组 {cpu_group} 没有找到算力配置，跳过归一化计算")
                    linear_normalization_c = 0.0
                    approximate_normalization_c = 0.0
                
                linear_t = linear_normalization_c * total_duration / 1024
                approximate_t = approximate_normalization_c * total_duration / 1024

                final_result_dict.setdefault(task_name, {})[cpu_group] = [pid, total_group_mcps, total_duration, task_mcps_result, linear_normalization_c, linear_t, approximate_normalization_c, approximate_t, task_linear_t_result, task_approximate_t_result]

        len_doframe = len(self._doframe_time_list)
        TEST_LOGGER.info(f"统计线程:{self._animation_thread_name} Choreographer#doFrame 列表长度：{len_doframe}")
        
        """
        计算总 CPU usage（所有任务在动效区间内的总 wall duration）
        同时按进程（PGID）统计每个进程的 Wall duration
        """
        total_wall_duration = 0.0
        process_wall_duration_dict = {}  # {pgid: {'wall_duration': float, 'process_name': str, 'pid': str, 'task_names': set}}
        if self._start_animation_time and self._end_animation_time:
            animation_time_range = self._end_animation_time - self._start_animation_time
            TEST_LOGGER.info(f"动效时间区间: [{self._start_animation_time}, {self._end_animation_time}], 区间长度: {animation_time_range:.6f} 秒")
            
            # 遍历所有 CPU 的所有任务时间片，计算在动效区间内的总 duration
            for cpu_id, task_slice_dict in task_slice_by_cpu.items():
                for task_name, task_slice_list in task_slice_dict.items():
                    for task_slice in task_slice_list:
                        # 计算时间片与动效区间的交集
                        slice_start = max(task_slice.start_time, self._start_animation_time)
                        slice_end = min(task_slice.end_time, self._end_animation_time)
                        
                        # 如果时间片与动效区间有交集
                        if slice_start < slice_end:
                            # 计算交集部分的 duration（按比例计算）
                            slice_duration = task_slice.duration
                            total_slice_time = task_slice.end_time - task_slice.start_time
                            
                            if total_slice_time > 0:
                                # 计算交集部分占时间片的比例
                                intersection_ratio = (slice_end - slice_start) / total_slice_time
                                # 累加交集部分的 duration
                                intersection_duration = slice_duration * intersection_ratio
                                total_wall_duration += intersection_duration
                                
                                # 按进程（PGID）统计 Wall duration
                                pgid = task_slice.pgid
                                task_name_tag, _ = split_by_last_dash(task_name)
                                
                                if pgid not in process_wall_duration_dict:
                                    process_wall_duration_dict[pgid] = {
                                        'wall_duration': 0.0,
                                        'process_name': task_name_tag,  # 临时使用第一个任务名
                                        'pid': task_slice.pid,
                                        'task_names': set()  # 收集所有任务名
                                    }
                                
                                process_wall_duration_dict[pgid]['wall_duration'] += intersection_duration
                                process_wall_duration_dict[pgid]['task_names'].add(task_name_tag)
            
            # 为每个进程选择最合适的进程名
            # 根据已知的进程名模式进行推断
            for pgid, process_info in process_wall_duration_dict.items():
                task_names = list(process_info['task_names'])
                if not task_names:
                    continue
                
                # 选择最长的任务名作为候选
                task_names.sort(key=len, reverse=True)
                best_name = task_names[0]
                all_task_names_str = ' '.join(task_names)
                
                # 根据已知模式推断进程名
                # 检查是否包含 systemui 相关的任务
                if 'ndroid.systemui' in all_task_names_str or 'systemui' in all_task_names_str.lower():
                    best_name = 'com.android.systemui'
                # 检查是否包含 system_server 相关的任务
                elif 'system_server' in all_task_names_str or 'android.display' in all_task_names_str:
                    best_name = 'system_server'
                # 检查是否包含 surfaceflinger 相关的任务
                elif 'surfaceflinger' in all_task_names_str.lower():
                    best_name = '/system/bin/surfaceflinger'
                # 检查是否包含 launcher3 相关的任务
                elif 'ssion.launcher3' in all_task_names_str or 'launcher3' in all_task_names_str.lower():
                    best_name = 'com.transsion.launcher3'
                # 检查是否包含 aivoiceassistant 相关的任务
                elif 'iceassistant' in all_task_names_str or 'aivoiceassistant' in all_task_names_str.lower():
                    best_name = 'com.transsion.aivoiceassistant'
                # 检查是否包含 logd 相关的任务
                elif 'logd' in all_task_names_str.lower():
                    best_name = '/system/bin/logd'
                # 检查是否包含 traced_probes 相关的任务
                elif 'traced_probes' in all_task_names_str.lower():
                    best_name = '/system/bin/traced_probes'
                # 对于其他情况，使用最长的任务名
                # 如果任务名看起来像线程名（包含 ":"），尝试提取进程名部分
                elif ':' in best_name and not best_name.startswith('binder'):
                    parts = best_name.split(':')
                    if len(parts) > 1 and '.' in parts[0] and len(parts[0]) > 5:
                        best_name = parts[0]
                
                process_info['process_name'] = best_name
            
            # 计算 CPU usage = 总 wall duration / 区间长度 × 100%
            cpu_usage_percent = (total_wall_duration / animation_time_range * 100.0) if animation_time_range > 0 else 0.0
            TEST_LOGGER.info(f"总 Wall Duration: {total_wall_duration:.6f} 秒, 动效区间长度: {animation_time_range:.6f} 秒, CPU Usage: {cpu_usage_percent:.2f}%")
            
            # 计算每个进程的 CPU usage（相对于总 Wall duration 的百分比）
            top_processes = []
            for pgid, process_info in process_wall_duration_dict.items():
                process_wall_duration = process_info['wall_duration']
                process_cpu_usage = (process_wall_duration / total_wall_duration * 100.0) if total_wall_duration > 0 else 0.0
                top_processes.append({
                    'pgid': pgid,
                    'process_name': process_info['process_name'],
                    'pid': process_info['pid'],
                    'wall_duration': process_wall_duration,
                    'cpu_usage_percent': process_cpu_usage
                })
            
            # 按 Wall duration 排序，取 Top 20
            top_processes.sort(key=lambda x: x['wall_duration'], reverse=True)
            top_20_processes = top_processes[:20]
            
            TEST_LOGGER.info(f"Top 20 进程 CPU Usage 统计:")
            for i, proc in enumerate(top_20_processes, 1):
                TEST_LOGGER.info(f"  {i}. {proc['process_name']} (PGID:{proc['pgid']}, PID:{proc['pid']}): "
                               f"Wall Duration={proc['wall_duration']:.6f}s, CPU Usage={proc['cpu_usage_percent']:.2f}%")
        else:
            animation_time_range = 0.0
            cpu_usage_percent = 0.0
            top_20_processes = []
            TEST_LOGGER.warn("未找到动效开始或结束时间，无法计算 CPU usage")
        
        """
        计算每帧负载
        """
        per_frame_load_dict = {}
        for task_name, mcps_result_dict in final_result_dict.items():
            total_linear_t = 0
            total_task_linear_t_result = 0
            total_approximate_t = 0
            total_task_approximate_t_result = 0
            
            for cpu_group, [pid, total_group_mcps, total_duration, task_mcps_result, linear_normalization_c, linear_t, approximate_normalization_c, approximate_t, task_linear_t_result, task_approximate_t_result] in mcps_result_dict.items():
                total_linear_t += linear_t
                total_task_linear_t_result += task_linear_t_result
                total_approximate_t += approximate_t
                total_task_approximate_t_result += task_approximate_t_result
            
            # 获取该任务自己的帧数
            task_name_tag, _ = split_by_last_dash(task_name)
            task_frame_info = self._task_frame_count_dict.get(task_name_tag)
            
            if task_frame_info:
                task_frame_count = task_frame_info['frame_count']
                task_frame_thread_name = task_frame_info['frame_thread_name']
            else:
                # 如果没有找到，使用默认的 len_doframe（兼容性）
                task_frame_count = len_doframe
                task_frame_thread_name = self._animation_thread_name or "unknown"
                TEST_LOGGER.warn(f"任务 {task_name} 未找到帧数统计信息，使用默认帧数 {task_frame_count}")
            
            if task_frame_count > 0:
                per_frame_linear_mcps = total_linear_t / task_frame_count
                per_frame_linear_freq = total_task_linear_t_result / task_frame_count
                per_frame_approximate_mcps = total_approximate_t / task_frame_count
                per_frame_approximate_freq = total_task_approximate_t_result / task_frame_count
                
                per_frame_load_dict[task_name] = {
                    'linear_mcps': per_frame_linear_mcps,
                    'linear_freq': per_frame_linear_freq,
                    'approximate_mcps': per_frame_approximate_mcps,
                    'approximate_freq': per_frame_approximate_freq,
                    'frame_count': task_frame_count,
                    'frame_thread_name': task_frame_thread_name
                }
                
                TEST_LOGGER.info(f"任务 {task_name} 每帧负载: 线性(MCPS)={per_frame_linear_mcps:.6f}, 线性(频点)={per_frame_linear_freq:.6f}, 相似(MCPS)={per_frame_approximate_mcps:.6f}, 相似(频点)={per_frame_approximate_freq:.6f}, 帧数={task_frame_count}, 帧数统计线程={task_frame_thread_name}")
            else:
                TEST_LOGGER.warn(f"任务 {task_name} 帧数为0，无法计算每帧负载")
                per_frame_load_dict[task_name] = {
                    'linear_mcps': 0.0,
                    'linear_freq': 0.0,
                    'approximate_mcps': 0.0,
                    'approximate_freq': 0.0,
                    'frame_count': 0,
                    'frame_thread_name': task_frame_thread_name if task_frame_info else "unknown"
                }
        
        """
        执行 SurfaceFlinger 分析
        """
        if self._start_animation_time and self._end_animation_time:
            TEST_LOGGER.info("=" * 80)
            TEST_LOGGER.info("开始 SurfaceFlinger 分析")
            TEST_LOGGER.info("=" * 80)
            
            try:
                sf_analyzer = SurfaceFlingerAnalysis(
                    self._html_file_path,
                    self._start_animation_time,
                    self._end_animation_time
                )
                self._sf_analysis_result = sf_analyzer.analyze()
                
                # 提取 SurfaceFlinger 分析结果
                self._sf_gpu_frame_count = self._sf_analysis_result.get('gpu_frame_count', 0)
                self._sf_gpu_total_time = self._sf_analysis_result.get('gpu_total_wait_time', 0.0)
                self._sf_gpu_avg_time_per_frame = self._sf_analysis_result.get('gpu_avg_wait_time_per_frame', 0.0)
                self._sf_frame_layer_info = self._sf_analysis_result.get('frame_layer_info', [])
                
                TEST_LOGGER.info(f"SurfaceFlinger GPU 统计: 帧数={self._sf_gpu_frame_count}, 总时间={self._sf_gpu_total_time:.6f}s, 平均每帧={self._sf_gpu_avg_time_per_frame:.6f}s")
                TEST_LOGGER.info(f"SurfaceFlinger Layer 统计: 分析了 {len(self._sf_frame_layer_info)} 帧")
                
            except Exception as e:
                TEST_LOGGER.error(f"SurfaceFlinger 分析失败: {e}")
                import traceback
                TEST_LOGGER.error(traceback.format_exc())
        else:
            TEST_LOGGER.warn("未找到动效时间区间，跳过 SurfaceFlinger 分析")
        
        """
        输出解析结果
        """
        result_dir = os.path.dirname(self._html_file_path)
        file_name = os.path.basename(self._html_file_path).replace(".html", "")
        result_file_path = os.path.join(result_dir, f"mcps_result_{file_name}_{self._start_animation_time}_{self._end_animation_time}.xls")
        excel = McpsExcel(result_file_path)
        excel.insert_mcps_data(
            final_result_dict,
            detail_task_slice_dict,
            self._animation_thread_name,
            len_doframe,
            per_frame_load_dict,
            total_wall_duration,
            animation_time_range,
            cpu_usage_percent,
            top_20_processes,
            self._gpu_frame_count,
            self._gpu_total_time,
            self._gpu_avg_time_per_frame,
            self._gpu_frequency_intervals,
            self._gpu_load,
            self._sf_gpu_frame_count,
            self._sf_gpu_total_time,
            self._sf_gpu_avg_time_per_frame,
            self._sf_frame_layer_info,
            key_process_name=self._process_name
        )

    def _init(self):
        """
        读取cpu_info.json，获取CPU核心配置
        """
        global cpu_core_dict
        global cpu_core_computing_power_dict
        global cpu_core_max_freq_dict

        mcps_config_file_path = os.path.join(PathManager.config_folder, "mcps_config.json")
        if not os.path.isfile(mcps_config_file_path):
            TEST_LOGGER.error(f"没有找到 mcps_config.json 文件，请检查：{mcps_config_file_path}")
            return False

        with open(mcps_config_file_path, "r") as f:
            mcps_config_dict = json.load(f)

            # 获取CPU配置信息飞书Tab页名称
            cpu_tab_info_dict = mcps_config_dict.get("cpu_tab")
            if cpu_tab_info_dict is None:
                TEST_LOGGER.error(f"没有获取到配置项 cpu_tab，请检查文件：{mcps_config_file_path}")
                return False

            cpu_tab = cpu_tab_info_dict.get(self._cpu_type)
            if cpu_tab is None:
                TEST_LOGGER.error(f"没有获取到cpu_type：{self._cpu_type} 的CPU核心配置飞书Tab页名称，请检查文件：{mcps_config_file_path}")
                return False
            else:
                TEST_LOGGER.info(f"获取CPU核心配置信息所在飞书页面的Tab：{cpu_tab}")

            # 获取动效Tag配置信息
            if self._animation_tag:
                TEST_LOGGER.info(f"指定动效Tag配置项：{self._animation_tag}，尝试获取对应的动效tag")
                animation_tag_dict = mcps_config_dict.get("animation_tag")
                if animation_tag_dict is None:
                    TEST_LOGGER.error(f"没有获取到配置项 animation_tag，请检查文件：{mcps_config_file_path}")
                    return False
                else:
                    animation_tag = animation_tag_dict.get(self._animation_tag)
                    if animation_tag is None:
                        TEST_LOGGER.error(f"没有获取到指定动效Tag：{self._animation_tag} 的配置信息，请检查文件：{mcps_config_file_path}")
                        return False
                    else:
                        self._start_thread_name = animation_tag.get("start_thread_name")
                        if self._start_thread_name:
                            # 自动截取后15位
                            self._start_thread_name = self._start_thread_name[-15:]
                        self._start_process_name = animation_tag.get("start_process_name")
                        if self._start_process_name:
                            # 自动截取后15位
                            self._start_process_name = self._start_process_name[-15:]
                        self._start_tag = animation_tag.get("start_tag")
                        self._start_tag_index = animation_tag.get("start_tag_index")
                        self._ms_after_start = float(animation_tag.get("ms_after_start"))
                        self._end_thread_name = animation_tag.get("end_thread_name")
                        if self._end_thread_name:
                            # 自动截取后15位
                            self._end_thread_name = self._end_thread_name[-15:]
                        self._end_process_name = animation_tag.get("end_process_name")
                        if self._end_process_name:
                            # 自动截取后15位
                            self._end_process_name = self._end_process_name[-15:]
                        self._end_tag = animation_tag.get("end_tag")
                        self._end_tag_index = animation_tag.get("end_tag_index")
                        self._animation_thread_name = animation_tag.get("animation_thread_name")
                        if self._animation_thread_name:
                            # 自动截取后15位
                            self._animation_thread_name = self._animation_thread_name[-15:]
                        else:
                            self._animation_thread_name = self._start_thread_name
                        TEST_LOGGER.info(f"start_thread_name: {self._start_thread_name}")
                        TEST_LOGGER.info(f"start_process_name: {self._start_process_name}")
                        TEST_LOGGER.info(f"start_tag: {self._start_tag}")
                        TEST_LOGGER.info(f"start_tag_index: {self._start_tag_index}")
                        TEST_LOGGER.info(f"ms_after_start: {self._ms_after_start}")
                        TEST_LOGGER.info(f"end_thread_name: {self._end_thread_name}")
                        TEST_LOGGER.info(f"end_process_name: {self._end_process_name}")
                        TEST_LOGGER.info(f"end_tag: {self._end_tag}")
                        TEST_LOGGER.info(f"end_tag_index: {self._end_tag_index}")
                        TEST_LOGGER.info(f"animation_thread_name: {self._animation_thread_name}")

            # 截断进程名以匹配线程名（线程名在sched_switch中最多15个字符）
            if self._process_name:
                # 自动截取后15位
                self._process_name = self._process_name[-15:]
                TEST_LOGGER.info(f"截断后的进程名（用于过滤）: {self._process_name}")

        rlt, cpu_core_dict, cpu_core_computing_power_dict, cpu_core_max_freq_dict = get_cpu_info_from_feishu(cpu_tab)
        return rlt


def get_cpu_group(cpu_id):
    for group_name, cpu_core_list in cpu_core_dict.items():
        if cpu_id in cpu_core_list:
            return group_name
    return None


def split_by_last_dash(text):
    # 找到最后一个 '-' 的位置
    last_dash_index = text.rfind('-')

    if last_dash_index == -1:
        # 如果没有找到 '-'，返回整个字符串和空字符串
        return text, ""
    else:
        # 分割字符串
        first_part = text[:last_dash_index]
        second_part = text[last_dash_index + 1:]
        return first_part, second_part


def get_frequency_intervals(df, start_time, end_time):
    """
    获取在指定时间范围内的频率变化区间和时间段

    参数:
    df (pd.DataFrame): 包含时间戳和CPU频率的DataFrame
    start_time (float): 查询开始时间
    end_time (float): 查询结束时间

    返回:
    list: 每个元素为元组 (频率, 开始时间, 结束时间, 持续时间)
    """
    if df.empty:
        return []
    
    # 特殊处理：当 start_time == end_time 时（duration=0），返回该时间点的频率
    if start_time == end_time:
        timestamps = df['时间戳'].values
        # 自动检测频率列名（CPU频率 或 GPU频率）
        if 'CPU频率' in df.columns:
            freqs = df['CPU频率'].values
        elif 'GPU频率' in df.columns:
            freqs = df['GPU频率'].values
        else:
            freqs = df.iloc[:, 1].values
        
        # 找到该时间点对应的频率
        idx = np.searchsorted(timestamps, start_time, side='right') - 1
        if idx < 0:
            idx = 0
        if idx < len(freqs):
            # 返回该时间点的频率，duration=0
            return [(freqs[idx], start_time, end_time, 0.0)]
        else:
            return []
    
    # 如果 start_time > end_time，返回空
    if start_time > end_time:
        return []

    # 获取时间戳和频率数组
    timestamps = df['时间戳'].values
    # 自动检测频率列名（CPU频率 或 GPU频率）
    if 'CPU频率' in df.columns:
        freqs = df['CPU频率'].values
    elif 'GPU频率' in df.columns:
        freqs = df['GPU频率'].values
    else:
        # 如果都不存在，尝试使用第二列
        freqs = df.iloc[:, 1].values

    # 找到开始时间对应的位置
    start_idx = np.searchsorted(timestamps, start_time, side='right') - 1
    if start_idx < 0:
        start_idx = 0  # 如果开始时间早于所有数据点，从第一个点开始

    # 找到结束时间对应的位置
    end_idx = np.searchsorted(timestamps, end_time, side='right')
    if end_idx > len(timestamps):
        end_idx = len(timestamps)  # 如果结束时间晚于所有数据点，到最后一个点结束

    # 提取查询范围内的子数组
    sub_timestamps = timestamps[start_idx:end_idx]
    sub_freqs = freqs[start_idx:end_idx]

    # 如果范围内没有数据点
    if len(sub_timestamps) == 0:
        return []

    # 初始化结果列表
    intervals = []
    current_freq = sub_freqs[0]
    current_start = max(sub_timestamps[0], start_time)

    # 遍历范围内的数据点
    for i in range(1, len(sub_timestamps)):
        ts = sub_timestamps[i]
        freq = sub_freqs[i]

        # 如果频率发生变化或到达结束时间
        if freq != current_freq or ts >= end_time:
            # 确定当前段的结束时间
            segment_end = min(ts, end_time)

            # 只记录持续时间大于0的区间
            if segment_end > current_start:
                duration = segment_end - current_start
                intervals.append((current_freq, current_start, segment_end, duration))

            # 更新当前频率和开始时间
            current_freq = freq
            current_start = ts

    # 处理最后一段
    if current_start < end_time:
        duration = end_time - current_start
        intervals.append((current_freq, current_start, end_time, duration))

    return intervals


class OriginData:
    def __init__(self, data_type, pgid, cpu_id, timestamp, prev_comm, prev_pid, next_comm, next_pid, line):
        self.data_type= data_type
        self.pgid = pgid
        self.cpu_id = cpu_id
        self.timestamp = timestamp
        self.prev_comm = prev_comm
        self.prev_pid = prev_pid
        self.next_comm = next_comm
        self.next_pid = next_pid
        self.line = line


class TaskSlice:
    def __init__(self, cpu_id, cpu_group, pgid, task_name, pid, start_time, end_time, is_renamed, old_task_name, frequency_intervals, in_animation_range, is_in_gpu_waiting=False):
        self.cpu_id = cpu_id
        self.cpu_group = cpu_group
        self.pgid = pgid
        self.task_name = task_name
        self.pid = pid
        self.start_time = start_time
        self.end_time = end_time
        self.duration = None
        self.is_renamed = is_renamed
        self.old_task_name = old_task_name
        self.frequency_intervals = frequency_intervals
        self.in_animation_range = in_animation_range
        self.is_in_gpu_waiting = is_in_gpu_waiting  # 是否在 GPU waiting 期间
        self.mcps = 0
        self.mcps_intervals = []
        self.linear_t = 0
        self.approximate_t = 0
        self._calculate_mcps()

    def _calculate_mcps(self):
        # 计算该时间片总的时间
        self.duration = self.end_time - self.start_time

        # 注意：如果该时间片在 GPU waiting 期间，我们仍然计算 MCPS
        # 但在后续统计时，可以选择性地排除或标记这些时间片
        # 这里保持原有逻辑，只是添加了 is_in_gpu_waiting 标记
        
        cpu_core_computing_power_df = cpu_core_computing_power_dict.get(self.cpu_group)
        for (current_freq, start_time, end_time, duration) in self.frequency_intervals:
            mcps_slice_temp = duration * current_freq
            self.mcps = self.mcps + mcps_slice_temp
            self.mcps_intervals.append((start_time, end_time, duration, current_freq, mcps_slice_temp))

            linear_c_temp = linear_normalization(self.cpu_group, current_freq, cpu_core_computing_power_df)
            linear_t_temp = linear_c_temp * duration
            self.linear_t = self.linear_t + linear_t_temp

            approximate_c_temp = approximate_normalization(self.cpu_group, current_freq, cpu_core_computing_power_df)
            approximate_t_temp = approximate_c_temp * duration
            self.approximate_t = self.approximate_t + approximate_t_temp

        gpu_waiting_flag = " [GPU waiting]" if self.is_in_gpu_waiting else ""
        TEST_LOGGER.info(f"CPU[{self.cpu_id}][{self.task_name}][{self.start_time} --> {self.end_time}], MCPS:{self.mcps}, 频率变化区间:{len(self.frequency_intervals)}{gpu_waiting_flag}")


def linear_normalization(cpu_group, freq, cpu_core_computing_power_df):
    """
    根据频率值从DataFrame中获取或计算对应的算力值

    参数:
    freq: float - 目标频率值
    cpu_core_computing_power_df: DataFrame - 包含频率和对应算力值的DataFrame，索引为频率

    返回:
    float - 目标频率对应的算力值
    """
    # 确保DataFrame索引是数值类型且已排序
    cpu_core_computing_power_df = cpu_core_computing_power_df.sort_index()

    # 获取所有频率值
    frequencies = cpu_core_computing_power_df.index.values

    # 检查目标频率是否超出范围
    if freq < frequencies.min() or freq > frequencies.max():
        raise Exception(f"频率{freq}超出[{frequencies.min()}, {frequencies.max()}] 范围，请检查配置文件是否正确")

    # 检查频率是否正好等于某个索引值
    if freq in cpu_core_computing_power_df.index:
        TEST_LOGGER.info(f"线性归一化：cpu_group:{cpu_group} 频率：{freq}：频率点 c:{cpu_core_computing_power_df.loc[freq].iloc[0]}")
        return cpu_core_computing_power_df.loc[freq].iloc[0]

    # 找到目标频率所在的区间
    for i in range(len(frequencies) - 1):
        f1 = frequencies[i]
        f2 = frequencies[i + 1]

        if f1 <= freq <= f2:
            # 获取对应的算力值
            c1 = cpu_core_computing_power_df.iloc[i].iloc[0]
            c2 = cpu_core_computing_power_df.iloc[i + 1].iloc[0]

            # 使用线性插值公式计算算力值
            c = c1 + (c2 - c1) * (freq - f1) / (f2 - f1)
            TEST_LOGGER.info(f"线性归一化：cpu_group:{cpu_group} 频率：{freq}： f1:{f1} c1:{c1} f2:{f2} c2:{c2} c:{c}")
            return c

    # 如果未找到合适的区间（理论上不应该执行到这里）
    return None


def approximate_normalization(cpu_group, freq, cpu_core_computing_power_df):
    """
    根据频率值从DataFrame中使用近似归一化方法获取算力值

    规则:
    - 当 f ≥ (f₁ + f₂)/2 时，取 c = c₂
    - 当 f < (f₁ + f₂)/2 时，取 c = c₁

    参数:
    freq: float - 目标频率值
    cpu_core_computing_power_df: DataFrame - 包含频率和对应算力值的DataFrame，有'频率'和'算力'两列

    返回:
    float - 目标频率对应的算力值
    """
    # 确保DataFrame索引是数值类型且已排序
    cpu_core_computing_power_df = cpu_core_computing_power_df.sort_index()

    # 获取所有频率值
    frequencies = cpu_core_computing_power_df.index.values

    # 检查目标频率是否超出范围
    if freq < frequencies.min() or freq > frequencies.max():
        raise Exception(f"频率{freq}超出[{frequencies.min()}, {frequencies.max()}] 范围，请检查配置文件是否正确")

    # 检查频率是否正好等于某个索引值
    if freq in cpu_core_computing_power_df.index:
        TEST_LOGGER.info(f"相似归一化：cpu_group:{cpu_group} 频率：{freq}：频率点 c:{cpu_core_computing_power_df.loc[freq].iloc[0]}")
        return cpu_core_computing_power_df.loc[freq].iloc[0]

    # 找到目标频率所在的区间
    for i in range(len(frequencies) - 1):
        f1 = frequencies[i]
        f2 = frequencies[i + 1]

        if f1 <= freq <= f2:
            # 获取对应的算力值
            c1 = cpu_core_computing_power_df.iloc[i].iloc[0]
            c2 = cpu_core_computing_power_df.iloc[i + 1].iloc[0]

            # 计算中点
            midpoint = (f1 + f2) / 2

            # 根据近似归一化规则选择算力值
            if freq >= midpoint:
                c = c2
            else:
                c = c1
            TEST_LOGGER.info(f"相似归一化：cpu_group:{cpu_group} 频率：{freq}： f1:{f1} c1:{c1} f2:{f2} c2:{c2} c:{c}")
            return c

    # 如果未找到合适的区间（理论上不应该执行到这里）
    return None
