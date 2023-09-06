#!/usr/bin/python3
# coding:utf-8

from errno import EIO
from errno import ENOENT
from errno import ENOEXEC
import os
from typing import List
from typing import Optional
from typing import Sequence

from xarg import add_command
from xarg import argp
from xarg import commands
from xarg import run_command

from ..utils import URL_PROG
from ..utils import __prog_list__
from ..utils import __version__
from ..utils import backup_check_pack
from ..utils import backup_description
from ..utils import backup_tarfile


@add_command(__prog_list__)
def add_cmd(_arg: argp):
    _arg.add_argument("--check",
                      action="store_true",
                      dest="_backup_check_on_",
                      help="Check the backup file")
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

    backup_file = backup_tarfile(backup_path, True)
    assert backup_file.readonly

    check_on = cmds.args._backup_check_on_
    if check_on and not backup_check_pack(tarfile=backup_file, fast=True):
        cmds.stdout("check error")
        backup_file.close()
        return EIO

    desc = backup_description.load(backup_file)
    for item in desc.checklist:
        line: List[str] = [f"{item.name}:"]
        line.append("l" if item.islink else "d" if item.isdir else "f" if item.
                    isfile else "-")

        if item.islink:
            assert isinstance(item.linkname, str)
            line.append(item.linkname)
        elif item.isfile:
            assert isinstance(item.md5, str)
            line.append(str(item.size))
            line.append(item.md5)

        cmds.stdout(" ".join(line))

    backup_file.close()
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    cmds = commands()
    cmds.version = __version__
    return cmds.run(root=add_cmd,
                    argv=argv,
                    prog=__prog_list__,
                    description="List all backup objects.",
                    epilog=f"For more, please visit {URL_PROG}.")
