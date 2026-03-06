# -*- coding: utf-8 -*-
# @Time     : 2025/1/10
# @Author   : AI Assistant
# @File     : run_gpu_analysis.py
# @Description : GPU分析可配置运行脚本

"""
GPU分析可配置运行脚本

功能：
1. 支持通过配置文件或命令行参数运行GPU分析
2. 支持自定义进程、线程、动效区间
3. 支持多种配置模式（配置文件优先、命令行覆盖）

使用方法：
1. 使用配置文件：
   python run_gpu_analysis.py --config configs/gpu_analysis_config.json

2. 使用命令行参数：
   python run_gpu_analysis.py -f trace.html -c MT6983 -t "RenderThread,wmshell.main" -p "com.android.systemui" -at LAUNCHER_APP_SWIPE_TO_RECENTS

3. 混合模式（配置文件 + 命令行覆盖）：
   python run_gpu_analysis.py --config configs/gpu_analysis_config.json -f custom_trace.html

4. 交互式模式：
   python run_gpu_analysis.py --interactive
"""

import argparse
import json
import os
import sys
import traceback
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.common.Logger import TEST_LOGGER
from modules.TraceHtml.TraceHtmlCpuMcps import TraceHtmlCpuMcps, MCPS_VERSION


class GPUAnalysisConfig:
    """GPU分析配置类"""
    
    def __init__(self):
        self.html_path = None
        self.cpu_type = None
        self.task_name_list = None
        self.process_name = None
        self.animation_tag = None
        self.config_file = None
        
    def load_from_file(self, config_file):
        """从配置文件加载配置"""
        if not os.path.isfile(config_file):
            TEST_LOGGER.error(f"配置文件不存在: {config_file}")
            return False
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 加载trace文件路径
            trace_config = config.get('trace_file', {})
            if trace_config.get('html_path'):
                self.html_path = trace_config['html_path']
            
            # 加载CPU配置
            cpu_config = config.get('cpu_config', {})
            if cpu_config.get('cpu_type'):
                self.cpu_type = cpu_config['cpu_type']
            
            # 加载进程过滤
            process_config = config.get('process_filter', {})
            if process_config.get('process_name'):
                self.process_name = process_config['process_name']
            
            # 加载任务列表
            task_config = config.get('task_list', {})
            if task_config.get('tasks'):
                self.task_name_list = task_config['tasks']
            
            # 加载动效配置
            animation_config = config.get('animation_config', {})
            if animation_config.get('animation_tag'):
                self.animation_tag = animation_config['animation_tag']
            
            TEST_LOGGER.info(f"成功从配置文件加载配置: {config_file}")
            return True
            
        except Exception as e:
            TEST_LOGGER.error(f"加载配置文件失败: {e}\n{traceback.format_exc()}")
            return False
    
    def load_from_args(self, args):
        """从命令行参数加载配置（覆盖配置文件）"""
        if args.file_path:
            self.html_path = args.file_path
        if args.cpu_type:
            self.cpu_type = args.cpu_type
        if args.task_name_list:
            self.task_name_list = args.task_name_list.split(',')
        if args.task_name_list_file:
            self.load_task_list_from_file(args.task_name_list_file)
        if args.process_name:
            self.process_name = args.process_name
        if args.animation_tag:
            self.animation_tag = args.animation_tag
    
    def load_task_list_from_file(self, task_file):
        """从文件加载任务列表"""
        if not os.path.isfile(task_file):
            TEST_LOGGER.error(f"任务列表文件不存在: {task_file}")
            return False
        
        try:
            with open(task_file, 'r', encoding='utf-8') as f:
                self.task_name_list = [line.strip() for line in f.readlines() if line.strip()]
            TEST_LOGGER.info(f"从文件加载任务列表: {task_file}, 共{len(self.task_name_list)}个任务")
            return True
        except Exception as e:
            TEST_LOGGER.error(f"加载任务列表文件失败: {e}")
            return False
    
    def validate(self):
        """验证配置是否完整"""
        errors = []
        
        if not self.html_path:
            errors.append("未指定trace文件路径 (html_path)")
        elif not os.path.isfile(self.html_path):
            errors.append(f"trace文件不存在: {self.html_path}")
        
        if not self.cpu_type:
            errors.append("未指定CPU类型 (cpu_type)")
        
        if not self.task_name_list:
            errors.append("未指定任务列表 (task_name_list)")
        
        if errors:
            TEST_LOGGER.error("配置验证失败:")
            for error in errors:
                TEST_LOGGER.error(f"  - {error}")
            return False
        
        return True
    
    def print_config(self):
        """打印当前配置"""
        TEST_LOGGER.info("=" * 80)
        TEST_LOGGER.info("当前配置:")
        TEST_LOGGER.info(f"  Trace文件: {self.html_path}")
        TEST_LOGGER.info(f"  CPU类型: {self.cpu_type}")
        TEST_LOGGER.info(f"  进程过滤: {self.process_name or '无（统计所有进程）'}")
        TEST_LOGGER.info(f"  任务列表: {', '.join(self.task_name_list) if self.task_name_list else '无'}")
        TEST_LOGGER.info(f"  动效Tag: {self.animation_tag or '无（不限制动效区间）'}")
        TEST_LOGGER.info("=" * 80)


def interactive_mode():
    """交互式配置模式"""
    TEST_LOGGER.info("=" * 80)
    TEST_LOGGER.info("进入交互式配置模式")
    TEST_LOGGER.info("=" * 80)
    
    config = GPUAnalysisConfig()
    
    # 1. 输入trace文件路径
    while True:
        html_path = input("\n请输入trace文件路径 (.html): ").strip()
        if os.path.isfile(html_path):
            config.html_path = html_path
            break
        else:
            print(f"文件不存在: {html_path}，请重新输入")
    
    # 2. 输入CPU类型
    print("\n常用CPU类型: MT6983, MT6895, Dimensity9000, Snapdragon8Gen1")
    config.cpu_type = input("请输入CPU类型: ").strip()
    
    # 3. 输入进程名（可选）
    config.process_name = input("\n请输入进程名（可选，留空则统计所有进程）: ").strip()
    
    # 4. 输入任务列表
    print("\n常用任务: RenderThread, wmshell.main, surfaceflinger, android.display")
    task_input = input("请输入任务列表（逗号分隔）: ").strip()
    config.task_name_list = [t.strip() for t in task_input.split(',') if t.strip()]
    
    # 5. 输入动效Tag（可选）
    print("\n常用动效Tag: LAUNCHER_APP_SWIPE_TO_RECENTS, LAUNCHER_SWIPE, APP_LAUNCH")
    config.animation_tag = input("请输入动效Tag（可选，留空则不限制动效区间）: ").strip()
    
    # 6. 确认配置
    print("\n" + "=" * 80)
    print("配置确认:")
    config.print_config()
    
    confirm = input("\n确认以上配置？(y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        return None
    
    return config


def create_sample_config():
    """创建示例配置文件"""
    sample_config = {
        "description": "GPU分析配置文件示例",
        "trace_file": {
            "html_path": "path/to/your/trace.html"
        },
        "cpu_config": {
            "cpu_type": "MT6983"
        },
        "process_filter": {
            "process_name": "com.android.systemui"
        },
        "task_list": {
            "tasks": [
                "RenderThread",
                "wmshell.main",
                "surfaceflinger"
            ]
        },
        "animation_config": {
            "animation_tag": "LAUNCHER_APP_SWIPE_TO_RECENTS"
        }
    }
    
    output_path = "configs/gpu_analysis_config_sample.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, indent=2, ensure_ascii=False)
    
    TEST_LOGGER.info(f"示例配置文件已创建: {output_path}")


def main():
    """主函数"""
    TEST_LOGGER.info("*" * 80)
    TEST_LOGGER.info(f"GPU分析工具 [V{MCPS_VERSION}]")
    TEST_LOGGER.info("*" * 80)
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='GPU分析可配置运行脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  1. 使用配置文件:
     python run_gpu_analysis.py --config configs/gpu_analysis_config.json
  
  2. 使用命令行参数:
     python run_gpu_analysis.py -f trace.html -c MT6983 -t "RenderThread,wmshell.main" -p "com.android.systemui"
  
  3. 交互式模式:
     python run_gpu_analysis.py --interactive
  
  4. 创建示例配置:
     python run_gpu_analysis.py --create-sample
        """
    )
    
    # 配置文件参数
    parser.add_argument('--config', dest='config_file', type=str, 
                       help='配置文件路径 (JSON格式)')
    
    # 基本参数
    parser.add_argument('-f', '--file', dest='file_path', type=str,
                       help='Trace文件路径 (.html)')
    parser.add_argument('-c', '--cpu', dest='cpu_type', type=str,
                       help='CPU类型 (如: MT6983, MT6895)')
    parser.add_argument('-t', '--tasks', dest='task_name_list', type=str,
                       help='任务列表，逗号分隔 (如: "RenderThread,wmshell.main")')
    parser.add_argument('-tf', '--task-file', dest='task_name_list_file', type=str,
                       help='任务列表文件路径')
    parser.add_argument('-p', '--process', dest='process_name', type=str,
                       help='进程名过滤 (如: com.android.systemui)')
    parser.add_argument('-at', '--animation-tag', dest='animation_tag', type=str,
                       help='动效Tag (如: LAUNCHER_APP_SWIPE_TO_RECENTS)')
    
    # 特殊模式
    parser.add_argument('--interactive', action='store_true',
                       help='交互式配置模式')
    parser.add_argument('--create-sample', action='store_true',
                       help='创建示例配置文件')
    
    args = parser.parse_args()
    
    # 处理特殊模式
    if args.create_sample:
        create_sample_config()
        return
    
    if args.interactive:
        config = interactive_mode()
        if not config:
            return
    else:
        # 创建配置对象
        config = GPUAnalysisConfig()
        
        # 优先加载配置文件
        if args.config_file:
            if not config.load_from_file(args.config_file):
                TEST_LOGGER.error("加载配置文件失败")
                sys.exit(1)
        
        # 命令行参数覆盖配置文件
        config.load_from_args(args)
    
    # 验证配置
    if not config.validate():
        TEST_LOGGER.error("配置验证失败，请检查配置")
        sys.exit(1)
    
    # 打印配置
    config.print_config()
    
    # 执行分析
    try:
        TEST_LOGGER.info("\n开始执行GPU分析...")
        trace_html = TraceHtmlCpuMcps(
            config.html_path,
            config.cpu_type,
            config.task_name_list,
            config.process_name,
            config.animation_tag
        )
        trace_html.analyse()
        TEST_LOGGER.info("\nGPU分析完成！")
        
    except Exception as e:
        TEST_LOGGER.error(f"分析过程中发生错误: {e}")
        TEST_LOGGER.error(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    main()













