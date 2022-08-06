# -*- coding: utf-8 -*-
"""
本模块提供aria2 json rpc的异步io交互接口 和aria2进程的管理器
"""
from aioaria2.client import Aria2HttpClient, Aria2WebsocketClient, Aria2WebsocketTrigger
from aioaria2.exceptions import Aria2rpcException
from aioaria2.parser import ControlFile, DHTFile
from aioaria2.server import Aria2Server, AsyncAria2Server
from aioaria2.utils import add_async_callback, run_sync

__version__ = "1.3.5rc2"

__author__ = "synodriver"
__all__ = [
    "Aria2Server",
    "AsyncAria2Server",
    "Aria2WebsocketTrigger",
    "Aria2HttpClient",
    "Aria2WebsocketClient",
    "Aria2rpcException",
    "ControlFile",
    "DHTFile",
    "run_sync",
    "add_async_callback",
]

#
# class Aria2Client:
#     def __init__(self, identity: str, url: str, token=None):
#         self._queue = asyncio.Queue()
#         self.req_generator = Aria2HttpClient(identity, url, "batch", token, self._queue)
#         # self.trigger=Aria2WebsocketTrigger()
#
#     @classmethod
#     async def create(cls, identity: str, url: str, token=None, queue=None):
#         self = cls(identity, url, token, queue)
#         self.trigger = await Aria2WebsocketTrigger.create(identity, url, "batch", token, self._queue)
#         return self
#
#     async def getVersion(self):
#         await self.req_generator.getVersion()
#
#     def register(self, func, type):
#         """
#         :return:
#         """
#         self.trigger.functions[type] = func
