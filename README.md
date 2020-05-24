提供aria2异步客户端的包
===

# 本模块提供与aria2异步通信的客户端与管理aria2进程的服务端

## 使用方法：
### 示例如下
```python
import aioaria2
import asyncio
from pprint import pprint
async def main():
    async with aioaria2.Aria2HttpClient("id", "http://192.168.0.107:6800/jsonrpc", "normal",
                                        token="admin") as client:
        pprint(await client.getVersion())
asyncio.run(main())
```
### client对象的相关方法见aria2手册 
```python
import aioaria2
import asyncio
from pprint import pprint
async def main():
    async with aioaria2.Aria2HttpClient("id", "http://192.168.0.107:6800/jsonrpc", "normal",
                                        token="admin") as client:
        pprint(await client.addUri(["http://www.demo.com"])) #即可下载
asyncio.run(main())
```
    运行该协程函数即可，方法对应aria2jsonrpc的方法
    对于服务端，每一个实例对应一个aria2进程
```python
import aioaria2
import asyncio
server=aioaria2.Aria2rpcServer(["path/aria2c.exe","--enable-rpc=true",
    "--rpc-listen-all=true","--rpc-secret=123"])
```
    即可启动一个aria2进程
[参考选项及设置](http://aria2.github.io/manual/en/html/)
### todolist
- [x] 异步http通信
- [x] 异步websocket通信
- [ ] 修复server类的bug
- [ ] 单元测试


[jsonrpc](https://xyne.archlinux.ca/projects/python3-aria2jsonrpc)
        本模块在其之上构建，提供了异步支持，以级websocket支持
####Notice
#####在最终v1.0发布之前不建议直接setup安装

![title](https://konachan.com/sample/c7f565c0cd96e58908bc852dd754f61a/Konachan.com%20-%20302356%20sample.jpg)