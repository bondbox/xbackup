#!/usr/bin/python3
# coding:utf-8

from datetime import datetime
from typing import Dict
from typing import Optional

from humanize import naturalsize
import yaml

from .checker import backup_check_list
from .package import backup_tarfile


class backup_description:

    VERSION = 1

    class btime:

        def __init__(self,
                     start: Optional[str] = None,
                     finish: Optional[str] = None):
            if start is not None:
                assert isinstance(start, str) and isinstance(finish, str)
                self.__start = datetime.fromisoformat(start)
                self.__finish = datetime.fromisoformat(finish)
            else:
                assert start is None and finish is None
                self.__start = datetime.now()
                self.__finish = None

            assert isinstance(self.__start, datetime)
            if isinstance(self.__finish, datetime):
                assert self.__finish >= self.__start
            else:
                assert self.__finish is None

        @property
        def start(self) -> datetime:
            assert isinstance(self.__start, datetime)
            return self.__start

        @property
        def finish(self) -> datetime:
            if self.__finish is None:
                self.__finish = datetime.now()
            assert self.__finish >= self.__start
            return self.__finish

        @property
        def start_isoformat(self) -> str:
            return self.start.isoformat()

        @property
        def finish_isoformat(self) -> str:
            return self.finish.isoformat()

        START = "start"
        FINISH = "finish"

        def dump_dict(self) -> Dict:
            return {
                self.START: self.start_isoformat,
                self.FINISH: self.finish_isoformat,
            }

        @classmethod
        def load_dict(cls, data: Dict):
            assert isinstance(data, dict)
            start = data[cls.START]
            finish = data[cls.FINISH]
            assert isinstance(start, str)
            assert isinstance(finish, str)
            return backup_description.btime(start, finish)

    def __init__(self,
                 timer: Optional[btime] = None,
                 checklist: Optional[backup_check_list] = None):
        self.__timestamp = timer if isinstance(timer,
                                               self.btime) else self.btime()
        self.__checklist = checklist if isinstance(
            checklist, backup_check_list) else backup_check_list()

    def __str__(self):
        strdata = self.data
        strdata[self.BAKTIME] = {
            backup_description.btime.START:
            self.timestamp.start.strftime("%Y-%m-%d %a %X.%f"),
            backup_description.btime.FINISH:
            self.timestamp.finish.strftime("%Y-%m-%d %a %X.%f"),
        }
        counter = strdata[self.CHKLIST][self.COUNTER]
        size = counter[backup_check_list.item_counter.SIZE]
        counter[backup_check_list.item_counter.SIZE] = "{0}({1})".format(
            size, naturalsize(size, gnu=True))
        return yaml.dump(strdata, default_flow_style=False,
                         sort_keys=False).strip()

    @property
    def timestamp(self) -> btime:
        return self.__timestamp

    @property
    def checklist(self) -> backup_check_list:
        return self.__checklist

    VERSION = "version"
    BAKTIME = "backup time"
    CHKLIST = "checklist"
    COUNTER = "counter"

    @property
    def data(self) -> Dict:
        return {
            self.VERSION: self.VERSION,
            self.BAKTIME: self.timestamp.dump_dict(),
            self.CHKLIST: {
                self.COUNTER: self.checklist.counter.dump_dict()
            }
        }

    def dump(self) -> str:
        return yaml.dump(self.data, default_flow_style=False, sort_keys=False)

    @classmethod
    def load(cls, backup_file: backup_tarfile):
        checklist = backup_file.checklist
        description = backup_file.description
        assert checklist is not None
        assert description is not None

        data = yaml.load(stream=description, Loader=yaml.FullLoader)
        return backup_description(
            backup_description.btime.load_dict(data[cls.BAKTIME]),
            backup_check_list.load(checklist))
