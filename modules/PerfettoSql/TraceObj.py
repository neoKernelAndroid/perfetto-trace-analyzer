# -*- coding: utf-8 -*-
# @Time     : 2025/4/11 14:15
# @Author   : yunqing.gui
# @Email    : yunqing.gui@transsion.com
# @File     : TraceObj.py


class TraceObj:
    def __init__(self):
        self.trace_file_path = None
        self.startup_info_dict = {
            "startup_id": None,
            "ts": None,
            "ts_end": None,
            "dur": None,
            "package_name": None,
            "startup_type": None
        }