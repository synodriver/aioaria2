# -*- coding: utf-8 -*-
"""
支持类型注释
"""
from typing import (Callable,
                    Dict,
                    Coroutine,
                    Any,
                    TypeVar,
                    TYPE_CHECKING)

Aria2WebsocketTrigger = TypeVar("Aria2WebsocketTrigger", bound="Aria2WebsocketTrigger")

if TYPE_CHECKING:
    from aioaria2 import Aria2WebsocketTrigger

CallBack = Callable[[Aria2WebsocketTrigger, Dict[str, Any]], Coroutine[Any, Any, Any]]
"""
Websocket事件的回调函数
"""
IdFactory = Callable[[], int]
"""
产生随机id的工厂函数
"""

# TODO 完成typing
