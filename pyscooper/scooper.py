#! /usr/bin/env python3

# std imports
from typing import Union, List, Optional, Dict, Set, Tuple, Sequence
import os
import pathlib
import glob
import shutil
import argparse
import itertools
import subprocess
import tempfile
from collections import namedtuple

# pip imports

# Image compression?
#  >>> from PIL import Image
#  # My image is a 200x374 jpeg that is 102kb large
#  >>> foo = Image.open("path\\to\\image.jpg")
#  >>> foo.size
#   (200,374)
#  # I downsize the image with an ANTIALIAS filter (gives the highest quality)
#  >>> foo = foo.resize((160,300),Image.ANTIALIAS)
#  >>> foo.save("path\\to\\save\\image_scaled.jpg",quality=95)
#  # The saved downsized image size is 24.8kb
#  >>> foo.save("path\\to\\save\\image_scaled_opt.jpg",optimize=True,quality=95)
#  # The saved downsized image size is 22.9kb


Resource = namedtuple('Resource', ['path', 'name'])

TEX_TEMPLATE = pathlib.Path(__file__).parent / 'template.tex'
SPLIT_TEXT = '% ---- PYTHON AUTO-SPLIT ----'

VALID_EXTS = {'.jpeg', '.jpg', '.png', '.pdf', }


def sanitize_tex(in_str: object) -> str:
    return (str(in_str)
            .replace('$', '')
            .replace('%', '')
            .replace('_', ' '))


def tree(path: pathlib.Path, max_depth: int = 0, _depth: int = 0) -> Dict[str, pathlib.Path]:
    if path.is_file():
        return path
    elif path.is_dir() and (max_depth <= 0 or _depth < max_depth):
        k_and_v = ((str(f.relative_to(path)), tree(f, max_depth=max_depth, _depth=_depth + 1))
                   for f in path.iterdir())
        return {k: v for k, v in k_and_v if v}


# def toc_tree(filemap: Union[Dict[str, pathlib.Path], pathlib.Path], _prefix=None) -> Dict[str, str]:
#     if _prefix is None:
#         _prefix = tuple()
#
#     if isinstance(filemap, dict):
#         return_d = dict()
#         for k, v in filemap.items():
#             if not isinstance(v, dict):
#                 return_d[_prefix + (k,)] = toc_tree(v, _prefix=_prefix + (k,))
#             else:
#                 return_d.update(toc_tree(v, _prefix=_prefix + (k,)))
#
#         return return_d
#
#     return filemap


def build_toc_tree(path: pathlib.Path,
                   max_depth: int = 0,
                   valid_exts: Set[str] = VALID_EXTS,
                   _prefix: Optional[Tuple[str]] = tuple(),
                   ) -> Dict[pathlib.Path, Tuple[str]]:
    if path.is_file() and path.suffix.lower() in valid_exts:
        return {path: _prefix + (path.name,)}
    elif path.is_dir() and (max_depth <= 0 or len(_prefix) < max_depth):
        f_trees = (build_toc_tree(f,
                                  max_depth=max_depth,
                                  valid_exts=valid_exts,
                                  _prefix=_prefix + (path.name,),
                                  ) for f in path.iterdir()
                   )
        f_trees = (ft for ft in f_trees if ft)
        out_d = dict()
        for ft in f_trees:
            out_d.update(ft)
        return out_d


def sort_toc_maps(*args: Sequence[Dict[pathlib.Path, Tuple[str]]]):
    global_toc_tree = dict()
    for toc_tree in args:
        global_toc_tree.update(toc_tree)

    return [(k, global_toc_tree[k])
            for k in
            sorted(global_toc_tree, key=lambda k: (len(global_toc_tree[k]), ' '.join(global_toc_tree[k])))]


# ans_d = build_toc_tree(pathlib.Path('/home/ignacio/PycharmProjects/scooper'))
#
# sort_toc_maps(ans_d)


# ans_d = tree(pathlib.Path('/home/ignacio/PycharmProjects/scooper'))
# ans_l = toc_tree(ans_d)
# print('\n'.join([str(k) for k in sorted(ans_l, key=lambda k: ''.join(k))]))


def export_tex_doc(tex_body: str, out_path: Union[str, pathlib.Path]) -> None:
    tex_splits = ['']
    with open(TEX_TEMPLATE, 'r') as fp:
        for line in fp:
            if line.strip() != SPLIT_TEXT:
                tex_splits[-1] += line
            else:
                tex_splits.append('')

    prefix = tex_splits[0:1]
    suffix = tex_splits[2:3]

    with open(out_path, 'w') as fp:
        fp.write('\n'.join(itertools.chain(prefix, [tex_body], suffix)))


def scoop_img(file: pathlib.Path) -> str:
    return '\n'.join(
        [r'\begin{centering}',
         r'\vspace*{\fill}',
         r'\includegraphics[width=\linewidth]{' + str(file.absolute()) + r'}',
         r'\vspace*{\fill}',
         r'\end{centering}',
         r'\pagebreak',
         r'',
         ])


def scoop_text(file: pathlib.Path) -> str:
    with open(file, 'r') as fp:
        contents = '\n'.join(fp.readlines())

    return '\n'.join(
        [r'\begin{centering}',
         r'\vspace*{\fill}',
         f"\n\n{contents}\n\n",
         r'\vspace*{\fill}',
         r'\end{centering}',
         r'\pagebreak',
         r'',
         ])


def scoop_pdf(file: pathlib.Path) -> str:
    return '\n'.join(
        [r'\begin{centering}',
         r'\vspace*{\fill}',
         r'\includepdf[pages=-,pagecommand={},width=\linewidth]{' + str(file.absolute()) + r'}',
         r'\vspace*{\fill}',
         r'\end{centering}',
         r'',
         ])


def scoop_vid(file: pathlib.Path) -> str:
    # TODO

    return '\n'.join(
        [r'\begin{centering}',
         r'\vspace*{\fill}',
         r'TODO',
         r'\vspace*{\fill}',
         r'\end{centering}',
         r'',
         ])


def scoop_3d(file: pathlib.Path) -> str:
    # TODO
    return '\n'.join(
        [r'\begin{centering}',
         r'\vspace*{\fill}',
         r'TODO',
         r'\vspace*{\fill}',
         r'\end{centering}',
         r'',
         ])


EXT_MAP = {
    '.jpg':  scoop_img,
    '.jpeg': scoop_img,
    '.png':  scoop_img,
    '.tex':  scoop_text,
    '.txt':  scoop_text,
    '.log':  scoop_text,
    '.pdf':  scoop_pdf,
    '.mp4':  scoop_vid,
}


def scoop(file: pathlib.Path) -> str:
    # TODO BUILD TOD ENTRY HERE!

    # def generate_toc_component(file: pathlib.Path, relative_to: Optional[pathlib.Path] = None):
    #     if relative_to:
    #         section_name = file.relative_to(relative_to)
    #     # TODO
    #     print("WTF")
    #     return '\n'.join([r'\phantomsection',
    #                       r'\addcontentsline{toc}{section}{\protect{' + str(file.stem) + r'}}',
    #                       r'',
    #                       ])

    #
    #
    # toc_component = '\n'.join(
    #     [r'\phantomsection',
    #      r'\addcontentsline{toc}{section}{\protect{' + str(file.stem).replace('$', '').replace('%', '').replace('_',
    #                                                                                                             ' ')
    #      + r'}}',
    #
    #      r'',
    #      ])

    return EXT_MAP[file.suffix.lower()](file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("sources",
                        nargs='*',
                        type=str,
                        default=pathlib.Path.cwd(),
                        help="What to include in the scoop: (files [JPG,PNG,PDF,MP3,MP4], directories, globs [*.jpg])",
                        )

    parser.add_argument('-r', '--recursive',
                        action='store_true',
                        help="Go down into each directory")

    args = parser.parse_args()

    sources = args.sources if isinstance(args.sources, list) else [args.sources]
    sources = [pathlib.Path(s).expanduser() for s in sources]  # For pre-expanded globs

    # Top-level files (can be overwritten by the glob matches)
    top_files = {f for f in sources if f.is_file() and f.suffix.lower() in VALID_EXTS}
    top_dirs = {d for d in sources if d.is_dir()}
    other_strings = sorted(map(str, set(sources).difference(top_files).difference(top_dirs)))
    glob_strings = [s for s in other_strings if '*' in s]
    other_strings = [s for s in other_strings if s not in glob_strings]
    if other_strings:
        print('\n\t>'.join([f"Did not know how to handle {len(other_strings)} inputs:"] + other_strings))

    toc_map = {f: (f.name,) for f in top_files}  # Direct files have the least priority

    for d in top_dirs:
        toc_map.update(build_toc_tree(d))

    for glob_str in glob_strings:
        glob_root = pathlib.Path(glob_str)
        glob_root_idx = next((idx for idx, s in enumerate(glob_root.parts[::-1]) if '*' not in s))
        glob_root = pathlib.Path(*glob_root.parts[:-glob_root_idx - 1])

        glob_res = glob.glob(str(glob_str), recursive=args.recursive)
        glob_res = (pathlib.Path(f) for f in glob_res)
        glob_res = (f for f in glob_res if f.is_file())

        toc_map.update({glob_f: glob_f.relative_to(glob_root).parts for glob_f in glob_res})

    tex_body = ''

    current_toc_position = [None, None, None]

    for f, toc_entry in sort_toc_maps(toc_map):
        toc_entry = list(toc_entry)

        # New subsubsection?
        s = slice(2, 3)
        # not_s = slice(0, 2)
        if toc_entry[s] and current_toc_position[s] != toc_entry[s]:
            current_toc_position[s] = toc_entry[s]
            title = sanitize_tex('/'.join(toc_entry[2:]))
            tex_body += r'\newsubsubsection{' + title + r'}'

        # New subsection
        s = slice(1, 2)
        if toc_entry[s] and current_toc_position[s] != toc_entry[s]:
            current_toc_position[s] = toc_entry[s]
            current_toc_position[2:] = [None]
            title = sanitize_tex(toc_entry[s][0])
            tex_body += r'\newsubsection{' + title + r'}'

        # New section
        s = slice(0, 1)
        if toc_entry[s] and current_toc_position[s] != toc_entry[s]:
            current_toc_position[s] = toc_entry[s]
            current_toc_position[1:] = [None, None]
            title = sanitize_tex(toc_entry[s][0])
            tex_body += r'\newsection{' + title + r'}'

        tex_body += scoop(f)

    with tempfile.TemporaryDirectory() as tmp:

        tmp_dir = pathlib.Path(tmp)
        src_tex = tmp_dir / 'src.tex'

        export_tex_doc(tex_body=tex_body, out_path=src_tex, )

        cmd = ['pdflatex',
               '-output-directory',
               str(tmp_dir),
               str(src_tex),
               ]
        p1 = subprocess.run(cmd)
        p2 = subprocess.run(cmd)

        if p1.returncode == 0 and p2.returncode == 0:
            pdf_path = next(tmp_dir.glob('*.pdf'))
            dst_path = pathlib.Path().cwd() / pdf_path.name

            # TODO Skip if ghostscript is missing...

            # # MOVE
            # if dst_path.is_file():
            #     os.remove(dst_path)
            # shutil.move(src=str(pdf_path), dst=str(dst_path))

            # COMPRESS
            # https://github.com/pts/pdfsizeopt
            print("Trying to compress the pdf...")

            prev_size = pdf_path.stat().st_size / 1e6  # [Mb]
            compress_cmd = ['gs',
                            '-sDEVICE=pdfwrite',
                            '-dCompatibilityLevel=1.5',
                            '-dNOPAUSE',
                            '-dQUIET',
                            '-dBATCH',
                            '-dPrinted=false',
                            f'-sOutputFile="{dst_path}"',
                            f'"{pdf_path}"',
                            ]
            post_size = dst_path.stat().st_size / 1e6  # [Mb]

            p3 = subprocess.run(compress_cmd)
            # gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.5 -dNOPAUSE -dQUIET -dBATCH -dPrinted=false -sOutputFile=foo-compressed.pdf foo.pdf
            if p3.returncode == 0:
                print(f"Compression reduced the output PDF size from "
                      f"{prev_size:.2f}[Mb] to {post_size:.2f}[Mb] ({(post_size - prev_size) / prev_size:+.1%})")
                print(f"Wrote {dst_path}!")
                print(f"Wrote {dst_path}!")
                print(f"Wrote {dst_path}!")
            else:
                print("OOPS")

        else:
            print("meow")
