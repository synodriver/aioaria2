# -*- coding: utf-8 -*-
"""
支持类型注释
"""
import asyncio
from typing import (Callable,
                    Coroutine,
                    Any,
                    TypeVar,
                    TYPE_CHECKING)

Aria2WebsocketTrigger = TypeVar("Aria2WebsocketTrigger", bound="Aria2WebsocketTrigger")

if TYPE_CHECKING:
    from aioaria2 import Aria2WebsocketTrigger

CallBack = Callable[[Aria2WebsocketTrigger, asyncio.Task], Coroutine[Any, Any, Any]]
"""
Websocket事件的回调函数
"""
IdFactory = Callable[[], int]
"""
产生随机id的工厂函数
"""

# TODO 完成typing
