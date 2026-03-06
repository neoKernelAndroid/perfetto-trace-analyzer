# -*- coding: utf-8 -*-
# @Time     : 2025/2/11
# @Author   : AI Assistant
# @File     : SurfaceFlingerAnalysis.py
# @Description : SurfaceFlinger GPU wait time 和 layer count 分析模块

import re
from modules.common.Logger import TEST_LOGGER


class SurfaceFlingerAnalysis:
    """SurfaceFlinger 分析类，用于统计 GPU wait time 和 layer count"""
    
    def __init__(self, html_file_path, start_time, end_time):
        self.html_file_path = html_file_path
        self.start_time = start_time
        self.end_time = end_time
        
        # SurfaceFlinger GPU wait time 统计
        self.sf_gpu_frame_count = 0
        self.sf_gpu_total_wait_time = 0.0
        self.sf_gpu_avg_wait_time_per_frame = 0.0
        self.sf_gpu_wait_intervals = []  # [(start, end, duration, frame_id), ...]
        
        # SurfaceFlinger layer count 统计
        self.frame_layer_info = []  # [{'frame_id': int, 'timestamp': float, 'layer_count': int, 'hwc_layers': [], 'gles_layers': []}, ...]
        
    def analyze(self):
        """执行 SurfaceFlinger 分析"""
        TEST_LOGGER.info("=" * 80)
        TEST_LOGGER.info("开始 SurfaceFlinger 分析")
        TEST_LOGGER.info(f"分析时间区间: [{self.start_time}, {self.end_time}]")
        TEST_LOGGER.info("=" * 80)
        
        # 分析 GPU wait time
        self._analyze_gpu_wait_time()
        
        # 分析 layer count
        self._analyze_layer_count()
        
        # 输出统计结果
        self._print_summary()
        
        return {
            'gpu_frame_count': self.sf_gpu_frame_count,
            'gpu_total_wait_time': self.sf_gpu_total_wait_time,
            'gpu_avg_wait_time_per_frame': self.sf_gpu_avg_wait_time_per_frame,
            'gpu_wait_intervals': self.sf_gpu_wait_intervals,
            'frame_layer_info': self.frame_layer_info
        }
    
    def _analyze_gpu_wait_time(self):
        """分析 SurfaceFlinger 的 GPU wait time
        
        策略：
        1. 帧数统计：使用 present for MTKDEV 事件（这才是真正的帧数）
        2. GPU 耗时统计：使用 RE Completion 线程的 waiting for RE Completion 事件
        3. 如果没有 waiting for RE Completion 事件，GPU 耗时统计为 0，但帧数仍然正常统计
        """
        TEST_LOGGER.info("开始分析 SurfaceFlinger GPU wait time...")
        
        with open(self.html_file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            
            # 1. 先统计帧数：使用 present for MTKDEV 事件
            pattern_present = r"(\d+\.\d+):\s+tracing_mark_write:.*?B\|.*?\|present for MTKDEV \((\d+)\) vsyncIn"
            present_matches = re.findall(pattern_present, content, re.MULTILINE)
            
            # 过滤出在时间区间内的 present 事件
            present_events = []
            for match in present_matches:
                timestamp = float(match[0])
                vsync_id = match[1]
                if self.start_time <= timestamp <= self.end_time:
                    present_events.append((timestamp, vsync_id))
            
            present_events.sort(key=lambda x: x[0])
            
            # 帧数 = present 事件数量
            self.sf_gpu_frame_count = len(present_events)
            TEST_LOGGER.info(f"找到 {self.sf_gpu_frame_count} 个 present for MTKDEV 事件（帧数）")
            
            # 2. 再统计 GPU 耗时：使用 RE Completion 线程的 waiting for RE Completion 事件
            pattern_re_wait_b = r"RE Completion.*?\(\s*\d+\).*?(\d+\.\d+):\s+tracing_mark_write:.*?B\|\d+\|waiting for RE Completion"
            pattern_re_wait_e = r"RE Completion.*?\(\s*\d+\).*?(\d+\.\d+):\s+tracing_mark_write:.*?E(?:\||$)"
            
            b_matches = re.findall(pattern_re_wait_b, content, re.MULTILINE)
            e_matches = re.findall(pattern_re_wait_e, content, re.MULTILINE)
            
            TEST_LOGGER.info(f"找到 {len(b_matches)} 个 RE Completion waiting B 事件，{len(e_matches)} 个 E 事件")
            
            if len(b_matches) > 0:
                # 将 B 事件转换为 [(timestamp), ...]
                b_events = []
                for match in b_matches:
                    timestamp = float(match)
                    if self.start_time <= timestamp <= self.end_time:
                        b_events.append(timestamp)
                
                e_events = []
                for match in e_matches:
                    timestamp = float(match)
                    if self.start_time <= timestamp <= self.end_time:
                        e_events.append(timestamp)
                
                b_events.sort()
                e_events.sort()
                
                TEST_LOGGER.info(f"在时间区间内找到 {len(b_events)} 个 B 事件，{len(e_events)} 个 E 事件")
                
                # 匹配 B 和 E 事件，计算 GPU waiting 时间
                e_index = 0
                gpu_wait_count = 0
                
                for b_time in b_events:
                    while e_index < len(e_events) and e_events[e_index] <= b_time:
                        e_index += 1
                    
                    if e_index < len(e_events):
                        e_time = e_events[e_index]
                        duration = e_time - b_time
                        
                        gpu_wait_count += 1
                        self.sf_gpu_wait_intervals.append((b_time, e_time, duration, gpu_wait_count))
                        self.sf_gpu_total_wait_time += duration
                        
                        TEST_LOGGER.info(f"SurfaceFlinger GPU等待 #{gpu_wait_count}: B时间={b_time:.6f}s, E时间={e_time:.6f}s, duration={duration:.6f}s ({duration*1000:.3f}ms)")
                        
                        e_index += 1
                    else:
                        TEST_LOGGER.warn(f"未找到 B 事件的对应 E 事件 (B时间={b_time:.6f}s)")
                
                # 计算平均每帧耗时（基于实际的帧数，而不是 GPU waiting 事件数）
                if self.sf_gpu_frame_count > 0:
                    self.sf_gpu_avg_wait_time_per_frame = self.sf_gpu_total_wait_time / self.sf_gpu_frame_count
                    TEST_LOGGER.info(f"GPU 等待事件数: {gpu_wait_count}, 总帧数: {self.sf_gpu_frame_count}")
            else:
                TEST_LOGGER.warn("未找到 RE Completion waiting 事件，GPU 耗时统计为 0")
                # GPU 耗时为 0，但帧数已经正确统计
                self.sf_gpu_total_wait_time = 0.0
                self.sf_gpu_avg_wait_time_per_frame = 0.0
    
    def _analyze_layer_count(self):
        """分析每一帧的 layer count - 使用 present 事件来确定帧边界"""
        TEST_LOGGER.info("开始分析 SurfaceFlinger layer count...")
        
        # 策略：使用 present for MTKDEV 事件来确定帧的边界
        # 每个 present 下面的 hwc 和 gles 事件总和就是该帧的 layer count
        # 格式: present for MTKDEV (<vsync_id>) vsyncIn <timestamp>
        
        # 1. 匹配 present for MTKDEV 事件（帧边界）
        pattern_present = r"(\d+\.\d+):\s+tracing_mark_write:.*?B\|.*?\|present for MTKDEV \((\d+)\) vsyncIn"
        
        # 2. 匹配 HWC 和 GLES 的 layer 信息（B 事件开始）
        pattern_hwc_layer = r"(\d+\.\d+):\s+tracing_mark_write:.*?B\|.*?\|hwc\s+\(([^)]+)\)"
        pattern_gles_layer = r"(\d+\.\d+):\s+tracing_mark_write:.*?B\|.*?\|gles\s+\(([^)]+)\)"
        
        with open(self.html_file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            
            # 查找所有 present for MTKDEV 事件
            present_matches = re.findall(pattern_present, content, re.MULTILINE)
            
            # 过滤出在时间区间内的 present 事件
            present_events = []
            for match in present_matches:
                timestamp = float(match[0])
                vsync_id = match[1]
                if self.start_time <= timestamp <= self.end_time:
                    present_events.append((timestamp, vsync_id))
            
            present_events.sort(key=lambda x: x[0])
            
            TEST_LOGGER.info(f"找到 {len(present_events)} 个 present for MTKDEV 事件（帧边界）")
            
            if not present_events:
                TEST_LOGGER.warn("未找到 present for MTKDEV 事件，无法确定帧边界")
                return
            
            # 查找所有 HWC 和 GLES layer 信息
            hwc_layer_matches = re.findall(pattern_hwc_layer, content, re.MULTILINE)
            gles_layer_matches = re.findall(pattern_gles_layer, content, re.MULTILINE)
            
            TEST_LOGGER.info(f"找到 {len(hwc_layer_matches)} 个 HWC layer 事件，{len(gles_layer_matches)} 个 GLES layer 事件")
            
            # 将 layer 信息按时间排序，并过滤出在时间区间内的
            hwc_layers = []
            for match in hwc_layer_matches:
                timestamp = float(match[0])
                layer_name = match[1]
                if self.start_time <= timestamp <= self.end_time:
                    hwc_layers.append((timestamp, layer_name))
            
            gles_layers = []
            for match in gles_layer_matches:
                timestamp = float(match[0])
                layer_name = match[1]
                if self.start_time <= timestamp <= self.end_time:
                    gles_layers.append((timestamp, layer_name))
            
            hwc_layers.sort(key=lambda x: x[0])
            gles_layers.sort(key=lambda x: x[0])
            
            TEST_LOGGER.info(f"在时间区间内找到 {len(hwc_layers)} 个 HWC layer，{len(gles_layers)} 个 GLES layer")
            
            # 根据 present 事件将 layers 分组到每一帧
            # 策略：每个 present 之后、下一个 present 之前的 hwc/gles 事件属于该帧
            # 时间窗口：present 时间往后推，直到下一个 present 或者最多 20ms
            frame_window = 0.020  # 20ms
            
            for frame_index in range(len(present_events)):
                present_time, vsync_id = present_events[frame_index]
                
                # 确定该帧的时间窗口
                if frame_index < len(present_events) - 1:
                    # 不是最后一帧，窗口到下一个 present
                    next_present_time = present_events[frame_index + 1][0]
                    frame_end_time = next_present_time
                else:
                    # 最后一帧，窗口为 present 后 20ms
                    frame_end_time = present_time + frame_window
                
                # 查找该帧的 layers（在 present 之后、frame_end_time 之前的 layers）
                # 使用字典记录每个 layer 的合成方式和时间，用于去重
                layer_dict = {}  # {layer_name: (type, time)}
                
                for layer_time, layer_name in hwc_layers:
                    if present_time < layer_time < frame_end_time:
                        # 如果 layer 已存在，保留时间更晚的（更接近实际合成的）
                        if layer_name not in layer_dict or layer_time > layer_dict[layer_name][1]:
                            layer_dict[layer_name] = ('hwc', layer_time)
                
                for layer_time, layer_name in gles_layers:
                    if present_time < layer_time < frame_end_time:
                        # 如果 layer 已存在，保留时间更晚的（更接近实际合成的）
                        if layer_name not in layer_dict or layer_time > layer_dict[layer_name][1]:
                            layer_dict[layer_name] = ('gles', layer_time)
                
                # 根据去重后的结果，分别统计 HWC 和 GLES layers
                frame_hwc_layers = []
                frame_gles_layers = []
                
                for layer_name, (layer_type, _) in layer_dict.items():
                    if layer_type == 'hwc':
                        frame_hwc_layers.append(layer_name)
                    else:
                        frame_gles_layers.append(layer_name)
                
                # 保存帧信息
                frame_info = {
                    'frame_id': f"frame_{frame_index + 1}",
                    'frame_type': 'composite',
                    'timestamp': present_time,
                    'vsync_id': vsync_id,
                    'layer_count': len(frame_hwc_layers) + len(frame_gles_layers),
                    'hwc_layer_count': len(frame_hwc_layers),
                    'gles_layer_count': len(frame_gles_layers),
                    'hwc_layers': frame_hwc_layers,
                    'gles_layers': frame_gles_layers
                }
                self.frame_layer_info.append(frame_info)
                
                TEST_LOGGER.info(f"帧 #{frame_index + 1} (vsync_id={vsync_id}, time={present_time:.6f}s): "
                               f"总layer={frame_info['layer_count']} (HWC={frame_info['hwc_layer_count']}, GLES={frame_info['gles_layer_count']})")
            
            TEST_LOGGER.info(f"总共分析了 {len(self.frame_layer_info)} 帧")
    
    def _print_summary(self):
        """输出统计结果摘要"""
        TEST_LOGGER.info("=" * 80)
        TEST_LOGGER.info("SurfaceFlinger 分析结果摘要")
        TEST_LOGGER.info("=" * 80)
        
        # GPU wait time 统计
        TEST_LOGGER.info("GPU Wait Time 统计:")
        TEST_LOGGER.info(f"  - 总帧数: {self.sf_gpu_frame_count} 帧")
        TEST_LOGGER.info(f"  - GPU总等待时间: {self.sf_gpu_total_wait_time:.6f} 秒 ({self.sf_gpu_total_wait_time*1000:.3f} ms)")
        TEST_LOGGER.info(f"  - GPU平均每帧等待时间: {self.sf_gpu_avg_wait_time_per_frame:.6f} 秒 ({self.sf_gpu_avg_wait_time_per_frame*1000:.3f} ms)")
        TEST_LOGGER.info(f"  - GPU waiting 区间数量: {len(self.sf_gpu_wait_intervals)}")
        
        # 说明
        TEST_LOGGER.info("")
        TEST_LOGGER.info("说明:")
        TEST_LOGGER.info("  - 帧数统计：基于 'present for MTKDEV' 事件（真实的合成帧数）")
        TEST_LOGGER.info("  - GPU 耗时统计：基于 'waiting for RE Completion' 事件")
        TEST_LOGGER.info("  - 如果 GPU 耗时为 0，说明没有 GPU 等待事件（GPU 处理非常快或使用 HWC 合成）")
        
        # Layer count 统计
        TEST_LOGGER.info("")
        TEST_LOGGER.info("Layer Count 统计:")
        TEST_LOGGER.info(f"  - 分析的帧数: {len(self.frame_layer_info)} 帧")
        
        if self.frame_layer_info:
            total_layers = sum(frame['layer_count'] for frame in self.frame_layer_info)
            avg_layers = total_layers / len(self.frame_layer_info)
            max_layers = max(frame['layer_count'] for frame in self.frame_layer_info)
            min_layers = min(frame['layer_count'] for frame in self.frame_layer_info)
            
            total_hwc_layers = sum(frame['hwc_layer_count'] for frame in self.frame_layer_info)
            avg_hwc_layers = total_hwc_layers / len(self.frame_layer_info)
            
            total_gles_layers = sum(frame['gles_layer_count'] for frame in self.frame_layer_info)
            avg_gles_layers = total_gles_layers / len(self.frame_layer_info)
            
            TEST_LOGGER.info(f"  - 平均每帧 layer 数量: {avg_layers:.2f}")
            TEST_LOGGER.info(f"  - 最大 layer 数量: {max_layers}")
            TEST_LOGGER.info(f"  - 最小 layer 数量: {min_layers}")
            TEST_LOGGER.info(f"  - 平均 HWC layer 数量: {avg_hwc_layers:.2f}")
            TEST_LOGGER.info(f"  - 平均 GLES layer 数量: {avg_gles_layers:.2f}")
            
            # 显示前5帧的详细信息
            TEST_LOGGER.info("")
            TEST_LOGGER.info("前5帧的详细 layer 信息:")
            for i, frame in enumerate(self.frame_layer_info[:5]):
                TEST_LOGGER.info(f"  帧 #{i+1} (frame_id={frame['frame_id']}):")
                TEST_LOGGER.info(f"    - 总 layer: {frame['layer_count']} (HWC: {frame['hwc_layer_count']}, GLES: {frame['gles_layer_count']})")
                if frame['hwc_layers']:
                    TEST_LOGGER.info(f"    - HWC layers: {', '.join(frame['hwc_layers'][:3])}{'...' if len(frame['hwc_layers']) > 3 else ''}")
                if frame['gles_layers']:
                    TEST_LOGGER.info(f"    - GLES layers: {', '.join(frame['gles_layers'][:3])}{'...' if len(frame['gles_layers']) > 3 else ''}")
        
        TEST_LOGGER.info("=" * 80)

