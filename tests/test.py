import unittest
import asyncio

import aioaria2


class TestWebsocket(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.client = aioaria2.Aria2HttpClient("test", "http://synodriver.asuscomm.com:6800/jsonrpc",
                                               token="adman")
        self.trigger = await aioaria2.Aria2WebsocketTrigger.new("test", "http://synodriver.asuscomm.com:6800/jsonrpc",
                                                                token="adman")
        asyncio.get_running_loop().create_task(self.trigger.listen())

    async def test_onDownloadStart(self):
        await self.client.addUri(["https://www.google.com"])

        @self.trigger.onDownloadStart
        async def handeler(trigger, task):
            data = task.result()
            print("我是1号回调,我收到了消息")
            self.assertEqual(data["method"], "aria2.onDownloadStart",
                             "回调断言失败,期待{0} 接收到了{1}".format("aria2.onDownloadStart", data["method"]))

        @self.trigger.onDownloadStart
        async def handeler(trigger, task):
            data = task.result()
            print("我是2号回调,我收到了消息")
            self.assertEqual(data["method"], "aria2.onDownloadStart",
                             "回调断言失败,期待{0} 接收到了{1}".format("aria2.onDownloadStart", data["method"]))

    async def asyncTearDown(self) -> None:
        await self.trigger.close()
        await self.client.close()


if __name__ == '__main__':
    unittest.main()
