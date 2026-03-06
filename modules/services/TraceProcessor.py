# -*- coding: utf-8 -*-
# @Time     : 2025/4/11 11:03
# @Author   : yunqing.gui
# @Email    : yunqing.gui@transsion.com
# @File     : TraceProcessor.py

import os
from perfetto.trace_processor import TraceProcessor, TraceProcessorConfig


class TraceProcessorBasic:

    def __init__(self, trace_file_path, bin_path=None, verbose=False):
        self.__trace_file_path = trace_file_path
        self.__bin_path = bin_path
        self.__verbose = verbose
        self._tp = None
        self._init()

    def _init(self):
        # 如果没有指定 bin_path，尝试使用我们下载的 trace_processor
        if self.__bin_path is None:
            default_path = os.path.expanduser('~/.local/share/perfetto/trace_processor_shell.exe')
            if os.path.exists(default_path):
                self.__bin_path = default_path
            else:
                # 尝试另一个可能的路径
                alt_path = os.path.expanduser('~/.local/share/perfetto/trace_processor.exe')
                if os.path.exists(alt_path):
                    self.__bin_path = alt_path
        
        config = TraceProcessorConfig(
            bin_path=self.__bin_path,
            verbose=self.__verbose
        )
        self._tp = TraceProcessor(trace=self.__trace_file_path, config=config)
