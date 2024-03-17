import asyncio
import unittest
from pprint import pprint

import ujson

import aioaria2


class TestHTTP(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.client = aioaria2.Aria2HttpClient(
            "http://aria.blackjoe.art:2082/jsonrpc", token="a489451594cda0792df1"
        )

    async def test_addUri(self):
        gid = await self.client.addUri(["https://www.google.com"])
        self.assertTrue(isinstance(gid, str))

    async def test_getVersion(self):
        data = await self.client.getVersion()
        self.assertTrue(isinstance(data, dict))

    async def asyncTearDown(self) -> None:
        await self.client.close()


class TestWebsocket(unittest.IsolatedAsyncioTestCase):
    onDownloadStart1 = None
    onDownloadStart2 = None
    onDownloadComplete1 = None
    onDownloadComplete2 = None

    async def asyncSetUp(self) -> None:
        # self.client = aioaria2.Aria2HttpClient("test", "http://aria.blackjoe.art:2082/jsonrpc",
        #                                        token="a489451594cda0792df1")
        self.trigger = await aioaria2.Aria2WebsocketTrigger.new(
            "http://aria.blackjoe.art:2082/jsonrpc",
            token="a489451594cda0792df1",
            loads=ujson.loads,
            dumps=ujson.dumps,
        )

        # asyncio.get_running_loop().create_task(self.trigger.listen())
        @self.trigger.onDownloadStart
        async def handeler1(trigger, data):
            print("我是1号回调,我收到了消息")
            self.__class__.onDownloadStart1 = data

        @self.trigger.onDownloadStart
        @aioaria2.run_sync
        def handeler2(trigger, data):
            print("我是2号回调,我收到了消息")
            self.__class__.onDownloadStart2 = data

        @self.trigger.onDownloadComplete
        async def handeler3(trigger, data):
            print("我是3号回调,我收到了消息")
            self.__class__.onDownloadComplete1 = data

        @self.trigger.onDownloadComplete
        @aioaria2.run_sync
        def handeler4(trigger, data):
            print("我是4号回调,我收到了消息")
            self.__class__.onDownloadComplete2 = data

        await asyncio.sleep(10)

    async def test_connect(self):
        data = await self.trigger.getVersion()
        pprint(data)
        print(self.trigger.functions)

        self.assertTrue(isinstance(data, dict))
        self.assertTrue(
            len(self.trigger.functions["aria2.onDownloadStart"]) == 2,
            len(self.trigger.functions["aria2.onDownloadStart"]),
        )
        self.assertTrue(
            len(self.trigger.functions["aria2.onDownloadComplete"]) == 2,
            len(self.trigger.functions["aria2.onDownloadComplete"]),
        )

    async def test_onDownloadStart_and_Stop(self):
        data = await self.trigger.addUri(["https://www.baidu.com"])
        pprint(data)
        self.assertTrue(isinstance(data, str), data)
        while True:
            if self.onDownloadComplete1 is not None:
                self.assertEqual(
                    self.onDownloadStart1["method"],
                    "aria2.onDownloadStart",
                    "回调断言失败,期待{0} 接收到了{1}".format(
                        "aria2.onDownloadStart", self.onDownloadStart1["method"]
                    ),
                )
                self.assertEqual(
                    self.onDownloadStart2["method"],
                    "aria2.onDownloadStart",
                    "回调断言失败,期待{0} 接收到了{1}".format(
                        "aria2.onDownloadStart", self.onDownloadStart1["method"]
                    ),
                )
                break
            await asyncio.sleep(1)
        while True:
            if self.onDownloadComplete1 is not None:
                self.assertEqual(
                    self.onDownloadComplete1["method"],
                    "aria2.onDownloadComplete",
                    "回调断言失败,期待{0} 接收到了{1}".format(
                        "aria2.onDownloadComplete", self.onDownloadComplete1["method"]
                    ),
                )
                self.assertEqual(
                    self.onDownloadComplete2["method"],
                    "aria2.onDownloadComplete",
                    "回调断言失败,期待{0} 接收到了{1}".format(
                        "aria2.onDownloadComplete", self.onDownloadComplete2["method"]
                    ),
                )
                break
            await asyncio.sleep(1)

    async def asyncTearDown(self) -> None:
        await self.trigger.close()


if __name__ == "__main__":
    unittest.main()
