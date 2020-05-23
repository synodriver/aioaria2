# -*- coding: utf-8 -*-
"""
本模块负责管理aria2进程
"""
from typing import List
import os
import logging
import subprocess
from typing import Dict
from functools import wraps
from .utils import read_configfile

# --------------------------#
ENCODING = "gbk"


# --------------------------#
def single_instance(cls: type):
    """
    单例模式装饰器，如果两个aria2进程一同开启必定端口冲突
    :param cls: 要装饰的类
    :return:
    """
    cache: Dict[str, object] = {}

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
class Aria2rpcServer:
    """
    每一个实例对应一个Aria2进程
    """

    def __init__(self, cmd: List[str] = None, run_bash: str = None, token: str = None, port: str = "6800",
                 timeout: int = 5):
        """
        :param cmd: 代表启动aria2进程的字符串数组，是一组附加命令
          arguments, eg.
              ['aria2c', '--rpc-listen-all=false', '--continue']
          or
              ['sudo', 'aria2c', '--rpc-listen-all=false', '--continue']
          不能包括以下命令
              --enable-rpc
              --rpc-secret
              --rpc-listen-port
          For local use it is recommended to include "--rpc-listen-all=false".
        :param token: --rpc-secret 命令的参数
        :param port: --rpc-listen-port 的参数

        example : server=aioaria2.Aria2rpcServer(["path/aria2c.exe","--enable-rpc=true","--rpc-listen-all=true","--rpc-secret=123"])
        """
        if cmd is None:
            cmd = []
        if not run_bash:
            self.cmd = cmd
            # 把该py解释器作为父进程
            self.cmd.append('--stop-with-process={:d}'.format(os.getpid()))
            if token:
                self.cmd.extend((
                    '--enable-rpc',
                    '--rpc-secret={0}'.format(token),
                    '--rpc-listen-port={0}'.format(str(port))
                ))
            else:
                self.cmd.extend((
                    '--enable-rpc',
                    '--rpc-listen-port={0}'.format(str(port))
                ))
            for option in self.cmd:
                if "--conf-path" in option:
                    path = option[12:]
                    new_args = [self.cmd[0]] + list(read_configfile(path))
                    self.cmd = new_args
                    # print(len(self.cmd))
                    break
        else:
            self.cmd = [run_bash]
        self.token = token
        self.port = port
        self.timeout = timeout
        # 设置日志
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter("[%(asctime)s %(name)s in %(module)s]%(levelname)s %(message)s"))
        logger.addHandler(handler)
        self.logger = logger
        self.process = None  # aria2 进程
        self.launch()

    def launch(self):
        self.process = subprocess.Popen(self.cmd,
                                        stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
        self.logger.info("starting aria2 process")

    def kill(self):
        if not self.process:
            return True
        self.logger.info("{0} attempt to stop aria2 which pid is {1}".format(self.__class__.__name__, self.process.pid))
        methods = (self.process.terminate, self.process.kill)

        for fun in methods:
            try:
                fun()
            except Exception as err:
                self.logger.error("sth wrong when terminate aria2 {0}".format(str(err)))
            try:
                exit_code = self.process.wait(self.timeout)
            except subprocess.TimeoutExpired:
                exit_code = None
            if exit_code is not None:
                self.logger.debug('{}: PID {:d} exit code: {:d}'.format(
                    self.__class__.__name__,
                    self.process.pid,
                    exit_code
                ))
                self.process = None
                return True

    def communicate(self, encoding="utf-8"):
        try:
            outs = self.process.stdout.read().decode(encoding)
            errs = self.process.stderr.read().decode(encoding)
            return outs, errs
        except Exception as e:
            self.logger.info("没有子进程消息,{0}".format(str(e)))


if __name__ == "__main__":
    pass
