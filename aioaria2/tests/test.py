# -*- coding: utf-8 -*-
import asyncio


async def my_callback(result):
    print("my_callback got:", result)
    return "My return value is ignored"


async def coro(number):
    await asyncio.sleep(number)
    return number + 1


async def add_success_callback(fut, callback):
    result = await fut
    await callback(result)
    return result


# loop = asyncio.get_event_loop()
# task = asyncio.ensure_future(coro(1))
task = add_success_callback(coro(1), my_callback)
response = asyncio.run(task)
print("response:", response)
