# -*- coding: utf-8 -*-
"""
本模块存放异常
"""
from typing import Optional


class Aria2rpcException(Exception):
    """
    Base exception raised by this module.
    """

    def __init__(self, msg: str, connection_error: Optional[bool] = False):
        super().__init__(msg)
        self.msg = msg
        self.connection_error = connection_error

    def __str__(self):
        return f"{self.__class__.__name__}: {self.msg}"
