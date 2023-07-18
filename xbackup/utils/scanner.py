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
            if not self.isfile:
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
        self.__paths = paths
        self.__exclude = exclude
        self.__objects: Dict[str, backup_scanner.object] = {}
        self.__load()

    def __iter__(self):
        return iter(self.__objects.values())

    def __load(self):
        current = os.getcwd()
        os.chdir(self.__start)

        def __objects(paths: Sequence[str]) -> Set[str]:
            objects = []
            for path in paths:
                assert isinstance(path, str)
                if os.path.isdir(path):
                    if os.path.islink(path):
                        objects.append(path)
                        continue
                    for root, dirs, files in os.walk(path, followlinks=True):
                        for filename in files:
                            # TODO: auto add link file
                            objects.append(os.path.join(root, filename))
                        # create backup object for directory symbolic link
                        # otherwise find every object under subdirectories
                        for dirname in [dir for dir in dirs]:
                            dirpath = os.path.join(root, dirname)
                            if os.path.islink(dirpath):
                                objects.append(dirpath)
                                dirs.remove(dirname)
                else:
                    objects.append(path)
            return set([os.path.abspath(obj) for obj in objects])

        new_objects: Dict[str, backup_scanner.object] = {}
        backup_objects = __objects(self.__paths) - __objects(self.__exclude)

        for path in backup_objects:
            new_objects[path] = backup_scanner.object(path, self.__start)

        self.__objects = new_objects
        os.chdir(current)

    @property
    def start(self) -> str:
        return self.__start

    # @property
    # def exclude(self) -> Iterator[str]:
    #     return iter(self.__exclude)

    def reload(self):
        self.__load()
