# -*- coding: utf-8 -*-
# infinite retry
import asyncio
from pprint import pprint

import aioaria2
import ujson

HOST = "http://127.0.0.1:6800/jsonrpc"


async def on_download_error(trigger: aioaria2.Aria2WebsocketTrigger, data: dict):
    print("Oops! It seems sth wrong with your network! Never mind, try again")
    gid: str = data["params"][0]["gid"]
    uri: str = (await trigger.getFiles(gid))[0]["uris"][0]["uri"]
    await trigger.addUri([uri])


async def on_download_complete(trigger: aioaria2.Aria2WebsocketTrigger, data: dict):
    print("Congratulations! You have successfully across the great wall")


async def main():
    client: aioaria2.Aria2WebsocketTrigger = await aioaria2.Aria2WebsocketTrigger.new("http://127.0.0.1:6800/jsonrpc",
                                                                                      token="token",
                                                                                      loads=ujson.loads,
                                                                                      dumps=ujson.dumps)
    client.onDownloadError(on_download_error)
    client.onDownloadComplete(on_download_complete)
    pprint(await client.addUri(["http://www.google.com"]))  #


loop = asyncio.get_event_loop()
loop.create_task(main())
loop.run_forever()
