# -*- coding: utf-8 -*-
# @Time     : 2025/8/19 19:26
# @Author   : yunqing.gui
# @Email    : yunqing.gui@transsion.com
# @File     : Excel.py
import xlwt

from modules.common.Logger import TEST_LOGGER


class McpsExcel(object):
    def __init__(self, excel_path):
        self.excel_path = excel_path

    def insert_mcps_data(self,
                         mcps_by_group_dict,
                         task_slice_dict,
                         animation_thread_name,
                         len_doframe,
                         per_frame_load_dict=None,
                         total_wall_duration=0.0,
                         animation_time_range=0.0,
                         cpu_usage_percent=0.0,
                         top_20_processes=None,
                         gpu_frame_count=0,
                         gpu_total_time=0.0,
                         gpu_avg_time_per_frame=0.0,
                         gpu_frequency_intervals=None,
                         gpu_load=0.0,
                         sf_gpu_frame_count=0,
                         sf_gpu_total_time=0.0,
                         sf_gpu_avg_time_per_frame=0.0,
                         sf_frame_layer_info=None,
                         key_process_name=None):
        style0 = xlwt.easyxf('font: height 200  ,name Times New Roman, color-index blue, bold on')
        style1 = xlwt.easyxf('font: name calibri')

        wb = xlwt.Workbook(encoding='utf-8')

        # 第一页，直接显示和
        work_sheet_result = wb.add_sheet(u'MCPS Result', cell_overwrite_ok=True)
        work_sheet_result.write(0, 0, "TaskName", style0)
        work_sheet_result.write(0, 1, "PGID", style0)
        work_sheet_result.write(0, 2, "TaskPid", style0)
        work_sheet_result.write(0, 3, "线性归一时间(MCPS)", style0)
        work_sheet_result.write(0, 4, "线性归一时间(频点)", style0)
        work_sheet_result.write(0, 5, "相似归一时间(MCPS)", style0)
        work_sheet_result.write(0, 6, "相似归一时间(频点)", style0)
        work_sheet_result.write(0, 7, "帧数统计线程", style0)
        work_sheet_result.write(0, 8, "帧数", style0)
        work_sheet_result.write(0, 9, "每帧线性负载(MCPS)", style0)
        work_sheet_result.write(0, 10, "每帧线性负载(频点)", style0)
        work_sheet_result.write(0, 11, "每帧相似负载(MCPS)", style0)
        work_sheet_result.write(0, 12, "每帧相似负载(频点)", style0)
        work_sheet_result.write(0, 13, "总Wall Duration(s)", style0)
        work_sheet_result.write(0, 14, "动效区间长度(s)", style0)
        work_sheet_result.write(0, 15, "CPU Usage(%)", style0)

        work_sheet_result.col(0).width = 70 * 100
        work_sheet_result.col(1).width = 30 * 100
        work_sheet_result.col(2).width = 30 * 100
        work_sheet_result.col(3).width = 50 * 100
        work_sheet_result.col(4).width = 50 * 100
        work_sheet_result.col(5).width = 50 * 100
        work_sheet_result.col(6).width = 50 * 100
        work_sheet_result.col(7).width = 50 * 100
        work_sheet_result.col(8).width = 50 * 100
        work_sheet_result.col(9).width = 50 * 100
        work_sheet_result.col(10).width = 50 * 100
        work_sheet_result.col(11).width = 50 * 100
        work_sheet_result.col(12).width = 50 * 100
        work_sheet_result.col(13).width = 50 * 100
        work_sheet_result.col(14).width = 50 * 100
        work_sheet_result.col(15).width = 50 * 100
        work_sheet_result.col(16).width = 50 * 100
        work_sheet_result.col(17).width = 50 * 100
        work_sheet_result.col(18).width = 50 * 100

        work_sheet = wb.add_sheet(u'MCPS Brief', cell_overwrite_ok=True)
        work_sheet.write(0, 0, "TaskName", style0)
        work_sheet.write(0, 1, "PGID", style0)
        work_sheet.write(0, 2, "TaskPid", style0)
        work_sheet.write(0, 3, "CpuGroup", style0)
        work_sheet.write(0, 4, "TotalMcps", style0)
        work_sheet.write(0, 5, "TotalDuration", style0)
        work_sheet.write(0, 6, "McpsResult", style0)
        work_sheet.write(0, 7, "线性归一算力(MCPS)", style0)
        work_sheet.write(0, 8, "线性归一时间(MCPS)", style0)
        work_sheet.write(0, 9, "线性归一时间(频点)", style0)
        work_sheet.write(0, 10, "相似归一算力(MCPS)", style0)
        work_sheet.write(0, 11, "相似归一时间(MCPS)", style0)
        work_sheet.write(0, 12, "相似归一时间(频点)", style0)

        work_sheet.col(0).width = 70 * 100
        work_sheet.col(1).width = 30 * 100
        work_sheet.col(2).width = 30 * 100
        work_sheet.col(3).width = 30 * 100
        work_sheet.col(4).width = 30 * 100
        work_sheet.col(5).width = 40 * 100
        work_sheet.col(6).width = 30 * 100
        work_sheet.col(7).width = 50 * 100
        work_sheet.col(8).width = 50 * 100
        work_sheet.col(9).width = 50 * 100
        work_sheet.col(10).width = 50 * 100
        work_sheet.col(11).width = 50 * 100
        work_sheet.col(12).width = 50 * 100

        result_dict = {}
        row_index = 1
        for task_name, mcps_result_dict in mcps_by_group_dict.items():

            for cpu_group, [pid, total_group_mcps, total_duration, task_mcps_result, linear_normalization_c, linear_t, approximate_normalization_c, approximate_t, task_linear_t_result, task_approximate_t_result] in mcps_result_dict.items():
                if "-" in task_name:
                    pgid = task_name.split("-")[1]
                else:
                    pgid = "NA"

                work_sheet.write(row_index, 0, task_name, style1)
                work_sheet.write(row_index, 1, pgid, style1)
                work_sheet.write(row_index, 2, pid, style1)
                work_sheet.write(row_index, 3, cpu_group, style1)
                work_sheet.write(row_index, 4, total_group_mcps, style1)
                work_sheet.write(row_index, 5, total_duration, style1)
                work_sheet.write(row_index, 6, task_mcps_result, style1)
                work_sheet.write(row_index, 7, linear_normalization_c, style1)
                work_sheet.write(row_index, 8, linear_t, style1)
                work_sheet.write(row_index, 9, task_linear_t_result, style1)
                work_sheet.write(row_index, 10, approximate_normalization_c, style1)
                work_sheet.write(row_index, 11, approximate_t, style1)
                work_sheet.write(row_index, 12, task_approximate_t_result, style1)
                row_index += 1

                temp_list = result_dict.setdefault(task_name, [pgid, pid, 0, 0, 0, 0])
                total_linear_t = temp_list[2] + linear_t
                total_task_linear_t_result = temp_list[3] + task_linear_t_result
                total_approximate_t = temp_list[4] + approximate_t
                total_task_approximate_t_result = temp_list[5] + task_approximate_t_result
                result_dict[task_name] = [pgid, pid, total_linear_t, total_task_linear_t_result, total_approximate_t, total_task_approximate_t_result]

        row_index = 1
        for task_name, [pgid, pid, total_linear_t, total_task_linear_t_result, total_approximate_t, total_task_approximate_t_result] in result_dict.items():
            work_sheet_result.write(row_index, 0, task_name, style1)
            work_sheet_result.write(row_index, 1, pgid, style1)
            work_sheet_result.write(row_index, 2, pid, style1)
            work_sheet_result.write(row_index, 3, total_linear_t, style1)
            work_sheet_result.write(row_index, 4, total_task_linear_t_result, style1)
            work_sheet_result.write(row_index, 5, total_approximate_t, style1)
            work_sheet_result.write(row_index, 6, total_task_approximate_t_result, style1)
            
            # 获取该任务自己的帧数和帧数统计线程
            if per_frame_load_dict and task_name in per_frame_load_dict:
                task_frame_count = per_frame_load_dict[task_name].get('frame_count', len_doframe)
                task_frame_thread_name = per_frame_load_dict[task_name].get('frame_thread_name', animation_thread_name)
                per_frame_linear_mcps = per_frame_load_dict[task_name].get('linear_mcps', 0)
                per_frame_linear_freq = per_frame_load_dict[task_name].get('linear_freq', 0)
                per_frame_approximate_mcps = per_frame_load_dict[task_name].get('approximate_mcps', 0)
                per_frame_approximate_freq = per_frame_load_dict[task_name].get('approximate_freq', 0)
            else:
                # 兼容性：如果没有找到，使用默认值
                task_frame_count = len_doframe
                task_frame_thread_name = animation_thread_name or "unknown"
                per_frame_linear_mcps = total_linear_t / len_doframe if len_doframe > 0 else 0
                per_frame_linear_freq = total_task_linear_t_result / len_doframe if len_doframe > 0 else 0
                per_frame_approximate_mcps = total_approximate_t / len_doframe if len_doframe > 0 else 0
                per_frame_approximate_freq = total_task_approximate_t_result / len_doframe if len_doframe > 0 else 0
            
            work_sheet_result.write(row_index, 7, task_frame_thread_name, style1)
            work_sheet_result.write(row_index, 8, task_frame_count, style1)
            work_sheet_result.write(row_index, 9, per_frame_linear_mcps, style1)
            work_sheet_result.write(row_index, 10, per_frame_linear_freq, style1)
            work_sheet_result.write(row_index, 11, per_frame_approximate_mcps, style1)
            work_sheet_result.write(row_index, 12, per_frame_approximate_freq, style1)
            # CPU usage 是全局指标，所有行都写入相同的值
            work_sheet_result.write(row_index, 13, total_wall_duration, style1)
            work_sheet_result.write(row_index, 14, animation_time_range, style1)
            work_sheet_result.write(row_index, 15, cpu_usage_percent, style1)
            row_index += 1
        
        # 在所有任务数据之后，添加GPU统计信息（单独一行）
        # GPU统计说明：
        # - GPU帧数：统计动效区间内 "waiting for GPU completion" 事件的帧数（根据vsync_id去重）
        # - GPU总时间：所有 "waiting for GPU completion" 事件的总耗时
        # - GPU平均每帧耗时：GPU总时间 / GPU帧数
        # - GPU负载：GPU总时间 × GPU频率 (MCPS)
        # - GPU频率区间：统计动效时间范围内 GPU 频率的最小 / 最大值，便于快速判断频率是否打满
        # 注意：GPU帧数可能与RenderThread/MainThread的帧数不同，原因：
        #   1. GPU统计的是GPU等待完成的帧，RenderThread统计的是DrawFrames事件
        #   2. 某些帧可能没有GPU等待（纯CPU渲染），或GPU等待时间极短未被捕获
        #   3. 时间区间边界处理不同：GPU使用交集判断，RenderThread使用严格区间判断
        if gpu_frame_count > 0:
            work_sheet_result.write(row_index, 0, "GPU统计", style0)
            work_sheet_result.write(row_index, 1, "帧数", style0)
            work_sheet_result.write(row_index, 2, gpu_frame_count, style1)
            work_sheet_result.write(row_index, 3, "总时间(s)", style0)
            work_sheet_result.write(row_index, 4, gpu_total_time, style1)
            work_sheet_result.write(row_index, 5, "平均每帧耗时(s)", style0)
            work_sheet_result.write(row_index, 6, gpu_avg_time_per_frame, style1)
            work_sheet_result.write(row_index, 7, "GPU负载(MCPS)", style0)
            work_sheet_result.write(row_index, 8, gpu_load, style1)
            
            # 计算GPU平均频率
            col_index = 9
            if gpu_total_time > 0:
                gpu_avg_freq = gpu_load / gpu_total_time
                work_sheet_result.write(row_index, col_index, "GPU平均频率(MHz)", style0)
                work_sheet_result.write(row_index, col_index + 1, gpu_avg_freq, style1)
                col_index += 2

            # 统计GPU频率区间（最小 / 最大频率），仅统计动效区间内实际使用过的频率
            if gpu_frequency_intervals and len(gpu_frequency_intervals) > 0:
                try:
                    freqs = [float(freq) for freq, _, _, _ in gpu_frequency_intervals]
                    min_freq = min(freqs)
                    max_freq = max(freqs)
                    work_sheet_result.write(row_index, col_index, "GPU最小频率(MHz)", style0)
                    work_sheet_result.write(row_index, col_index + 1, min_freq, style1)
                    work_sheet_result.write(row_index, col_index + 2, "GPU最大频率(MHz)", style0)
                    work_sheet_result.write(row_index, col_index + 3, max_freq, style1)
                except Exception as e:
                    TEST_LOGGER.warn(f"计算GPU频率区间失败: {e}")
            
            row_index += 1
        
        # 添加 SurfaceFlinger GPU completion 统计信息
        if sf_gpu_frame_count > 0:
            work_sheet_result.write(row_index, 0, "SurfaceFlinger GPU统计", style0)
            work_sheet_result.write(row_index, 1, "帧数", style0)
            work_sheet_result.write(row_index, 2, sf_gpu_frame_count, style1)
            work_sheet_result.write(row_index, 3, "总等待时间(s)", style0)
            work_sheet_result.write(row_index, 4, sf_gpu_total_time, style1)
            work_sheet_result.write(row_index, 5, "平均每帧等待时间(s)", style0)
            work_sheet_result.write(row_index, 6, sf_gpu_avg_time_per_frame, style1)
            work_sheet_result.write(row_index, 7, "平均每帧等待时间(ms)", style0)
            work_sheet_result.write(row_index, 8, sf_gpu_avg_time_per_frame * 1000, style1)
            row_index += 1
        
        # 添加 SurfaceFlinger Layer Count 统计信息
        if sf_frame_layer_info and len(sf_frame_layer_info) > 0:
            # 计算平均值
            total_layers = sum(frame['layer_count'] for frame in sf_frame_layer_info)
            avg_layers = total_layers / len(sf_frame_layer_info)
            max_layers = max(frame['layer_count'] for frame in sf_frame_layer_info)
            min_layers = min(frame['layer_count'] for frame in sf_frame_layer_info)
            
            total_hwc_layers = sum(frame['hwc_layer_count'] for frame in sf_frame_layer_info)
            avg_hwc_layers = total_hwc_layers / len(sf_frame_layer_info)
            
            total_gles_layers = sum(frame['gles_layer_count'] for frame in sf_frame_layer_info)
            avg_gles_layers = total_gles_layers / len(sf_frame_layer_info)
            
            work_sheet_result.write(row_index, 0, "SurfaceFlinger Layer统计", style0)
            work_sheet_result.write(row_index, 1, "分析帧数", style0)
            work_sheet_result.write(row_index, 2, len(sf_frame_layer_info), style1)
            work_sheet_result.write(row_index, 3, "平均Layer数", style0)
            work_sheet_result.write(row_index, 4, avg_layers, style1)
            work_sheet_result.write(row_index, 5, "最大Layer数", style0)
            work_sheet_result.write(row_index, 6, max_layers, style1)
            work_sheet_result.write(row_index, 7, "最小Layer数", style0)
            work_sheet_result.write(row_index, 8, min_layers, style1)
            work_sheet_result.write(row_index, 9, "平均HWC Layer", style0)
            work_sheet_result.write(row_index, 10, avg_hwc_layers, style1)
            work_sheet_result.write(row_index, 11, "平均GLES Layer", style0)
            work_sheet_result.write(row_index, 12, avg_gles_layers, style1)
            row_index += 1
        
        # 添加GPU频率区间详细信息（如果有）
        if gpu_frequency_intervals and len(gpu_frequency_intervals) > 0:
            gpu_freq_sheet = wb.add_sheet(u'GPU Frequency Intervals', cell_overwrite_ok=True)
            gpu_freq_sheet.write(0, 0, "GPU频率(MHz)", style0)
            gpu_freq_sheet.write(0, 1, "开始时间(s)", style0)
            gpu_freq_sheet.write(0, 2, "结束时间(s)", style0)
            gpu_freq_sheet.write(0, 3, "持续时间(s)", style0)
            gpu_freq_sheet.write(0, 4, "负载(MCPS)", style0)
            
            gpu_freq_sheet.col(0).width = 30 * 100
            gpu_freq_sheet.col(1).width = 40 * 100
            gpu_freq_sheet.col(2).width = 40 * 100
            gpu_freq_sheet.col(3).width = 40 * 100
            gpu_freq_sheet.col(4).width = 40 * 100
            
            row_index_gpu = 1
            for freq, start, end, duration in gpu_frequency_intervals:
                load = duration * freq
                # 转换numpy类型为Python原生类型，避免xlwt报错
                gpu_freq_sheet.write(row_index_gpu, 0, int(freq), style1)
                gpu_freq_sheet.write(row_index_gpu, 1, float(start), style1)
                gpu_freq_sheet.write(row_index_gpu, 2, float(end), style1)
                gpu_freq_sheet.write(row_index_gpu, 3, float(duration), style1)
                gpu_freq_sheet.write(row_index_gpu, 4, float(load), style1)
                row_index_gpu += 1

        # ------------------------------------------------------------------------------
        # MCPS Result sheet summary block
        # ------------------------------------------------------------------------------
        summary_start_row = row_index + 2
        cur_row = summary_start_row

        # 1) 每帧线性负载汇总（Per-frame linear MCPS by task）
        if per_frame_load_dict:
            work_sheet_result.write(cur_row, 0, "Per-frame linear load (MCPS)", style0)
            cur_row += 1

            for task_name, load_info in per_frame_load_dict.items():
                per_frame_linear_mcps = load_info.get('linear_mcps', 0.0)
                work_sheet_result.write(cur_row, 0, task_name, style1)
                work_sheet_result.write(cur_row, 1, "每帧线性负载(MCPS)", style1)
                work_sheet_result.write(cur_row, 3, per_frame_linear_mcps, style1)
                cur_row += 1

        # 2) CPU usage summary：整体 + 关键进程 + GPU/Layer quick view
        if cpu_usage_percent is not None:
            cur_row += 1
            work_sheet_result.write(cur_row, 0, "CPU usage summary", style0)
            cur_row += 1

            # overall
            work_sheet_result.write(cur_row, 0, "Overall CPU usage", style1)
            work_sheet_result.write(cur_row, 3, cpu_usage_percent, style1)
            cur_row += 1

            def _find_process_cpu_usage(name_keyword: str):
                if not top_20_processes:
                    return None
                for proc in top_20_processes:
                    proc_name = proc.get('process_name', '')
                    if proc_name == name_keyword or name_keyword in proc_name:
                        return proc.get('cpu_usage_percent', None)
                return None

            # system_server
            system_server_usage = _find_process_cpu_usage("system_server")
            if system_server_usage is not None:
                work_sheet_result.write(cur_row, 0, "system_server", style1)
                work_sheet_result.write(cur_row, 3, system_server_usage, style1)
                cur_row += 1

            # SurfaceFlinger
            sf_usage = _find_process_cpu_usage("surfaceflinger")
            if sf_usage is not None:
                work_sheet_result.write(cur_row, 0, "surfaceflinger", style1)
                work_sheet_result.write(cur_row, 3, sf_usage, style1)
                cur_row += 1

            # key monitored process (e.g. launcher / systemui)
            if key_process_name:
                key_usage = _find_process_cpu_usage(key_process_name)
                if key_usage is None:
                    # 有些进程名很长，只匹配关键子串（如 launcher3）
                    short_name = key_process_name.split(".")[-1]
                    key_usage = _find_process_cpu_usage(short_name)
                if key_usage is not None:
                    label = f"Key process ({key_process_name})"
                    work_sheet_result.write(cur_row, 0, label, style1)
                    work_sheet_result.write(cur_row, 3, key_usage, style1)
                    cur_row += 1

            # Separator / hint line (GPU metrics start from next row)
            work_sheet_result.write(cur_row, 0, "GPU related metrics below", style0)
            cur_row += 1

            # RenderThread GPU average time per frame
            if gpu_avg_time_per_frame > 0:
                work_sheet_result.write(cur_row, 0, "RenderThread GPU统计", style1)
                work_sheet_result.write(cur_row, 1, "平均每帧耗时(s)", style1)
                work_sheet_result.write(cur_row, 3, gpu_avg_time_per_frame, style1)
                cur_row += 1

            # SurfaceFlinger GPU average time per frame
            if sf_gpu_avg_time_per_frame > 0:
                work_sheet_result.write(cur_row, 0, "SurfaceFlinger GPU统计", style1)
                work_sheet_result.write(cur_row, 1, "平均每帧等待时间(s)", style1)
                work_sheet_result.write(cur_row, 3, sf_gpu_avg_time_per_frame, style1)
                cur_row += 1

            # SurfaceFlinger maximum layer count
            if sf_frame_layer_info and len(sf_frame_layer_info) > 0:
                try:
                    max_layers_summary = max(frame['layer_count'] for frame in sf_frame_layer_info)
                    work_sheet_result.write(cur_row, 0, "SurfaceFlinger Layer统计", style1)
                    work_sheet_result.write(cur_row, 1, "最大Layer数", style1)
                    work_sheet_result.write(cur_row, 3, max_layers_summary, style1)
                    cur_row += 1
                except Exception as e:
                    TEST_LOGGER.warn(f"计算SurfaceFlinger最大Layer数失败: {e}")
        
        # 添加 SurfaceFlinger 每帧 Layer 详细信息（如果有）
        if sf_frame_layer_info and len(sf_frame_layer_info) > 0:
            sf_layer_sheet = wb.add_sheet(u'SurfaceFlinger Layer Detail', cell_overwrite_ok=True)
            sf_layer_sheet.write(0, 0, "帧序号", style0)
            sf_layer_sheet.write(0, 1, "Frame ID", style0)
            sf_layer_sheet.write(0, 2, "Frame Type", style0)
            sf_layer_sheet.write(0, 3, "时间戳(s)", style0)
            sf_layer_sheet.write(0, 4, "总Layer数", style0)
            sf_layer_sheet.write(0, 5, "HWC Layer数", style0)
            sf_layer_sheet.write(0, 6, "GLES Layer数", style0)
            sf_layer_sheet.write(0, 7, "HWC Layers", style0)
            sf_layer_sheet.write(0, 8, "GLES Layers", style0)
            
            sf_layer_sheet.col(0).width = 20 * 100
            sf_layer_sheet.col(1).width = 30 * 100
            sf_layer_sheet.col(2).width = 30 * 100
            sf_layer_sheet.col(3).width = 40 * 100
            sf_layer_sheet.col(4).width = 30 * 100
            sf_layer_sheet.col(5).width = 30 * 100
            sf_layer_sheet.col(6).width = 30 * 100
            sf_layer_sheet.col(7).width = 100 * 100
            sf_layer_sheet.col(8).width = 100 * 100
            
            row_index_sf = 1
            for i, frame_info in enumerate(sf_frame_layer_info, 1):
                sf_layer_sheet.write(row_index_sf, 0, i, style1)
                sf_layer_sheet.write(row_index_sf, 1, str(frame_info.get('frame_id', 'unknown')), style1)
                sf_layer_sheet.write(row_index_sf, 2, str(frame_info.get('frame_type', 'unknown')), style1)
                sf_layer_sheet.write(row_index_sf, 3, float(frame_info.get('timestamp', 0.0)), style1)
                sf_layer_sheet.write(row_index_sf, 4, int(frame_info.get('layer_count', 0)), style1)
                sf_layer_sheet.write(row_index_sf, 5, int(frame_info.get('hwc_layer_count', 0)), style1)
                sf_layer_sheet.write(row_index_sf, 6, int(frame_info.get('gles_layer_count', 0)), style1)
                
                # HWC layers 列表
                hwc_layers = frame_info.get('hwc_layers', [])
                hwc_layers_str = ', '.join(hwc_layers) if hwc_layers else ''
                sf_layer_sheet.write(row_index_sf, 7, hwc_layers_str, style1)
                
                # GLES layers 列表
                gles_layers = frame_info.get('gles_layers', [])
                gles_layers_str = ', '.join(gles_layers) if gles_layers else ''
                sf_layer_sheet.write(row_index_sf, 8, gles_layers_str, style1)
                
                row_index_sf += 1

        detail_sheet = wb.add_sheet(u'Detail', cell_overwrite_ok=True)
        detail_sheet.write(0, 0, "TaskName", style0)
        detail_sheet.write(0, 1, "PGID", style0)
        detail_sheet.write(0, 2, "TaskPid", style0)
        detail_sheet.write(0, 3, "CpuGroup", style0)
        detail_sheet.write(0, 4, "CpuId", style0)
        detail_sheet.write(0, 5, "StartTime", style0)
        detail_sheet.write(0, 6, "EndTime", style0)
        detail_sheet.write(0, 7, "Duration", style0)
        detail_sheet.write(0, 8, "Mcps", style0)
        detail_sheet.write(0, 9, "isRenamed", style0)
        detail_sheet.write(0, 10, "inAnimationRange", style0)
        detail_sheet.write(0, 11, "OldTaskName", style0)
        detail_sheet.write(0, 12, "FrequencyIntervals", style0)

        detail_sheet.col(0).width = 70 * 100
        detail_sheet.col(1).width = 30 * 100
        detail_sheet.col(2).width = 30 * 100
        detail_sheet.col(3).width = 30 * 100
        detail_sheet.col(4).width = 30 * 100
        detail_sheet.col(5).width = 40 * 100
        detail_sheet.col(6).width = 40 * 100
        detail_sheet.col(7).width = 40 * 100
        detail_sheet.col(8).width = 40 * 100
        detail_sheet.col(9).width = 30 * 100
        detail_sheet.col(10).width = 70 * 100
        detail_sheet.col(11).width = 70 * 100
        detail_sheet.col(12).width = 100 * 100

        row_index = 1
        for task_name, task_slice_list in task_slice_dict.items():
            for task_slice in task_slice_list:
                task_name = task_slice.task_name
                pgid = task_slice.pgid
                pid = task_slice.pid
                cpu_group = task_slice.cpu_group
                cpu_id = task_slice.cpu_id
                start_time = task_slice.start_time
                end_time = task_slice.end_time
                duration = task_slice.duration
                mcps = task_slice.mcps
                is_renamed = task_slice.is_renamed
                in_animation_range = task_slice.in_animation_range
                old_task_name = task_slice.old_task_name
                frequency_intervals = task_slice.frequency_intervals

                detail_sheet.write(row_index, 0, task_name, style1)
                detail_sheet.write(row_index, 1, pgid, style1)
                detail_sheet.write(row_index, 2, pid, style1)
                detail_sheet.write(row_index, 3, cpu_group, style1)
                detail_sheet.write(row_index, 4, cpu_id, style1)
                detail_sheet.write(row_index, 5, start_time, style1)
                detail_sheet.write(row_index, 6, end_time, style1)
                detail_sheet.write(row_index, 7, duration, style1)
                detail_sheet.write(row_index, 8, mcps, style1)
                detail_sheet.write(row_index, 9, is_renamed, style1)
                detail_sheet.write(row_index, 10, in_animation_range, style1)
                detail_sheet.write(row_index, 11, old_task_name, style1)
                detail_sheet.write(row_index, 12, str(frequency_intervals), style1)
                row_index += 1

        # 添加 Top 20 进程 CPU Usage 统计表
        if top_20_processes:
            top_processes_sheet = wb.add_sheet(u'Top20 Process CPU Usage', cell_overwrite_ok=True)
            
            # 在第一行添加全局统计信息
            top_processes_sheet.write(0, 0, "总Wall Duration(s)", style0)
            top_processes_sheet.write(0, 1, total_wall_duration, style1)
            top_processes_sheet.write(0, 2, "动效区间长度(s)", style0)
            top_processes_sheet.write(0, 3, animation_time_range, style1)
            top_processes_sheet.write(0, 4, "CPU Usage(%)", style0)
            top_processes_sheet.write(0, 5, cpu_usage_percent, style1)
            
            # 空一行
            row_index = 2
            
            # Top 20 进程表头
            top_processes_sheet.write(row_index, 0, "Rank", style0)
            top_processes_sheet.write(row_index, 1, "Process Name", style0)
            top_processes_sheet.write(row_index, 2, "PGID", style0)
            top_processes_sheet.write(row_index, 3, "PID", style0)
            top_processes_sheet.write(row_index, 4, "Wall Duration(s)", style0)
            top_processes_sheet.write(row_index, 5, "CPU Usage(%)", style0)

            top_processes_sheet.col(0).width = 20 * 100
            top_processes_sheet.col(1).width = 70 * 100
            top_processes_sheet.col(2).width = 30 * 100
            top_processes_sheet.col(3).width = 30 * 100
            top_processes_sheet.col(4).width = 50 * 100
            top_processes_sheet.col(5).width = 50 * 100

            row_index += 1
            for i, proc in enumerate(top_20_processes, 1):
                top_processes_sheet.write(row_index, 0, i, style1)
                top_processes_sheet.write(row_index, 1, proc['process_name'], style1)
                top_processes_sheet.write(row_index, 2, proc['pgid'], style1)
                top_processes_sheet.write(row_index, 3, proc['pid'], style1)
                top_processes_sheet.write(row_index, 4, proc['wall_duration'], style1)
                top_processes_sheet.write(row_index, 5, proc['cpu_usage_percent'], style1)
                row_index += 1

        wb.save(self.excel_path)
        TEST_LOGGER.info("已生成文件：{}".format(self.excel_path))


class ThreadCountExcel(object):
    """线程数统计 Excel 导出类"""
    
    def __init__(self, excel_path):
        self.excel_path = excel_path
    
    def export_thread_count_data(self, top_processes=None, key_processes=None, process_details=None):
        """
        导出线程数统计数据到 Excel
        
        :param top_processes: Top N 进程列表 [{'process_name': '', 'pid': 0, 'thread_count': 0}, ...]
        :param key_processes: 关键进程字典 {'process_name': {'pid': 0, 'thread_count': 0}, ...}
        :param process_details: 进程详细信息字典 {'process_name': {'thread_count': 0, 'threads': [...]}, ...}
        """
        style0 = xlwt.easyxf('font: height 200, name Times New Roman, color-index blue, bold on')
        style1 = xlwt.easyxf('font: name calibri')
        
        wb = xlwt.Workbook(encoding='utf-8')
        
        # Sheet 1: Top 进程线程数统计
        if top_processes:
            top_sheet = wb.add_sheet(u'Top进程线程数', cell_overwrite_ok=True)
            top_sheet.write(0, 0, "排名", style0)
            top_sheet.write(0, 1, "进程名称", style0)
            top_sheet.write(0, 2, "PID", style0)
            top_sheet.write(0, 3, "线程数", style0)
            
            top_sheet.col(0).width = 20 * 100
            top_sheet.col(1).width = 70 * 100
            top_sheet.col(2).width = 30 * 100
            top_sheet.col(3).width = 30 * 100
            
            for i, process in enumerate(top_processes, 1):
                top_sheet.write(i, 0, i, style1)
                top_sheet.write(i, 1, process['process_name'], style1)
                top_sheet.write(i, 2, process['pid'], style1)
                top_sheet.write(i, 3, process['thread_count'], style1)
        
        # Sheet 2: 关键进程线程数统计
        if key_processes:
            key_sheet = wb.add_sheet(u'关键进程线程数', cell_overwrite_ok=True)
            key_sheet.write(0, 0, "进程名称", style0)
            key_sheet.write(0, 1, "PID", style0)
            key_sheet.write(0, 2, "线程数", style0)
            
            key_sheet.col(0).width = 70 * 100
            key_sheet.col(1).width = 30 * 100
            key_sheet.col(2).width = 30 * 100
            
            row_index = 1
            for process_name, info in key_processes.items():
                key_sheet.write(row_index, 0, process_name, style1)
                key_sheet.write(row_index, 1, info['pid'], style1)
                key_sheet.write(row_index, 2, info['thread_count'], style1)
                row_index += 1
        
        # Sheet 3: 进程详细线程信息
        if process_details:
            for process_name, details in process_details.items():
                # 为每个进程创建一个 sheet
                # 1. 替换非法字符（Excel sheet 名称不能包含: \ / ? * [ ] :）
                sheet_name = process_name.replace('/', '_').replace('\\', '_').replace('?', '_').replace('*', '_').replace('[', '_').replace(']', '_').replace(':', '_')
                # 2. 截断过长的名称（Excel sheet 名称最多 31 个字符）
                sheet_name = sheet_name[:31] if len(sheet_name) > 31 else sheet_name
                detail_sheet = wb.add_sheet(sheet_name, cell_overwrite_ok=True)
                
                # 写入进程信息
                detail_sheet.write(0, 0, "进程名称", style0)
                detail_sheet.write(0, 1, process_name, style1)
                detail_sheet.write(1, 0, "线程总数", style0)
                detail_sheet.write(1, 1, details['thread_count'], style1)
                
                # 空一行
                detail_sheet.write(3, 0, "序号", style0)
                detail_sheet.write(3, 1, "TID", style0)
                detail_sheet.write(3, 2, "线程名称", style0)
                
                detail_sheet.col(0).width = 20 * 100
                detail_sheet.col(1).width = 30 * 100
                detail_sheet.col(2).width = 70 * 100
                
                row_index = 4
                for i, thread in enumerate(details['threads'], 1):
                    thread_name = thread['thread_name'] if thread['thread_name'] else '<unnamed>'
                    detail_sheet.write(row_index, 0, i, style1)
                    detail_sheet.write(row_index, 1, thread['tid'], style1)
                    detail_sheet.write(row_index, 2, thread_name, style1)
                    row_index += 1
        
        wb.save(self.excel_path)
        TEST_LOGGER.info("已生成线程数统计文件：{}".format(self.excel_path))