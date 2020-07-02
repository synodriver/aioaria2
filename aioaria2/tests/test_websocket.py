# -*- coding: utf-8 -*-
import aioaria2
import asyncio
from pprint import pprint

q = asyncio.Queue()

failed_q = asyncio.Queue()

HOST = "http://192.168.0.107:6800/jsonrpc"


async def callback(future):
    await asyncio.sleep(0)
    print("下载开始{0}".format(future.result()))


async def callback2(future):
    print("下载完成{0}".format(future.result()))


async def callback3(future):
    data = future.result()
    print("下载中断{0}".format(data))


async def onresult(future):
    print("结果")
    pprint(future.result())


async def get_client():
    async with aioaria2.Aria2HttpClient("id", HOST, "normal",
                                        token="admin", queue=q) as client:
        pprint(await client.addUri(["http://odrive.aptx.xin/%E5%8A%A8%E7%94%BB/2004/200445.zip"]))
        # pprint(await client.getFiles("6b25a38d701dee4c"))

    pass


async def get_trigger():
    client = await aioaria2.Aria2WebsocketTrigger.create("id",
                                                         HOST,
                                                         token="admin",
                                                         queue=q)

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
    tasks = [loop.create_task(get_trigger())]#, loop.create_task(get_client())]
    loop.run_until_complete(asyncio.wait(tasks))


if __name__ == "__main__":
    main()
