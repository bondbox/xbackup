#!/usr/bin/python3
# coding:utf-8

from hashlib import md5
import os
import tarfile
from typing import IO
from typing import List
from typing import Optional
from typing import Union

DEFAULT_COMPRESS_TYPE = "gz"
COMPRESS_TYPE = ["gz", "bz2", "xz"]


class backup_tarfile:

    def __init__(self,
                 path: str,
                 readonly: bool = True,
                 comptype: Optional[str] = None):
        assert isinstance(path, str)
        realpath = os.path.realpath(path)

        def tarfile_mode(readonly: bool, comptype: Optional[str] = None):
            comptype = "" if not isinstance(comptype, str) else comptype
            return "r:*" if readonly else f"x:{comptype}"

        self.__realpath = realpath
        self.__tarfile: Optional[tarfile.TarFile] = tarfile.open(
            name=realpath, mode=tarfile_mode(readonly, comptype))

    def __del__(self):
        self.close()

    def close(self):
        if isinstance(self.__tarfile, tarfile.TarFile):
            # TODO: add readme for write mode
            self.__tarfile.close()
            self.__tarfile = None

    @property
    def readonly(self) -> bool:
        assert isinstance(self.__tarfile, tarfile.TarFile)
        return self.__tarfile.mode == "r"

    @property
    def path(self) -> str:
        return self.__realpath

    @property
    def names(self) -> List[str]:
        assert isinstance(self.__tarfile, tarfile.TarFile)
        return self.__tarfile.getnames()

    @property
    def members(self) -> List[tarfile.TarInfo]:
        assert isinstance(self.__tarfile, tarfile.TarFile)
        return self.__tarfile.getmembers()

    def getmember(self, name: str) -> tarfile.TarInfo:
        assert isinstance(name, str)
        assert isinstance(self.__tarfile, tarfile.TarFile)
        return self.__tarfile.getmember(name)

    def add(self,
            name: str,
            arcname: Optional[str] = None,
            recursive: bool = False) -> None:
        assert isinstance(self.__tarfile, tarfile.TarFile)
        assert not self.readonly
        self.__tarfile.add(name, arcname, recursive)

    def extractfile(
            self, member: Union[str, tarfile.TarInfo]) -> Optional[IO[bytes]]:
        assert isinstance(self.__tarfile, tarfile.TarFile)
        return self.__tarfile.extractfile(member)

    def file_md5(self, member: Union[str, tarfile.TarInfo]) -> Optional[str]:
        tarf = self.extractfile(member)
        if not tarf:
            return None

        try:
            hash_md5 = md5()
            while True:
                data = tarf.read(1024**2)
                if not data:
                    break
                hash_md5.update(data)
            return hash_md5.hexdigest()
        except Exception:
            return None
        finally:
            tarf.close()

    README = os.path.join(".xbackup", "readme")
    CHECKLIST = os.path.join(".xbackup", "checklist")
    DESCRIPTION = os.path.join(".xbackup", "description")

    @property
    def checklist(self) -> Optional[IO[bytes]]:
        return self.extractfile(self.CHECKLIST)

    @checklist.setter
    def checklist(self, value: str):
        if os.path.isfile(value) and self.CHECKLIST not in self.names:
            self.add(value, self.CHECKLIST)

    @property
    def description(self) -> Optional[IO[bytes]]:
        return self.extractfile(self.DESCRIPTION)

    @description.setter
    def description(self, value: str):
        if os.path.isfile(value) and self.DESCRIPTION not in self.names:
            self.add(value, self.DESCRIPTION)
