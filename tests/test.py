import unittest
import asyncio
from pprint import pprint
import aioaria2


class TestWebsocket(unittest.IsolatedAsyncioTestCase):
    onDownloadStart1 = None
    onDownloadStart2 = None
    onDownloadStop1 = None
    onDownloadStop2 = None

    async def asyncSetUp(self) -> None:
        # self.client = aioaria2.Aria2HttpClient("test", "http://aria.blackjoe.art:2082/jsonrpc",
        #                                        token="a489451594cda0792df1")
        self.trigger = await aioaria2.Aria2WebsocketTrigger.new("http://aria.blackjoe.art:2082/jsonrpc",
                                                                token="a489451594cda0792df1")

        # asyncio.get_running_loop().create_task(self.trigger.listen())

        await asyncio.sleep(10)

    async def test_connect(self):
        data = await self.trigger.getVersion()
        pprint(data)
        print(self.trigger.functions)

        self.assertTrue(isinstance(data, dict))

    async def test_onDownloadStart_and_Stop(self):
        @self.trigger.onDownloadStart
        async def handeler(trigger, data):
            print("我是1号回调,我收到了消息")
            self.__class__.onDownloadStart1 = data

        @self.trigger.onDownloadStart
        @aioaria2.run_sync
        def handeler(trigger, data):
            print("我是2号回调,我收到了消息")
            self.__class__.onDownloadStart2 = data

        @self.trigger.onDownloadStop
        async def handeler(trigger, data):
            print("我是3号回调,我收到了消息")
            self.__class__.onDownloadStop1 = data

        @self.trigger.onDownloadStop
        @aioaria2.run_sync
        def handeler(trigger, data):
            print("我是4号回调,我收到了消息")
            self.__class__.onDownloadStop2 = data


        data = await self.trigger.addUri(["https://www.baidu.com"])
        pprint(data)
        self.assertTrue(isinstance(data, str), data)

        self.assertEqual(self.onDownloadStart1["method"], "aria2.onDownloadStart",
                         "回调断言失败,期待{0} 接收到了{1}".format("aria2.onDownloadStart", self.onDownloadStart1["method"]))
        self.assertEqual(self.onDownloadStart2["method"], "aria2.onDownloadStart",
                         "回调断言失败,期待{0} 接收到了{1}".format("aria2.onDownloadStart", self.onDownloadStart1["method"]))
        while True:
            if self.onDownloadStop1 is not None:
                self.assertEqual(self.onDownloadStop1["method"], "aria2.onDownloadStop",
                                 "回调断言失败,期待{0} 接收到了{1}".format("aria2.onDownloadSStop", self.onDownloadStop1["method"]))
                self.assertEqual(self.onDownloadStop2["method"], "aria2.onDownloadStop",
                                 "回调断言失败,期待{0} 接收到了{1}".format("aria2.onDownloadSStop", self.onDownloadStop2["method"]))
                print(self.onDownloadStop2)
                break
            await asyncio.sleep(1)

    async def asyncTearDown(self) -> None:
        await self.trigger.close()


if __name__ == '__main__':
    unittest.main()
