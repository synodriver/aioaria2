# -*- coding: utf-8 -*-
"""
本模块存放工具函数
"""
import sys
import json
import base64
import asyncio
from functools import wraps, partial
import contextvars
from typing import Optional, Any, Awaitable, Dict, Generator, Callable

import aiofiles

from aioaria2.exceptions import Aria2rpcException

JSON_ENCODING = "utf-8"
DEFAULT_JSON_DECODER = json.loads
DEFAULT_JSON_ENCODER = json.dumps


def __init__():
    pass


class ResultStore:
    """
    websocket 结果缓存类
    """
    _id = 1  # jsonrpc的id
    _futures: Dict[int, asyncio.Future] = {}  # 暂存id对应的未来对象

    @classmethod
    def get_id(cls) -> int:
        """
        jsonrpc的自增id 默认的id生成工厂函数
        :return:
        """
        s = cls._id
        cls._id = (cls._id + 1) % sys.maxsize
        return s

    @classmethod
    def add_result(cls, result: Dict[str, Any]) -> None:
        """
        收到websocket消息的时候,用这个类存储结果 表示一次特定的请求返回了
        :param result: jsonrpc的回复格式 {'id':int,'jsonrpc','2.0','result':xxx}
        :return:
        """
        if isinstance(result, dict):
            future = cls._futures.get(result["id"])
            if future and not future.done():
                future.set_result(result)
            else:
                # 没有这个future fetch没有被调用 future=None
                future = asyncio.get_event_loop().create_future()
                cls._futures[result["id"]] = future
                future.set_result(result)

    @classmethod
    async def fetch(cls, identity: int, timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        返回暂存在本类中的结果
        :param identity: jsonrpc返回的id
        :param timeout: 等待结果超时
        :return: 返回完整的jsonrpc 返回数据而不是仅仅有result字段 判断在后续来处理
        """
        if cls._futures.get(identity):  # 已经存在这个id的future了 不用创建了
            future = cls._futures[identity]
        else:
            future = asyncio.get_event_loop().create_future()  # todo 可能会导致Future泄漏吗?
            cls._futures[identity] = future
        try:
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            raise Aria2rpcException("jsonrpc over websocket call timeout") from None
        finally:
            del cls._futures[identity]


def run_sync(func: Callable[..., Any]) -> Callable[..., Awaitable[Any]]:
    """
    一个用于包装 sync function 为 async function 的装饰器
    :param func:
    :return:
    """

    @wraps(func)
    async def _wrapper(*args: Any, **kwargs: Any) -> Any:
        loop = asyncio.get_running_loop()
        pfunc = partial(func, *args, **kwargs)
        context = contextvars.copy_context()
        context_run = context.run
        result = await loop.run_in_executor(None, context_run, pfunc)
        return result

    return _wrapper


async def add_async_callback(task: asyncio.Task, callback) -> asyncio.Task:
    assert asyncio.iscoroutinefunction(callback), "callback must be a coroutinefunction"
    result = await task
    await callback(task)
    return result


def add_options_and_position(params: list, options=None, position=None) -> list:
    """
    Convenience method for adding options and position to parameters.
    """
    if options:
        params.append(options)
    if position:
        if not isinstance(position, int):
            try:
                position = int(position)
            except ValueError:
                position = -1
        if position >= 0:
            params.append(position)
    return params


async def b64encode_file(path: str) -> str:
    """
    读取文件，转换b64编码
    """
    async with aiofiles.open(path, 'rb') as handle:
        return str(base64.b64encode(await handle.read()), JSON_ENCODING)


def get_status(response: Dict) -> Any:
    """
    Process a status response.
    """
    if response:
        try:
            return response['status']
        except KeyError:
            return 'error'
    else:
        return 'error'


def read_configfile(path: str, prefix: str = "--") -> Generator[str, None, None]:
    """
    从配置文件中读取可用配置
    :param path: aria2配置文件路径
    :param prefix: yield之前的前缀
    :return:
    """
    with open(path, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if line and not line.startswith("#"):
                temp = prefix + line
                yield temp


if __name__ == "__main__":
    pass
