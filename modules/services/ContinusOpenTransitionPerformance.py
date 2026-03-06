# -*- coding: utf-8 -*-
# @Time     : 2025/9/5 16:10
# @Author   : yunqing.gui
# @Email    : yunqing.gui@transsion.com
# @File     : ContinusOpenTransitionPerformance.py

import os
import json

from modules.PerfettoSql.PerfettoSqlCommon import (get_slice_by_name_via_thread, get_slice_by_name_via_process, get_start_package_name)
from modules.common.Logger import TEST_LOGGER
from modules.common.Path import PathManager
from modules.services.TraceProcessor import TraceProcessorBasic


class ContinusOpenTransitionPerformance(TraceProcessorBasic):
    def __init__(self, trace_file_path, device_tag, bin_path=None, verbose=None):
        super().__init__(trace_file_path, bin_path, verbose)
        self._config_file_path = None
        self._configs = None

        self._scene_tag = None
        self._load_configs(device_tag)

    def _load_configs(self, device_tag):
        # 读取配置文件
        self._config_file_path = os.path.join(PathManager.config_folder, "config_open_transition.json")
        with open(self._config_file_path, "r") as f:
            self._configs = json.load(f)

        self._tag_dict = self._configs.get(device_tag)
        if not self._tag_dict:
            TEST_LOGGER.error(f"配置文件没有{device_tag}的TAG配置信息，请检查配置文件 {self._config_file_path}")
            raise Exception("配置文件没有TAG配置信息，请检查配置文件")

    def get_click_open_response_phase_time(self):
        """
        获取点击桌面图标启动响应各阶段的时间
        """

        """
        Phase1 屏幕响应阶段:  暂不获取
        Phase2 手势识别阶段:  暂不获取
        Phase3 事件分发阶段：  Launcher接收到Up事件 --> SystemServer开始执行startActivity
        Phase4 系统执行阶段：  SystemServer开始执行startActivity --> 窗口onTransactionReady
        Phase5 动画响应时延：  窗口onTransactionReady --> openApp_Window 开始
        """
        self._scene_tag = "ClickIconOpen"

        # 获取 ACTION_UP 的Slice信息
        slice_tag, process_name = self._get_sql_tag("ACTION_UP")
        action_up_slice_list = get_slice_by_name_via_thread(self._tp, slice_tag, process_name)
        if action_up_slice_list:
            TEST_LOGGER.info(f"获取ACTION_UP的Slice信息：")
            for action_up_slice in action_up_slice_list:
                name = action_up_slice.name
                ts = action_up_slice.ts
                dur = action_up_slice.dur
                te = action_up_slice.te
                track_id = action_up_slice.track_id
                TEST_LOGGER.info(f"ACTION_UP: [{name}] --- [{ts}] --- [{dur}] --- [{te}] --- [{track_id}]")
        else:
            TEST_LOGGER.error(f"获取ACTION_UP的Slice信息失败！")
            return

        # 获取 SystemServer开始执行startActivity 的Slice信息
        slice_tag, process_name = self._get_sql_tag("startActivity")
        start_activity_slice_list = get_slice_by_name_via_thread(self._tp, slice_tag, process_name)
        if start_activity_slice_list:
            TEST_LOGGER.info(f"获取startActivity的Slice信息：")
            for start_activity_slice in start_activity_slice_list:
                name = start_activity_slice.name
                ts = start_activity_slice.ts
                dur = start_activity_slice.dur
                te = start_activity_slice.te
                track_id = start_activity_slice.track_id
                TEST_LOGGER.info(f"startActivity: [{name}] --- [{ts}] --- [{dur}] --- [{te}] --- [{track_id}]")
        else:
            TEST_LOGGER.error(f"获取startActivity的Slice信息失败！")
            return

        # 获取 窗口onTransactionReady 的Slice信息
        slice_tag, process_name = self._get_sql_tag("onTransitionReady")
        on_transition_ready_slice_list = get_slice_by_name_via_thread(self._tp, slice_tag, process_name)
        if on_transition_ready_slice_list:
            TEST_LOGGER.info(f"获取onTransitionReady的Slice信息：")
            for on_transition_ready_slice in on_transition_ready_slice_list:
                name = on_transition_ready_slice.name
                ts = on_transition_ready_slice.ts
                dur = on_transition_ready_slice.dur
                te = on_transition_ready_slice.te
                track_id = on_transition_ready_slice.track_id
                TEST_LOGGER.info(f"onTransitionReady: [{name}] --- [{ts}] --- [{dur}] --- [{te}] --- [{track_id}]")
        else:
            TEST_LOGGER.error(f"获取onTransitionReady的Slice信息失败！")
            return

        # 获取 openApp_Window 开始 的Slice信息
        open_app_window_slice_list = None
        slice_tag, process_name = self._get_sql_tag("openApp_Window")
        if slice_tag and process_name:
            open_app_window_slice_list = get_slice_by_name_via_process(self._tp, slice_tag, process_name)
            if open_app_window_slice_list:
                TEST_LOGGER.info(f"获取openApp_Window的Slice信息：")
                for open_app_window_slice in open_app_window_slice_list:
                    name = open_app_window_slice.name
                    ts = open_app_window_slice.ts
                    dur = open_app_window_slice.dur
                    te = open_app_window_slice.te
                    track_id = on_transition_ready_slice.track_id
                    TEST_LOGGER.info(f"openApp_Window: [{name}] --- [{ts}] --- [{dur}] --- [{te}] --- [{track_id}]")
            else:
                TEST_LOGGER.warn(f"获取openApp_Window的Slice信息失败！")
        else:
            TEST_LOGGER.warn(f"没有配置openApp_Window的tag，不获取openApp_Window的Slice信息！")

        # 传音项目通过 特殊标记 Transsion-start 获取对应的应用名称
        find_start_apk_tag = self._tag_dict.get(self._scene_tag).get("findPkgTag")
        ignore_package = self._tag_dict.get(self._scene_tag).get("ignore_package")
        start_package_dict = get_start_package_name(self._tp, find_start_apk_tag, ignore_package)
        if start_package_dict:
            TEST_LOGGER.info(f"获取启动时间与应用报名的映射关系：")
            for ts, package_name in start_package_dict.items():
                TEST_LOGGER.info(f"Package: [{ts}] --- [{package_name}]")
        else:
            TEST_LOGGER.warn(f"无法获取启动时间与应用报名的映射关系！")


        """
        ## 不用倒推，还是从ACTION_UP开始往后推，倒推会碰到 onTransitionReady 有很多的问题
        优化以start_activity为基准点，往前取最近的ACTION_UP
        """
        # 首先获取有效的 start_activity_slice_list
        if start_activity_slice_list and open_app_window_slice_list:
            start_activity_slice_list = get_valid_start_activity_list(start_activity_slice_list, open_app_window_slice_list)

        event_response_obj_list = []
        # 优化以start_activity为基准点，往前取最近的ACTION_UP
        for start_activity_slice in start_activity_slice_list:
            # 为每一个start_activity 创建一个 EventResponseObj 对象
            event_response_obj = EventResponseObj(self._scene_tag)
            event_response_obj_list.append(event_response_obj)

            ts_start_activity = start_activity_slice.ts
            dur_start_activity = start_activity_slice.dur
            te_start_activity = start_activity_slice.te

            # 遍历 action_up_slice_list，取最接近的那个ACTION_UP
            # 反向遍历action_up_slice_list

            for action_up_slice in reversed(action_up_slice_list):
                ts_action_up = action_up_slice.ts
                dur_action_up = action_up_slice.dur
                te_action_up = action_up_slice.te

                if ts_start_activity > ts_action_up:
                    event_response_obj.slice_detail.update(
                        {
                            "ts_action_up": ts_action_up,
                            "dur_action_up": dur_action_up,
                            "te_action_up": te_action_up
                        }
                    )

                    # T3: 手势分发阶段
                    event_response_obj.response_start_t3 = ts_action_up
                    event_response_obj.response_end_t3 = ts_start_activity
                    event_response_obj.response_dur_t3 = (ts_start_activity - ts_action_up) / 1e6

                    event_response_obj.slice_detail.update(
                        {
                            "ts_start_activity": ts_start_activity,
                            "dur_start_activity": dur_start_activity,
                            "te_start_activity": te_start_activity,
                            "response_start_t3": ts_action_up,
                            "response_end_t3": ts_start_activity,
                            "response_dur_t3": (ts_start_activity - ts_action_up) / 1e6
                        }
                    )
                    break

            # T4: 系统执行阶段
            # 获取第一个比 startActivity 大的  ts_on_transition_ready
            for on_transition_ready_slice in on_transition_ready_slice_list:
                ts_on_transition_ready = on_transition_ready_slice.ts
                dur_on_transition_ready = on_transition_ready_slice.dur
                te_on_transition_ready = on_transition_ready_slice.te

                if ts_on_transition_ready > ts_start_activity:
                    event_response_obj.response_start_t4 = ts_start_activity
                    event_response_obj.response_end_t4 = ts_on_transition_ready
                    event_response_obj.response_dur_t4 = (ts_on_transition_ready - ts_start_activity) / 1e6
                    event_response_obj.slice_detail.update(
                        {
                            "ts_on_transition_ready": ts_on_transition_ready,
                            "dur_on_transition_ready": dur_on_transition_ready,
                            "te_on_transition_ready": te_on_transition_ready,
                            "response_start_t4": ts_start_activity,
                            "response_end_t4": ts_on_transition_ready,
                            "response_dur_t4": (ts_on_transition_ready - ts_start_activity) / 1e6
                        }
                    )

                    # T5: 动画响应时延
                    if open_app_window_slice_list:

                        for open_app_window_slice in open_app_window_slice_list:
                            ts_open_app_window = open_app_window_slice.ts
                            dur_open_app_window = open_app_window_slice.dur
                            te_open_app_window = open_app_window_slice.te

                            # 获取第一个比 ts_on_transition_ready 大的  ts_open_app_window
                            if ts_open_app_window > ts_on_transition_ready:
                                # T5: 动画响应时延
                                event_response_obj.response_start_t5 = ts_on_transition_ready
                                event_response_obj.response_end_t5 = ts_open_app_window
                                event_response_obj.response_dur_t5 = (ts_open_app_window - ts_on_transition_ready) / 1e6
                                event_response_obj.slice_detail.update(
                                    {
                                        "ts_open_app_window": ts_open_app_window,
                                        "dur_open_app_window": dur_open_app_window,
                                        "te_open_app_window": te_open_app_window,
                                        "response_start_t5": ts_on_transition_ready,
                                        "response_end_t5": ts_open_app_window,
                                        "response_dur_t5": (ts_open_app_window - ts_on_transition_ready) / 1e6
                                    }
                                )

                                # T6: 窗口动画阶段
                                event_response_obj.response_start_t6 = ts_open_app_window
                                event_response_obj.response_end_t6 = te_open_app_window
                                event_response_obj.response_dur_t6 = dur_open_app_window / 1e6
                                event_response_obj.slice_detail.update(
                                    {
                                        "response_start_t6": ts_open_app_window,
                                        "response_end_t6": te_open_app_window,
                                        "response_dur_t6": dur_open_app_window / 1e6
                                    }
                                )
                                break
                    break

        # 获取包名
        # 尝试获取 ts_action_up 对应的 package_name
        if start_package_dict:
            for event_response_obj in event_response_obj_list:
                ts_action_up = event_response_obj.slice_detail.get("ts_action_up")
                # 尝试获取第一条比 ts_action_up 大的 package_name
                for ts, package in start_package_dict.items():
                    if ts > ts_action_up:
                        event_response_obj.package_name = package
                        event_response_obj.slice_detail.update(
                            {
                                "package_name": package
                            }
                        )
                        break

        response_info_list = []
        TEST_LOGGER.info(f"********** 获取点击桌面图标启动响应时延 **********")
        for event_response_obj in event_response_obj_list:
            package_name = event_response_obj.package_name
            response_dur_t3 = event_response_obj.response_dur_t3
            response_dur_t4 = event_response_obj.response_dur_t4
            response_dur_t5 = event_response_obj.response_dur_t5
            response_dur_t6 = event_response_obj.response_dur_t6
            slice_detail = event_response_obj.slice_detail
            TEST_LOGGER.info(f"[{package_name}] --- T3:[{response_dur_t3}], T4:[{response_dur_t4}], T5:[{response_dur_t5}], T6:[{response_dur_t6}]")
            response_info_list.append((package_name, response_dur_t3, response_dur_t4, response_dur_t5, response_dur_t6, slice_detail))

        return response_info_list

    def get_home_exit_response_phase_time(self):
        """
        获取点击Home退出场景的响应时延
        """

        """
        Phase1 屏幕响应阶段：  暂不获取
        Phase2 手势识别阶段：  暂不获取
        Phase3 事件分发阶段：  taskbar接收到Up事件 --> SystemServer开始执行startActivity
        Phase4 系统执行阶段：  SystemServer开始执行startActivity --> 窗口onTransactionReady
        Phase5 动画响应时延：  窗口onTransactionReady --> closeApp_Window_enter 开始
        """
        self._scene_tag = "clickHomeExit"

        # 获取 ACTION_UP 的Slice信息
        slice_tag, process_name = self._get_sql_tag("ACTION_UP")
        action_up_slice_list = get_slice_by_name_via_thread(self._tp, slice_tag, process_name)
        if action_up_slice_list:
            TEST_LOGGER.info(f"获取ACTION_UP的Slice信息：")
            for action_up_slice in action_up_slice_list:
                name = action_up_slice.name
                ts = action_up_slice.ts
                dur = action_up_slice.dur
                te = action_up_slice.te
                track_id = action_up_slice.track_id
                TEST_LOGGER.info(f"ACTION_UP: [{name}] --- [{ts}] --- [{dur}] --- [{te}] --- [{track_id}]")
        else:
            TEST_LOGGER.error(f"获取ACTION_UP的Slice信息失败！")
            return

        # 获取 SystemServer开始执行startActivity 的Slice信息
        slice_tag, process_name = self._get_sql_tag("startActivity")
        start_activity_slice_list = get_slice_by_name_via_thread(self._tp, slice_tag, process_name)
        if start_activity_slice_list:
            TEST_LOGGER.info(f"获取startActivity的Slice信息：")
            for start_activity_slice in start_activity_slice_list:
                name = start_activity_slice.name
                ts = start_activity_slice.ts
                dur = start_activity_slice.dur
                te = start_activity_slice.te
                track_id = start_activity_slice.track_id
                TEST_LOGGER.info(f"startActivity: [{name}] --- [{ts}] --- [{dur}] --- [{te}] --- [{track_id}]")
        else:
            TEST_LOGGER.error(f"获取startActivity的Slice信息失败！")
            return

        # 获取 窗口onTransactionReady 的Slice信息
        slice_tag, process_name = self._get_sql_tag("onTransitionReady")
        on_transition_ready_slice_list = get_slice_by_name_via_thread(self._tp, slice_tag, process_name)
        if on_transition_ready_slice_list:
            TEST_LOGGER.info(f"获取onTransitionReady的Slice信息：")
            for on_transition_ready_slice in on_transition_ready_slice_list:
                name = on_transition_ready_slice.name
                ts = on_transition_ready_slice.ts
                dur = on_transition_ready_slice.dur
                te = on_transition_ready_slice.te
                track_id = on_transition_ready_slice.track_id
                TEST_LOGGER.info(f"onTransitionReady: [{name}] --- [{ts}] --- [{dur}] --- [{te}] --- [{track_id}]")
        else:
            TEST_LOGGER.error(f"获取onTransitionReady的Slice信息失败！")
            return

        # 获取 openApp_Window 开始 的Slice信息
        open_app_window_slice_list = None
        slice_tag, process_name = self._get_sql_tag("openApp_Window")
        if slice_tag and process_name:
            open_app_window_slice_list = get_slice_by_name_via_process(self._tp, slice_tag, process_name)
            if open_app_window_slice_list:
                TEST_LOGGER.info(f"获取openApp_Window的Slice信息：")
                for open_app_window_slice in open_app_window_slice_list:
                    name = open_app_window_slice.name
                    ts = open_app_window_slice.ts
                    dur = open_app_window_slice.dur
                    te = open_app_window_slice.te
                    track_id = on_transition_ready_slice.track_id
                    TEST_LOGGER.info(f"openApp_Window: [{name}] --- [{ts}] --- [{dur}] --- [{te}] --- [{track_id}]")
            else:
                TEST_LOGGER.warn(f"获取openApp_Window的Slice信息失败！")
        else:
            TEST_LOGGER.warn(f"没有配置openApp_Window的tag，不获取openApp_Window的Slice信息！")

        # 传音项目通过 特殊标记 Transsion-start 获取对应的应用名称
        find_start_apk_tag = self._tag_dict.get(self._scene_tag).get("findPkgTag")
        ignore_package = self._tag_dict.get(self._scene_tag).get("ignore_package")
        start_package_dict = get_start_package_name(self._tp, find_start_apk_tag, ignore_package,False)
        if start_package_dict:
            TEST_LOGGER.info(f"获取启动时间与应用报名的映射关系：")
            for ts, package_name in start_package_dict.items():
                TEST_LOGGER.info(f"Package: [{ts}] --- [{package_name}]")
        else:
            TEST_LOGGER.warn(f"无法获取启动时间与应用报名的映射关系！")


        """
        ## 不用倒推，还是从ACTION_UP开始往后推，倒推会碰到 onTransitionReady 有很多的问题
        优化以start_activity为基准点，往前取最近的ACTION_UP
        """
        event_response_obj_list = []

        # 首先获取有效的 start_activity_slice_list
        if start_activity_slice_list and open_app_window_slice_list:
            start_activity_slice_list = get_valid_start_activity_list(start_activity_slice_list, open_app_window_slice_list)

        # 优化以start_activity为基准点，往前取最近的ACTION_UP
        for start_activity_slice in start_activity_slice_list:

            # 为每一个start_activity 创建一个 EventResponseObj 对象
            event_response_obj = EventResponseObj(self._scene_tag)
            event_response_obj_list.append(event_response_obj)

            ts_start_activity = start_activity_slice.ts
            dur_start_activity = start_activity_slice.dur
            te_start_activity = start_activity_slice.te

            # 反向遍历action_up_slice_list，取最接近的那个ACTION_UP
            for action_up_slice in reversed(action_up_slice_list):
                ts_action_up = action_up_slice.ts
                dur_action_up = action_up_slice.dur
                te_action_up = action_up_slice.te

                if ts_start_activity > ts_action_up:
                    event_response_obj.slice_detail.update(
                        {
                            "ts_action_up": ts_action_up,
                            "dur_action_up": dur_action_up,
                            "te_action_up": te_action_up
                        }
                    )

                    # T3: 手势分发阶段
                    event_response_obj.response_start_t3 = ts_action_up
                    event_response_obj.response_end_t3 = ts_start_activity
                    event_response_obj.response_dur_t3 = (ts_start_activity - ts_action_up) / 1e6

                    event_response_obj.slice_detail.update(
                        {
                            "ts_start_activity": ts_start_activity,
                            "dur_start_activity": dur_start_activity,
                            "te_start_activity": te_start_activity,
                            "response_start_t3": ts_action_up,
                            "response_end_t3": ts_start_activity,
                            "response_dur_t3": (ts_start_activity - ts_action_up) / 1e6
                        }
                    )
                    break

            # T4: 系统执行阶段
            # 获取第一个比 startActivity 大的  ts_on_transition_ready
            for on_transition_ready_slice in on_transition_ready_slice_list:
                ts_on_transition_ready = on_transition_ready_slice.ts
                dur_on_transition_ready = on_transition_ready_slice.dur
                te_on_transition_ready = on_transition_ready_slice.te

                if ts_on_transition_ready > ts_start_activity:
                    event_response_obj.response_start_t4 = ts_start_activity
                    event_response_obj.response_end_t4 = ts_on_transition_ready
                    event_response_obj.response_dur_t4 = (ts_on_transition_ready - ts_start_activity) / 1e6
                    event_response_obj.slice_detail.update(
                        {
                            "ts_on_transition_ready": ts_on_transition_ready,
                            "dur_on_transition_ready": dur_on_transition_ready,
                            "te_on_transition_ready": te_on_transition_ready,
                            "response_start_t4": ts_start_activity,
                            "response_end_t4": ts_on_transition_ready,
                            "response_dur_t4": (ts_on_transition_ready - ts_start_activity) / 1e6
                        }
                    )

                    # T5: 动画响应时延
                    if open_app_window_slice_list:

                        for open_app_window_slice in open_app_window_slice_list:
                            ts_open_app_window = open_app_window_slice.ts
                            dur_open_app_window = open_app_window_slice.dur
                            te_open_app_window = open_app_window_slice.te

                            # 获取第一个比 ts_on_transition_ready 大的  ts_open_app_window
                            if ts_open_app_window > ts_on_transition_ready:
                                # T5: 动画响应时延
                                event_response_obj.response_start_t5 = ts_on_transition_ready
                                event_response_obj.response_end_t5 = ts_open_app_window
                                event_response_obj.response_dur_t5 = (ts_open_app_window - ts_on_transition_ready) / 1e6
                                event_response_obj.slice_detail.update(
                                    {
                                        "ts_open_app_window": ts_open_app_window,
                                        "dur_open_app_window": dur_open_app_window,
                                        "te_open_app_window": te_open_app_window,
                                        "response_start_t5": ts_on_transition_ready,
                                        "response_end_t5": ts_open_app_window,
                                        "response_dur_t5": (ts_open_app_window - ts_on_transition_ready) / 1e6
                                    }
                                )

                                # T6: 窗口动画阶段
                                event_response_obj.response_start_t6 = ts_open_app_window
                                event_response_obj.response_end_t6 = te_open_app_window
                                event_response_obj.response_dur_t6 = dur_open_app_window / 1e6
                                event_response_obj.slice_detail.update(
                                    {
                                        "response_start_t6": ts_open_app_window,
                                        "response_end_t6": te_open_app_window,
                                        "response_dur_t6": dur_open_app_window / 1e6
                                    }
                                )
                                break
                    break

        # 获取包名
        # 尝试获取 ts_action_up 对应的 package_name
        if start_package_dict:
            for event_response_obj in event_response_obj_list:
                ts_action_up = event_response_obj.slice_detail.get("ts_action_up")
                # 尝试获取第一条比 ts_action_up 小的 package_name
                for ts, package in start_package_dict.items():
                    if ts < ts_action_up:
                        event_response_obj.package_name = package
                        event_response_obj.slice_detail.update(
                            {
                                "package_name": package
                            }
                        )
                        break

        response_info_list = []
        TEST_LOGGER.info(f"********** 获取点击Home退出响应时延 **********")
        for event_response_obj in event_response_obj_list:
            package_name = event_response_obj.package_name
            response_dur_t3 = event_response_obj.response_dur_t3
            response_dur_t4 = event_response_obj.response_dur_t4
            response_dur_t5 = event_response_obj.response_dur_t5
            response_dur_t6 = event_response_obj.response_dur_t6
            slice_detail = event_response_obj.slice_detail
            TEST_LOGGER.info(f"[{package_name}] --- T3:[{response_dur_t3}], T4:[{response_dur_t4}], T5:[{response_dur_t5}], T6:[{response_dur_t6}]")
            response_info_list.append((package_name, response_dur_t3, response_dur_t4, response_dur_t5, response_dur_t6, slice_detail))

        return response_info_list

    def get_app_to_recent_response_phase_time(self):
        """
        获取应用界面按菜单键进入Recent响应各阶段的时间
        """

        """
        Phase1 屏幕响应阶段：  暂不获取
        Phase2 手势识别阶段：  暂不获取
        Phase3 手势分发阶段：  taskbar接收到Up事件 --> SystemServer开始执行startNewTransition
        Phase4 系统执行阶段：  SystemServer开始执行startNewTransition --> 窗口onTransactionReady
        Phase5 动画响应时延：  窗口onTransactionReady --> animator:App To Recents 开始
        """
        self._scene_tag = "clickToRecent"

        # 获取 ACTION_UP 的Slice信息
        slice_tag, process_name = self._get_sql_tag("ACTION_UP")
        action_up_slice_list = get_slice_by_name_via_thread(self._tp, slice_tag, process_name)
        if action_up_slice_list:
            TEST_LOGGER.info(f"获取ACTION_UP的Slice信息：")
            for action_up_slice in action_up_slice_list:
                name = action_up_slice.name
                ts = action_up_slice.ts
                dur = action_up_slice.dur
                te = action_up_slice.te
                track_id = action_up_slice.track_id
                TEST_LOGGER.info(f"ACTION_UP: [{name}] --- [{ts}] --- [{dur}] --- [{te}] --- [{track_id}]")
        else:
            TEST_LOGGER.error(f"获取ACTION_UP的Slice信息失败！")
            return

        # 获取 SystemServer开始执行startNewTransition 的Slice信息
        slice_tag, process_name = self._get_sql_tag("startNewTransition")
        start_new_transition_slice_list = get_slice_by_name_via_thread(self._tp, slice_tag, process_name)
        if start_new_transition_slice_list:
            TEST_LOGGER.info(f"获取startNewTransition的Slice信息：")
            for start_new_transition_slice in start_new_transition_slice_list:
                name = start_new_transition_slice.name
                ts = start_new_transition_slice.ts
                dur = start_new_transition_slice.dur
                te = start_new_transition_slice.te
                track_id = start_new_transition_slice.track_id
                TEST_LOGGER.info(f"startNewTransition: [{name}] --- [{ts}] --- [{dur}] --- [{te}] --- [{track_id}]")
        else:
            TEST_LOGGER.error(f"获取startNewTransition的Slice信息失败！")
            return

        # 获取 窗口onTransactionReady 的Slice信息
        slice_tag, process_name = self._get_sql_tag("onTransitionReady")
        on_transition_ready_slice_list = get_slice_by_name_via_thread(self._tp, slice_tag, process_name)
        if on_transition_ready_slice_list:
            TEST_LOGGER.info(f"获取onTransitionReady的Slice信息：")
            for on_transition_ready_slice in on_transition_ready_slice_list:
                name = on_transition_ready_slice.name
                ts = on_transition_ready_slice.ts
                dur = on_transition_ready_slice.dur
                te = on_transition_ready_slice.te
                track_id = on_transition_ready_slice.track_id
                TEST_LOGGER.info(f"onTransitionReady: [{name}] --- [{ts}] --- [{dur}] --- [{te}] --- [{track_id}]")
        else:
            TEST_LOGGER.error(f"获取onTransitionReady的Slice信息失败！")
            return

        # 获取 appToRecents 开始 的Slice信息
        app_to_recents_slice_list = None
        slice_tag, process_name = self._get_sql_tag("appToRecents")
        if slice_tag and process_name:
            app_to_recents_slice_list = get_slice_by_name_via_process(self._tp, slice_tag, process_name)
            if app_to_recents_slice_list:
                TEST_LOGGER.info(f"获取appToRecents的Slice信息：")
                for app_to_recents_slice in app_to_recents_slice_list:
                    name = app_to_recents_slice.name
                    ts = app_to_recents_slice.ts
                    dur = app_to_recents_slice.dur
                    te = app_to_recents_slice.te
                    track_id = app_to_recents_slice.track_id
                    TEST_LOGGER.info(f"appToRecents: [{name}] --- [{ts}] --- [{dur}] --- [{te}] --- [{track_id}]")
            else:
                TEST_LOGGER.warn(f"获取appToRecents的Slice信息失败！")
        else:
            TEST_LOGGER.warn(f"没有配置appToRecents的tag，不获取appToRecents的Slice信息！")

        """
        不用倒推，还是从ACTION_UP开始往后推，倒推会碰到 onTransitionReady 有很多的问题
        """
        event_response_obj_list = []

        # 首先获取 T3: 手势识别阶段 的数据
        for action_up_slice in action_up_slice_list:
            # 为每一个ACTION_UP 创建一个 EventResponseObj 对象
            event_response_obj = EventResponseObj(self._scene_tag)
            event_response_obj_list.append(event_response_obj)

            ts_action_up = action_up_slice.ts
            dur_action_up = action_up_slice.dur
            te_action_up = action_up_slice.te

            event_response_obj.slice_detail.update(
                {
                    "ts_action_up": ts_action_up,
                    "dur_action_up": dur_action_up,
                    "te_action_up": te_action_up
                }
            )

            for start_new_transition_slice in start_new_transition_slice_list:
                ts_start_new_transition = start_new_transition_slice.ts
                dur_start_new_transition = start_new_transition_slice.dur
                te_start_new_transition = start_new_transition_slice.te

                # 获取第一个比 ts_action_up 大的 start_new_transition
                if ts_start_new_transition > ts_action_up:
                    # T3: 手势分发阶段
                    event_response_obj.response_start_t3 = ts_action_up
                    event_response_obj.response_end_t3 = ts_start_new_transition
                    event_response_obj.response_dur_t3 = (ts_start_new_transition - ts_action_up) / 1e6

                    event_response_obj.slice_detail.update(
                        {
                            "ts_start_new_transition": ts_start_new_transition,
                            "dur_start_new_transition": dur_start_new_transition,
                            "te_start_new_transition": te_start_new_transition,
                            "response_start_t3": ts_action_up,
                            "response_end_t3": ts_start_new_transition,
                            "response_dur_t3": (ts_start_new_transition - ts_action_up) / 1e6
                        }
                    )

                    # T4: 系统执行阶段
                    # 获取第一个比 start_new_transition 大的  ts_on_transition_ready
                    for on_transition_ready_slice in on_transition_ready_slice_list:
                        ts_on_transition_ready = on_transition_ready_slice.ts
                        dur_on_transition_ready = on_transition_ready_slice.dur
                        te_on_transition_ready = on_transition_ready_slice.te

                        if ts_on_transition_ready > ts_start_new_transition:
                            event_response_obj.response_start_t4 = ts_start_new_transition
                            event_response_obj.response_end_t4 = ts_on_transition_ready
                            event_response_obj.response_dur_t4 = (ts_on_transition_ready - ts_start_new_transition) / 1e6
                            event_response_obj.slice_detail.update(
                                {
                                    "ts_on_transition_ready": ts_on_transition_ready,
                                    "dur_on_transition_ready": dur_on_transition_ready,
                                    "te_on_transition_ready": te_on_transition_ready,
                                    "response_start_t4": ts_start_new_transition,
                                    "response_end_t4": ts_on_transition_ready,
                                    "response_dur_t4": (ts_on_transition_ready - ts_start_new_transition) / 1e6
                                }
                            )

                            # T5: 动画响应时延
                            if app_to_recents_slice_list:
                                for app_to_recents_slice in app_to_recents_slice_list:
                                    ts_app_to_recents = app_to_recents_slice.ts
                                    dur_app_to_recents = app_to_recents_slice.dur
                                    te_app_to_recents = app_to_recents_slice.te

                                    # 取第一个比 ts_on_transition_ready 大的 app_to_recents
                                    if ts_app_to_recents > ts_on_transition_ready:

                                        # T5: 动画响应时延
                                        event_response_obj.response_start_t5 = ts_on_transition_ready
                                        event_response_obj.response_end_t5 = ts_app_to_recents
                                        event_response_obj.response_dur_t5 = (ts_app_to_recents - ts_on_transition_ready) / 1e6
                                        event_response_obj.slice_detail.update(
                                            {
                                                "ts_app_to_recents": ts_app_to_recents,
                                                "dur_app_to_recents": dur_app_to_recents,
                                                "te_app_to_recents": te_app_to_recents,
                                                "response_start_t5": ts_on_transition_ready,
                                                "response_end_t5": ts_app_to_recents,
                                                "response_dur_t5": (ts_app_to_recents - ts_on_transition_ready) / 1e6
                                            }
                                        )

                                        # T6: 窗口动画阶段
                                        event_response_obj.response_start_t6 = ts_app_to_recents
                                        event_response_obj.response_end_t6 = te_app_to_recents
                                        event_response_obj.response_dur_t6 = dur_app_to_recents / 1e6
                                        event_response_obj.slice_detail.update(
                                            {
                                                "response_start_t6": ts_app_to_recents,
                                                "response_end_t6": te_app_to_recents,
                                                "response_dur_t6": dur_app_to_recents / 1e6
                                            }
                                        )
                                        break
                                break
                            break
                    break

        response_info_list = []
        TEST_LOGGER.info(f"********** 获取应用界面按菜单进入Recents响应时延 **********")
        for event_response_obj in event_response_obj_list:
            package_name = event_response_obj.package_name
            response_dur_t3 = event_response_obj.response_dur_t3
            response_dur_t4 = event_response_obj.response_dur_t4
            response_dur_t5 = event_response_obj.response_dur_t5
            response_dur_t6 = event_response_obj.response_dur_t6
            slice_detail = event_response_obj.slice_detail
            TEST_LOGGER.info(f"[{package_name}] --- T3:[{response_dur_t3}], T4:[{response_dur_t4}], T5:[{response_dur_t5}], T6:[{response_dur_t6}]")
            response_info_list.append((package_name, response_dur_t3, response_dur_t4, response_dur_t5, response_dur_t6, slice_detail))

        return response_info_list

    def get_recent_to_app_response_phase_time(self):
        """
        获取Recent点击卡片启动应用响应各阶段的时间
        """

        """
        Phase1 屏幕响应阶段：  暂不获取
        Phase2 手势识别阶段：  暂不获取
        Phase3 手势分发阶段：  launcher接收到Up事件 --> SystemServer开始执行startActivityFromRecents
        Phase4 系统执行阶段：  SystemServer开始执行startActivityFromRecents --> 窗口onTransactionReady
        Phase5 动画响应时延：  窗口onTransactionReady --> animator:App To Recents 开始
        """
        self._scene_tag = "recentToApp"

        # 获取 ACTION_UP 的Slice信息
        slice_tag, process_name = self._get_sql_tag("ACTION_UP")
        action_up_slice_list = get_slice_by_name_via_thread(self._tp, slice_tag, process_name, False)
        if action_up_slice_list:
            TEST_LOGGER.info(f"获取ACTION_UP的Slice信息：")
            for action_up_slice in action_up_slice_list:
                name = action_up_slice.name
                ts = action_up_slice.ts
                dur = action_up_slice.dur
                te = action_up_slice.te
                track_id = action_up_slice.track_id
                TEST_LOGGER.info(f"ACTION_UP: [{name}] --- [{ts}] --- [{dur}] --- [{te}] --- [{track_id}]")
        else:
            TEST_LOGGER.error(f"获取ACTION_UP的Slice信息失败！")
            return

        # 获取 SystemServer开始执行startActivityFromRecents 的Slice信息
        slice_tag, process_name = self._get_sql_tag("startActivityFromRecents")
        start_activity_from_recents_slice_list = get_slice_by_name_via_thread(self._tp, slice_tag, process_name)
        if start_activity_from_recents_slice_list:
            TEST_LOGGER.info(f"获取startActivityFromRecents的Slice信息：")
            for start_activity_from_recents_slice in start_activity_from_recents_slice_list:
                name = start_activity_from_recents_slice.name
                ts = start_activity_from_recents_slice.ts
                dur = start_activity_from_recents_slice.dur
                te = start_activity_from_recents_slice.te
                track_id = start_activity_from_recents_slice.track_id
                TEST_LOGGER.info(f"startActivityFromRecents: [{name}] --- [{ts}] --- [{dur}] --- [{te}] --- [{track_id}]")
        else:
            TEST_LOGGER.error(f"获取startActivityFromRecents的Slice信息失败！")
            return

        # 获取 窗口onTransactionReady 的Slice信息
        slice_tag, process_name = self._get_sql_tag("onTransitionReady")
        on_transition_ready_slice_list = get_slice_by_name_via_thread(self._tp, slice_tag, process_name)
        if on_transition_ready_slice_list:
            TEST_LOGGER.info(f"获取onTransitionReady的Slice信息：")
            for on_transition_ready_slice in on_transition_ready_slice_list:
                name = on_transition_ready_slice.name
                ts = on_transition_ready_slice.ts
                dur = on_transition_ready_slice.dur
                te = on_transition_ready_slice.te
                track_id = on_transition_ready_slice.track_id
                TEST_LOGGER.info(f"onTransitionReady: [{name}] --- [{ts}] --- [{dur}] --- [{te}] --- [{track_id}]")
        else:
            TEST_LOGGER.error(f"获取onTransitionReady的Slice信息失败！")
            return

        # 获取 animator:Task Launch 开始 的Slice信息
        animator_task_launch_slice_list = None
        slice_tag, process_name = self._get_sql_tag("animatorTaskLaunch")
        if slice_tag and process_name:
            animator_task_launch_slice_list = get_slice_by_name_via_process(self._tp, slice_tag, process_name)
            if animator_task_launch_slice_list:
                TEST_LOGGER.info(f"获取animatorTaskLaunch的Slice信息：")
                for animator_task_launch_slice in animator_task_launch_slice_list:
                    name = animator_task_launch_slice.name
                    ts = animator_task_launch_slice.ts
                    dur = animator_task_launch_slice.dur
                    te = animator_task_launch_slice.te
                    track_id = animator_task_launch_slice.track_id
                    TEST_LOGGER.info(f"animatorTaskLaunch: [{name}] --- [{ts}] --- [{dur}] --- [{te}] --- [{track_id}]")
            else:
                TEST_LOGGER.warn(f"获取animatorTaskLaunch的Slice信息失败！")
        else:
            TEST_LOGGER.warn(f"没有配置animatorTaskLaunch的tag，不获取animatorTaskLaunch的Slice信息！")

        """
        不用倒推，还是从ACTION_UP开始往后推，倒推会碰到 onTransitionReady 有很多的问题
        """
        event_response_obj_list = []

        # 首先获取 T3: 手势识别阶段 的数据
        # 由于ACTION_UP的数据可能过多，从 startActivityFromRecents 开始定位
        for start_activity_from_recents_slice in start_activity_from_recents_slice_list:
            # 为每一个ACTION_UP 创建一个 EventResponseObj 对象
            event_response_obj = EventResponseObj(self._scene_tag)
            event_response_obj_list.append(event_response_obj)

            ts_start_activity_from_recents = start_activity_from_recents_slice.ts
            dur_start_activity_from_recents = start_activity_from_recents_slice.dur
            te_start_activity_from_recents = start_activity_from_recents_slice.te

            # 首先往前倒推最近的ACTION_UP
            for action_up_slice in action_up_slice_list:
                ts_action_up = action_up_slice.ts
                dur_action_up = action_up_slice.dur
                te_action_up = action_up_slice.te

                # 获取第一个比 ts_start_activity_from_recents 小的 ts_action_up
                if ts_start_activity_from_recents > ts_action_up:
                    event_response_obj.slice_detail.update(
                        {
                            "ts_action_up": ts_action_up,
                            "dur_action_up": dur_action_up,
                            "te_action_up": te_action_up
                        }
                    )

                    # T3: 手势分发阶段
                    event_response_obj.response_start_t3 = ts_action_up
                    event_response_obj.response_end_t3 = ts_start_activity_from_recents
                    event_response_obj.response_dur_t3 = (ts_start_activity_from_recents - ts_action_up) / 1e6

                    event_response_obj.slice_detail.update(
                        {
                            "ts_start_activity_from_recents": ts_start_activity_from_recents,
                            "dur_start_activity_from_recents": dur_start_activity_from_recents,
                            "te_start_activity_from_recents": te_start_activity_from_recents,
                            "response_start_t3": ts_action_up,
                            "response_end_t3": ts_start_activity_from_recents,
                            "response_dur_t3": (ts_start_activity_from_recents - ts_action_up) / 1e6
                        }
                    )
                    break

            # T4: 系统执行阶段
            # 获取第一个比 ts_start_activity_from_recents 大的  ts_on_transition_ready
            for on_transition_ready_slice in on_transition_ready_slice_list:
                ts_on_transition_ready = on_transition_ready_slice.ts
                dur_on_transition_ready = on_transition_ready_slice.dur
                te_on_transition_ready = on_transition_ready_slice.te

                if ts_on_transition_ready > ts_start_activity_from_recents:
                    event_response_obj.response_start_t4 = ts_start_activity_from_recents
                    event_response_obj.response_end_t4 = ts_on_transition_ready
                    event_response_obj.response_dur_t4 = (ts_on_transition_ready - ts_start_activity_from_recents) / 1e6
                    event_response_obj.slice_detail.update(
                        {
                            "ts_on_transition_ready": ts_on_transition_ready,
                            "dur_on_transition_ready": dur_on_transition_ready,
                            "te_on_transition_ready": te_on_transition_ready,
                            "response_start_t4": ts_start_activity_from_recents,
                            "response_end_t4": ts_on_transition_ready,
                            "response_dur_t4": (ts_on_transition_ready - ts_start_activity_from_recents) / 1e6
                        }
                    )

                    # T5: 动画响应时延
                    if animator_task_launch_slice_list:
                        for animator_task_launch_slice in animator_task_launch_slice_list:
                            ts_animator_task_launch = animator_task_launch_slice.ts
                            dur_animator_task_launch = animator_task_launch_slice.dur
                            te_animator_task_launch = animator_task_launch_slice.te

                            # ************************************************
                            # 取第一个比 ts_on_transition_ready 大的 ts_animator_task_launch
                            # ************************************************
                            if ts_animator_task_launch > ts_on_transition_ready:

                                # T5: 动画响应时延
                                event_response_obj.response_start_t5 = ts_on_transition_ready
                                event_response_obj.response_end_t5 = ts_animator_task_launch
                                event_response_obj.response_dur_t5 = (ts_animator_task_launch - ts_on_transition_ready) / 1e6
                                event_response_obj.slice_detail.update(
                                    {
                                        "ts_animator_task_launch": ts_animator_task_launch,
                                        "dur_animator_task_launch": dur_animator_task_launch,
                                        "te_animator_task_launch": te_animator_task_launch,
                                        "response_start_t5": ts_on_transition_ready,
                                        "response_end_t5": ts_animator_task_launch,
                                        "response_dur_t5": (ts_animator_task_launch - ts_on_transition_ready)  / 1e6
                                    }
                                )

                                # T6: 窗口动画阶段
                                event_response_obj.response_start_t6 = ts_animator_task_launch
                                event_response_obj.response_end_t6 = te_animator_task_launch
                                event_response_obj.response_dur_t6 = dur_animator_task_launch / 1e6
                                event_response_obj.slice_detail.update(
                                    {
                                        "response_start_t6": ts_animator_task_launch,
                                        "response_end_t6": te_animator_task_launch,
                                        "response_dur_t6": dur_animator_task_launch / 1e6
                                    }
                                )
                                break
                    break

        response_info_list = []
        TEST_LOGGER.info(f"********** 获取Recents点击启动应用响应时延 **********")
        for event_response_obj in event_response_obj_list:
            package_name = event_response_obj.package_name
            response_dur_t3 = event_response_obj.response_dur_t3
            response_dur_t4 = event_response_obj.response_dur_t4
            response_dur_t5 = event_response_obj.response_dur_t5
            response_dur_t6 = event_response_obj.response_dur_t6
            slice_detail = event_response_obj.slice_detail
            TEST_LOGGER.info(f"[{package_name}] --- T3:[{response_dur_t3}], T4:[{response_dur_t4}], T5:[{response_dur_t5}], T6:[{response_dur_t6}]")
            response_info_list.append((package_name, response_dur_t3, response_dur_t4, response_dur_t5, response_dur_t6, slice_detail))

        return response_info_list

    def _get_sql_tag(self, action_tag):
        slice_tag, process_name = None, None
        action_tag_dict = self._tag_dict.get(self._scene_tag).get(action_tag)
        if action_tag_dict:
            slice_tag = action_tag_dict.get("slice_tag")
            process_name = action_tag_dict.get("process")
        return slice_tag, process_name


def get_valid_start_activity_list(start_activity_slice_list, open_app_window_slice_list):
    valid_start_activity_list = []
    # 获取 open_app_window_slice_list 中每个open app window 前的第一个start activity
    for open_app_window_slice in open_app_window_slice_list:
        ts_open_app_window = open_app_window_slice.ts
        for start_activity_slice in reversed(start_activity_slice_list):
            ts_start_activity = start_activity_slice.ts
            if ts_start_activity < ts_open_app_window:
                valid_start_activity_list.append(start_activity_slice)
                break
    return valid_start_activity_list


class EventResponseObj:
    def __init__(self, event_type):
        self.event_type = event_type
        self.package_name = None
        self.response_dur_t1 = None
        self.response_start_t1 = None
        self.response_end_t1 = None
        self.response_dur_t2 = None
        self.response_start_t2 = None
        self.response_end_t2 = None
        self.response_dur_t3 = None
        self.response_start_t3 = None
        self.response_end_t3 = None
        self.response_dur_t4 = None
        self.response_start_t4 = None
        self.response_end_t4 = None
        self.response_dur_t5 = None
        self.response_start_t5 = None
        self.response_end_t5 = None
        self.response_dur_t6 = None
        self.response_start_t6 = None
        self.response_end_t6 = None
        self.slice_detail = {}


if __name__ == '__main__':
    # tp = ContinusOpenTransitionPerformance(r'D:\Logs\trace\连续启动示例Trace\精简动画\启动退出\redmi_trace_0_002_000.perfetto-trace', "redmi")
    # tp = ContinusOpenTransitionPerformance(r'D:\Logs\trace\TECNO_CM5_连续启动_精简.perfetto-trace', "CM5")
    # start_response_list = tp.get_click_open_response_phase_time()
    # start_response_list = tp.get_home_exit_response_phase_time()
    # tp = ContinusOpenTransitionPerformance(r'D:\Logs\trace\TECNO_CM5_连续切换_精简.perfetto-trace', "CM5")
    # start_response_list = tp.get_app_to_recent_response_phase_time()
    # start_response_list = tp.get_recent_to_app_response_phase_time()
    bin_path = r"D:\trace_processor_shell.exe"
    tp = ContinusOpenTransitionPerformance(r'\\10.205.4.20\sw_log\体验测试Log\xuewei.li\X6887\连续启动模型\Redmi14\连续启动\20251031_153059_pcss_24094RAD4I_AQPRFMIRWWRSVCTO\session_logs\trace\conti_launch_traces\20251031_153133_1_pcss_conti_launch_连续启动第1轮第1组.pftrace', "com.miui.home", bin_path=bin_path)
    start_response_list = tp.get_click_open_response_phase_time()
    # start_response_list = tp.get_home_exit_response_phase_time()

