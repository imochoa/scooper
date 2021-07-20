#! /usr/bin/env python3
import ipdb

# std imports
import typing as T
import pprint
import os
import pathlib
import glob
import shutil
import argparse
import itertools
import subprocess
import tempfile
import uuid

from pyscooper.attachments import scoop, VALID_EXTS
from pyscooper.cli_utils import debug, info, warning, error
# from pyscooper.tableofcontents import build_toc_tree, build_filetree, sort_toc_maps, filemap2tocmap
from pyscooper.tex_utils import (sanitize_tex, export_tex_doc, compile_doc, compress_doc,
                                 tex_section, tex_subsection, tex_subsubsection,
                                 TOC_HEADING_FCN_MAP)
# from pyscooper.tex_template import tex_section, tex_subsection, tex_subsubsection, LATEX_PREFIX, LATEX_SUFFIX
# from pyscooper import VALID_EXTS, Resource, TEX_TEMPLATE, SPLIT_TEXT

from typing import NamedTuple, Any


# class TOCFile(NamedTuple):
#     filepath: pathlib.Path
#     # To the PARENT dir!
#     keypath: T.Tuple[str]

# TODO add joining fcn instead of f"{}/{}"

class TOCFile:

    def __init__(self, filepath: pathlib.Path, keypath: T.Tuple[str], ):
        # To the PARENT dir!
        self.filepath = filepath
        self.keypath = keypath

    def __repr__(self):
        return f"<{self.__class__} filepath={self.filepath}, keypath={self.keypath}>"


def fold_empty_nodes(recd: dict,
                     ) -> T.Tuple[T.Dict, bool]:
    """
    RECURSIVE!

    :param recd:
    :return: updated recd, helper bool)
    """
    # preparation
    dks = [k for k, v in recd.items() if isinstance(v, dict)]
    foldable = len(recd) == 1 and len(dks) == 1

    for k in dks:
        ld, lf = fold_empty_nodes(recd[k])

        if lf:
            [lk] = ld.keys()
            recd[f"{k}/{lk}"] = recd.pop(k).pop(lk)

    return recd, foldable


def extract_entries(recd,
                    keypath=None,
                    ) -> T.List[TOCFile]:
    # preparation
    keypath = keypath or []
    vs = list(recd.values())

    # Exit condition
    if len(vs) == 1 and isinstance(vs[0], pathlib.Path):
        return [TOCFile(filepath=vs[0], keypath=keypath, )]

    res = []
    for k, v in recd.items():
        if isinstance(v, pathlib.Path):
            res.append(TOCFile(filepath=v, keypath=keypath, ))
        else:
            res.extend(extract_entries(v, keypath=keypath + [k]))

    return res


DFEAULT_OUTPDF = pathlib.Path().cwd() / 'out.pdf'

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "sources",
        nargs="*",
        type=str,
        default=pathlib.Path.cwd(),
        help="What to include in the scoop: (files [JPG,PNG,PDF,MP3,MP4], directories, globs [*.jpg])",
    )

    parser.add_argument(
        "-r", "--recursive", action="store_true", help="Go down into each directory"
    )

    parser.add_argument(
        "-o", "--output", type=pathlib.Path, help="Where to save the output PDF", default=DFEAULT_OUTPDF,
    )

    args = parser.parse_args()

    sources = args.sources if isinstance(args.sources, list) else [args.sources]
    sources = [pathlib.Path(s).expanduser() for s in sources]  # For pre-expanded globs

    # Top-level files (can be overwritten by the glob matches)
    top_files = {f for f in sources if f.is_file() and f.suffix.lower() in VALID_EXTS}
    top_dirs = {d for d in sources if d.is_dir()}
    other_strings = sorted(
        map(str, set(sources).difference(top_files).difference(top_dirs))
    )
    # glob_strings = [s for s in other_strings if "*" in s]
    # other_strings = [s for s in other_strings if s not in glob_strings]
    if top_files:
        info(
            "\n\t> ".join(
                [f"Found [{len(top_files)}] files:"] + [str(d) for d in top_files]
            )
        )
    if top_dirs:
        info(
            "\n\t> ".join(
                [f"Found [{len(top_dirs)}] directories:"] + [str(d) for d in top_dirs]
            )
        )
    # if glob_strings:
    #     warning(
    #         "\n\t> ".join(
    #             [f"Expanding {len(glob_strings)} possible globs:"] + glob_strings
    #         )
    #     )
    # if other_strings:
    #     warning(
    #         "\n\t> ".join(
    #             [f"Did not know how to handle {len(other_strings)} inputs:"]
    #             + other_strings
    #         )
    #     )

    # BUILD FILE DICT

    # Top files -> Top level
    filemap = {f.name: f for f in top_files}

    # Dirs and globs -> search!
    for top_dir in top_dirs:
        fs = (f for f in top_dir.rglob('*') if f.is_file())
        fs = (f for f in fs if f.suffix.lower() in VALID_EXTS)
        for f in fs:
            relpath = f.relative_to(top_dir)
            *ancestors, filename = relpath.parts
            aux_dict = filemap
            for ancestor in ancestors:
                aux_dict = aux_dict.setdefault(ancestor, dict())
            aux_dict[filename] = f
    # Collapse first!

    filemap, _ = fold_empty_nodes(filemap)
    entries = extract_entries(filemap)

    # Write LaTeX document
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = pathlib.Path(tmp)
        link_dir = tmp_dir / 'links'
        link_dir.mkdir()

        # Build LaTeX source

        tex_body = ""
        toc_lvl = 0

        for entry in entries:
            last_toc_level = toc_lvl
            toc_lvl = {0: 0,
                       1: 1,
                       }.get(len(entry.keypath), 2)

            toc_entry_fcn = TOC_HEADING_FCN_MAP[toc_lvl]

            # TOC Nesting
            toc_delta = toc_lvl - last_toc_level
            if toc_lvl > last_toc_level:
                try:
                    parts = list(entry.filepath.parts[:-1])
                    folded_dirs = [(p1, p2) for p1, p2 in zip(parts[:-1], parts[1:]) if f"{p1}/{p2}" in entry.keypath]
                    for p1, p2 in folded_dirs[::-1]:
                        p1_idx = parts.index(p1)
                        parts[p1_idx] = f"{p1}/{parts.pop(p1_idx + 1)}"
                    top_lvl = parts[parts.index(entry.keypath[0]) - 1]
                except ValueError as e:
                    debug(f"Failed to find parent of {entry.filepath}")
                    top_lvl = '/'
                deepest_lvl = max(TOC_HEADING_FCN_MAP.keys())
                entries_beyond_depth = ' / '.join(entry.keypath[deepest_lvl:])
                entries_beyond_depth = [' / '.join(entries_beyond_depth)] if entries_beyond_depth else []
                path2entry = entry.keypath[:deepest_lvl] + entries_beyond_depth
                path2entry = [top_lvl] if not path2entry else path2entry
                nested_tocs = dict()
                for idx in range(last_toc_level, toc_lvl):
                    tex_body += TOC_HEADING_FCN_MAP[idx](path2entry[idx])

                # for idx, p in enumerate(path2entry):
                #     tex_body += TOC_HEADING_FCN_MAP[idx](p)

            # TOC entry (real file name)
            tex_body += toc_entry_fcn(entry.filepath.name)

            # Include a LINK to the file -> avoids filename issues (like with spaces)
            link = link_dir / f"{uuid.uuid4()}{entry.filepath.suffix.lower()}"
            link.symlink_to(entry.filepath)
            tex_body += scoop(link)

        src_tex = tmp_dir / "src.tex"
        export_tex_doc(
            tex_body=tex_body,
            out_path=src_tex,
        )

        pdf_path = compile_doc(src_tex, tmp_dir)

        shutil.copy(pdf_path, args.output)
        info(f"Wrote {args.output} ({args.output.stat().st_size / 1e6:.2g} [Mb])")

        # compress?
        # if pdf_path:
        #     compress_doc()
