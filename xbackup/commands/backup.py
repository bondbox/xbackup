#!/usr/bin/python3
# coding:utf-8

from datetime import datetime
from errno import EEXIST
from errno import ENOENT
from errno import ENOEXEC
import os
import tempfile
from typing import Optional
from typing import Sequence

from xarg import add_command
from xarg import argp
from xarg import commands
from xarg import run_command

from ..utils import COMPRESS_TYPE
from ..utils import DEFAULT_COMPRESS_TYPE
from ..utils import URL_PROG
from ..utils import __prog__
from ..utils import __version__
from ..utils import backup_pack
from ..utils import backup_scanner


@add_command(__prog__)
def add_cmd(_arg: argp):
    group = _arg.argument_group("backup objects")
    group.add_argument("-s",
                       "--start",
                       type=str,
                       nargs="?",
                       metavar="DIR",
                       dest="_backup_start_directory_",
                       help="Specify start directory")
    # action="extend" requires Python >= 3.8
    group.add_argument("--exclude",
                       type=str,
                       nargs="+",
                       default=[],
                       metavar="OBJ",
                       action="extend",
                       dest="_backup_exclude_",
                       help="Specify exclude directorys or files")
    group.add_argument("_backup_paths_",
                       type=str,
                       nargs="+",
                       metavar="OBJ",
                       help="Specify all backup objects(directorys or files)")

    group = _arg.argument_group("backup file")
    group.add_argument("--no-check",
                       action="store_true",
                       dest="_backup_check_off_",
                       help="Do not check the backup file")
    # Support for temp directory under Linux and Windows
    group.add_argument("--dir",
                       type=str,
                       nargs="?",
                       const=tempfile.gettempdir(),
                       default=".",
                       metavar="DIR",
                       dest="_backup_file_directory_",
                       help="Specify the backup directory")
    group.add_argument("--name",
                       type=str,
                       nargs="?",
                       default="xbackup",
                       metavar="NAME",
                       dest="_backup_file_name_",
                       help="Specify the backup name")
    group.add_argument("--compress",
                       type=str,
                       nargs="?",
                       const=DEFAULT_COMPRESS_TYPE,
                       choices=COMPRESS_TYPE,
                       dest="_backup_file_comptype_",
                       help="Specify the backup file compression type")


@run_command(add_cmd)
def run_cmd(cmds: commands) -> int:

    backup_dir = cmds.args._backup_file_directory_
    if not isinstance(backup_dir, str) or not os.path.isdir(backup_dir):
        cmds.logger.error(f"The backup directory {backup_dir} does not exist.")
        return ENOENT

    backup_name = cmds.args._backup_file_name_
    if not isinstance(backup_name, str):
        cmds.logger.error("Please specify a backup file name.")
        return ENOEXEC

    comptype = cmds.args._backup_file_comptype_
    assert isinstance(comptype, str) or comptype is None
    filename = os.path.basename(backup_name)
    _, ext = os.path.splitext(filename)
    if isinstance(ext, str) and ext[1:] in COMPRESS_TYPE:
        comptype = ext[1:]
    ext = f".tar.{comptype}" if isinstance(comptype, str) else ".tar"
    if not filename.endswith(ext) and not filename.endswith(".tar"):
        timestamp = datetime.now().strftime("%y%m%d%H%M%S")
        filename = f"{filename}-{timestamp}{ext}"

    backup_path = os.path.join(os.path.normpath(backup_dir), filename)
    if os.path.exists(backup_path):
        cmds.logger.error(f"The backup file {backup_path} already exists.")
        return EEXIST

    start = cmds.args._backup_start_directory_
    paths = cmds.args._backup_paths_
    exclude = cmds.args._backup_exclude_
    check = not cmds.args._backup_check_off_
    scanner = backup_scanner(start, paths, exclude)
    return backup_pack(scanner, backup_path, comptype, check)


def main(argv: Optional[Sequence[str]] = None) -> int:
    cmds = commands()
    cmds.version = __version__
    return cmds.run(
        root=add_cmd,
        argv=argv,
        prog=__prog__,
        description="Create backup.",
        epilog=f"For more, please visit {URL_PROG}.")
