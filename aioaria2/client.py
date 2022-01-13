# -*- coding: utf-8 -*-
"""
本模块负责与aria2 json rpc通信

参数参考 http://aria2.github.io/manual/en/html/aria2c.html#rpc-interface
"""
import asyncio
from collections import defaultdict
from inspect import stack
from typing import Any, Optional, Union, List, Iterable, Dict, DefaultDict, AsyncGenerator, NoReturn
import warnings

import aiohttp
from typing_extensions import Literal

from aioaria2.exceptions import Aria2rpcException
from aioaria2.utils import (add_options_and_position,
                            DEFAULT_JSON_DECODER,
                            DEFAULT_JSON_ENCODER,
                            b64encode_file,
                            get_status,
                            ResultStore)
from aioaria2.typing import CallBack, IdFactory


class _Aria2BaseClient:
    """
    与jsonrpc通信的接口
    """

    def __init__(self,
                 url: str,
                 identity: Optional[IdFactory] = None,
                 mode: Literal['normal', 'batch', 'format'] = 'normal',
                 token: str = None,
                 queue: asyncio.Queue = None):
        """
            :param identity: 操作rpc接口的id 生成他的工厂函数
            :param url: rpc服务器地址
            :param mode:
                normal - 立即处理请求
                batch - 请求加入队列，由process_queue方法处理
                format - 返回rpc请求json结构
            :param token: rpc服务器密码 (用 `--rpc-secret`设置)
        """
        if queue is None:
            self.queue: asyncio.Queue = asyncio.Queue()
        else:
            self.queue = queue
        self.identity = identity or ResultStore.get_id
        self.url = url
        self.mode = mode
        self.token = token

    async def jsonrpc(self, method: str, params: Optional[List[Any]] = None, prefix: str = 'aria2.') -> Union[
        Dict[str, Any], List[Any], str, None]:
        """
        组装json数据
        :param method: 请求方法
        :param params: 参数
        :param prefix: 请求的头部
        :return: 响应结果
        """
        if not params:
            params = []

        if self.token is not None:
            token_str = 'token:{}'.format(self.token)
            if method == 'multicall':
                for param in params[0]:
                    try:
                        param['params'].insert(0, token_str)
                    except KeyError:
                        param['params'] = [token_str]
            else:
                params.insert(0, token_str)

        identity = self.identity()
        if asyncio.iscoroutine(identity):
            identity = await identity
        req_obj = {
            'jsonrpc': '2.0',
            'id': identity,
            'method': prefix + method,
            'params': params,
        }
        if self.mode == 'batch':
            await self.queue.put(req_obj)
            return None
        if self.mode == 'format':
            return req_obj
        return await self.send_request(req_obj)

    async def send_request(self, req_obj: Dict[str, Any]) -> Union[Dict[str, Any], Any]:
        raise NotImplementedError

    async def process_queue(self) -> List:
        """
        处理队列请求
        """
        # req_obj = self.queue
        # self.queue = []
        # return await self.send_request(req_obj)
        req_objs = []
        while not self.queue.empty():
            req_objs.append(await self.queue.get())

        results = await asyncio.gather(*map(self.send_request, req_objs))
        return results

    async def addUri(self, uris: List[str], options: Dict[str, Any] = None, position: int = None) -> str:
        """
        添加新的任务到下载队列
        :param uris: 要添加的链接 务必是list HTTP/FTP/SFTP/BitTorrent URIs (strings)
        :param options:附加参数
        :param position:在下载队列中的位置
        :return:包含结果的json
        {"result":"2089b05ecca3d829"}
        """
        params = [uris]
        params = add_options_and_position(params, options, position)
        return await self.jsonrpc('addUri', params)  # type: ignore

    async def addTorrent(self, torrent: str, uris: List[str] = None, options: Dict[str, Any] = None,
                         position: int = None) -> Union[Dict[str, Any], Any]:
        """
        下载种子
        :param torrent: base64编码的种子文件 base64.b64encode(open("xxx.torrent","rb").read())
        :param uris: uri用于播种 对于单个文件，URI可以是指向资源的完整URI;如果URI以/结尾，则添加到torrent文件。
            对于多文件的torrent，则会在torrent文件中添加名称和路径以生成每个文件的URI。
        :param options:参数字典
        :param position:在下载队列中的位置
        :return:包含结果的json
        {"result":"2089b05ecca3d829"}
        """
        params = [torrent]
        if uris:
            params.append(uris)  # type: ignore
        params = add_options_and_position(params, options, position)
        return await self.jsonrpc('addTorrent', params)

    async def addMetalink(self, metalink: List, options: Dict[str, Any] = None, position: int = None) -> Union[
        Dict[str, Any], Any]:
        """
        此方法通过上载一个来添加一个Metalink下载 metalink是一个用base64编码的字符串，其中包含“.metalink”文件。
        :param metalink: base64编码的字符串 base64.b64encode(open('file.meta4',"rb").read())
        :param options:参数字典
        :param position:在下载队列中的位置
        :return:包含结果的json
        {"result":"2089b05ecca3d829"}
        """
        params = [metalink]
        params = add_options_and_position(params, options, position)
        return await self.jsonrpc('addMetalink', params)

    async def remove(self, gid: str) -> Union[Dict[str, Any], Any]:
        """
        正在下载的停止下载 停止的删除状态
        :param gid: GID(或GID)是管理每个下载的密钥。每个下载将被分配一个唯一的GID。GID在aria2中存储为64位二进制值。
        :return:包含结果的json
        {"result":"2089b05ecca3d829"}
        """
        params = [gid]
        return await self.jsonrpc('remove', params)

    async def forceRemove(self, gid: str) -> Union[Dict[str, Any], Any]:
        """
        此方法删除由gid表示的下载。这个方法的行为就像aria2.remove(),但是会立即生效，而不执行任何需要时间的操作，
        例如联系BitTorrent跟踪器先取消下载。
        :param gid: GID(或GID)是管理每个下载的密钥。每个下载将被分配一个唯一的GID。GID在aria2中存储为64位二进制值。
        :return:包含结果的json
        """
        params = [gid]
        return await self.jsonrpc('forceRemove', params)

    async def pause(self, gid: str) -> Union[Dict[str, Any], Any]:
        """
        此方法暂停由gid(字符串)表示的下载。暂停下载的状态变为暂停。如果下载是活动的，下载将放在等待队列的前面。
        当状态暂停时，下载不会启动。要将状态更改为等待，请使用aria2.unpause()方法
        :param gid: GID(或GID)是管理每个下载的密钥。每个下载将被分配一个唯一的GID。GID在aria2中存储为64位二进制值。
        :return:包含结果的json
        """
        params = [gid]
        return await self.jsonrpc('pause', params)

    async def pauseAll(self) -> Union[Dict[str, Any], Any]:
        """
        这个方法相当于为每个活动/等待的下载调用aria2.pause()。这个方法返回OK。
        :return:包含结果的json
        """
        return await self.jsonrpc('pauseAll')

    async def forcePause(self, gid) -> Union[Dict[str, Any], Any]:
        """
        此方法暂停由gid表示的下载。这个方法的行为就像aria2.pause()，只是这个方法暂停下载，不执行任何需要时间的操作，
        比如联系BitTorrent tracker先取消下载。
        :param gid:GID(或GID)是管理每个下载的密钥。每个下载将被分配一个唯一的GID。GID在aria2中存储为64位二进制值。
        :return:包含结果的json
        """
        params = [gid]
        return await self.jsonrpc('forcePause', params)

    async def forcePauseAll(self) -> Union[Dict[str, Any], Any]:
        """
        这个方法相当于对每个活动/等待的下载调用aria2.forcePause()。这个方法返回OK
        :return:包含结果的json
        """
        return await self.jsonrpc('forcePauseAll')

    async def unpause(self, gid: str) -> Union[Dict[str, Any], Any]:
        """
        此方法将由gid (string)表示的下载状态从暂停更改为等待，从而使下载符合重新启动的条件。此方法返回未暂停下载的GID。
        :param gid:GID(或GID)是管理每个下载的密钥。每个下载将被分配一个唯一的GID。GID在aria2中存储为64位二进制值。
        :return:包含结果的json
        """
        params = [gid]
        return await self.jsonrpc('unpause', params)

    async def unpauseAll(self) -> Union[Dict[str, Any], Any]:
        """
        这个方法相当于对每个暂停的下载调用aria2.unpause()。这个方法返回OK
        :return:包含结果的json
        """
        return await self.jsonrpc('unpauseAll')

    async def tellStatus(self, gid: str, keys: List[str] = None) -> Union[Dict[str, Any], Any]:
        """
        此方法返回由gid(字符串)表示的下载进度
        :param gid: GID(或GID)是管理每个下载的密钥。每个下载将被分配一个唯一的GID。GID在aria2中存储为64位二进制值。
        :param keys:如果指定，则返回结果只包含keys数组中的键。如果键keys空或省略，则返回结果包含所有键。
            status:
                active: 当前下载/做种
                waiting: 等待队列
                paused: 当前暂停的下载
                error: 出错的下载
                complete: 停止和完成的下载
                removed: 用户移除的下载
            totalLength: 文件总长度(字节)
            completedLength: 已经下载的长度(字节)
            uploadLength: 已经上传的长度(字节)
            bitfield:下载进度的十六进制表示。最高位对应于下标0处的块。任何为1的位表示已加载的块，而为0位表示尚未加载和/或缺失的块。
                    任何最后的溢出位都被置为0。当下载尚未启动时，此key将不包含在响应中。
            downloadSpeed: 下载速度 单位bytes/sec
            uploadSpeed:  上传速度 单位bytes/sec
            infoHash: hash值 仅针对bt下载
            numSeeders: 连接的peer数，仅针对bt下载
            seeder: 如果本机在做种true 否则false 仅针对bt下载
            pieceLength: 分片长度 单位byte
            numPieces: 分片数量
            connections: aria2连接的种子/服务器数量
            errorCode: 错误代码 仅针对停止/完成的下载
            errorMessage: 与errorCode关联的错误信息
            followedBy: 下载结果的gid列表
            following: 此结果在followedBy中，是他的反向连接
            belongsTo: 父下载的GID。有些下载是另一个下载的一部分。例如，如果一个文件在一个Metalink有BitTorrent资源，
            下载的“.torrent“文件是父文件的一部分。如果此下载没有父节点，则此键将不会包含在响应中。
            dir: 保存文件的路径
            files: 返回文件列表。这个列表的元素与aria2.getFiles()方法中使用的结构相同
            bittorrent: 从种子文件检索到的信息结构，仅针对bt 包含以下
                announceList: 匿名uri的列表。如果种子文件包含announcement而没有announcer -list, announcement将被转换成announcer -list格式
                comment: 种子的评论 如果可以将使用utf-8
                creationDate: 创造时间轴。该值是自元年以来的整数，以秒为单位。
                mode: 文件模式。不是single就是multi
                info: 包含json数据的信息 包括以下key
                    name: 字典的名字。如果可以将使用utf-8
            verifiedLength: 文件被哈希检查时已验证的字节数。此键仅在对下载任务进行散列检查时存在。
            verifyIntegrityPending: 如果此下载任务正在队列中等待hash检查，则为true。此key仅在下载文件在队列中时存在。

        :return: json格式的结果
        {'bitfield': '0000000000',
             'completedLength': '901120',
             'connections': '1',
             'dir': '/downloads',
             'downloadSpeed': '15158',
             'files': [{'index': '1',
                         'length': '34896138',
                         'completedLength': '34896138',
                         'path': '/downloads/file',
                         'selected': 'true',
                         'uris': [{'status': 'used',
                                    'uri': 'http://example.org/file'}]}],
             'gid': '2089b05ecca3d829',
             'numPieces': '34',
             'pieceLength': '1048576',
             'status': 'active',
             'totalLength': '34896138',
             'uploadLength': '0',
             'uploadSpeed': '0'}

        :example:  await client.tellStatus(xxxxx,["status","downloadSpeed"])
        """
        params = [gid]
        if keys:
            params.append(keys)  # type: ignore
        return await self.jsonrpc('tellStatus', params)

    async def getUris(self, gid: str) -> Union[Dict[str, Any], Any]:
        """
        此方法返回由gid(字符串)表示的下载中使用的uri。响应是一个json，它包含以下键。值是字符串
        :param gid: GID(或GID)是管理每个下载的密钥。每个下载将被分配一个唯一的GID。GID在aria2中存储为64位二进制值。
        :return:json格式的结果
        [{'status': 'used',  如果url已经使用就是used ，还在队列中就是waiting
              'uri': 'http://example.org/file'},...]
        """
        params = [gid]
        return await self.jsonrpc('getUris', params)

    async def getFiles(self, gid: str) -> Union[Dict[str, Any], Any]:
        """
        返回下载文件列表
        :param gid: GID(或GID)是管理每个下载的密钥。每个下载将被分配一个唯一的GID。GID在aria2中存储为64位二进制值。
        :return:
         [{'index': '1',  件的索引，从1开始，与文件在多文件中出现的顺序相同
              'length': '34896138',  文件大小 byte
              'completedLength': '34896138',  此文件的完整长度(以字节为单位)。请注意，
                        completedLength的和可能小于aria2.tellStatus()方法返回的completedLength。
                      这是因为在aria2.getFiles()中completedLength只包含完成的片段。
                      另一方面，在aria2.tellStatus()中完成的长度也包括部分完成的片段。
              'path': '/downloads/file',   路径
              'selected': 'true',   如果此文件是由——select-file选项选择的，则为true。
              如果——select-file没有指定，或者这是单文件的torrent文件，或者根本不是torrent下载，那么这个值总是为真。否则错误。
              'uris': [{'status': 'used',  返回此文件的uri列表。元素类型与aria2.getUris()方法中使用的结构相同。
                         'uri': 'http://example.org/file'}]}]
        """
        params = [gid]
        return await self.jsonrpc('getFiles', params)

    async def getPeers(self, gid: str) -> Union[Dict[str, Any], Any]:
        """
        返回下载对象，仅适用于bt
        :param gid: GID(或GID)是管理每个下载的密钥。每个下载将被分配一个唯一的GID。GID在aria2中存储为64位二进制值。
        :return:
        [{'amChoking': 'true',
              'bitfield': 'ffffffffffffffffffffffffffffffffffffffff',
              'downloadSpeed': '10602',
              'ip': '10.0.0.9',
              'peerChoking': 'false',
              'peerId': 'aria2%2F1%2E10%2E5%2D%87%2A%EDz%2F%F7%E6',
              'port': '6881',
              'seeder': 'true',
              'uploadSpeed': '0'},
             {'amChoking': 'false',
              'bitfield': 'ffffeff0fffffffbfffffff9fffffcfff7f4ffff',
              'downloadSpeed': '8654',
              'ip': '10.0.0.30',
              'peerChoking': 'false',
              'peerId': 'bittorrent client758',
              'port': '37842',
              'seeder': 'false',
              'uploadSpeed': '6890'}]
        """
        params = [gid]
        return await self.jsonrpc('getPeers', params)

    async def getServers(self, gid: str) -> Union[Dict[str, Any], Any]:
        """
        此方法返回当前连接的HTTP(S)/FTP/SFTP服务器的下载，用gid(字符串)表示。响应是一个结构数组，包含以下key。值是字符串。
        :param gid:GID(或GID)是管理每个下载的密钥。每个下载将被分配一个唯一的GID。GID在aria2中存储为64位二进制值。
        :return:
        [{'index': '1',
              'servers': [{'currentUri': 'http://example.org/file',  # 正在使用的
                            'downloadSpeed': '10467',    # 下载速度(byte/sec)
                            'uri': 'http://example.org/file'}]}]}  #原url
        """
        params = [gid]
        return await self.jsonrpc('getServers', params)

    async def tellActive(self, keys: Optional[List[str]] = None) -> Union[Dict[str, Any], Any]:
        """
        此方法返回活动下载列表。响应是一个与aria2.tellStatus()方法返回的结构相同的数组。关于keys参数，请参考aria2.tellStatus()方法。
        :param keys: 如果指定，则返回结果只包含keys数组中的键。如果键keys空或省略，则返回结果包含所有键。
        :return:
        json格式的结果
        {'bitfield': '0000000000',
             'completedLength': '901120',
             'connections': '1',
             'dir': '/downloads',
             'downloadSpeed': '15158',
             'files': [{'index': '1',
                         'length': '34896138',
                         'completedLength': '34896138',
                         'path': '/downloads/file',
                         'selected': 'true',
                         'uris': [{'status': 'used',
                                    'uri': 'http://example.org/file'}]}],
             'gid': '2089b05ecca3d829',
             'numPieces': '34',
             'pieceLength': '1048576',
             'status': 'active',
             'totalLength': '34896138',
             'uploadLength': '0',
             'uploadSpeed': '0'}

        :example:  await client.tellActive(xxxxx,["status","downloadSpeed"])
        """
        if keys:
            params = [keys]
        else:
            params = None  # type: ignore
        return await self.jsonrpc('tellActive', params)

    async def tellWaiting(self, offset: int, num: int, keys: List[str] = None) -> Union[Dict[str, Any], Any]:
        """
        此方法返回等待下载的列表，包括暂停的下载。偏移量是一个整数，它指定等待在前面的下载的偏移量。
        num是一个整数，指定最大值。要返回的下载数量。关于keys参数，请参考aria2.tellStatus()方法。
        :param offset: 起始索引
        :param num: 数量
        :param keys: 同上
        :return: 同上
        """
        params = [offset, num]
        if keys:
            params.append(keys)  # type: ignore
        return await self.jsonrpc('tellWaiting', params)

    async def tellStopped(self, offset: int, num: int, keys: List[str] = None) -> Union[Dict[str, Any], Any]:
        """
        此方法返回停止下载的列表 关于keys参数，请参考aria2.tellStatus()方法。
        :param offset: 起始索引
        :param num: 数量
        :param keys: 同上
        :return: 同上
        """
        params = [offset, num]
        if keys:
            params.append(keys)  # type: ignore
        return await self.jsonrpc('tellStopped', params)

    async def changePosition(self, gid: str, pos: int, how: str) -> Union[Dict[str, Any], Any]:
        """
        此方法更改队列中由gid表示的下载位置。pos是一个整数。how是一个字符串。
        如果how是POS_SET，它将下载移动到相对于队列开头的位置。
        如果how是POS_CUR，它将下载移动到相对于当前位置的位置。
        如果how是POS_END，它将下载移动到相对于队列末尾的位置。
        如果目标位置小于0或超过队列的末尾，则将下载分别移动到队列的开头或末尾。响应是一个表示结果位置的整数。
        :param gid: GID(或GID)是管理每个下载的密钥。每个下载将被分配一个唯一的GID。GID在aria2中存储为64位二进制值。
        :param pos: 偏移量
        :param how: 方法
        :return：位置 int
        """
        params = [gid, pos, how]
        return await self.jsonrpc('changePosition', params)

    async def changeUri(self, gid: str, fileIndex: int, delUris: List[str], addUris: List[str], position: int = None) -> \
            Union[Dict[str, Any], Any]:
        """
        此方法从delUris中删除uri，并将addUris中的uri附加到以gid表示的下载中。
        delUris和addUris是字符串列表。下载可以包含多个文件，每个文件都附加了uri。
        fileIndex用于选择要删除/附加哪个文件。fileIndex从0开始。

        当位置被省略时，uri被附加到列表的后面。这个方法首先执行删除，然后执行添加。
        position是删除uri后的位置，而不是调用此方法时的位置。在删除URI时，如果下载中存在相同的URI，
        则对于deluri中的每个URI只删除一个URI。换句话说，如果有三个uri http://example.org/aria2，并且您希望将它们全部删除，
        则必须在delUris中指定(至少)3个http://example.org/aria2。这个方法返回一个包含两个整数的列表。第一个整数是删除uri的数目。
        第二个整数是添加的uri的数量。

        :param gid: GID(或GID)是管理每个下载的密钥。每个下载将被分配一个唯一的GID。GID在aria2中存储为64位二进制值。
        :param fileIndex:用于选择要删除/附加哪个文件。fileIndex从0开始。
        :param delUris: 要删除的
        :param addUris: 要添加的
        :param position: position用于指定在现有的等待URI列表中插入URI的位置 0开始
        :return:
         [0, 1]
        """
        params = [gid, fileIndex, delUris, addUris]
        if position:
            params.append(position)
        return await self.jsonrpc('changeUri', params)

    async def getOption(self, gid: str) -> Union[Dict[str, Any], Any]:
        """
        此方法返回由gid表示的下载选项。
        注意，此方法不会返回没有默认值,也没有在配置文件或RPC方法的命令行上设置这些的选项
        :param gid: GID(或GID)是管理每个下载的密钥。每个下载将被分配一个唯一的GID。GID在aria2中存储为64位二进制值。
        :return:
        {'allow-overwrite': 'false',
             'allow-piece-length-change': 'false',
             'always-resume': 'true',
             'async-dns': 'true',
        """
        params = [gid]
        return await self.jsonrpc('getOption', params)

    async def changeOption(self, gid: str, options: Dict[str, Any]) -> Literal["OK"]:
        """
        此方法动态地更改由gid (string)表示的下载选项。options是一个字典。输入文件小节中列出的选项是可用的，但以下选项除外:
            dry-run
            metalink-base-uri
            parameterized-uri
            pause
            piece-length
            rpc-save-upload-metadata
        除了以下选项外，更改活动下载的其他选项将使其重新启动(重新启动本身由aria2管理，不需要用户干预):
            bt-max-peers
            bt-request-peer-speed-limit
            bt-remove-unselected-file
            force-save
            max-download-limit
            max-upload-limit
        此方法返回OK表示成功。
        :param gid: GID(或GID)是管理每个下载的密钥。每个下载将被分配一个唯一的GID。GID在aria2中存储为64位二进制值。
        :param options:
        :return:
        "OK"
        """
        params = [gid, options]
        return await self.jsonrpc('changeOption', params)  # type: ignore

    async def getGlobalOption(self) -> Union[Dict[str, Any], Any]:
        """
        此方法返回全局选项。响应是一个结构体。它的键是选项的名称。值是字符串。
        注意，此方法不会返回没有默认值的选项，也不会在配置文件或RPC方法的命令行上设置这些选项。
        因为全局选项用作新添加下载选项的模板，所以响应包含aria2.getOption()方法返回的键。
        :return:
        """
        return await self.jsonrpc('getGlobalOption')

    async def changeGlobalOption(self, options: Dict[str, Any]) -> Union[Dict[str, Any], Any]:
        """
        此方法动态更改全局选项。options是一个字典。以下是可供选择的方案:
            bt-max-open-files
            download-result
            keep-unfinished-download-result
            log
            log-level
            max-concurrent-downloads
            max-download-result
            max-overall-download-limit
            max-overall-upload-limit
            optimize-concurrent-downloads
            save-cookies
            save-session
            server-stat-of
        :param options: 参数字典
        :return:  "OK"
        """
        params = [options]
        return await self.jsonrpc('changeGlobalOption', params)

    async def getGlobalStat(self) -> Dict[str, str]:
        """
        此方法返回全局统计信息，如总下载和上传速度。响应是一个字典，包含以下键。值是字符串
        :return:
        {'downloadSpeed': '21846',
             'numActive': '2',  #活动下载数
             'numStopped': '0',  #  当前会话中停止的下载数量。以 --max-download-result 选项为上限
             'numWaiting': '0',  # 等待下载数
             'uploadSpeed': '0'}
        """
        return await self.jsonrpc('getGlobalStat')  # type: ignore

    async def purgeDownloadResult(self) -> Literal["OK"]:
        """
        此方法将已完成/错误/删除的下载清除到空闲内存。这个方法返回OK。
        :return: "OK"
        """
        return await self.jsonrpc('purgeDownloadResult')  # type: ignore

    async def removeDownloadResult(self, gid: str) -> Literal["OK"]:
        """
        此方法从内存中删除由gid表示的已完成/错误/已删除的下载。此方法返回OK表示成功。
        :param gid: GID(或GID)是管理每个下载的密钥。每个下载将被分配一个唯一的GID。GID在aria2中存储为64位二进制值
        :return: "OK"
        """
        params = [gid]
        return await self.jsonrpc('removeDownloadResult', params)  # type: ignore

    async def getVersion(self) -> Dict[str, str]:
        """
        此方法返回aria2的版本和启用的特性列表
        :return:一个字典，包含以下键
            version: aria2的版本
            enabledFeatures: 启用功能的列表。每个特性都以字符串的形式给出
        """
        return await self.jsonrpc('getVersion')  # type: ignore

    async def getSessionInfo(self) -> Dict[str, str]:
        """
        返回会话信息
        :return:字典，包含以下键
            sessionId: 每次调用aria2时生成的会话id
        """
        return await self.jsonrpc('getSessionInfo')  # type: ignore

    async def shutdown(self) -> Literal["OK"]:
        """
        关闭aria2
        :return: "OK"
        """
        return await self.jsonrpc('shutdown')  # type: ignore

    async def forceShutdown(self) -> Literal["OK"]:
        """
        该方法关闭了aria2()。该方法的行为像aria2.shutdown而没有执行任何需要时间的操作，比如联系BitTorrent跟踪器先注销下载。
        :return:"OK"
        """
        return await self.jsonrpc('forceShutdown')  # type: ignore

    async def saveSession(self) -> Literal["OK"]:
        """
        此方法将当前会话保存到由——save-session选项指定的文件中。
        :return:"OK"
        """
        return await self.jsonrpc('saveSession')  # type: ignore

    async def multicall(self, methods: List[Dict[str, Any]]) -> List[Any]:
        """
        此方法将多个方法调用封装在单个请求中
        :param methods: 字典数组。结构包含两个键:methodName和params。methodName是要调用的方法名，params是包含方法调用参数的数组。
            此方法返回一个响应数组。元素要么是一个包含方法调用返回值的单条目数组，要么是一个封装的方法调用失败时的fault元素结构。
            example: [{'methodName':'aria2.addUri',
                                  'params':[['http://example.org']]},
                                {'methodName':'aria2.addTorrent',
                                  'params':[base64.b64encode(open('file.torrent').read())]}]
        :return:
        """
        return await self.jsonrpc('multicall', [methods], prefix='system.')  # type: ignore

    async def listMethods(self) -> List[str]:
        """
        此方法在字符串数组中返回所有可用的RPC方法。与其他方法不同，此方法不需要秘密令牌。这是安全的，因为这个方法只返回可用的方法名。
        :return:
        """
        return await self.jsonrpc('listMethods', prefix='system.')  # type: ignore

    async def listNotifications(self) -> List[str]:
        """
        此方法以字符串数组的形式返回所有可用的RPC通知。与其他方法不同，此方法不需要秘密令牌。
        这是安全的，因为这个方法只返回可用的通知名称。
        :return:
        """
        return await self.jsonrpc('listNotifications', prefix='system.')  # type: ignore

    # ----------------------以下是进一步抽象的高级方法----------------------------

    async def add_torrent(self, path: str, uris: List[str] = None, options: Dict[str, Any] = None,
                          position: int = None) -> Union[Dict[str, Any], Any]:
        """
        直接添加种子路径
        :param path: 文件路径
        :param uris:  参考addTorrent方法
        :param options: 参考addTorrent方法
        :param position: 参考addTorrent方法
        :return:包含结果的json   gid
        """
        torrent = await b64encode_file(path)
        return await self.addTorrent(torrent, uris, options, position)

    async def add_metalink(self, path, options: Dict[str, Any] = None, position: int = None) -> Union[
        Dict[str, Any], Any]:
        """
        直接添加metalink路径
        :param path:  文件路径
        :param options:  参考addMetalink方法
        :param position: 参考addMetalink方法
        :return:
        """
        metalink = await b64encode_file(path)
        return await self.addMetalink(metalink, options, position)  # type: ignore

    async def get_status(self, gid: str) -> Dict[str, str]:
        """
        取一个gid的状态
        :param gid:
        :return:
        """
        response = await self.tellStatus(gid, ['status'])
        return get_status(response)

    async def get_statuses(self, gids: Iterable) -> AsyncGenerator[
        Literal["active", "waiting", "paused", "error", "complete", "removed", "error"], None]:
        """
        取得每个gid的状态 是一个异步生成器
        :param gids:
        :return:
        """
        methods = [
            {
                'methodName': 'aria2.tellStatus',
                'params': [gid, ['gid', 'status']]
            }
            for gid in gids
        ]
        results = await self.multicall(methods)
        if results:
            status = dict((r[0]['gid'], r[0]['status']) for r in results)
            for gid in gids:
                try:
                    yield status[gid]
                except KeyError:
                    yield 'error'
        else:
            for gid in gids:
                yield 'error'

    async def close(self) -> None:
        await self.client_session.close()  # type: ignore


class Aria2HttpClient(_Aria2BaseClient):
    def __init__(self,
                 url: str,
                 identity: IdFactory = None,
                 mode: Literal['normal', 'batch', 'format'] = 'normal',
                 token: str = None,
                 queue=None,
                 client_session: aiohttp.ClientSession = None,
                 **kw):
        """
        :param identity: 操作rpc接口的id
        :param url: rpc服务器地址
        :param mode:
            normal - 立即处理请求
            batch - 请求加入队列，由process_queue方法处理
            format - 返回rpc请求json结构
        :param token: rpc服务器密码 (用 `--rpc-secret`设置)
        :param queue: 请求队列
        :param client_session: aiohttp的session
        :param kw: aiohttp.session.post的相关参数
            new in v1.3.1 loads: DEFAULT_JSON_DECODER   json.loads
            dumps json.dumps
        """
        super().__init__(url, identity, mode, token, queue)
        self.kw = kw
        self.loads = self.kw.pop("loads") if "loads" in self.kw else DEFAULT_JSON_DECODER  # json serialize
        self.dumps = self.kw.pop("dumps") if "dumps" in self.kw else DEFAULT_JSON_ENCODER
        self.client_session = client_session or aiohttp.ClientSession(json_serialize=self.dumps)  # aiohttp的会话

    async def send_request(self, req_obj: Dict[str, Any]) -> Union[Dict[str, Any], Any]:
        try:
            async with self.client_session.post(self.url, json=req_obj, **self.kw) as response:
                try:
                    data = await response.json(loads=self.loads)
                    return data["result"]
                # 没有result就是异常
                except KeyError:
                    raise Aria2rpcException('unexpected result: {}'.format(data))
        except aiohttp.ClientConnectionError as err:
            raise Aria2rpcException(str(err), connection_error=("Cannot connect" in str(err))) from err

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class Aria2WebsocketTrigger(_Aria2BaseClient):
    def __init__(self,
                 url: str,
                 identity: IdFactory = None,
                 mode: Literal['normal', 'batch', 'format'] = 'normal',
                 token=None,
                 queue: asyncio.Queue = None,
                 client_session: aiohttp.ClientSession = None,
                 reconnect_interval: int = 1,
                 **kw):
        """
            :param identity: 操作rpc接口的id 工厂函数
            :param url: rpc服务器地址
            :param mode:
                normal - 立即处理请求
                batch - 请求加入队列，由process_queue方法处理
                format - 返回rpc请求json结构
            :param token: rpc服务器密码 (用 `--rpc-secret`设置)
            :param queue: 请求队列
            :param kw: ws_connect()的相关参数
                new in v1.3.1 loads: DEFAULT_JSON_DECODER   json.loads
                dumps json.dumps
        """
        if (stack()[1].function) not in ("new", "eval_in_context"):
            warnings.warn(
                "do not init directly,use {0} instead".format("await " + self.__class__.__name__ + ".new"))
        super().__init__(url, identity, mode, token, queue)
        self.kw = kw
        self.loads = self.kw.pop("loads") if "loads" in self.kw else DEFAULT_JSON_DECODER  # json serialize
        self.dumps = self.kw.pop("dumps") if "dumps" in self.kw else DEFAULT_JSON_ENCODER
        self._client_session = client_session or aiohttp.ClientSession(
            json_serialize=self.dumps)  # type: aiohttp.ClientSession
        self.reconnect_interval = reconnect_interval
        self.functions: DefaultDict[str, List[CallBack]] = defaultdict(list)  # 存放各个notice的回调
        self._listen_task = None  # type: asyncio.Task

    @classmethod
    async def new(cls,
                  url: str,
                  identity: IdFactory = None,
                  mode: Literal['normal', 'batch', 'format'] = 'normal',
                  token: str = None,
                  queue: asyncio.Queue = None,
                  client_session: aiohttp.ClientSession = None,
                  reconnect_interval: int = 1,
                  **kw) -> "Aria2WebsocketTrigger":
        """
        真正创建实例
        :param queue: 继承下来的任务队列
        :param identity: 操作rpc接口的id
        :param url:  rpc服务器地址
        :param mode: 同上
        :param token: rpc服务器密码 (用 `--rpc-secret`设置)
        :param kw: ws_connect()的相关参数
        :return: 真正的实例
        """
        try:
            self = cls(url, identity, mode, token, queue, client_session, reconnect_interval, **kw)
            self.client_session = await self._client_session.ws_connect(self.url, **self.kw)
            self._listen_task = asyncio.create_task(self.listen())
            return self
        except aiohttp.ClientError as err:
            await self._client_session.close()
            raise Aria2rpcException(str(err), connection_error=("Cannot connect" in str(err))) from err

    async def send_request(self, req_obj: Dict[str, Any]) -> Union[Dict[str, Any], str, NoReturn]:  # type: ignore
        try:
            await self.client_session.send_json(req_obj, dumps=self.dumps)
            data = await ResultStore.fetch(req_obj["id"], self.kw.get("timeout", None) or 10.0)
            return data["result"]
        except KeyError:  # 'error':xxx
            raise Aria2rpcException('unexpected result: {}'.format(data))
        except Aria2rpcException as err:
            if not self.closed and "timeout" in err.msg:
                await asyncio.sleep(self.reconnect_interval)
                return await self.send_request(req_obj)
        except Exception as err:
            raise Aria2rpcException(str(err), connection_error=("Cannot connect" in str(err))) from err

    @property
    def closed(self) -> bool:
        return self.client_session.closed

    async def close(self) -> None:
        if self._listen_task and not self._listen_task.cancelled():
            self._listen_task.cancel()
        await super().close()
        await self._client_session.close()

    async def listen(self) -> None:
        """
        轮询返回数据
        """
        try:
            while not self.closed:
                try:
                    data = await self.client_session.receive_json(loads=self.loads)
                except TypeError:  # aria2抽了
                    continue
                if not data or not isinstance(data, dict):
                    continue
                asyncio.create_task(self.handle_event(data))
        except asyncio.CancelledError:
            pass

    async def handle_event(self, data: dict) -> None:
        """
        基础回调函数 当websocket服务器向客户端发送数据时候 此方法会自动调用
        :param data: receive_json包装对象 显然,与http不同,你得自己过滤出result字段,因为这个是完整的jsonrpc响应
        :return:
        """
        # 1.2.3更新:回调只能是异步函数了,同一种可以注册多个方法,同步的需要用run_sync包装
        if "result" in data or "error" in data:
            # 等效于post数据的结果
            ResultStore.add_result(data)
            # if "result" in self.functions:
            #     await asyncio.gather(*map(lambda x: x(self, future), self.functions["result"]))
        if "method" in data:
            # 来自aria2的notice信息
            method = data["method"]
            if method in self.functions:  # TODO 有鬼
                await asyncio.gather(*map(lambda x: x(self, data), self.functions[method]))

    def register(self, func: CallBack, type_: str) -> None:
        """
        注册响应websocket的事件
        :return:
        """
        self.functions[type_].append(func)

    def unregister(self, func: CallBack, type_: str) -> None:
        """
        取消注册响应websocket的事件
        :return:
        """
        try:
            self.functions[type_].remove(func)
        except ValueError:
            pass

    # ----------以下这些推荐作为装饰器使用---------------------

    def onDownloadStart(self, func: CallBack) -> CallBack:
        """
        注册回调事件
        func的第二个参数的task.result()型如{'jsonrpc': '2.0', 'method': 'aria2.onDownloadStart', 'params': [{'gid': '5de52dc4eba048ca'}]}
        :param func:
        :return:
        """
        self.register(func, "aria2.onDownloadStart")
        return func

    def onDownloadPause(self, func: CallBack) -> CallBack:
        """
        注册回调事件
        :param func:
        :return:
        """
        self.register(func, "aria2.onDownloadPause")
        return func

    def onDownloadStop(self, func: CallBack) -> CallBack:
        """
        注册回调事件
        :param func:
        :return:
        """
        self.register(func, "aria2.onDownloadStop")
        return func

    def onDownloadComplete(self, func: CallBack) -> CallBack:
        """
        注册回调事件
        :param func:
        :return:
        """
        self.register(func, "aria2.onDownloadComplete")
        return func

    def onDownloadError(self, func: CallBack) -> CallBack:
        """
        注册回调事件
        :param func:
        :return:
        """
        self.register(func, "aria2.onDownloadError")
        return func

    def onBtDownloadComplete(self, func: CallBack) -> CallBack:
        """
        注册回调事件
        :param func:
        :return:
        """
        self.register(func, "aria2.onBtDownloadComplete")
        return func

    async def __aenter__(self):
        if not hasattr(self, "client_session"):
            self.client_session: aiohttp.ClientWebSocketResponse = await self._client_session.ws_connect(self.url,
                                                                                                         **self.kw)
            self._listen_task = asyncio.create_task(self.listen())
            return self
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


Aria2WebsocketClient = Aria2WebsocketTrigger
