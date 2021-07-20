#! /usr/bin/env python3

# std imports
import logging
import typing as T
import pathlib
import functools


def sanitize_path(in_str: T.Union[pathlib.Path, str], ) -> str:
    return (str(in_str)
            .replace(' ', r'\space ')
            )


def parametrized(dec):
    """This decorator can be used to create other decorators that accept arguments"""

    def layer(*args, **kwargs):
        def repl(f):
            return dec(f, *args, **kwargs)

        return repl

    return layer


@parametrized
def tex_centering(fcn, add_pagebreak: bool = False):
    def wrapper(p):
        out_str = "\n".join(
            ["",
             r"\begin{centering}",
             r"    \vspace*{\fill}",
             f"        {fcn(p)}",
             r"    \vspace*{\fill}",
             r"\end{centering}",
             "",
             ]
        )

        if add_pagebreak:
            out_str += "\n" + r"\pagebreak" + "\n"
        return out_str

    return wrapper


def blank_pad(fcn):
    @functools.wraps(fcn)
    def wrapper(*args, **kwargs):
        pad = '\n' * 2
        return f"{pad}{fcn(*args, **kwargs)}{pad}"

    return wrapper


@blank_pad
@tex_centering(add_pagebreak=True)
def scoop_img(file: pathlib.Path, width: None = None, ) -> str:
    return r'\includegraphics[width=\linewidth]{' + sanitize_path(file.absolute()) + r'}'


@blank_pad
@tex_centering()
def scoop_text(file: pathlib.Path) -> str:
    try:
        with open(file, 'r') as fp:
            contents = '\n'.join(fp.readlines())

    except FileNotFoundError as e:
        logging.exception(exc_info=True)
        contents = f"FILE DID NOT EXIST"
    return contents


@blank_pad
def scoop_pdf(file: pathlib.Path, ) -> str:
    return r'\includepdf[pages=-,pagecommand={},width=\linewidth]{' + sanitize_path(file.absolute()) + r'}'
    #
    # return '\n'.join(
    #     [
    #         r'',
    #         r'\begin{centering}',
    #         r'\vspace*{\fill}',
    #         r'\includepdf[pages=-,pagecommand={},width=\linewidth]{' + sanitize_path(file.absolute()) + r'}',
    #         r'\vspace*{\fill}',
    #         r'\end{centering}',
    #         r'',
    #     ])


@tex_centering()
def scoop_vid(file: pathlib.Path) -> str:
    return "TODO"


@tex_centering()
def scoop_song(file: pathlib.Path) -> str:
    return "TODO"


@tex_centering()
def scoop_3d(file: pathlib.Path) -> str:
    return "TODO "


EXT_MAP = {
    '.jpg': scoop_img,
    '.jpeg': scoop_img,
    '.png': scoop_img,
    '.tex': scoop_text,
    '.txt': scoop_text,
    '.log': scoop_text,
    '.py': scoop_text,
    '.pdf': scoop_pdf,
    '.mp4': scoop_vid,
    '.mp3': scoop_song,
}

VALID_EXTS = set(EXT_MAP.keys())


def scoop(file: pathlib.Path) -> str:
    """
    Return a command that will load the contents of *file* and insert them in the PDF
    As long as *file* has one of the accepted extensions
    """
    return EXT_MAP[file.suffix.lower()](file)


if __name__ == '__main__':
    print(scoop_img('hoho'))
