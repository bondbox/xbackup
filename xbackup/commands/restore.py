#!/usr/bin/python3
# coding:utf-8

from typing import Optional
from typing import Sequence

from xarg import add_command
from xarg import argp
from xarg import commands
from xarg import run_command

from ..utils import URL_PROG
from ..utils import __prog__
from ..utils import __version__


@add_command(__prog__)
def add_cmd(_arg: argp):
    pass


@run_command(add_cmd)
def run_cmd(cmds: commands) -> int:
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    cmds = commands()
    cmds.version = __version__
    return cmds.run(
        root=add_cmd,
        argv=argv,
        prog=__prog__,
        # description="Backup. Restore.",
        epilog=f"For more, please visit {URL_PROG}.")
