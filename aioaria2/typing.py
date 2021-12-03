# -*- coding: utf-8 -*-
"""
支持类型注释
"""
from typing import (Callable,
                    Dict,
                    Awaitable,
                    Any,
                    Union,
                    TypeVar,
                    TYPE_CHECKING)

Aria2WebsocketTrigger = TypeVar("Aria2WebsocketTrigger", bound="Aria2WebsocketTrigger")

if TYPE_CHECKING:
    from aioaria2 import Aria2WebsocketTrigger

"""
Websocket事件的回调函数
"""
CallBack = Callable[[Aria2WebsocketTrigger, Dict[str, Any]], Union[Awaitable[Any], Awaitable[None]]]

"""
产生随机id的工厂函数 如果一定要参数可以用functools.partial
"""
IdFactory = Callable[[], Union[int, Awaitable[int]]]
