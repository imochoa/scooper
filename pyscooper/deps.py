#! /usr/bin/env python3

import typing as T
import tempfile
import pathlib
import subprocess
import itertools

from pyscooper.cli_utils import debug


def was_pdflatex_found() -> bool:
    p = subprocess.run(['pdflatex', '-v'], capture_output=True, check=True)
    debug(f"Ghostscript results:"
          f"\n\tSTDOUT:\n{p.stdout.decode('ascii')}\n"
          f"\n\tSTDERR:\n{p.stderr.decode('ascii')}\n")
    return p.returncode == 0


def was_ghostscript_found() -> bool:
    p = subprocess.run(['gs', '-v'], capture_output=True, check=True)
    debug(f"Ghostscript results:"
          f"\n\tSTDOUT:\n{p.stdout.decode('ascii')}\n"
          f"\n\tSTDERR:\n{p.stderr.decode('ascii')}\n")
    return p.returncode == 0


if __name__ == '__main__':
    was_pdflatex_found()
    was_ghostscript_found()
