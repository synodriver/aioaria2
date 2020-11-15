import unittest
import asyncio
from pprint import pprint
import aioaria2


class TestWebsocket(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        # self.client = aioaria2.Aria2HttpClient("test", "http://aria.blackjoe.art:2082/jsonrpc",
        #                                        token="a489451594cda0792df1")
        self.trigger = await aioaria2.Aria2WebsocketTrigger.new("http://aria.blackjoe.art:2082/jsonrpc",
                                                                token="a489451594cda0792df1")
        # asyncio.get_running_loop().create_task(self.trigger.listen())

    async def test_connect(self):
        data = await self.trigger.getVersion()
        pprint(data)

        self.assertTrue(isinstance(data, dict))

    async def test_onDownloadStart(self):
        data = await self.trigger.addUri(["https://www.google.com"])
        pprint(data)
        self.assertTrue(isinstance(data, str), data)

        @self.trigger.onDownloadStart
        async def handeler(trigger, task):
            data = task.result()
            print("我是1号回调,我收到了消息")
            self.assertEqual(data["method"], "aria2.onDownloadStart",
                             "回调断言失败,期待{0} 接收到了{1}".format("aria2.onDownloadStart", data["method"]))

        @self.trigger.onDownloadStart
        @aioaria2.run_sync
        def handeler(trigger, task):
            data = task.result()
            print("我是2号回调,我收到了消息")
            self.assertEqual(data["method"], "aria2.onDownloadStart",
                             "回调断言失败,期待{0} 接收到了{1}".format("aria2.onDownloadStart", data["method"]))

    async def test_onDownloadStop(self):
        @self.trigger.onDownloadStop
        async def handeler(trigger, task):
            data = task.result()
            print("我是3号回调,我收到了消息")
            self.assertEqual(data["method"], "aria2.onDownloadStop",
                             "回调断言失败,期待{0} 接收到了{1}".format("aria2.onDownloadSStop", data["method"]))

        @self.trigger.onDownloadStop
        @aioaria2.run_sync
        def handeler(trigger, task):
            data = task.result()
            print("我是4号回调,我收到了消息")
            self.assertEqual(data["method"], "aria2.onDownloadStop",
                             "回调断言失败,期待{0} 接收到了{1}".format("aria2.onDownloadStop", data["method"]))

    async def asyncTearDown(self) -> None:
        await self.trigger.close()


if __name__ == '__main__':
    unittest.main()
