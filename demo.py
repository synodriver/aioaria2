# -*- coding: utf-8 -*-
import asyncio
import aioaria2
import threading
from queue import Queue

q = asyncio.Queue()
failed_gid = asyncio.Queue()
failed_url = Queue()


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


def onresult(future):
    data = future.result()["result"]
    url = data[0]["uri"]
    failed_url.put_nowait(url)


async def get_trigger():
    client = await aioaria2.Aria2WebsocketTrigger.create("id", "http://192.168.0.107:6800/jsonrpc", "batch",
                                                         token="admin", queue=q)

    client.onDownloadStart(callback)
    client.onDownloadComplete(callback2)
    client.onDownloadError(callback3)
    client.onResullt(onresult)
    await client.start_ws()


async def get_client():
    client = aioaria2.Aria2HttpClient("id", "http://192.168.0.107:6800/jsonrpc", "normal", token="admin", queue=q)
    # q.put_nowait("1")
    print("success init")
    # print(failed_gid._qsize())
    while True:
        gid=await failed_gid.get()
        print("取得gid:{0}".format(gid))
        data = await client.getFiles(gid)
        url = data[0]["uris"][0]["uri"]
        print("取得url:{0}".format(url))
        gid = await client.addUri([url])

        print("重新入队成功:{0}".format(gid))


def start_loop(loop: asyncio.AbstractEventLoop):
    asyncio.set_event_loop(loop)
    task = loop.create_task(get_trigger())
    loop.run_until_complete(task)


def main():
    loop = asyncio.get_event_loop()
    tasks = [loop.create_task(get_trigger()), loop.create_task(get_client())]
    loop.run_until_complete(asyncio.wait(tasks))
    # loop_thread = threading.Thread(target=start_loop, args=(asyncio.new_event_loop(),))
    # loop_thread.start()
    # task = loop.create_task(get_client())
    # loop.run_until_complete(task)


if __name__ == "__main__":
    main()

