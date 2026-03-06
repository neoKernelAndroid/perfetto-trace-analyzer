# -*- coding: utf-8 -*-
# @Time     : 2025/2/11
# @Author   : AI Assistant
# @File     : run_surfaceflinger_analysis.py
# @Description : SurfaceFlinger GPU wait time 和 layer count 独立分析脚本

import argparse
import os
import sys
import traceback
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.common.Logger import TEST_LOGGER
from modules.TraceHtml.SurfaceFlingerAnalysis import SurfaceFlingerAnalysis
import xlsxwriter


def export_to_excel(sf_result, output_path):
    """导出 SurfaceFlinger 分析结果到 Excel"""
    workbook = xlsxwriter.Workbook(output_path)
    
    # 定义格式
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 14,
        'bg_color': '#4472C4',
        'font_color': 'white',
        'align': 'center',
        'valign': 'vcenter'
    })
    
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#D9E1F2',
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    })
    
    data_format = workbook.add_format({
        'align': 'left',
        'valign': 'vcenter',
        'border': 1
    })
    
    number_format = workbook.add_format({
        'align': 'right',
        'valign': 'vcenter',
        'border': 1,
        'num_format': '0.000'
    })
    
    # 创建工作表
    summary_sheet = workbook.add_worksheet('SurfaceFlinger汇总')
    detail_sheet = workbook.add_worksheet('每帧详细数据')
    
    # ========== 汇总表 ==========
    row = 0
    summary_sheet.write(row, 0, 'SurfaceFlinger GPU Wait Time 和 Layer Count 分析', title_format)
    summary_sheet.merge_range(row, 0, row, 3, 'SurfaceFlinger GPU Wait Time 和 Layer Count 分析', title_format)
    row += 2
    
    # GPU Wait Time 统计
    summary_sheet.write(row, 0, 'GPU Wait Time 统计', header_format)
    summary_sheet.merge_range(row, 0, row, 1, 'GPU Wait Time 统计', header_format)
    row += 1
    
    summary_sheet.write(row, 0, '总帧数', header_format)
    summary_sheet.write(row, 1, sf_result['gpu_frame_count'], data_format)
    row += 1
    
    summary_sheet.write(row, 0, 'GPU总等待时间(秒)', header_format)
    summary_sheet.write(row, 1, sf_result['gpu_total_wait_time'], number_format)
    row += 1
    
    summary_sheet.write(row, 0, 'GPU总等待时间(毫秒)', header_format)
    summary_sheet.write(row, 1, sf_result['gpu_total_wait_time'] * 1000, number_format)
    row += 1
    
    summary_sheet.write(row, 0, 'GPU平均每帧等待时间(秒)', header_format)
    summary_sheet.write(row, 1, sf_result['gpu_avg_wait_time_per_frame'], number_format)
    row += 1
    
    summary_sheet.write(row, 0, 'GPU平均每帧等待时间(毫秒)', header_format)
    summary_sheet.write(row, 1, sf_result['gpu_avg_wait_time_per_frame'] * 1000, number_format)
    row += 2
    
    # Layer Count 统计
    summary_sheet.write(row, 0, 'Layer Count 统计', header_format)
    summary_sheet.merge_range(row, 0, row, 1, 'Layer Count 统计', header_format)
    row += 1
    
    frame_layer_info = sf_result['frame_layer_info']
    if frame_layer_info:
        total_layers = sum(frame['layer_count'] for frame in frame_layer_info)
        avg_layers = total_layers / len(frame_layer_info)
        max_layers = max(frame['layer_count'] for frame in frame_layer_info)
        min_layers = min(frame['layer_count'] for frame in frame_layer_info)
        
        total_hwc_layers = sum(frame['hwc_layer_count'] for frame in frame_layer_info)
        avg_hwc_layers = total_hwc_layers / len(frame_layer_info)
        
        total_gles_layers = sum(frame['gles_layer_count'] for frame in frame_layer_info)
        avg_gles_layers = total_gles_layers / len(frame_layer_info)
        
        summary_sheet.write(row, 0, '分析的帧数', header_format)
        summary_sheet.write(row, 1, len(frame_layer_info), data_format)
        row += 1
        
        summary_sheet.write(row, 0, '平均每帧 Layer 数量', header_format)
        summary_sheet.write(row, 1, avg_layers, number_format)
        row += 1
        
        summary_sheet.write(row, 0, '最大 Layer 数量', header_format)
        summary_sheet.write(row, 1, max_layers, data_format)
        row += 1
        
        summary_sheet.write(row, 0, '最小 Layer 数量', header_format)
        summary_sheet.write(row, 1, min_layers, data_format)
        row += 1
        
        summary_sheet.write(row, 0, '平均 HWC Layer 数量', header_format)
        summary_sheet.write(row, 1, avg_hwc_layers, number_format)
        row += 1
        
        summary_sheet.write(row, 0, '平均 GLES Layer 数量', header_format)
        summary_sheet.write(row, 1, avg_gles_layers, number_format)
        row += 1
    
    # 调整列宽
    summary_sheet.set_column(0, 0, 30)
    summary_sheet.set_column(1, 1, 20)
    
    # ========== 详细表 ==========
    row = 0
    detail_sheet.write(row, 0, 'SurfaceFlinger 每帧详细数据', title_format)
    detail_sheet.merge_range(row, 0, row, 7, 'SurfaceFlinger 每帧详细数据', title_format)
    row += 2
    
    # 表头
    detail_sheet.write(row, 0, '帧序号', header_format)
    detail_sheet.write(row, 1, 'Frame ID', header_format)
    detail_sheet.write(row, 2, '时间戳(秒)', header_format)
    detail_sheet.write(row, 3, 'GPU Wait Time(ms)', header_format)
    detail_sheet.write(row, 4, '总Layer数', header_format)
    detail_sheet.write(row, 5, 'HWC Layer数', header_format)
    detail_sheet.write(row, 6, 'GLES Layer数', header_format)
    detail_sheet.write(row, 7, 'HWC Layers', header_format)
    detail_sheet.write(row, 8, 'GLES Layers', header_format)
    row += 1
    
    # 创建 frame_id 到 GPU wait time 的映射
    gpu_wait_dict = {}
    for start, end, duration, frame_id in sf_result['gpu_wait_intervals']:
        if frame_id not in gpu_wait_dict:
            gpu_wait_dict[frame_id] = 0
        gpu_wait_dict[frame_id] += duration * 1000  # 转换为毫秒
    
    # 数据行
    for i, frame in enumerate(frame_layer_info):
        frame_id = frame['frame_id']
        gpu_wait_time = gpu_wait_dict.get(frame_id, 0)
        
        detail_sheet.write(row, 0, i + 1, data_format)
        detail_sheet.write(row, 1, str(frame_id), data_format)
        detail_sheet.write(row, 2, frame['timestamp'], number_format)
        detail_sheet.write(row, 3, gpu_wait_time, number_format)
        detail_sheet.write(row, 4, frame['layer_count'], data_format)
        detail_sheet.write(row, 5, frame['hwc_layer_count'], data_format)
        detail_sheet.write(row, 6, frame['gles_layer_count'], data_format)
        detail_sheet.write(row, 7, ', '.join(frame['hwc_layers']), data_format)
        detail_sheet.write(row, 8, ', '.join(frame['gles_layers']), data_format)
        row += 1
    
    # 调整列宽
    detail_sheet.set_column(0, 0, 10)
    detail_sheet.set_column(1, 1, 15)
    detail_sheet.set_column(2, 3, 18)
    detail_sheet.set_column(4, 6, 15)
    detail_sheet.set_column(7, 8, 60)
    
    workbook.close()
    TEST_LOGGER.info(f"结果已导出到: {output_path}")


def main():
    """主函数"""
    TEST_LOGGER.info("*" * 80)
    TEST_LOGGER.info("SurfaceFlinger GPU Wait Time 和 Layer Count 分析工具")
    TEST_LOGGER.info("*" * 80)
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='SurfaceFlinger 分析工具')
    parser.add_argument('-f', '--file', dest='file_path', type=str, required=True,
                       help='Trace文件路径 (.html)')
    parser.add_argument('-at', '--animation-tag', dest='animation_tag', type=str, required=True,
                       help='动效Tag (如: openApp_Window_enter)')
    
    args = parser.parse_args()
    
    # 验证文件存在
    if not os.path.isfile(args.file_path):
        TEST_LOGGER.error(f"Trace文件不存在: {args.file_path}")
        sys.exit(1)
    
    TEST_LOGGER.info(f"Trace文件: {args.file_path}")
    TEST_LOGGER.info(f"动效Tag: {args.animation_tag}")
    
    try:
        # 读取配置文件获取动效时间区间
        from modules.common.Path import PathManager
        import json
        
        mcps_config_file_path = os.path.join(PathManager.config_folder, "mcps_config.json")
        if not os.path.isfile(mcps_config_file_path):
            TEST_LOGGER.error(f"配置文件不存在: {mcps_config_file_path}")
            sys.exit(1)
        
        with open(mcps_config_file_path, "r", encoding='utf-8') as f:
            mcps_config_dict = json.load(f)
        
        animation_tag_dict = mcps_config_dict.get("animation_tag", {})
        animation_config = animation_tag_dict.get(args.animation_tag)
        
        if not animation_config:
            TEST_LOGGER.error(f"未找到动效Tag配置: {args.animation_tag}")
            sys.exit(1)
        
        # 从 trace 文件中提取时间区间
        # 这里简化处理，使用整个 trace 的时间范围
        # 实际应该根据 animation_tag 配置提取精确的时间区间
        
        # 简化：直接分析整个 trace 文件
        # 你可以根据需要添加时间区间提取逻辑
        import re
        
        # 提取 trace 文件的时间范围
        start_time = None
        end_time = None
        
        TEST_LOGGER.info("正在从 trace 文件中提取时间范围...")
        
        # 使用 sched_switch 事件提取时间
        pattern = re.compile(r'(\d+\.\d+):\s+sched_switch:')
        
        with open(args.file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                match = pattern.search(line)
                if match:
                    timestamp = float(match.group(1))
                    if start_time is None:
                        start_time = timestamp
                    end_time = timestamp
        
        if not start_time or not end_time:
            TEST_LOGGER.error("无法从 trace 文件中提取时间范围")
            TEST_LOGGER.error("请确保 trace 文件包含 sched_switch 事件")
            sys.exit(1)
        
        TEST_LOGGER.info(f"分析时间区间: [{start_time}, {end_time}]")
        
        # 执行 SurfaceFlinger 分析
        sf_analyzer = SurfaceFlingerAnalysis(
            args.file_path,
            start_time,
            end_time
        )
        sf_result = sf_analyzer.analyze()
        
        # 导出到 Excel
        trace_dir = os.path.dirname(args.file_path)
        trace_name = os.path.basename(args.file_path).replace('.html', '')
        output_path = os.path.join(trace_dir, f"surfaceflinger_analysis_{trace_name}_{start_time}_{end_time}.xlsx")
        
        export_to_excel(sf_result, output_path)
        
        TEST_LOGGER.info("*" * 80)
        TEST_LOGGER.info("分析完成！")
        TEST_LOGGER.info(f"结果文件: {output_path}")
        TEST_LOGGER.info("*" * 80)
        
    except Exception as e:
        TEST_LOGGER.error(f"分析失败: {e}")
        TEST_LOGGER.error(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    main()

