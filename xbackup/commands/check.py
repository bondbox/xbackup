#!/usr/bin/python3
# coding:utf-8

from errno import EIO
from errno import ENOENT
from errno import ENOEXEC
import os
from typing import Optional
from typing import Sequence

from xarg import add_command
from xarg import argp
from xarg import commands
from xarg import run_command

from ..utils import URL_PROG
from ..utils import __prog_check__
from ..utils import __version__
from ..utils import backup_check


@add_command(__prog_check__)
def add_cmd(_arg: argp):
    _arg.add_argument("_backup_path_",
                      type=str,
                      nargs="?",
                      metavar="FILE",
                      help="Specify the backup file")


@run_command(add_cmd)
def run_cmd(cmds: commands) -> int:

    backup_path = cmds.args._backup_path_
    if not isinstance(backup_path, str):
        cmds.logger.error("Please specify a backup file.")
        return ENOEXEC

    if not os.path.isfile(backup_path):
        cmds.logger.error(f"The backup file {backup_path} does not exist.")
        return ENOENT

    if backup_check(backup_path) is not True:
        cmds.stdout("check error")
        return EIO

    cmds.stdout("check ok")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    cmds = commands()
    cmds.version = __version__
    return cmds.run(root=add_cmd,
                    argv=argv,
                    prog=__prog_check__,
                    description="Check backup file.",
                    epilog=f"For more, please visit {URL_PROG}.")
