# -*- coding: utf-8 -*-
import asyncio
import time
from pprint import pprint

import ujson

import aioaria2

HOST = "http://aria.blackjoe.art:2082/jsonrpc"


async def callback(trigger, data):
    print("下载开始{0}".format(data))


async def callback2(trigger: aioaria2.Aria2WebsocketTrigger, data):
    print("下载完成{0}".format(data))


async def callback3(trigger: aioaria2.Aria2WebsocketTrigger, future):
    print("下载中断")
    data = future.result()
    gid = data["params"][0]["gid"]
    trigger.identity = "getFiles"
    await trigger.getFiles(gid)
    trigger.identity = "id"


async def onresult(trigger, data):
    print("结果")
    if data["id"] == "getFiles":
        # 如同http一样的返回     getFiles调用
        url = data["result"][0]["uris"][0]["uri"]
        trigger.identity = "addUri"
        await trigger.addUri([url])
        trigger.identity = "id"
    elif data["id"] == "addUri":
        print("重新入队成功:{0}".format(data["result"]))


async def get_client():
    async with aioaria2.Aria2HttpClient(
        HOST, token="a489451594cda0792df1", loads=ujson.loads, dumps=ujson.dumps
    ) as client:
        # pprint(await client.addUri(["http://odrive.aptx.xin/%E5%8A%A8%E7%94%BB/2004/200445.zip"]))
        pprint(await client.getVersion())


async def get_trigger():
    try:
        client = await aioaria2.Aria2WebsocketTrigger.new(
            "https://127.0.0.1:443", token="a489451594cda0792df1"
        )
        # client=aioaria2.Aria2WebsocketTrigger("id", HOST,token="adman",)
        client.onDownloadStart(callback)
        client.onDownloadComplete(callback2)
        await client.addUri(["https://www.baidu.com"])
    except aioaria2.Aria2rpcException as e:
        print("can't connect ")


def main():
    loop = asyncio.get_event_loop()
    # loop.call_soon_threadsafe()
    # asyncio.run_coroutine_threadsafe()
    # tasks = [loop.create_task(get_trigger()),loop.create_task(get_client())]  # , loop.create_task(get_client())]
    tasks = [loop.create_task(get_trigger()), asyncio.sleep(100)]
    loop.run_until_complete(asyncio.wait(tasks))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(get_trigger())
    try:
        loop.run_forever()
    finally:
        loop.close()
    # main()
