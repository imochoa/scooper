#! /usr/bin/env python3

# std imports
import logging
import typing as T
import pathlib
import functools
import glob
import fnmatch

from pyscooper.tex_utils import sanitize_tex
from pyscooper.deps import PYGMENTIZE_OK, get_pygmentize_lexers
from pyscooper.cli_utils import debug, info, warning, error


class TOCFile:

    def __init__(self, filepath: pathlib.Path, keypath: T.Tuple[str], ext_key: T.Optional[str] = None):
        self.filepath = filepath
        self.ext_key = ext_key if ext_key is not None else ext_match(filepath)
        self.keypath = keypath  # To the PARENT dir!

    def __repr__(self):
        return (f"<{self.__class__}"
                f" filepath={self.filepath}"
                f", ext_key={self.ext_key}"
                f", keypath={self.keypath}"
                ">")


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


def verbatim(fcn):
    def wrapper(p):
        return "\n".join(
            ["",
             r"\begin{verbatim}",
             f"{fcn(p)}",
             r"\end{verbatim}",
             "",
             ]
        )

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
@pagebreak_after
@centering
@verbatim
def scoop_text(file: pathlib.Path) -> str:
    with open(file, 'r') as fp:
        contents = sanitize_tex('\n'.join(fp.readlines()))
    # Ensure the encodings are OK
    encoding = 'ascii'  # Safe for TeX
    # encoding='utf-8' # Should work... might be riskier for TeX
    contents = contents.encode(encoding, 'ignore').decode(encoding)
    return contents


@blank_pad
def scoop_pdf(file: pathlib.Path, ) -> str:
    return r'\includepdf[pages=-,pagecommand={},width=\linewidth]{' + sanitize_path(file.absolute()) + r'}'


@blank_pad
@pagebreak_after
@centering
def scoop_vid(file: pathlib.Path) -> str:
    return "TODO"


@blank_pad
@pagebreak_after
@centering
def scoop_song(file: pathlib.Path) -> str:
    return "TODO"


@blank_pad
@pagebreak_after
@centering
def scoop_3d(file: pathlib.Path) -> str:
    return "TODO "


# Minted scoopers -> All the same with different types
def scoop_minted_fcn(lexer: str) -> T.Callable[[pathlib.Path], str]:
    @blank_pad
    @pagebreak_after
    def wrapped(file: pathlib.Path, ) -> str:
        return r'\inputminted{' + str(lexer) + r"}{" + sanitize_path(file.absolute()) + r'}'

    return wrapped


EXT_MAP = {
    '*.jpg': scoop_img,
    '*.jpeg': scoop_img,
    '*.png': scoop_img,
    '*.txt': scoop_text,
    '*.log': scoop_text,
    # '*.svg': 'todo',
    # '*.eps': 'todo',
    # '*.csv': 'todo',
    # '*.tsv': 'todo',
    '*.pdf': scoop_pdf,
    '*.mp4': scoop_vid,
    # '*.gif': 'todo',
    '*.mp3': scoop_song,
}

MINTED_LEXERS = dict()
MINTED_EXTS = set()
if PYGMENTIZE_OK:
    unique_ext2lexer = {
        '*.abap': 'abap',
        '*.abnf': 'abnf',
        '*.ada': 'ada',
        '*.adb': 'ada',
        '*.ads': 'ada',
        '*.adl': 'adl',
        '*.adlf': 'adl',
        '*.adls': 'adl',
        '*.adlx': 'adl',
        '*.agda': 'agda',
        '*.aheui': 'aheui',
        '*.als': 'alloy',
        '*.at': 'ambienttalk',
        '*.isa': 'amdgpu',
        '*.run': 'ampl',
        '*.ans': 'ansys',
        '.htaccess': 'apacheconf',
        'apache.conf': 'apacheconf',
        'apache2.conf': 'apacheconf',
        '*.apl': 'apl',
        '*.aplc': 'apl',
        '*.aplf': 'apl',
        '*.apli': 'apl',
        '*.apln': 'apl',
        '*.aplo': 'apl',
        '*.dyalog': 'apl',
        '*.applescript': 'applescript',
        '*.ino': 'arduino',
        '*.arw': 'arrow',
        '*.aj': 'aspectj',
        '*.asy': 'asymptote',
        '*.aug': 'augeas',
        '*.ahk': 'autohotkey',
        '*.ahkl': 'autohotkey',
        '*.au3': 'autoit',
        '*.awk': 'awk',
        '*.bare': 'bare',
        '*.bash': 'bash',
        '*.ebuild': 'bash',
        '*.eclass': 'bash',
        '*.exheres-0': 'bash',
        '*.exlib': 'bash',
        '*.ksh': 'bash',
        '*.sh': 'bash',
        '*.zsh': 'bash',
        '.bash_*': 'bash',
        '.bashrc': 'bash',
        '.zshrc': 'bash',
        'bash_*': 'bash',
        'bashrc': 'bash',
        'pkgbuild': 'bash',
        'zshrc': 'bash',
        '*.bat': 'batch',
        '*.cmd': 'batch',
        '*.bbc': 'bbcbasic',
        '*.bc': 'bc',
        '*.befunge': 'befunge',
        '*.bib': 'bibtex',
        '*.bb': 'blitzbasic',
        '*.decls': 'blitzbasic',
        '*.bmx': 'blitzmax',
        '*.bnf': 'bnf',
        '*.boa': 'boa',
        '*.boo': 'boo',
        '*.bpl': 'boogie',
        '*.bf': 'brainfuck',
        '*.bst': 'bst',
        '*.c-objdump': 'c-objdump',
        '*.idc': 'c',
        '*.cadl': 'cadl',
        '*.camkes': 'camkes',
        '*.idl4': 'camkes',
        '*.cdl': 'capdl',
        '*.capnp': 'capnp',
        '*.cddl': 'cddl',
        '*.ceylon': 'ceylon',
        '*.cfc': 'cfc',
        '*.cf': 'cfengine3',
        '*.cfm': 'cfm',
        '*.cfml': 'cfm',
        '*.chai': 'chaiscript',
        '*.chpl': 'chapel',
        '*.ci': 'charmci',
        '*.spt': 'cheetah',
        '*.tmpl': 'cheetah',
        '*.cirru': 'cirru',
        '*.clay': 'clay',
        '*.dcl': 'clean',
        '*.icl': 'clean',
        '*.clj': 'clojure',
        '*.cljs': 'clojurescript',
        '*.cmake': 'cmake',
        'cmakelists.txt': 'cmake',
        '*.cob': 'cobol',
        '*.cpy': 'cobol',
        '*.cbl': 'cobolfree',
        '*.coffee': 'coffeescript',
        '*.cl': 'common-lisp',
        '*.lisp': 'common-lisp',
        '*.cps': 'componentpascal',
        '*.sh-session': 'console',
        '*.shell-session': 'console',
        '*.c++': 'cpp',
        '*.cc': 'cpp',
        '*.cpp': 'cpp',
        '*.cxx': 'cpp',
        '*.h++': 'cpp',
        '*.hpp': 'cpp',
        '*.hxx': 'cpp',
        '*.c++-objdump': 'cpp-objdump',
        '*.cpp-objdump': 'cpp-objdump',
        '*.cxx-objdump': 'cpp-objdump',
        '*.cpsa': 'cpsa',
        '*.cr': 'cr',
        '*.crmsh': 'crmsh',
        '*.pcmk': 'crmsh',
        '*.croc': 'croc',
        '*.cry': 'cryptol',
        '*.cs': 'csharp',
        '*.orc': 'csound',
        '*.udo': 'csound',
        '*.csd': 'csound-document',
        '*.sco': 'csound-score',
        '*.css.in': 'css+mozpreproc',
        '*.css': 'css',
        '*.cu': 'cuda',
        '*.cuh': 'cuda',
        '*.cyp': 'cypher',
        '*.cypher': 'cypher',
        '*.pxd': 'cython',
        '*.pxi': 'cython',
        '*.pyx': 'cython',
        '*.d-objdump': 'd-objdump',
        '*.d': 'd',
        '*.di': 'd',
        '*.dart': 'dart',
        '*.dasm': 'dasm16',
        '*.dasm16': 'dasm16',
        'control': 'debcontrol',
        'sources.list': 'debsources',
        '*.dpr': 'delphi',
        '*.pas': 'delphi',
        '*.dts': 'devicetree',
        '*.dtsi': 'devicetree',
        '*.dg': 'dg',
        '*.diff': 'diff',
        '*.patch': 'diff',
        '*.docker': 'docker',
        'dockerfile': 'docker',
        '*.darcspatch': 'dpatch',
        '*.dpatch': 'dpatch',
        '*.dtd': 'dtd',
        '*.duel': 'duel',
        '*.jbst': 'duel',
        '*.dylan-console': 'dylan-console',
        '*.hdp': 'dylan-lid',
        '*.lid': 'dylan-lid',
        '*.dyl': 'dylan',
        '*.dylan': 'dylan',
        '*.intr': 'dylan',
        '*.eg': 'earl-grey',
        '*.ezt': 'easytrieve',
        '*.mac': 'easytrieve',
        '*.ebnf': 'ebnf',
        '*.ec': 'ec',
        '*.eh': 'ec',
        '*.e': 'eiffel',
        '*.eex': 'elixir',
        '*.ex': 'elixir',
        '*.exs': 'elixir',
        '*.leex': 'elixir',
        '*.elm': 'elm',
        '*.el': 'emacs-lisp',
        '*.eml': 'email',
        '*.erl-sh': 'erl',
        '*.erl': 'erlang',
        '*.es': 'erlang',
        '*.escript': 'erlang',
        '*.hrl': 'erlang',
        '*.evoque': 'evoque',
        '*.exec': 'execline',
        '*.xtm': 'extempore',
        '*.factor': 'factor',
        '*.fan': 'fan',
        '*.fancypack': 'fancy',
        '*.fy': 'fancy',
        '*.flx': 'felix',
        '*.flxh': 'felix',
        '*.fnl': 'fennel',
        '*.fish': 'fish',
        '*.load': 'fish',
        '*.flo': 'floscript',
        '*.frt': 'forth',
        '*.f03': 'fortran',
        '*.f90': 'fortran',
        '*.f': 'fortranfixed',
        '*.prg': 'foxpro',
        '*.edp': 'freefem',
        '*.fsi': 'fsharp',
        '*.fst': 'fstar',
        '*.fsti': 'fstar',
        '*.fut': 'futhark',
        '*.gap': 'gap',
        '*.gi': 'gap',
        '*.gcode': 'gcode',
        '*.kid': 'genshi',
        '*.feature': 'gherkin',
        '*.frag': 'glsl',
        '*.geo': 'glsl',
        '*.vert': 'glsl',
        '*.plot': 'gnuplot',
        '*.plt': 'gnuplot',
        '*.go': 'go',
        '*.golo': 'golo',
        '*.gdc': 'gooddata-cl',
        '*.gs': 'gosu',
        '*.gsp': 'gosu',
        '*.gsx': 'gosu',
        '*.vark': 'gosu',
        '*.dot': 'graphviz',
        '*.gv': 'graphviz',
        '*.[1234567]': 'groff',
        '*.man': 'groff',
        '*.gradle': 'groovy',
        '*.groovy': 'groovy',
        '*.gst': 'gst',
        '*.haml': 'haml',
        '*.hs': 'haskell',
        '*.hx': 'haxe',
        '*.hxsl': 'haxe',
        '*.hxml': 'haxeml',
        '*.hlsl': 'hlsl',
        '*.hlsli': 'hlsl',
        '*.hsail': 'hsail',
        '*.handlebars': 'html+handlebars',
        '*.hbs': 'html+handlebars',
        '*.ng2': 'html+ng2',
        '*.phtml': 'html+php',
        '*.twig': 'html+twig',
        '*.htm': 'html',
        '*.xhtml': 'html',
        '*.hyb': 'hybris',
        '*.i6t': 'i6t',
        '*.icon': 'icon',
        '*.idr': 'idris',
        '*.ipf': 'igor',
        '*.i7x': 'inform7',
        '*.ni': 'inform7',
        '*.cfg': 'ini',
        '*.ini': 'ini',
        '*.io': 'io',
        '*.ik': 'ioke',
        '*.weechatlog': 'irc',
        '*.thy': 'isabelle',
        '*.ijs': 'j',
        '*.jag': 'jags',
        '*.java': 'java',
        '*.js.in': 'javascript+mozpreproc',
        '*.cjs': 'javascript',
        '*.js': 'javascript',
        '*.jsm': 'javascript',
        '*.mjs': 'javascript',
        '*.jcl': 'jcl',
        '*.jsgf': 'jsgf',
        '*.json': 'json',
        'pipfile.lock': 'json',
        '*.jsonld': 'jsonld',
        '*.jsp': 'jsp',
        '*.jl': 'julia',
        '*.juttle': 'juttle',
        '*.kal': 'kal',
        '*config.in*': 'kconfig',
        'external.in*': 'kconfig',
        'kconfig*': 'kconfig',
        'standard-modules.in': 'kconfig',
        '*.dmesg': 'kmsg',
        '*.kmsg': 'kmsg',
        '*.kk': 'koka',
        '*.kki': 'koka',
        '*.kt': 'kotlin',
        '*.kts': 'kotlin',
        '*.kn': 'kuin',
        '*.lasso': 'lasso',
        '*.lasso[89]': 'lasso',
        '*.lean': 'lean',
        '*.less': 'less',
        'lighttpd.conf': 'lighttpd',
        '*.liquid': 'liquid',
        '*.lagda': 'literate-agda',
        '*.lcry': 'literate-cryptol',
        '*.lhs': 'literate-haskell',
        '*.lidr': 'literate-idris',
        '*.ls': 'livescript',
        '*.mir': 'llvm-mir',
        '*.ll': 'llvm',
        '*.x': 'logos',
        '*.xi': 'logos',
        '*.xm': 'logos',
        '*.xmi': 'logos',
        '*.lgt': 'logtalk',
        '*.logtalk': 'logtalk',
        '*.lsl': 'lsl',
        '*.lua': 'lua',
        '*.wlua': 'lua',
        '*.mak': 'make',
        '*.mk': 'make',
        'gnumakefile': 'make',
        'makefile': 'make',
        'makefile.*': 'make',
        '*.mao': 'mako',
        '*.maql': 'maql',
        '*.markdown': 'markdown',
        '*.md': 'markdown',
        '*.mask': 'mask',
        '*.mc': 'mason',
        '*.mhtml': 'mason',
        '*.mi': 'mason',
        'autohandler': 'mason',
        'dhandler': 'mason',
        '*.cdf': 'mathematica',
        '*.ma': 'mathematica',
        '*.nb': 'mathematica',
        '*.nbp': 'mathematica',
        '*.ms': 'miniscript',
        '*.mo': 'modelica',
        '*.mod': 'modula2',
        '*.monkey': 'monkey',
        '*.mt': 'monte',
        '*.moo': 'moocode',
        '*.moon': 'moonscript',
        '*.mos': 'mosel',
        '*.mq4': 'mql',
        '*.mq5': 'mql',
        '*.mqh': 'mql',
        '*.msc': 'mscgen',
        '*.mu': 'mupad',
        '*.mxml': 'mxml',
        '*.myt': 'myghty',
        'autodelegate': 'myghty',
        '*.ncl': 'ncl',
        '*.nc': 'nesc',
        '*.nt': 'nestedtext',
        '*.kif': 'newlisp',
        '*.lsp': 'newlisp',
        '*.nl': 'newlisp',
        '*.ns2': 'newspeak',
        'nginx.conf': 'nginx',
        '*.nim': 'nimrod',
        '*.nimrod': 'nimrod',
        '*.nit': 'nit',
        '*.nix': 'nixos',
        '*.nsh': 'nsis',
        '*.nsi': 'nsis',
        '*.smv': 'nusmv',
        '*.objdump-intel': 'objdump-nasm',
        '*.objdump': 'objdump',
        '*.mm': 'objective-c++',
        '*.ml': 'ocaml',
        '*.mli': 'ocaml',
        '*.mll': 'ocaml',
        '*.mly': 'ocaml',
        '*.odin': 'odin',
        '*.idl': 'omg-idl',
        '*.pidl': 'omg-idl',
        '*.ooc': 'ooc',
        '*.opa': 'opa',
        '*.cls': 'openedge',
        'pacman.conf': 'pacmanconf',
        '*.pan': 'pan',
        '*.psi': 'parasail',
        '*.psl': 'parasail',
        '*.pwn': 'pawn',
        '*.peg': 'peg',
        '*.perl': 'perl',
        '*.6pl': 'perl6',
        '*.6pm': 'perl6',
        '*.nqp': 'perl6',
        '*.p6': 'perl6',
        '*.p6l': 'perl6',
        '*.p6m': 'perl6',
        '*.pl6': 'perl6',
        '*.pm6': 'perl6',
        '*.raku': 'perl6',
        '*.rakudoc': 'perl6',
        '*.rakumod': 'perl6',
        '*.rakutest': 'perl6',
        '*.php': 'php',
        '*.php[345]': 'php',
        '*.pig': 'pig',
        '*.pike': 'pike',
        '*.pmod': 'pike',
        '*.pc': 'pkgconfig',
        '*.ptls': 'pointless',
        '*.pony': 'pony',
        '*.eps': 'postscript',
        '*.ps': 'postscript',
        '*.po': 'pot',
        '*.pot': 'pot',
        '*.pov': 'pov',
        '*.ps1': 'powershell',
        '*.psm1': 'powershell',
        '*.praat': 'praat',
        '*.proc': 'praat',
        '*.psc': 'praat',
        '*.prolog': 'prolog',
        '*.promql': 'promql',
        '*.properties': 'properties',
        '*.proto': 'protobuf',
        '*.jade': 'pug',
        '*.pug': 'pug',
        '*.pp': 'puppet',
        '*.py2tb': 'py2tb',
        '*.pypylog': 'pypylog',
        '*.py3tb': 'pytb',
        '*.pytb': 'pytb',
        '*.bzl': 'python',
        '*.jy': 'python',
        '*.py': 'python',
        '*.pyw': 'python',
        '*.sage': 'python',
        '*.tac': 'python',
        'buck': 'python',
        'build': 'python',
        'build.bazel': 'python',
        'sconscript': 'python',
        'sconstruct': 'python',
        'workspace': 'python',
        '*.qbs': 'qml',
        '*.qml': 'qml',
        '*.qvto': 'qvto',
        '*.rkt': 'racket',
        '*.rktd': 'racket',
        '*.rktl': 'racket',
        '*.rout': 'rconsole',
        '*.rd': 'rd',
        '*.re': 'reasonml',
        '*.rei': 'reasonml',
        '*.r3': 'rebol',
        '*.reb': 'rebol',
        '*.red': 'red',
        '*.reds': 'red',
        '*.cw': 'redcode',
        '*.reg': 'registry',
        '*.rest': 'restructuredtext',
        '*.rst': 'restructuredtext',
        '*.arexx': 'rexx',
        '*.rex': 'rexx',
        '*.rexx': 'rexx',
        '*.rx': 'rexx',
        '*.rhtml': 'rhtml',
        '*.ride': 'ride',
        '*.rnc': 'rng-compact',
        '*.graph': 'roboconf-graph',
        '*.instances': 'roboconf-instances',
        '*.robot': 'robotframework',
        '*.rql': 'rql',
        '*.rsl': 'rsl',
        '*.duby': 'ruby',
        '*.gemspec': 'ruby',
        '*.rake': 'ruby',
        '*.rb': 'ruby',
        '*.rbw': 'ruby',
        '*.rbx': 'ruby',
        'gemfile': 'ruby',
        'rakefile': 'ruby',
        '*.rs': 'rust',
        '*.rs.in': 'rust',
        '*.sarl': 'sarl',
        '*.sas': 'sas',
        '*.sass': 'sass',
        '*.scala': 'scala',
        '*.scaml': 'scaml',
        '*.scdoc': 'scdoc',
        '*.scm': 'scheme',
        '*.ss': 'scheme',
        '*.sce': 'scilab',
        '*.sci': 'scilab',
        '*.tst': 'scilab',
        '*.scss': 'scss',
        '*.sgf': 'sgf',
        '*.shen': 'shen',
        '*.shex': 'shexc',
        '*.sieve': 'sieve',
        '*.siv': 'sieve',
        '*.sil': 'silver',
        '*.vpr': 'silver',
        'singularity': 'singularity',
        '*.sla': 'slash',
        '*.slim': 'slim',
        '*.sl': 'slurm',
        '*.smali': 'smali',
        '*.st': 'smalltalk',
        '*.tpl': 'smarty',
        '*.fun': 'sml',
        '*.sig': 'sml',
        '*.sml': 'sml',
        '*.snobol': 'snobol',
        '*.sbl': 'snowball',
        '*.sol': 'solidity',
        '*.sp': 'sp',
        '*.rq': 'sparql',
        '*.sparql': 'sparql',
        '*.spec': 'spec',
        '.renviron': 'splus',
        '.rhistory': 'splus',
        '.rprofile': 'splus',
        '*.sqlite3-console': 'sqlite3',
        'squid.conf': 'squidconf',
        '*.ssp': 'ssp',
        '*.stan': 'stan',
        '*.ado': 'stata',
        '*.do': 'stata',
        '*.swift': 'swift',
        '*.i': 'swig',
        '*.swg': 'swig',
        '*.sv': 'systemverilog',
        '*.svh': 'systemverilog',
        '*.tap': 'tap',
        '*.tasm': 'tasm',
        '*.rvt': 'tcl',
        '*.tcl': 'tcl',
        '*.csh': 'tcsh',
        '*.tcsh': 'tcsh',
        '*.tea': 'tea',
        '*.teal': 'teal',
        'termcap': 'termcap',
        'termcap.src': 'termcap',
        'terminfo': 'terminfo',
        'terminfo.src': 'terminfo',
        '*.tf': 'terraform',
        '*.aux': 'tex',
        '*.tex': 'tex',
        '*.toc': 'tex',
        '*.txt': 'text',
        '*.thrift': 'thrift',
        '*.ti': 'ti',
        '*.tid': 'tid',
        '*.tnt': 'tnt',
        '*.todotxt': 'todotxt',
        'todo.txt': 'todotxt',
        '*.toml': 'toml',
        'pipfile': 'toml',
        'poetry.lock': 'toml',
        '*.rts': 'trafficscript',
        '*.treetop': 'treetop',
        '*.tt': 'treetop',
        '*.ts': 'typescript',
        '*.tsx': 'typescript',
        '*.typoscript': 'typoscript',
        '*.u1': 'ucode',
        '*.u2': 'ucode',
        '*.icn': 'unicon',
        '*.usd': 'usd',
        '*.usda': 'usd',
        '*.vala': 'vala',
        '*.vapi': 'vala',
        '*.vb': 'vb.net',
        '*.vbs': 'vbscript',
        '*.vcl': 'vcl',
        '*.fhtml': 'velocity',
        '*.vm': 'velocity',
        '*.rpf': 'vgl',
        '*.vhd': 'vhdl',
        '*.vhdl': 'vhdl',
        '*.vim': 'vim',
        '.exrc': 'vim',
        '.gvimrc': 'vim',
        '.vimrc': 'vim',
        '_exrc': 'vim',
        '_gvimrc': 'vim',
        '_vimrc': 'vim',
        'gvimrc': 'vim',
        'vimrc': 'vim',
        '*.wast': 'wast',
        '*.wat': 'wast',
        '*.wdiff': 'wdiff',
        '*.webidl': 'webidl',
        '*.whiley': 'whiley',
        '*.x10': 'x10',
        '*.rss': 'xml',
        '*.wsdl': 'xml',
        '*.wsf': 'xml',
        '*.xsd': 'xml',
        'xorg.conf': 'xorg.conf',
        '*.xq': 'xquery',
        '*.xql': 'xquery',
        '*.xqm': 'xquery',
        '*.xquery': 'xquery',
        '*.xqy': 'xquery',
        '*.xpl': 'xslt',
        '*.xtend': 'xtend',
        '*.xul.in': 'xul+mozpreproc',
        '*.sls': 'yaml+jinja',
        '*.yaml': 'yaml',
        '*.yml': 'yaml',
        '*.yang': 'yang',
        '*.bro': 'zeek',
        '*.zeek': 'zeek',
        '*.zep': 'zephir',
        '*.zig': 'zig',
    }
    ambiguous_ext2lexer = {
        '*.c': 'c',
        '*.h': 'c',
        '*.cp': 'cpp',
        '*.hh': 'cpp',
        '*.html': 'cpp',
        '*.xml': 'xml',
        '*.xsl': 'xslt',
        '*.xslt': 'xslt',
        '*.sql': 'sql',
        '*.r': 'rebol',

    }

    manual_tuning = dict()
    for ext, lexer in {**unique_ext2lexer, **ambiguous_ext2lexer, **manual_tuning}.items():
        if ext in EXT_MAP:
            debug(f"Skipping {ext} ...")
            continue
        MINTED_EXTS.add(ext)
        EXT_MAP[ext] = scoop_minted_fcn(lexer)


def ext_match(file: pathlib.Path) -> T.Optional[str]:
    """Return the first valid exension string (key in EXT_MAP) that matches the file OR None if it was not known"""
    l_name = file.name.lower()
    return next((pat for pat in EXT_MAP if fnmatch.fnmatch(name=l_name, pat=pat.lower())),
                None)


def scoop(file: T.Union[pathlib.Path, TOCFile]) -> str:
    """
    Return a command that will load the contents of *file* and insert them in the PDF
    As long as *file* has one of the accepted extensions
    """
    if isinstance(file, pathlib.Path):
        return EXT_MAP[ext_match(file)](file)
    elif isinstance(file, TOCFile):
        return EXT_MAP[file.ext_key](file.filepath)
    raise TypeError(f"Invalid *file* type {file}")


if __name__ == '__main__':
    ext_match(pathlib.Path('/ho/hi/ho/Dockerfile'))
    print(scoop('/path/to/your/image.jpg'))
    print(scoop('/path/to/your/doc.pdf'))
