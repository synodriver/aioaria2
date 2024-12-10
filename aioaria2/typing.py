# -*- coding: utf-8 -*-
"""
支持类型注释
"""
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict, TypeVar, Union

Aria2WebsocketClient = TypeVar("Aria2WebsocketClient", bound="Aria2WebsocketClient")

if TYPE_CHECKING:
    from aioaria2 import Aria2WebsocketClient

"""
Websocket事件的回调函数
"""
CallBack = Callable[
    [Aria2WebsocketClient, Dict[str, Any]], Union[Awaitable[Any], Awaitable[None]]
]

"""
产生随机id的工厂函数 如果一定要参数可以用functools.partial
"""
IdFactory = Callable[[], Union[int, Awaitable[int]]]
