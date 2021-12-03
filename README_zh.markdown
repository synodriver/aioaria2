# aioaria2

提供aria2异步客户端通信

[![pypi](https://img.shields.io/pypi/v/aioaria2.svg)](https://pypi.org/project/aioaria2/)
![python](https://img.shields.io/pypi/pyversions/aioaria2)
![implementation](https://img.shields.io/pypi/implementation/aioaria2)
![wheel](https://img.shields.io/pypi/wheel/aioaria2)
![license](https://img.shields.io/github/license/synodriver/aioaria2.svg)

## 提供与aria2异步通信的客户端与管理aria2进程的服务端

## 使用方法：

### 示例

```python
import asyncio
from pprint import pprint

import aioaria2


async def main():
    async with aioaria2.Aria2HttpClient("http://117.0.0.1:6800/jsonrpc",
                                        token="token") as client:
        pprint(await client.getVersion())


asyncio.run(main())
```

### 相关ip地址应该换成自己的

### client对象的相关方法见aria2手册

```python
# 示例http协议
import asyncio
from pprint import pprint

import aioaria2
import ujson


async def main():
    async with aioaria2.Aria2HttpClient("http://127.0.0.1:6800/jsonrpc",
                                        token="token",
                                        loads=ujson.loads,
                                        dumps=ujson.dumps) as client:
        pprint(await client.addUri(["http://www.demo.com"]))  # 即可下载


asyncio.run(main())
```

```python
# 示例websocket协议
import asyncio
from pprint import pprint

import aioaria2
import ujson


@aioaria2.run_sync
def on_download_complete(trigger, data):
    print(f"downlaod complete {data}")


async def main():
    client: aioaria2.Aria2WebsocketTrigger = await aioaria2.Aria2WebsocketTrigger.new("http://127.0.0.1:6800/jsonrpc",
                                                                                      token="token",
                                                                                      loads=ujson.loads,
                                                                                      dumps=ujson.dumps)
    client.onDownloadComplete(on_download_complete)
    pprint(await client.addUri(["http://www.demo.com"]))  # 即可下载


loop = asyncio.get_event_loop()
loop.create_task(main())
loop.run_forever()
```

- 运行该协程函数即可，方法对应aria2jsonrpc的方法。对于服务端，每一个实例对应一个aria2进程

```python
import aioaria2
import asyncio


async def main():
    server = aioaria2.AsyncAria2Server(r"aria2c.exe",
                                       r"--conf-path=aria2.conf", "--rpc-secret=admin", daemon=True)
    await server.start()
    await server.wait()


asyncio.run(main())
```

#### 即可启动一个aria2进程

[参考选项及设置](http://aria2.github.io/manual/en/html/)

### todolist

- [x] 异步http通信
- [x] 异步websocket通信
- [x] 修复server类的bug
- [x] 单元测试

本模块在[aria2jsonrpc](https://xyne.archlinux.ca/projects/python3-aria2jsonrpc)
之上构建，提供了异步支持，以级websocket支持

### windows用户应该加上以下设置

```
# 为了启动异步子进程管理
asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
asyncio.set_event_loop(asyncio.ProactorEventLoop())
```

    python3.8以后默认是ProactorEventLoop，因此可以不用修改

#### v1.2.0更新

新增Aria2WebsocketTrigger类，可以监听websocket消息, 使用on*方法注册自定义回调函数,既可以是同步也可以是异步的

如下

```
@trigger.onDownloadStart
async def onDownloadStart(trigger, future):
    print("下载开始{0}".format(future.result()))
```

#### v1.2.3更新

可以给一个事件注册多个回调,现在只能是协程函数,同步函数需要自行从utils.run_sync包装

```
@trigger.onDownloadStart
async def callback1(trigger, future):
    print("第一个回调{0}".format(future.result()))

@trigger.onDownloadStart
@run_sync
def callback2(trigger, future):
    print("第二个回调{0}".format(future.result()))
```

#### v1.3.0更新

*本版本大量修改了```Aria2WebsocketTrigger```类的方法,```Aria2HttpClient```保持不变*

* 回调直接接受```dict```参数而不再是```asyncio.Future```
* ```Aria2WebsocketTrigger```的相应方法获得了返回值，等效于http协议
* id现在需要传入一个可以调用的id工厂函数作为uuid使用,否则将使用默认的uuid生成器


```
@trigger.onDownloadStart
async def callback1(trigger, data:dict):
    print("第一个回调{0}".format(data))

@trigger.onDownloadStart
@run_sync
def callback2(trigger, data:dict):
    print("第二个回调{0}".format(data))
```

### v1.3.1更新

* 可以使用自定义的json序列化函数,使用关键字参数```loads=``` ```dumps=```传入构造方法

### v1.3.2更新

* 修复了ws_connect中，如果抛异常则连接不会关闭的问题
* ```Aria2WebsocketTrigger``` 有了一个别名 ```Aria2WebsocketClient```

### v1.3.3

* 修改了笔误造成的问题

### v1.3.4rc1

* 简单处理websocket掉线
* 修复ping aria2时造成的aria2不讲武德不回复pong的问题

### v1.3.4

* 异步id工厂函数
* 取消websocketclient注册的回调 ```unregister```
* ```run_sync``` 加入contextvars支持


![title](https://konachan.com/sample/c7f565c0cd96e58908bc852dd754f61a/Konachan.com%20-%20302356%20sample.jpg)