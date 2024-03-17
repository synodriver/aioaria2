# -*- coding: utf-8 -*-
import os
import re

from setuptools import find_packages, setup


def get_version() -> str:
    path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "aioaria2", "__init__.py"
    )
    with open(path, "r", encoding="utf-8") as f:
        data = f.read()
    result = re.findall(r"(?<=__version__ = \")\S+(?=\")", data)
    return result[0]


def get_dis():
    with open("README.markdown", "r", encoding="utf-8") as f:
        return f.read()


packages = find_packages(exclude=("test", "tests.*", "test*"))


def main():
    version: str = get_version()

    dis = get_dis()
    setup(
        name="aioaria2",
        version=version,
        url="https://github.com/synodriver/aioaria2",
        packages=packages,
        keywords=["asyncio", "Aria2"],
        description="Support Aria2 rpc client and manage server with async/await",
        long_description_content_type="text/markdown",
        long_description=dis,
        author="synodriver",
        author_email="diguohuangjiajinweijun@gmail.com",
        maintainer="v-vinson",
        python_requires=">=3.6",
        install_requires=["aiohttp", "aiofiles", "typing-extensions"],
        license="GPLv3",
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Framework :: AsyncIO",
            "Operating System :: OS Independent",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            "Programming Language :: Python",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: Implementation :: CPython",
        ],
        include_package_data=True,
    )


if __name__ == "__main__":
    main()
