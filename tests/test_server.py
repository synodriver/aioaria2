# -*- coding: utf-8 -*-
import asyncio
import sys

import aioaria2


async def main():
    server = aioaria2.AsyncAria2Server(
        r"128aria2c.exe", r"--conf-path=aria2.conf", "--rpc-secret=admin", daemon=True
    )
    await server.start()
    await server.wait()
    print("不等他")


if __name__ == "__main__":
    # if sys.platform == "win32":
    #     # 想不到吧，官方文档说要在windows使用asyncio.create_subprocess_shell，只说了修改event_loop_policy，
    #     # 没想到还要修改默认的事件循环，哈哈
    #     # windows就是矫情
    #     asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    #     asyncio.set_event_loop(asyncio.ProactorEventLoop())
    # asyncio.run(main())
    # main()
    def a(c=1, d=2):
        print(c, d)

    a(None)
