# -*- coding: utf-8 -*-
import aioaria2
import asyncio
from pprint import pprint

q = asyncio.Queue()

failed_q = asyncio.Queue()


def callback(future):
    print("下载开始{0}".format(future.result()))


def callback2(future):
    print("下载完成{0}".format(future.result()))


def callback3(future):
    data = future.result()
    print("下载中断{0}".format(data))

def onresult(future):
    print("结果")
    pprint(future.result())


async def get_client():
    async with aioaria2.Aria2HttpClient("id", "http://192.168.0.107:6800/jsonrpc", "normal",
                                        token="admin", queue=q) as client:
        pprint(await client.getGlobalOption())
        # pprint(await client.getFiles("6b25a38d701dee4c"))


    pass


async def get_trigger():
    client = await aioaria2.Aria2WebsocketTrigger.create("id",
                                                         "http://192.168.0.107:6800/jsonrpc",
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
    tasks = [loop.create_task(get_trigger()), loop.create_task(get_client())]
    loop.run_until_complete(asyncio.wait(tasks))


if __name__ == "__main__":
    main()
