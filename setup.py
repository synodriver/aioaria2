# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import os
import re


def get_version() -> str:
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "aioaria2", "__init__.py")
    with open(path, "r", encoding="utf-8") as f:
        data = f.read()
    result = re.findall(r"(?<=__version__ = )\"\S+\"\r?", data)
    return result[0]


def get_dis():
    with open("README.md", "r", encoding="utf-8") as f:
        return f.read()


def main():
    version: str = get_version()

    dis = get_dis()
    setup(
        name="aioaria2",
        version=version,
        packages=find_packages(),
        keywords=["asyncio","Aria2"],
        description="Support Aria2 rpc client and manage server with async/await",
        long_description_content_type="text/x-rst",
        long_description=dis,
        author=["帝国皇家近卫军","synodriver"],
        author_email="diguohuangjiajinweijun@gmail.com",
        maintainer="",
        python_requires=">=3.6",
        install_requires=["aiohttp","aiofiles"],
        license='GPL3.0',
        include_package_data=True
    )
    pass


if __name__ == "__main__":
    main()
