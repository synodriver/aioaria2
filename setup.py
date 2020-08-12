# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import os
import re


def get_version() -> str:
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "aioaria2", "__init__.py")
    with open(path, "r", encoding="utf-8") as f:
        data = f.read()
    result = re.findall(r"(?<=__version__ = \")\S+(?=\")", data)
    return result[0]


def get_dis():
    with open("README.md", "r", encoding="utf-8") as f:
        return f.read()


packages = find_packages(exclude=('tests', 'tests.*', "test*"))


def main():
    version: str = get_version()

    dis = get_dis()
    setup(
        name="aioaria2",
        version=version,
        packages=packages,
        keywords=["asyncio", "Aria2"],
        description="Support Aria2 rpc client and manage server with async/await",
        long_description_content_type="text/markdown",
        long_description=dis,
        author=["帝国皇家近卫军", "synodriver"],
        author_email="diguohuangjiajinweijun@gmail.com",
        maintainer="v-vinson",
        python_requires=">=3.6",
        install_requires=["aiohttp", "aiofiles"],
        license='GPLv3',
        classifiers=[
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            "Programming Language :: Python",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: Implementation :: CPython"
        ],
        include_package_data=True
    )


if __name__ == "__main__":
    main()
