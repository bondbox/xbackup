#!/usr/bin/python3
# coding:utf-8

import os
import tarfile
from typing import IO
from typing import List
from typing import Optional

from .definer import DEFAULT_DIR


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
    def path(self) -> str:
        return self.__realpath

    @property
    def wrap(self) -> tarfile.TarFile:
        assert isinstance(self.__tarfile, tarfile.TarFile)
        return self.__tarfile

    @property
    def readonly(self) -> bool:
        assert isinstance(self.__tarfile, tarfile.TarFile)
        return self.__tarfile.mode == "r"

    @property
    def names(self) -> List[str]:
        assert isinstance(self.__tarfile, tarfile.TarFile)
        return self.__tarfile.getnames()

    @property
    def members(self) -> List[tarfile.TarInfo]:
        assert isinstance(self.__tarfile, tarfile.TarFile)
        return self.__tarfile.getmembers()

    README = os.path.join(DEFAULT_DIR, "readme")
    CHECKLIST = os.path.join(DEFAULT_DIR, "checklist")
    DESCRIPTION = os.path.join(DEFAULT_DIR, "description")

    @property
    def checklist(self) -> Optional[IO[bytes]]:
        return self.wrap.extractfile(self.CHECKLIST)

    @checklist.setter
    def checklist(self, value: str):
        if os.path.isfile(value) and self.CHECKLIST not in self.names:
            self.wrap.add(value, self.CHECKLIST)

    @property
    def description(self) -> Optional[IO[bytes]]:
        return self.wrap.extractfile(self.DESCRIPTION)

    @description.setter
    def description(self, value: str):
        if os.path.isfile(value) and self.DESCRIPTION not in self.names:
            self.wrap.add(value, self.DESCRIPTION)
