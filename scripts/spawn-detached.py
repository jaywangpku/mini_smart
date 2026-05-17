#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Spawn a detached development process.")
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--pid-file", required=True)
    parser.add_argument("--log-file", required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    if not args.command or args.command[0] != "--":
        parser.error("command must be passed after --")
    command = args.command[1:]
    if not command:
        parser.error("missing command")

    log_path = Path(args.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_handle = log_path.open("ab", buffering=0)
    process = subprocess.Popen(
        command,
        cwd=args.cwd,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        close_fds=True,
        start_new_session=True,
    )
    Path(args.pid_file).write_text(f"{process.pid}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
