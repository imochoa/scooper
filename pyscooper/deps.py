#! /usr/bin/env python3

import typing as T
import re
import tempfile
import pathlib
import subprocess
import itertools

from pyscooper.cli_utils import debug


def was_pdflatex_found() -> bool:
    p = subprocess.run(['pdflatex', '-v'], capture_output=True, check=True)
    debug(f"Ghostscript results:"
          f"\n\tSTDOUT:\n{p.stdout.decode('utf8')}\n"
          f"\n\tSTDERR:\n{p.stderr.decode('utf8')}\n")
    return p.returncode == 0


def was_ghostscript_found() -> bool:
    p = subprocess.run(['gs', '-v'], capture_output=True, check=True)
    debug(f"Ghostscript results:"
          f"\n\tSTDOUT:\n{p.stdout.decode('utf8')}\n"
          f"\n\tSTDERR:\n{p.stderr.decode('utf8')}\n")
    return p.returncode == 0


def was_pygmentize_found() -> bool:
    """


        # from pygments.formatters import LatexFormatter
        # print(LatexFormatter().get_style_defs())
    :return:
    """
    p = subprocess.run(['pygmentize', '-h'], capture_output=True, check=True)
    debug(f"Pygmentize results:"
          f"\n\tSTDOUT:\n{p.stdout.decode('utf8')}\n"
          f"\n\tSTDERR:\n{p.stderr.decode('utf8')}\n")
    return p.returncode == 0


def return_pygmentize_lexers() -> T.Dict[str, T.Set[str]]:
    # Assumes pygmentize was found...
    p = subprocess.run(['pygmentize', '-L', 'lexers'], capture_output=True, check=True)
    lexer_stdout = p.stdout.decode('utf8')

    regex_iter = re.finditer(
        pattern=r'^\* ([^,:]+)[^:]*:\n\s+.*?\(filenames(.*)\)',
        string=lexer_stdout,
        flags=re.MULTILINE,
    )

    if p.returncode != 0:
        raise OSError("Calling pygmentize to get the lexers FAILED!")

    lexer_map = dict()

    for m in regex_iter:
        lexer, filenames = m.groups()
        lexer_map[lexer] = [f.strip() for f in filenames.split(',')]

    return lexer_map


def was_pandas_found() -> bool:
    import importlib.util
    import sys

    # For illustrative purposes.
    name = 'itertools'

    if name in sys.modules:
        print(f"{name!r} already in sys.modules")
    elif (spec := importlib.util.find_spec(name)) is not None:
        # If you choose to perform the actual import ...
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        print(f"{name!r} has been imported")
    else:
        print(f"can't find the {name!r} module")
    return True


if __name__ == '__main__':
    was_pdflatex_found()
    was_ghostscript_found()
    was_pygmentize_found()
    return_pygmentize_lexers()
