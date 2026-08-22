# -*- coding: utf-8 -*-
"""
支持类型注释
"""
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aioaria2 import Aria2WebsocketClient

"""
Websocket事件的回调函数
"""
CallBack = Callable[
    ["Aria2WebsocketClient", dict[str, Any]], Awaitable[Any] | Awaitable[None]
]

"""
产生随机id的工厂函数 如果一定要参数可以用functools.partial
"""
IdFactory = Callable[[], int | Awaitable[int]]
