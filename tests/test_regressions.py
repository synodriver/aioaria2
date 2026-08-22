# -*- coding: utf-8 -*-
import json
import unittest
from unittest.mock import AsyncMock, patch

from aioaria2.client import Aria2WebsocketClient, _Aria2BaseClient
from aioaria2.exceptions import Aria2rpcException
from aioaria2.utils import ResultStore
from aioaria2 import Aria2HttpClient


class _FakeResponse:
    def __init__(self, body, status=200):
        self.body = body
        self.status = status

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None

    async def text(self):
        return self.body


class _FakeHttpSession:
    closed = False

    def __init__(self, body, status=200):
        self.body = body
        self.status = status

    def post(self, *args, **kwargs):
        return _FakeResponse(self.body, self.status)

    async def close(self):
        self.closed = True


class _FakeClient(_Aria2BaseClient):
    async def send_request(self, req_obj):
        return None


class RegressionTests(unittest.IsolatedAsyncioTestCase):
    async def test_optional_position_slots(self):
        client = Aria2HttpClient("http://example.invalid", mode="format")
        try:
            self.assertEqual(
                (await client.addUri(["uri"], position=0))["params"],
                [["uri"], {}, 0],
            )
            self.assertEqual(
                (await client.addUri(["uri"], options={}, position=0))["params"],
                [["uri"], {}, 0],
            )
            self.assertEqual(
                (await client.addTorrent("torrent", position=1))["params"],
                ["torrent", [], {}, 1],
            )
            self.assertEqual(
                (await client.addMetalink("metalink", position=0))["params"],
                ["metalink", {}, 0],
            )
            self.assertEqual(
                (await client.changeUri("gid", 0, [], ["uri"], position=0))["params"],
                ["gid", 0, [], ["uri"], 0],
            )
        finally:
            await client.close()

    async def test_negative_positions_are_rejected(self):
        client = Aria2HttpClient("http://example.invalid", mode="format")
        try:
            with self.assertRaises(ValueError):
                await client.addUri(["uri"], position=-1)
            with self.assertRaises(ValueError):
                await client.addTorrent("torrent", position=-1)
            with self.assertRaises(ValueError):
                await client.addMetalink("metalink", position=-1)
            with self.assertRaises(ValueError):
                await client.changeUri("gid", 0, [], ["uri"], position=-1)
            with self.assertRaises(ValueError):
                await client.addUri(["uri"], position="not-a-position")
        finally:
            await client.close()

    async def test_get_statuses_materializes_iterable_and_handles_fault(self):
        client = _FakeClient("http://example.invalid")
        client.multicall = AsyncMock(
            return_value=[
                [{"gid": "a", "status": "active"}],
                {"faultCode": 1, "faultString": "not found"},
            ]
        )
        statuses = [status async for status in client.get_statuses(iter(["a", "b"]))]
        self.assertEqual(statuses, ["active", "error"])

    async def test_http_errors_are_library_exceptions(self):
        for body, status in (("not json", 200), (json.dumps({"error": "failed"}), 500)):
            session = _FakeHttpSession(body, status)
            client = Aria2HttpClient("http://example.invalid", client_session=session)
            with self.assertRaises(Aria2rpcException):
                await client.getVersion()
            await client.close()

    async def test_websocket_timeout_attempts_are_bounded(self):
        client = Aria2WebsocketClient.__new__(Aria2WebsocketClient)
        client.max_attempts = 3
        client.reconnect_interval = 0
        client.kw = {"timeout": 0.01}
        client.dumps = json.dumps
        client.client_session = type(
            "Socket", (), {"closed": False, "send_json": AsyncMock()}
        )()
        timeout = Aria2rpcException("jsonrpc over websocket call timeout")
        with patch.object(ResultStore, "fetch", new=AsyncMock(side_effect=timeout)):
            with self.assertRaises(Aria2rpcException):
                await client.send_request({"id": 1})
        self.assertEqual(client.client_session.send_json.await_count, 3)

    async def test_websocket_connect_cleanup_covers_value_error(self):
        session = _FakeHttpSession("")
        session.ws_connect = AsyncMock(side_effect=ValueError("bad websocket URL"))
        with self.assertRaises(Aria2rpcException):
            await Aria2WebsocketClient.new(
                "ws://example.invalid", client_session=session, max_attempts=1
            )
        self.assertTrue(session.closed)


if __name__ == "__main__":
    unittest.main()
