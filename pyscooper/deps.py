#! /usr/bin/env python3

import typing as T
import re
import tempfile
import pathlib
import subprocess
import itertools

from pyscooper.cli_utils import debug, info


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


def get_pygmentize_lexers() -> T.Dict[str, T.Set[str]]:
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
        lexer_map[lexer.strip()] = sorted({f.strip().lower() for f in filenames.split(',')})

    return lexer_map


def was_pandas_found() -> bool:
    try:
        import pandas as pd
        return True
    except ModuleNotFoundError:
        pass
    return False


PYGMENTIZE_OK = was_pygmentize_found()
PANDAS_OK = was_pandas_found()
PDFLATEX_OK = was_pdflatex_found()
GHOSTSCRIPT_OK = was_ghostscript_found()

if __name__ == '__main__':
    was_pdflatex_found()
    was_ghostscript_found()
    was_pygmentize_found()

    # Use this to generate the MINTED_LEXERS dictionary!
    if was_pygmentize_found():
        MINTED_LEXERS = get_pygmentize_lexers()
        MINTED_EXTS = set()
        EXT2LEXER = dict()
        if PYGMENTIZE_OK:
            MINTED_LEXERS = get_pygmentize_lexers()
            repeated_globs = set()
            for lexer, exts in MINTED_LEXERS.items():
                for ext in exts:
                    if ext in MINTED_EXTS:
                        repeated_globs.add(ext)
                    else:
                        MINTED_EXTS.add(ext)
                        EXT2LEXER[ext] = lexer
                        # EXT_MAP[ext] = scoop_minted_fcn(lexer)

            if repeated_globs:
                MINTED_EXTS = MINTED_EXTS.difference(repeated_globs)
                for k in repeated_globs:
                    EXT2LEXER.pop(k)
            info("Unique extensions")
            info('\n'.join([f"'{k}' : '{vs}' , " for k, vs in EXT2LEXER.items()]))

            if repeated_globs:
                debug('\n\t> '.join([f"[{len(repeated_globs)}] Non-unique extensions"] + sorted(repeated_globs)))
                # debug('\n'.join([f"'{k}' :{vs}, " for k, vs in MINTED_LEXERS.items()
                #                  if any(v for v in vs if v in repeated_globs)]))
