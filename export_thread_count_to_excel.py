# -*- coding: utf-8 -*-
# @Time     : 2025/1/20
# @Author   : chao.liu8
# @File     : export_thread_count_to_excel.py
# @Description: 导出线程数统计到 Excel

import sys
import os
import io
from datetime import datetime

# 设置标准输出编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from modules.services.Performacne import PerformanceTraceProcessor
from modules.common.Excel import ThreadCountExcel


def export_thread_count_to_excel(trace_path, output_path=None, top_n=20, key_processes=None, detail_processes=None):
    """
    导出线程数统计到 Excel
    
    :param trace_path: trace 文件路径
    :param output_path: 输出 Excel 路径，如果为 None 则自动生成
    :param top_n: Top N 进程数量
    :param key_processes: 关键进程列表，如果为 None 则使用默认列表
    :param detail_processes: 需要详细信息的进程列表，如果为 None 则使用关键进程
    :return: 输出文件路径
    """
    
    print("="*80)
    print("  线程数统计导出工具")
    print("="*80)
    print()
    
    print(f"[INFO] 开始分析 trace 文件: {trace_path}")
    print(f"[INFO] 正在加载 trace 文件...")
    
    try:
        tp = PerformanceTraceProcessor(trace_path, bin_path=None, verbose=False)
        print(f"[OK] trace 文件加载成功!\n")
    except Exception as e:
        print(f"\n[ERROR] 加载 trace 文件失败!")
        print(f"错误详情: {e}")
        return None
    
    # 生成输出文件路径
    if output_path is None:
        trace_dir = os.path.dirname(trace_path)
        trace_name = os.path.splitext(os.path.basename(trace_path))[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(trace_dir, f"{trace_name}_thread_count_{timestamp}.xls")
    
    print(f"[INFO] 输出文件: {output_path}\n")
    
    # 1. 获取 Top N 进程
    print(f"[INFO] 正在获取线程数最多的前 {top_n} 个进程...")
    top_processes = tp.get_all_process_thread_count(top_n=top_n)
    print(f"[OK] 已获取 {len(top_processes)} 个进程\n")
    
    # 2. 获取关键进程
    if key_processes is None:
        key_processes = [
            'system_server',
            'com.android.systemui',
            'com.transsion.launcher3',
            '/system/bin/surfaceflinger'
        ]
    
    print(f"[INFO] 正在获取关键进程线程数...")
    key_processes_result = tp.monitor_key_processes_thread_count(key_processes)
    print(f"[OK] 已获取 {len(key_processes_result)} 个关键进程\n")
    
    # 3. 获取详细线程信息
    if detail_processes is None:
        detail_processes = list(key_processes_result.keys())
    
    print(f"[INFO] 正在获取详细线程信息...")
    process_details = {}
    for process_name in detail_processes:
        try:
            result = tp.get_process_thread_count(process_name)
            if result['thread_count'] > 0:
                process_details[process_name] = result
                print(f"  - {process_name}: {result['thread_count']} 个线程")
        except Exception as e:
            print(f"  - {process_name}: 获取失败 ({e})")
    print()
    
    # 4. 导出到 Excel
    print(f"[INFO] 正在导出到 Excel...")
    excel = ThreadCountExcel(output_path)
    excel.export_thread_count_data(
        top_processes=top_processes,
        key_processes=key_processes_result,
        process_details=process_details
    )
    
    print(f"[OK] 导出完成!")
    print(f"[OK] 文件路径: {output_path}")
    print()
    
    return output_path


def main():
    """
    主函数
    使用方法:
        python export_thread_count_to_excel.py <trace_file_path> [output_path] [top_n]
    
    参数:
        trace_file_path: trace 文件路径（必需）
        output_path: 输出 Excel 路径（可选，默认自动生成）
        top_n: Top N 进程数量（可选，默认 20）
    
    示例:
        python export_thread_count_to_excel.py trace.perfetto-trace
        python export_thread_count_to_excel.py trace.perfetto-trace output.xls
        python export_thread_count_to_excel.py trace.perfetto-trace output.xls 50
    """
    
    if len(sys.argv) < 2:
        print("[ERROR] 错误: 缺少 trace 文件路径")
        print("\n使用方法:")
        print("  python export_thread_count_to_excel.py <trace_file_path> [output_path] [top_n]")
        print("\n示例:")
        print("  python export_thread_count_to_excel.py trace.perfetto-trace")
        print("  python export_thread_count_to_excel.py trace.perfetto-trace output.xls")
        print("  python export_thread_count_to_excel.py trace.perfetto-trace output.xls 50")
        sys.exit(1)
    
    trace_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    top_n = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    
    result = export_thread_count_to_excel(trace_path, output_path, top_n)
    
    if result:
        print("="*80)
        print("  完成!")
        print("="*80)
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()


