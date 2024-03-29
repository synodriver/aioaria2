# -*- coding: utf-8 -*-
# 示例下载豆瓣top250 movie的封面
import asyncio

import aiohttp
from bs4 import BeautifulSoup

import aioaria2

start_url = "https://movie.douban.com/top250?start={0}&filter="

header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36"
}

HOST = "http://127.0.0.1:6800/jsonrpc"
SEC = "token"


def parse(html: str):
    soup = BeautifulSoup(html, "lxml")
    return [
        tag.attrs["src"] for tag in soup.find_all(name="img", attrs={"width": "100"})
    ]


async def fetch(
    session: aiohttp.ClientSession, url: str, client: aioaria2.Aria2HttpClient
):
    async with session.get(url, headers=header) as resp:
        pic_urls = parse(await resp.text())
        for url in pic_urls:
            await client.addUri([url])


async def get_client():
    async with aioaria2.Aria2HttpClient(
        HOST, token=SEC
    ) as client, aiohttp.ClientSession() as session:
        urls = [start_url.format(i * 25) for i in range(10)]  # 每个页面
        tasks = [asyncio.create_task(fetch(session, url, client)) for url in urls]
        await asyncio.wait(tasks)


if __name__ == "__main__":
    asyncio.run(get_client())
