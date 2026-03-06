# -*- coding: utf-8 -*-
# @Time     : 2026/01/05
# @Author   : Auto Generated
# @File     : run_mcps_analysis.py
"""
通用的 MCPS 分析脚本
支持通过配置文件动态指定要分析的线程、进程和动效区间
"""

import argparse
import json
import os
import sys
from pathlib import Path

from modules.common.Logger import TEST_LOGGER
from modules.TraceHtml.TraceHtmlCpuMcps import TraceHtmlCpuMcps, MCPS_VERSION

def load_config(config_file):
    """加载配置文件"""
    if not os.path.exists(config_file):
        TEST_LOGGER.error(f"配置文件不存在: {config_file}")
        return None
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        TEST_LOGGER.error(f"加载配置文件失败: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(
        description='通用的 MCPS 分析工具 - 支持动态配置',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 使用配置文件
  python run_mcps_analysis.py -c config.json
  
  # 直接指定参数（覆盖配置文件）
  python run_mcps_analysis.py -c config.json -f trace.html -t "thread1,thread2" -p "process_name"
  
配置文件格式 (JSON):
{
  "trace_file": "path/to/trace-perfetto-con.html",
  "cpu_type": "G200",
  "thread_names": "ssion.launcher3,RenderThread",
  "process_name": "com.transsion.launcher3",
  "animation_tag": "LAUNCHER_APP_SWIPE_TO_RECENTS"
}
        """
    )
    
    parser.add_argument("-c", "--config", dest="config_file", 
                       metavar="配置文件路径", type=str, required=True,
                       help='JSON 配置文件路径')
    parser.add_argument("-f", "--file", dest="trace_file", 
                       metavar="Trace文件路径", type=str, default=None,
                       help='Trace 文件路径（覆盖配置文件）')
    parser.add_argument("-cpu", "--cpu_type", dest="cpu_type", 
                       metavar="CPU类型", type=str, default=None,
                       help='CPU 类型，如 G200（覆盖配置文件）')
    parser.add_argument("-t", "--threads", dest="thread_names", 
                       metavar="线程名列表", type=str, default=None,
                       help='线程名列表，用逗号分隔（覆盖配置文件）')
    parser.add_argument("-p", "--process", dest="process_name", 
                       metavar="进程名", type=str, default=None,
                       help='进程名（覆盖配置文件）')
    parser.add_argument("-at", "--animation_tag", dest="animation_tag", 
                       metavar="动效标签", type=str, default=None,
                       help='动效标签（覆盖配置文件）')
    
    args = parser.parse_args()
    
    # 加载配置文件
    config = load_config(args.config_file)
    if config is None:
        sys.exit(1)
    
    # 获取配置参数（命令行参数优先）
    trace_file = args.trace_file or config.get('trace_file')
    cpu_type = args.cpu_type or config.get('cpu_type')
    thread_names_str = args.thread_names or config.get('thread_names')
    process_name = args.process_name or config.get('process_name')
    animation_tag = args.animation_tag or config.get('animation_tag')
    
    # 验证必需参数
    if not trace_file:
        TEST_LOGGER.error("未指定 trace_file，请在配置文件或命令行中指定")
        sys.exit(1)
    
    if not cpu_type:
        TEST_LOGGER.error("未指定 cpu_type，请在配置文件或命令行中指定")
        sys.exit(1)
    
    if not thread_names_str:
        TEST_LOGGER.error("未指定 thread_names，请在配置文件或命令行中指定")
        sys.exit(1)
    
    if not os.path.exists(trace_file):
        TEST_LOGGER.error(f"Trace 文件不存在: {trace_file}")
        sys.exit(1)
    
    # 解析线程名列表
    thread_name_list = [name.strip() for name in thread_names_str.split(',')]
    
    # 打印配置信息
    TEST_LOGGER.info("*" * 50)
    TEST_LOGGER.info(f"启动MCPS解析工具[V{MCPS_VERSION}] - 通用配置模式")
    TEST_LOGGER.info("*" * 50)
    TEST_LOGGER.info(f"配置文件: {args.config_file}")
    TEST_LOGGER.info(f"Trace 文件: {trace_file}")
    TEST_LOGGER.info(f"CPU 类型: {cpu_type}")
    TEST_LOGGER.info(f"线程列表: {thread_name_list}")
    TEST_LOGGER.info(f"进程名: {process_name}")
    TEST_LOGGER.info(f"动效标签: {animation_tag}")
    TEST_LOGGER.info("*" * 50)
    
    # 创建分析对象并执行分析
    trace_html = TraceHtmlCpuMcps(
        trace_file, 
        cpu_type, 
        thread_name_list, 
        process_name, 
        animation_tag
    )
    trace_html.analyse()
    
    TEST_LOGGER.info("*" * 50)
    TEST_LOGGER.info("分析完成！")
    TEST_LOGGER.info("*" * 50)

if __name__ == '__main__':
    main()




















