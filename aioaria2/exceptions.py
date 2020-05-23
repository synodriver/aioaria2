# -*- coding: utf-8 -*-
"""
本模块存放异常
"""


class Aria2rpcException(Exception):
    """
    Base exception raised by this module.
    """

    def __init__(self, msg, connection_error=False):
        super().__init__(msg)
        self.msg = msg
        self.connection_error = connection_error

    def __str__(self):
        return '{}: {}'.format(self.__class__.__name__, self.msg)



def main():
    pass


if __name__ == "__main__":
    main()