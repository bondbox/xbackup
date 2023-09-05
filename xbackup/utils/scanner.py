#!/usr/bin/python3
# coding:utf-8

from hashlib import md5
from hashlib import sha1
from hashlib import sha256
import os
from typing import Dict
from typing import Optional
from typing import Sequence
from typing import Set

from xarg import commands

from .definer import DEFAULT_DIR


class backup_scanner:
    '''
    scan backup abspath
    '''

    class object:

        def __init__(self, path: str, start: Optional[str] = None):
            assert isinstance(path, str)
            self.__start: str = start if isinstance(start,
                                                    str) else os.getcwd()
            self.__path = os.path.normpath(path)
            self.__abspath = os.path.abspath(self.__path)
            self.__relpath = os.path.relpath(self.__abspath, start)
            self.__realpath = os.path.realpath(self.__abspath)

        @property
        def path(self) -> str:
            return self.__path

        @property
        def start(self) -> str:
            return self.__start

        @property
        def abspath(self) -> str:
            return self.__abspath

        @property
        def relpath(self) -> str:
            return self.__relpath

        @property
        def realpath(self) -> str:
            return self.__realpath

        @property
        def size(self) -> int:
            return os.stat(self.abspath).st_size if self.isfile else 0

        @property
        def isdir(self) -> bool:
            return os.path.isdir(self.abspath)

        @property
        def isfile(self) -> bool:
            return os.path.isfile(self.abspath)

        @property
        def islink(self) -> bool:
            return os.path.islink(self.abspath)

        @property
        def md5(self) -> Optional[str]:
            return self.__hash(md5())

        @property
        def sha1(self) -> Optional[str]:
            return self.__hash(sha1())

        @property
        def sha256(self) -> Optional[str]:
            return self.__hash(sha256())

        def __hash(self, hash) -> Optional[str]:
            if not self.isfile or self.islink:
                return None

            with open(self.abspath, "rb") as f:
                while True:
                    data = f.read(1024**2)
                    if not data:
                        break
                    hash.update(data)
            return hash.hexdigest()

    def __init__(self,
                 start: Optional[str] = None,
                 paths: Sequence[str] = [],
                 exclude: Sequence[str] = []):
        assert isinstance(start, str) or start is None
        assert isinstance(paths, Sequence)
        assert isinstance(exclude, Sequence)
        self.__start: str = start if isinstance(start, str) else os.getcwd()
        self.__paths = set(paths)
        self.__exclude = set(exclude)
        self.__objects: Dict[str, backup_scanner.object] = {}
        self.__load()

    def __iter__(self):
        return iter(self.__objects.values())

    def __load(self):
        current = os.getcwd()
        os.chdir(self.__start)

        def scan(paths: Set[str]) -> Dict[str, backup_scanner.object]:
            cmds = commands()

            def rpath(path: str) -> str:
                assert isinstance(path, str)
                return os.path.relpath(path)

            # filter files and directorys, such as: ".xbackup"
            def filter() -> Set[str]:
                filter_paths = {rpath(DEFAULT_DIR)}

                for path in self.__exclude:
                    filter_paths.add(rpath(path))

                return filter_paths

            filter_paths: Set[str] = filter()
            objects: Dict[str, backup_scanner.object] = {}

            def add(path: str) -> bool:
                path = rpath(path)
                assert isinstance(path, str)
                if path not in filter_paths:
                    obj = backup_scanner.object(path, self.start)
                    cmds.logger.debug(f"Scan {obj.relpath}")
                    objects[path] = obj
                    return True
                else:
                    return False

            for path in paths:
                assert isinstance(path, str)
                if os.path.isdir(path):
                    if os.path.islink(path):
                        add(path)
                        continue

                    for root, dirs, files in os.walk(path, followlinks=True):
                        for filename in files:
                            # TODO: auto add link file
                            add(os.path.join(root, filename))

                        for dirname in [dir for dir in dirs]:
                            dirpath = os.path.join(root, dirname)

                            if rpath(dirpath) in filter_paths:
                                dirs.remove(dirname)
                                continue

                            # create backup object for directory symbolic link
                            # otherwise find every object under subdirectories
                            if os.path.islink(dirpath):
                                dirs.remove(dirname)
                                add(dirpath)
                else:
                    add(path)
            return objects

        self.__objects = scan(self.__paths)
        os.chdir(current)

    @property
    def start(self) -> str:
        return self.__start

    def reload(self):
        self.__load()
