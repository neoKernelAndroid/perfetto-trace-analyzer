# -*- coding: utf-8 -*-
# @Time     : 2025/2/26 17:19
# @Author   : yunqing.gui
# @Email    : yunqing.gui@transsion.com
# @File     : Path.py

import os
import sys


class PATH:

    @property
    def project_folder(self):
        if sys.argv[0].endswith(".py") or sys.argv[0].endswith(".pyc"):
            # 如果执行的是 py或 pyc文件, 表示执行对象未打包
            modules_folder = os.path.dirname(os.path.abspath(__file__))
            modules_folder = os.path.dirname(modules_folder)
            return os.path.dirname(modules_folder)
        else:
            # 如果执行的是非py文件, 表示执行对象已打包, 则返回打包文件目录的绝对路径
            return os.path.dirname(os.path.abspath(sys.argv[0]))

    @property
    def log_folder(self):
        return os.path.join(self.project_folder, "logs")

    @property
    def result_folder(self):
        return os.path.join(self.project_folder, "result")

    @property
    def tools_folder(self):
        return os.path.join(self.project_folder, "tools")

    @property
    def config_folder(self):
        return os.path.join(self.project_folder, "configs")

    @property
    def tmp_folder(self):
        return os.path.join(self.project_folder, "tmp")


PathManager = PATH()
