#!/usr/bin/python3
# coding:utf-8

from hashlib import md5
from hashlib import sha1
from hashlib import sha256
import os
from queue import Empty
from queue import Queue
import stat
from threading import Thread
from threading import current_thread
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Set

from xarg import commands

from .definer import DEFAULT_DIR
from .definer import THDNUM_BAKSCAN


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
        def stat(self) -> os.stat_result:
            return os.stat(self.abspath)

        @property
        def lstat(self) -> os.stat_result:
            return os.lstat(self.abspath)

        @property
        def size(self) -> int:
            return self.stat.st_size

        @property
        def isdir(self) -> bool:
            return stat.S_ISDIR(self.stat.st_mode)

        @property
        def isreg(self) -> bool:
            return stat.S_ISREG(self.stat.st_mode)

        @property
        def isfile(self) -> bool:
            return self.isreg

        @property
        def islink(self) -> bool:
            return stat.S_ISLNK(self.lstat.st_mode)

        @property
        def issym(self) -> bool:
            return self.islink

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
        cmds = commands()
        current = os.getcwd()
        os.chdir(self.__start)

        def rpath(path: str) -> str:
            assert isinstance(path, str)
            return os.path.relpath(path)

        # filter files and directorys, such as: ".xbackup"
        def filter() -> Set[str]:
            filter_paths = {rpath(DEFAULT_DIR)}

            for path in self.__exclude:
                filter_paths.add(rpath(path))

            return filter_paths

        class task_stat:

            def __init__(self):
                self.exit = False
                self.q_obj = Queue()
                self.q_path = Queue()
                self.filter = filter()
                self.objects: Dict[str, backup_scanner.object] = {}

        scan_stat = task_stat()

        def task_scan_path():
            name = current_thread().name
            cmds.logger.debug(f"Task scan thread[{name}] start.")
            while not scan_stat.exit:
                try:
                    path = scan_stat.q_path.get(timeout=0.01)
                except Empty:
                    continue

                path = rpath(path)
                assert isinstance(path, str)

                if path in scan_stat.filter or not os.path.exists(path):
                    cmds.logger.debug(f"Scan filter {path}.")
                    scan_stat.q_path.task_done()
                    continue

                if os.path.isdir(path) and not os.path.islink(path):
                    cmds.logger.debug(f"Scan {path}.")
                    for sub in os.listdir(path=path):
                        spath = os.path.join(path, sub)
                        scan_stat.q_path.put(spath)

                    scan_stat.q_path.task_done()
                    continue

                obj = backup_scanner.object(path=path, start=self.start)
                scan_stat.q_obj.put(obj)
                scan_stat.q_path.task_done()
            cmds.logger.debug(f"Task scan thread[{name}] exit.")

        def task_scan():
            name = current_thread().name
            cmds.logger.debug(f"Task scan thread[{name}] start.")
            while not scan_stat.exit:
                try:
                    object = scan_stat.q_obj.get(timeout=0.01)
                except Empty:
                    continue

                assert isinstance(object, backup_scanner.object)
                cmds.logger.debug(f"Scan {object.relpath}.")
                scan_stat.objects[object.path] = object
                scan_stat.q_obj.task_done()
            cmds.logger.debug(f"Task scan thread[{name}] exit.")

        task_threads: List[Thread] = []
        task_threads.append(Thread(target=task_scan, name="xbak-scan"))
        task_threads.extend([
            Thread(target=task_scan_path, name=f"xbak-scan{i}")
            for i in range(THDNUM_BAKSCAN)
        ])

        for thread in task_threads:
            thread.start()

        for path in self.__paths:
            scan_stat.q_path.put(path)

        scan_stat.q_path.join()
        scan_stat.exit = True

        for thread in task_threads:
            thread.join()

        self.__objects = scan_stat.objects
        os.chdir(current)

    @property
    def start(self) -> str:
        return self.__start

    def reload(self):
        self.__load()
