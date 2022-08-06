# -*- coding: utf-8 -*-
"""
See https://aria2.github.io/manual/en/html/technical-notes.html
"""
from dataclasses import dataclass
from ipaddress import IPv4Address, IPv6Address
from pathlib import Path
from typing import IO, List, Union


@dataclass
class InFlightPiece:
    index: int
    length: int
    piece_bitfield_length: int
    piece_bitfield: bytes

    @classmethod
    def from_reader(cls, reader: IO[bytes], version: int) -> "InFlightPiece":
        index = int.from_bytes(reader.read(4), "big" if version == 1 else "little")
        length = int.from_bytes(reader.read(4), "big" if version == 1 else "little")
        piece_bitfield_length = int.from_bytes(
            reader.read(4), "big" if version == 1 else "little"
        )
        piece_bitfield = reader.read(piece_bitfield_length)
        return cls(
            index=index,
            length=length,
            piece_bitfield_length=piece_bitfield_length,
            piece_bitfield=piece_bitfield,
        )

    def save(self, file: IO[bytes], version: int) -> None:
        file.write(self.index.to_bytes(4, "big" if version == 1 else "little"))
        file.write(self.length.to_bytes(4, "big" if version == 1 else "little"))
        file.write(
            len(self.piece_bitfield).to_bytes(4, "big" if version == 1 else "little")
        )
        file.write(self.piece_bitfield)


@dataclass
class ControlFile:
    """
    Parse .aria2 files
    """

    version: int
    ext: bytes
    info_hash_length: int
    info_hash: bytes
    piece_length: int
    total_length: int
    upload_length: int
    bitfield_length: int
    bitfield: bytes
    num_inflight_piece: int
    inflight_pieces: List[InFlightPiece]

    @classmethod
    def from_file(cls, file: Union[str, Path]) -> "ControlFile":
        with open(file, "rb") as f:
            return cls.from_reader(f)

    @classmethod
    def from_reader(cls, reader: IO[bytes]) -> "ControlFile":
        version = int.from_bytes(reader.read(2), "big")
        ext = reader.read(4)
        info_hash_length = int.from_bytes(
            reader.read(4), "big" if version == 1 else "little"
        )
        if info_hash_length == 0 and ext[3] & 1 == 1:
            raise ValueError(
                '"infoHashCheck" extension is enabled but info hash length is 0'
            )
        info_hash = reader.read(info_hash_length)
        piece_length = int.from_bytes(
            reader.read(4), "big" if version == 1 else "little"
        )
        total_length = int.from_bytes(
            reader.read(8), "big" if version == 1 else "little"
        )
        upload_length = int.from_bytes(
            reader.read(8), "big" if version == 1 else "little"
        )
        bitfield_length = int.from_bytes(
            reader.read(4), "big" if version == 1 else "little"
        )
        bitfield = reader.read(bitfield_length)
        num_inflight_piece = int.from_bytes(
            reader.read(4), "big" if version == 1 else "little"
        )
        inflight_pieces = [
            InFlightPiece.from_reader(reader, version)
            for _ in range(num_inflight_piece)
        ]

        return cls(
            version=version,
            ext=ext,
            info_hash_length=info_hash_length,
            info_hash=info_hash,
            piece_length=piece_length,
            total_length=total_length,
            upload_length=upload_length,
            bitfield_length=bitfield_length,
            bitfield=bitfield,
            num_inflight_piece=num_inflight_piece,
            inflight_pieces=inflight_pieces,
        )

    def save(self, file: IO[bytes]) -> None:
        file.write(self.version.to_bytes(2, "big" if self.version == 1 else "little"))
        file.write(self.ext)
        file.write(
            len(self.info_hash).to_bytes(4, "big" if self.version == 1 else "little")
        )
        file.write(self.info_hash)
        file.write(
            self.piece_length.to_bytes(4, "big" if self.version == 1 else "little")
        )
        file.write(
            self.total_length.to_bytes(8, "big" if self.version == 1 else "little")
        )
        file.write(
            self.upload_length.to_bytes(8, "big" if self.version == 1 else "little")
        )
        file.write(
            len(self.bitfield).to_bytes(4, "big" if self.version == 1 else "little")
        )
        file.write(self.bitfield)
        file.write(
            len(self.inflight_pieces).to_bytes(
                4, "big" if self.version == 1 else "little"
            )
        )
        for piece in self.inflight_pieces:
            piece.save(file, self.version)


@dataclass
class NodeInfo:
    plen: int
    compact_peer_info: tuple
    node_id: bytes

    @classmethod
    def from_reader(cls, reader: IO[bytes]) -> "NodeInfo":
        plen = int.from_bytes(reader.read(1), "big")
        reader.read(7)
        class_ = IPv4Address if plen == 6 else IPv6Address
        temp = reader.read(plen)
        compact_peer_info = (class_(temp[:-2]), int.from_bytes(temp[-2:], "big"))
        reader.read(24 - plen)
        node_id = reader.read(20)
        reader.read(4)
        return cls(plen=plen, compact_peer_info=compact_peer_info, node_id=node_id)

    def save(self, file: IO[bytes]) -> None:
        file.write(self.plen.to_bytes(1, "big"))
        file.write(b"\x00" * 7)

        file.write(self.compact_peer_info[0].packed)
        file.write(self.compact_peer_info[1].to_bytes(2, "big"))

        file.write(b"\x00" * (24 - self.plen))
        file.write(self.node_id)
        file.write(b"\x00" * 4)


@dataclass
class DHTFile:
    """
    Parse dht.dat/dht6.dat files
    """

    mgc: bytes
    fmt: bytes
    ver: bytes
    mtime: int
    localnode_id: bytes
    num_node: int
    nodes: List[NodeInfo]

    @classmethod
    def from_file(cls, file: Union[str, Path]) -> "DHTFile":
        with open(file, "rb") as f:
            return cls.from_reader(f)

    @classmethod
    def from_reader(cls, reader: IO[bytes]) -> "DHTFile":
        mgc = reader.read(2)
        assert mgc == b"\xa1\xa2", "wrong magic number"
        fmt = reader.read(1)
        assert fmt == b"\x02", "wrong format idr"
        ver = reader.read(2)
        # assert ver == b'\x00\x03', "wrong version number"
        reader.read(3)
        mtime = int.from_bytes(reader.read(8), "big")
        reader.read(8)
        localnode_id = reader.read(20)
        reader.read(4)
        num_node = int.from_bytes(reader.read(4), "big")
        reader.read(4)
        nodes = [NodeInfo.from_reader(reader) for _ in range(num_node)]
        return cls(
            mgc=mgc,
            fmt=fmt,
            ver=ver,
            mtime=mtime,
            localnode_id=localnode_id,
            num_node=num_node,
            nodes=nodes,
        )

    def save(self, file: IO[bytes]) -> None:
        file.write(self.mgc)
        file.write(self.fmt)
        file.write(self.ver)
        file.write(b"\x00" * 3)
        file.write(self.mtime.to_bytes(8, "big"))
        file.write(b"\x00" * 8)
        file.write(self.localnode_id)
        file.write(b"\x00" * 4)
        file.write(len(self.nodes).to_bytes(4, "big"))
        file.write(b"\x00" * 4)
        for node in self.nodes:
            node.save(file)
