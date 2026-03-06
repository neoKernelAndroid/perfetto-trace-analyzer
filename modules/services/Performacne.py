# -*- coding: utf-8 -*-
# @Time     : 2025/4/11 11:05
# @Author   : yunqing.gui
# @Email    : yunqing.gui@transsion.com
# @File     : Performacne.py


from modules.PerfettoSql.PerfettoSqlCommon import get_startup_info, get_translation_info, \
    get_render_thread_drowFrames, get_choreographer_doFrame, get_dequeueBuffer, get_vsync_sf, get_backpressure, \
    get_process_thread_count, get_all_process_thread_count, get_multiple_process_thread_count

from modules.services.TraceProcessor import TraceProcessorBasic


class PerformanceTraceProcessor(TraceProcessorBasic):
    def __init__(self, trace_file_path, bin_path=None, verbose=None):
        super().__init__(trace_file_path, bin_path, verbose)


    def get_startup_info(self):
        startup_info_list = get_startup_info(self._tp)
        for startup_info in startup_info_list:
            print(startup_info)

    def get_translation_info(self):
        translation_info_list = get_translation_info(self._tp)
        for translation_info in translation_info_list:
            print(translation_info)

    def get_frame_drop_thread(self, package_name):
        doFrame_dict = get_choreographer_doFrame(self._tp, package_name)
        drawFrames_dict = get_render_thread_drowFrames(self._tp)
        dequeueBuffer_list = get_dequeueBuffer(self._tp)
        frame_dur_dict = {}

        for vsync_id, ts in doFrame_dict.items():
            ts_end = drawFrames_dict.get(vsync_id)
            if ts_end:
                dur = ts_end - ts
                # 找出这一段的dequequeBuffer时长
                for dequeque_buffer_ts, dequeque_buffer_ts_end, dequeque_buffer_dur in dequeueBuffer_list:
                    if dequeque_buffer_ts > ts and dequeque_buffer_ts_end < ts_end:
                        dur = dur - dequeque_buffer_dur
                        print(f"find dequeque_buffer_dur: {dequeque_buffer_dur}")
                        break
                frame_dur_dict[vsync_id] = dur

        for vsync_id, dur in frame_dur_dict.items():
            if dur / 1e6 > 25:
                print(f"***** 发现超时帧： vsync_id {vsync_id}, dur:{dur}")

    def get_frame_drop_sf(self, hz):
        delta_threshold = 2 * (1000.0 / hz)
        sf_jank_count = 0

        vsync_sf_list = get_vsync_sf(self._tp)
        for i in range(len(vsync_sf_list) - 1):
            delta_vsync_value = (vsync_sf_list[i + 1] - vsync_sf_list[i]) / 1e6
            if delta_vsync_value > delta_threshold:
                jank_count = int(delta_vsync_value / (1000 / hz) - 1)
                sf_jank_count = sf_jank_count + jank_count

        backpressure_list = get_backpressure(self._tp)
        backpressure_count = len(backpressure_list)
        total_sf_jank_count = sf_jank_count + backpressure_count
        return total_sf_jank_count, sf_jank_count, backpressure_count

    def get_process_thread_count(self, process_name):
        """
        获取指定进程的线程数量和详细信息
        :param process_name: 进程名称，如 'system_server', 'com.android.systemui'
        :return: 包含线程数和线程列表的字典
        """
        return get_process_thread_count(self._tp, process_name)

    def get_all_process_thread_count(self, top_n=20):
        """
        获取所有进程的线程数统计（按线程数降序）
        :param top_n: 返回前N个进程
        :return: 进程线程数统计列表
        """
        return get_all_process_thread_count(self._tp, top_n)

    def monitor_key_processes_thread_count(self, process_names=None):
        """
        监控关键进程的线程数
        :param process_names: 进程名称列表，默认监控 system_server, systemui, launcher
        :return: 进程线程数统计字典
        """
        if process_names is None:
            # 默认监控的关键进程
            process_names = [
                'system_server',
                'com.android.systemui',
                'com.android.launcher3',
                '/system/bin/surfaceflinger'
            ]
        
        return get_multiple_process_thread_count(self._tp, process_names)


if __name__ == '__main__':
    # tp = PerformanceTraceProcessor(r'D:\Logs\trace.perfetto-trace')
    tp = PerformanceTraceProcessor(r'D:\Logs\trace\连续启动示例Trace\精简动画\启动退出\x6725b_trace_0_002_000.perfetto-trace')
    # tp = PerformanceTraceProcessor(r'E:\yunqing.gui\Downloads\StartUp_com.lemon.lvoverseas_2025-08-11_20_48_40_630_snASALE3741B000022_9_1ms.trace')
    # tp = PerformanceTraceProcessor(r'E:\yunqing.gui\Downloads\trace解析时长\trace解析时长\Infinix-X6873_Transition_com.instagram.android_com.instagram.creation.activity.MediaCaptureActivity_2025-03-28_03_32_28_241.trace')
    # tp = PerformanceTraceProcessor(r"\\10.150.152.37\fans_log\performance_dfx\KM4\2025-04-09\aliyun\KM4-15.1.0.015SP01(OP001PL001AZ)FANS\145053752K000090\data\TNE\0x0050\0x00500004_2025_04_04_09_48_40_5\DFX.20250404094831.perfetto-trace")
    # tp.get_startup_info()
    # tp.get_translation_info()


