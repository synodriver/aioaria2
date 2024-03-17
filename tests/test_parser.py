# -*- coding: utf-8 -*-
from io import BytesIO
from os.path import dirname, join
from unittest import TestCase

from aioaria2 import ControlFile, DHTFile


class Testarser(TestCase):
    def test_ControlFile(self):
        s = BytesIO()
        data = ControlFile.from_file("180P_225K_242958531.webm.aria2")
        data.save(s)
        self.assertEqual(
            s.getvalue(), open("180P_225K_242958531.webm.aria2", "rb").read()
        )

    def test_DHTFile(self):
        s = BytesIO()
        data = DHTFile.from_file(join(dirname(__file__), "dht.dat"))
        data.save(s)
        self.assertEqual(
            len(s.getvalue()),
            len(open(join(dirname(__file__), "dht.dat"), "rb").read()),
        )

    def test_DHTFilev6(self):
        s = BytesIO()
        data = DHTFile.from_file(join(dirname(__file__), "dht6.dat"))
        data.save(s)
        self.assertEqual(
            len(s.getvalue()),
            len(open(join(dirname(__file__), "dht6.dat"), "rb").read()),
        )
