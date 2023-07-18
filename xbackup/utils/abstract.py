#!/usr/bin/python3
# coding:utf-8

from datetime import datetime
from typing import Dict
from typing import Optional

import yaml

from .checker import backup_check_list
from .package import backup_tarfile


class backup_description:

    VERSION = 1

    class btime:

        def __init__(self,
                     start: Optional[str] = None,
                     finish: Optional[str] = None):
            self.__start = start if isinstance(start, str) else self.now()
            self.__finish = finish if isinstance(finish, str) else None

        @classmethod
        def now(cls) -> str:
            now = datetime.now()
            return now.strftime("%Y-%m-%d %a %X.%f")

        @property
        def start(self) -> str:
            return self.__start

        @property
        def finish(self) -> str:
            return self.now() if self.__finish is None else self.__finish

    def __init__(self,
                 timer: Optional[btime] = None,
                 checklist: Optional[backup_check_list] = None):
        self.__timer = timer if isinstance(timer, self.btime) else self.btime()
        self.__checklist = checklist if isinstance(
            checklist, backup_check_list) else backup_check_list()

    @property
    def timer(self) -> btime:
        return self.__timer

    @property
    def checklist(self) -> backup_check_list:
        return self.__checklist

    @property
    def backup_time(self) -> Dict:
        return {
            "start": self.timer.start,
            "finish": self.timer.finish,
        }

    @property
    def counter(self) -> Dict:
        return {
            "items": self.checklist.counter.items,
            "sizes": self.checklist.counter.sizes,
            "dirs": self.checklist.counter.dirs,
            "files": self.checklist.counter.files,
            "links": self.checklist.counter.links,
        }

    @property
    def data(self) -> Dict:
        return {
            "version": self.VERSION,
            "backup time": self.backup_time,
            "checklist": {
                "counter": self.counter
            }
        }

    def dump(self) -> str:
        return yaml.dump(self.data, default_flow_style=False, sort_keys=False)

    @classmethod
    def from_file(cls, backup_file: backup_tarfile):
        checklist = backup_file.checklist
        description = backup_file.description
        assert checklist is not None
        assert description is not None

        data = yaml.load(stream=description, Loader=yaml.FullLoader)
        start = data["backup time"]["start"]
        finish = data["backup time"]["finish"]
        return backup_description(backup_description.btime(start, finish),
                                  backup_check_list.from_file(checklist))
