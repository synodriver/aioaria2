# -*- coding: utf-8 -*-
"""
本模块存放工具函数
"""
import base64
import aiofiles

JSON_ENCODING = "utf-8"


def __init():
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


def read_configfile(path: str, prex: str = "--"):
    """
    从配置文件中读取可用配置
    :param path: aria2配置文件路径
    :param prex: yield之前的前缀
    :return:
    """
    with open(path, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if line and not line.startswith("#"):
                temp = prex + line
                yield temp


if __name__ == "__main__":
    # import asyncio
    #
    # loop = asyncio.get_event_loop()
    # task = loop.create_task(b64encode_file(
    #     "F:\jhc\PanDownload\[kisssub.org][Moozzi2] 国家队比翼之吻 Darling in the Franxx 1-24 (BD 1920x1080 x.264 FLACx2).torrent"))
    # loop.run_until_complete(task)
    # print(task.result())
    # with open("F:\jhc\PanDownload\[kisssub.org][Moozzi2] 国家队比翼之吻 Darling in the Franxx 1-24 (BD 1920x1080 x.264 FLACx2).torrent","rb") as f:
    #     a=f.read()
    #     b=base64.b64encode(a)
    #     c=b.encode("utf-8")
    #     pass
    pass
