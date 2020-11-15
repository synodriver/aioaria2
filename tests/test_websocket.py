# -*- coding: utf-8 -*-
import aioaria2
import asyncio
import time
from pprint import pprint

HOST = 'http://aria.blackjoe.art:2082/jsonrpc'


async def callback(trigger, future):
    print("下载开始{0}".format(future.result()))


async def callback2(trigger: aioaria2.Aria2WebsocketTrigger, future):
    data = future.result()
    print("下载完成{0}".format(data))


async def callback3(trigger: aioaria2.Aria2WebsocketTrigger, future):
    print("下载中断")
    data = future.result()
    gid = data["params"][0]["gid"]
    trigger.identity = "getFiles"
    await trigger.getFiles(gid)
    trigger.identity = "id"


async def onresult(trigger, future):
    print("结果")
    data = future.result()
    if data['id'] == "getFiles":
        # 如同http一样的返回     getFiles调用
        url = data["result"][0]["uris"][0]["uri"]
        trigger.identity = "addUri"
        await trigger.addUri([url])
        trigger.identity = "id"
    elif data['id'] == "addUri":
        print("重新入队成功:{0}".format(data["result"]))


async def get_client():
    async with aioaria2.Aria2HttpClient("id", HOST, "normal",
                                        token="a489451594cda0792df1") as client:
        # pprint(await client.addUri(["http://odrive.aptx.xin/%E5%8A%A8%E7%94%BB/2004/200445.zip"]))
        pprint(await client.getVersion())

    pass


async def get_trigger():
    async with await aioaria2.Aria2WebsocketTrigger.new(HOST, token="a489451594cda0792df1") as client:
    # client=aioaria2.Aria2WebsocketTrigger("id", HOST,token="adman",)
        pprint(await client.getVersion())
        pprint(await client.addUri(["https://www.google.com"]))
        client.onDownloadStart(callback)
        client.onDownloadStart(callback2)
        client.onDownloadComplete(callback2)
        client.onDownloadError(callback3)
        start = time.time()
        await asyncio.sleep(100)
        pass


def main():
    loop = asyncio.get_event_loop()
    # loop.call_soon_threadsafe()
    # asyncio.run_coroutine_threadsafe()
    # tasks = [loop.create_task(get_trigger()),loop.create_task(get_client())]  # , loop.create_task(get_client())]
    tasks = [loop.create_task(get_trigger())]
    loop.run_until_complete(asyncio.wait(tasks))


if __name__ == "__main__":
    asyncio.run(get_trigger())
