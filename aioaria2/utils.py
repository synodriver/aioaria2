# -*- coding: utf-8 -*-
"""
本模块存放工具函数
"""
import base64
import aiofiles

JSON_ENCODING = "utf-8"


def __init__():
    pass


def add_options_and_position(params, options=None, position=None):
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


async def b64encode_file(path):
    """
    读取文件，转换b64编码
    """
    async with aiofiles.open(path, 'rb') as handle:
        return str(base64.b64encode(await handle.read()), JSON_ENCODING)


def get_status(response):
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


def read_configfile(path: str, prefix: str = "--"):
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
