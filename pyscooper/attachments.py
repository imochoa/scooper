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


def centering(fcn):
    @functools.wraps(fcn)
    def wrapper(*args, **kwargs):
        return "\n" + r"\begin{centering}" + f"\n{fcn(*args, **kwargs)}\n" + r"\end{centering}" + "\n"

    return wrapper


def vspace(fcn):
    @functools.wraps(fcn)
    def wrapper(*args, **kwargs):
        return "\n\t" + r"\vspace*{\fill}" + f"\n{fcn(*args, **kwargs)}\n\t" + r"\vspace*{\fill}" + "\n"

    return wrapper


def pagebreak_after(fcn):
    @functools.wraps(fcn)
    def wrapper(*args, **kwargs):
        return f"{fcn(*args, **kwargs)}\n" + r"\pagebreak" + "\n"

    return wrapper


@blank_pad
@pagebreak_after
@centering
@vspace
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


@tex_centering()
def scoop_vid(file: pathlib.Path) -> str:
    return "TODO"


@tex_centering()
def scoop_song(file: pathlib.Path) -> str:
    return "TODO"


@tex_centering()
def scoop_3d(file: pathlib.Path) -> str:
    return "TODO "


# Minted scoopers -> All the same with different types
def scoop_minted_fcn(lexer: str) -> T.Callable[[pathlib.Path], str]:
    @blank_pad
    def wrapped(file: pathlib.Path, ) -> str:
        return r'\inputminted{' + str(lexer) + r"}{" + sanitize_path(file.absolute()) + r'}'

    return wrapped


EXT_MAP = {
    '.jpg': scoop_img,
    '.jpeg': scoop_img,
    '.png': scoop_img,
    '.txt': scoop_text,
    '.log': scoop_text,
    # '.svg': 'todo',
    # '.eps': 'todo',
    # '.csv': 'todo',
    # '.tsv': 'todo',
    '.pdf': scoop_pdf,
    '.mp4': scoop_vid,
    # '.gif': 'todo',
    '.mp3': scoop_song,
}

# TODO Autogenerate them!
# TODO change to filename globs? (to match eg "Dockerfile ...")
MINTED_LEXERS = {
    'python': ['.py', ],
    'json': ['.json', ],
    'sh': ['.sh'],
    'bash': ['.bash', '.bashrc', ],
    'zsh': ['.zsh', '.zshrc', ],
    'html': ['.html', '.htm', '.xhtml', '.xslt'],
    'css': ['.css'],
    'javascript': ['.js', '.jsm', '.mjs', ],
    'cmake': ['.cmake', ],
    'docker': ['.docker', ],
    'cpp': ['.cpp', '.hpp', '.c++', '.h++', '.cc', '.hh', '.cxx', '.hxx'],
    'xml': ['.xml', '.xsl', '.rss', '.xslt', '.xsd', '.wsdl', '.wsf', ]
}

MINTED_EXTS = set()

for lexer, exts in MINTED_LEXERS.items():
    for ext in exts:
        MINTED_EXTS.add(ext)
        EXT_MAP[ext] = scoop_minted_fcn(lexer)

VALID_EXTS = set(EXT_MAP.keys())


def scoop(file: pathlib.Path) -> str:
    """
    Return a command that will load the contents of *file* and insert them in the PDF
    As long as *file* has one of the accepted extensions
    """
    return EXT_MAP[file.suffix.lower()](file)


if __name__ == '__main__':
    print(scoop_img('hoho'))
