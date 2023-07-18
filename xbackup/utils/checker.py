#!/usr/bin/python3
# coding:utf-8

from base64 import b64decode
from base64 import b64encode
import enum
import os
from typing import IO
from typing import List
from typing import Optional

from xarg import commands

from .package import backup_tarfile
from .scanner import backup_scanner


class backup_check_list:

    @enum.unique
    class item_flag(enum.IntFlag):
        none = 0
        isdir = 1 << 0
        isfile = 1 << 1
        islink = 1 << 2

    class item:

        def __init__(self, relpath: str, size: int, isdir: bool, isfile: bool,
                     islink: bool, md5: Optional[str],
                     linkname: Optional[str]):
            assert isinstance(relpath, str)
            assert isinstance(size, int)
            assert isinstance(isdir, bool)
            assert isinstance(isfile, bool)
            assert isinstance(islink, bool)
            assert (isdir and not isfile) or (not isdir and isfile)
            assert isinstance(md5, str) if isfile else md5 is None
            assert isinstance(linkname, str) if islink else linkname is None
            self.__relpath = relpath
            self.__size = size
            self.__isdir = isdir
            self.__isfile = isfile
            self.__islink = islink
            self.__md5 = md5
            self.__linkname = linkname

        def __str__(self):
            flags = backup_check_list.item_flag.none

            if self.isdir:
                flags |= backup_check_list.item_flag.isdir

            if self.isfile:
                assert self.size >= 0 and isinstance(self.md5, str)
                flags |= backup_check_list.item_flag.isfile

            if self.islink:
                assert isinstance(self.linkname, str)
                flags |= backup_check_list.item_flag.islink

            line = [str(flags.value)]

            if isinstance(self.md5, str):
                assert self.isfile
                line.append(self.md5)
                line.append(str(self.size))

            def __encode(s: str) -> str:
                return b64encode(s.encode()).decode()

            # The path and linkname must be base64 encoded to support
            # invisible characters such as blank space.

            if isinstance(self.linkname, str):
                assert self.islink
                line.append(__encode(self.linkname))

            line.append(__encode(self.relpath))
            return " ".join(line)

        @property
        def relpath(self) -> str:
            return self.__relpath

        @property
        def size(self) -> int:
            return self.__size

        @property
        def isdir(self) -> bool:
            return self.__isdir

        @property
        def isfile(self) -> bool:
            return self.__isfile

        @property
        def islink(self) -> bool:
            return self.__islink

        @property
        def md5(self) -> Optional[str]:
            return self.__md5

        @property
        def linkname(self) -> Optional[str]:
            return self.__linkname

    class item_counter:

        def __init__(self):
            self.__sizes = 0
            self.__items = 0
            self.__dirs = 0
            self.__files = 0
            self.__links = 0

        def __str__(self):
            return "\n\t".join([
                f"{self.items} backup items:", f"{self.dirs} dirs",
                f"{self.files} files", f"{self.links} symbolic links"
            ])

        @property
        def sizes(self) -> int:
            return self.__sizes

        @property
        def items(self) -> int:
            return self.__items

        @property
        def dirs(self) -> int:
            return self.__dirs

        @property
        def files(self) -> int:
            return self.__files

        @property
        def links(self) -> int:
            return self.__links

        def inc(self, item):
            assert isinstance(item, backup_check_list.item)
            self.__sizes += item.size
            self.__items += 1

            if item.isdir:
                self.__dirs += 1

            if item.isfile:
                self.__files += 1

            if item.islink:
                self.__links += 1

    def __init__(self):
        self.__items: List[backup_check_list.item] = []
        self.__counter = self.item_counter()

    def __iter__(self):
        return iter(self.__items)

    @property
    def counter(self) -> item_counter:
        return self.__counter

    def add(self, item: item):
        assert isinstance(item, self.item)
        self.__items.append(item)
        self.counter.inc(item)

    def add_line(self, line: str):

        def __decode(s: str) -> str:
            return b64decode(s.encode()).decode()

        assert isinstance(line, str)
        items = line.strip().split()
        flags = int(items.pop(0))
        isdir = True if flags & backup_check_list.item_flag.isdir else False
        isfile = True if flags & backup_check_list.item_flag.isfile else False
        islink = True if flags & backup_check_list.item_flag.islink else False
        md5 = items.pop(0) if isfile else None
        size = int(items.pop(0)) if isfile else 0
        linkname = __decode(items.pop(0)) if islink else None
        relpath = __decode(items.pop(0))
        assert len(items) == 0
        item = self.item(relpath, size, isdir, isfile, islink, md5, linkname)
        self.add(item)

    def add_object(self, object: backup_scanner.object):
        assert isinstance(object, backup_scanner.object)
        item = self.item(
            object.relpath, object.size, object.isdir, object.isfile,
            object.islink, object.md5 if object.isfile else None,
            os.readlink(object.abspath) if object.islink else None)
        self.add(item)

    @classmethod
    def from_file(cls, fd: IO[bytes]):
        check_list = backup_check_list()
        for line in fd.readlines():
            check_list.add_line(line.decode())
        return check_list


def backup_check_file(tarfile: backup_tarfile) -> bool:
    assert isinstance(tarfile, backup_tarfile)
    assert tarfile.readonly

    cmds = commands()
    checklist = tarfile.checklist
    assert checklist is not None
    check_list = backup_check_list.from_file(checklist)
    for item in check_list:
        cmds.logger.debug(f"{item}")

    def check_file(item: backup_check_list.item,
                   tarfile: backup_tarfile) -> bool:
        assert isinstance(item, backup_check_list.item)
        assert isinstance(tarfile, backup_tarfile)

        md5 = tarfile.file_md5(item.relpath)
        if md5 == item.md5:
            return True

        cmds.logger.debug(f"Check {item.relpath} md5 is {md5}, "
                          f"expected {item.md5}.")
        return False

    def check_item(item: backup_check_list.item,
                   tarfile: backup_tarfile) -> bool:
        assert isinstance(item, backup_check_list.item)
        assert isinstance(tarfile, backup_tarfile)
        member = tarfile.getmember(item.relpath)

        if member.isdir() and item.isdir != member.isdir():
            cmds.logger.error(f"Check {item.relpath} isdir failed.")
            return False

        if member.isfile():
            if item.isfile != member.isfile():
                cmds.logger.error(f"Check {item.relpath} isfile failed.")
                return False

            if check_file(item, tarfile) is not True:
                cmds.logger.error(f"Check {item.relpath} file md5 failed.")
                return False

        if member.issym():
            if item.islink != member.issym():
                cmds.logger.error(f"Check {item.relpath} islink failed.")
                return False

            # check symbolic link
            if item.linkname != member.linkname:
                cmds.logger.debug(
                    f"Check {item.relpath} linkname is {member.linkname}, "
                    f"expected {item.linkname}.")
                cmds.logger.error(f"Check {item.relpath} linkname failed.")
                return False

        # if member.islnk():
        #     cmds.logger.error(f"Check {item.relpath} hard link failed.")
        #     return False

        # if member.isdev():
        #     cmds.logger.error(f"Check {item.relpath} device failed.")
        #     return False

        # if member.isreg():
        #     cmds.logger.error(f"Check {item.relpath} regular file failed.")
        #     return False

        # if member.chksum:
        #     cmds.logger.error(f"Check {item.relpath} regular file failed.")
        #     return False

        cmds.logger.debug(f"Check {item.relpath} ok.")
        return True

    members = tarfile.members
    if set([i.relpath for i in check_list]) - set([m.name for m in members]):
        return False

    for item in check_list:
        if check_item(item, tarfile) is not True:
            return False

    return True
