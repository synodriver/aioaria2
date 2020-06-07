# -*- coding: utf-8 -*-
"""
本模块负责管理aria2进程
"""

import os
import subprocess
from typing import Dict
from functools import wraps
import asyncio

# --------------------------#
ENCODING = "gbk"

# --------------------------#

cache: Dict[str, object] = {}


def single_instance(cls: type):
    """
    单例模式装饰器，如果两个aria2进程一同开启必定端口冲突
    :param cls: 要装饰的类
    :return:
    """

    @wraps(cls)
    def inner(*args, **kw):
        class_name = cls.__name__
        if class_name in cache:
            return cache[class_name]
        else:
            instance = cls(*args, **kw)
            cache[class_name] = instance
            return instance
    return inner


@single_instance
class Aria2Server:
    """
    aria2进程对象
    """

    def __init__(self, *args: str, daemon=False):
        """
        :param args: 启动aria2的命令行参数
        :param daemon: True:aria2随python解释器同生共死
        """
        if args:
            self.cmd = list(args)
        else:
            self.cmd = []
        if daemon:
            self.cmd.append('--stop-with-process={:d}'.format(os.getpid()))
        self.process = None
        self._is_running = False

    def start(self):
        self.process = subprocess.Popen(self.cmd)
        self._is_running = True

    def wait(self):
        """
        等待进程结束
        :return:
        """
        self.process.wait()
        self._is_running = False

    def terminate(self):
        self.process.terminate()
        self.wait()

    def kill(self):
        self.process.kill()
        self.wait()

    @property
    def pid(self):
        return self.process.pid

    @property
    def returncode(self):
        return self.process.returncode

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._is_running:
            self.terminate()


@single_instance
class AsyncAria2Server(Aria2Server):
    """
    aria2进程对象
    异步io
    """

    def __init__(self, *args: str, daemon=False):
        super().__init__(*args, daemon=daemon)

    async def start(self):
        cmd = ""
        for i in self.cmd:
            cmd += i + " "
        # program, *args = self.cmd
        self.process = await asyncio.create_subprocess_shell(cmd)
        self._is_running = True

    async def wait(self):
        await self.process.wait()
        self._is_running = False

    async def terminate(self):
        self.process.terminate()
        await self.wait()

    async def kill(self):
        self.process.kill()
        await self.wait()

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._is_running:
            await self.terminate()


if __name__ == "__main__":
    pass
