"""
Copyright (c) 2008-2023 synodriver <diguohuangjiajinweijun@gmail.com>
"""
from io import BytesIO

from aioaria2 import ControlFile, DHTFile

data = ControlFile.from_file("180P_225K_242958531.webm.aria2")
print(data)
# do something with .aria2 file
data.save(BytesIO())

dht = DHTFile.from_file("dht.dat")  # or dht6.dat
print(dht)
# do something with dht file
dht.save(BytesIO())