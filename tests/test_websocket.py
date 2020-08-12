# -*- coding: utf-8 -*-
import aioaria2
import asyncio
from pprint import pprint

HOST = "http://192.168.0.107:6800/jsonrpc"


async def callback(trigger, future):
    print("下载开始{0}".format(future.result()))


async def callback2(trigger: aioaria2.Aria2WebsocketTrigger, future):
    data = future.result()
    print("下载完成{0}".format(data))


async def callback3(trigger: aioaria2.Aria2WebsocketTrigger, future):
    data = future.result()
    gid = data["params"][0]["gid"]
    await trigger.getFiles(gid)


async def onresult(trigger, future):
    print("结果")
    try:
        data = future.result()["result"]  # 如同http一样的返回     getFiles调用
        url = data[0]["uris"][0]["uri"]
        await trigger.addUri([url])
    except TypeError:
        # addUri返回 data是str,必然进入这个 就是gid
        print("重新入队成功:{0}".format(data))


async def get_client():
    async with aioaria2.Aria2HttpClient("id", HOST, "normal",
                                        token="adman") as client:
        # pprint(await client.addUri(["http://odrive.aptx.xin/%E5%8A%A8%E7%94%BB/2004/200445.zip"]))
        pprint(await client.getVersion())

    pass


async def get_trigger():
    client = await aioaria2.Aria2WebsocketTrigger.create("id",
                                                         HOST,
                                                         token="adman",
                                                         )
    # client=aioaria2.Aria2WebsocketTrigger("id", HOST,token="adman",)
    client.onDownloadStart(callback)
    client.onDownloadComplete(callback2)
    client.onDownloadError(callback3)
    client.onResullt(onresult)
    await client.start_ws()
    pass


def main():
    loop = asyncio.get_event_loop()
    # loop.call_soon_threadsafe()
    # asyncio.run_coroutine_threadsafe()
    # tasks = [loop.create_task(get_trigger()),loop.create_task(get_client())]  # , loop.create_task(get_client())]
    tasks = [loop.create_task(get_trigger())]
    loop.run_until_complete(asyncio.wait(tasks))


if __name__ == "__main__":
    main()
