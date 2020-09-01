# -*- coding: utf-8 -*-
import asyncio
import aioaria2
import shlex
from queue import Queue

q = asyncio.Queue()
failed_gid = asyncio.Queue()
failed_url = Queue()
HOST = "http://127.0.0.1:6800/jsonrpc"


def callback(future):
    print("下载开始{0}".format(future.result()))


def callback2(future):
    print("下载完成{0}".format(future.result()))


def callback3(future):
    data = future.result()
    print("下载中断{0}".format(data))
    gid = data["params"][0]["gid"]
    print(gid)
    # print(id(failed_gid))
    failed_gid.put_nowait(gid)
    # print(failed_gid.queue)
    print("自动重新下载")


async def get_trigger():
    client = await aioaria2.Aria2WebsocketTrigger.create("id", HOST, "batch",
                                                         token="admin", queue=q)

    client.onDownloadStart(callback)
    client.onDownloadComplete(callback2)
    client.onDownloadError(callback3)
    await client.start_ws()


async def get_client():
    client = aioaria2.Aria2HttpClient("id", HOST, "normal", token="admin", queue=q)
    # q.put_nowait("1")
    print("success init")
    # print(failed_gid._qsize())
    while True:
        gid = await failed_gid.get()
        print("取得gid:{0}".format(gid))
        data = await client.getFiles(gid)
        url = data[0]["uris"][0]["uri"]
        print("取得url:{0}".format(url))
        gid = await client.addUri([url])

        print("重新入队成功:{0}".format(gid))


def main():
    loop = asyncio.get_event_loop()
    tasks = [loop.create_task(get_trigger()), loop.create_task(get_client())]
    loop.run_until_complete(asyncio.wait(tasks))


if __name__ == "__main__":
    main()
