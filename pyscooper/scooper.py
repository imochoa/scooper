#! /usr/bin/env python3

# std imports
import typing as T
import tempfile
import pprint
import os
import sys
import pathlib
import glob
import shutil
import argparse
import itertools
import subprocess
import tempfile
import uuid

from pyscooper.attachments import (scoop,
                                   MINTED_EXTS,
                                   PANDAS_EXTS,
                                   ext_match,
                                   TOCFile,
                                   EXT_MAP,
                                   )
from pyscooper import deps
from pyscooper.cli_utils import debug, info, warning, error
# from pyscooper.tableofcontents import build_toc_tree, build_filetree, sort_toc_maps, filemap2tocmap
from pyscooper.tex_utils import (sanitize_tex, export_tex_doc, compile_doc, compress_doc,
                                 tex_section, tex_subsection, tex_subsubsection,
                                 TOC_HEADING_FCN_MAP,
                                 DEEPEST_TOC_LVL,
                                 )


def get_search_root(entry: TOCFile, default: str = '/') -> str:
    try:
        parts = list(entry.filepath.parts[:-1])
        folded_dirs = [(p1, p2) for p1, p2 in zip(parts[:-1], parts[1:]) if folding_fcn(p1, p2) in entry.keypath]
        for p1, p2 in folded_dirs[::-1]:
            p1_idx = parts.index(p1)
            parts[p1_idx] = folding_fcn(p1, parts.pop(p1_idx + 1))
        return parts[parts.index(entry.keypath[0]) - 1]
    except ValueError as e:
        debug(f"Failed to find parent of {entry.filepath}")
    return default


def folding_fcn(s1: str, s2: str) -> str:
    return f"{s1}/{s2}"


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
            recd[folding_fcn(k, lk)] = recd.pop(k).pop(lk)
            # recd[f"{k}/{lk}"] = recd.pop(k).pop(lk)

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

    # TODO max depth

    parser.add_argument(
        "-d", "--debug", action="store_true", help="Leaves the LaTeX source directory after finishing"
    )

    parser.add_argument(
        "-o", "--output", type=pathlib.Path, help="Where to save the output PDF", default=DFEAULT_OUTPDF,
    )

    args = parser.parse_args()

    # Check deps
    use_minted = deps.PYGMENTIZE_OK
    if not use_minted:
        warning("Pygmentize was not found")
        # warning('\n\t> '.join([f"Removing {len(MINTED_EXTS)} extensions"] + sorted(MINTED_EXTS)))
        # VALID_EXTS = set(EXT_MAP).difference(MINTED_EXTS)
    elif args.debug:
        debug("Found Pygmentize!")

    use_pandas = deps.PANDAS_OK
    if not use_pandas:
        warning("Pandas not found")
    else:
        debug("Found Pandas")

    # Start the search
    sources = args.sources if isinstance(args.sources, list) else [args.sources]
    sources = [pathlib.Path(s).expanduser() for s in sources]  # For pre-expanded globs

    # Top-level files (can be overwritten by the glob matches)
    top_files = {f for f in sources if f.is_file() and ext_match(f)}
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
        fs = (f for f in fs if ext_match(f) is not None)
        for f in fs:
            relpath = f.relative_to(top_dir)
            *ancestors, filename = relpath.parts
            aux_dict = filemap
            for ancestor in ancestors:
                aux_dict = aux_dict.setdefault(ancestor, dict())
            aux_dict[filename] = f
    # Collapse first!

    filemap, _ = fold_empty_nodes(filemap)
    if args.debug:
        debug("Found the following files:")
        debug(pprint.pformat(filemap))

    # TODO flatten to max DEEPEST_TOC_LVL levels!

    entries = extract_entries(filemap)

    # Don't include minted unless it is required
    use_minted = use_minted and any(e for e in entries if e.ext_key in MINTED_EXTS)
    use_pandas = use_pandas and any(e for e in entries if e.ext_key in PANDAS_EXTS)

    # Write LaTeX document
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = pathlib.Path(tmp)
        link_dir = tmp_dir / 'links'
        link_dir.mkdir()

        # Build LaTeX source

        toc_lvl_map = {idx: idx for idx in range(DEEPEST_TOC_LVL + 1)}
        tex_body = ""
        curr_path = []
        for entry in entries:
            last_path = curr_path
            curr_path = entry.keypath
            toc_lvl = toc_lvl_map.get(len(entry.keypath), DEEPEST_TOC_LVL)

            # TOC NESTING
            update_map = {toc_lvl: entry.filepath.name}
            diff_detected = False
            for idx in range(toc_lvl):
                last_val = last_path[idx] if idx < len(last_path) else None
                curr_val = curr_path[idx] if idx < len(curr_path) else None

                diff_detected = diff_detected or (curr_val is not None
                                                  and curr_val != last_val)
                if diff_detected:
                    update_map[idx] = curr_path[idx]

            for idx in sorted(update_map):
                tex_body += TOC_HEADING_FCN_MAP[idx](update_map[idx])
                tex_body += '\n'

            # Include a LINK to the file -> avoids filename issues (like with spaces)
            link = link_dir / f"{uuid.uuid4()}{entry.filepath.suffix.lower()}"
            link.symlink_to(entry.filepath)
            tex_body += scoop(link)

        src_tex = tmp_dir / "src.tex"
        export_tex_doc(
            tex_body=tex_body,
            out_path=src_tex,
            use_minted=use_minted,
            use_pandas=use_pandas,
        )

        pdf_path = compile_doc(src_tex, tmp_dir)

        shutil.copy(pdf_path, args.output)
        info(f"Wrote {args.output} ({args.output.stat().st_size / 1e6:.2g} [Mb])")

        # compress?
        # if pdf_path:
        #     compress_doc()

        if args.debug:
            aux_debug_dir = pathlib.Path(tempfile.gettempdir()) / str(uuid.uuid4())
            # shutil.rmtree(aux_debug_dir, ignore_errors=True)
            shutil.copytree(tmp_dir, aux_debug_dir, symlinks=True)
        else:
            aux_debug_dir = None
    if aux_debug_dir:
        info(f"Recovering the LaTeX debug dir {src_tex.absolute()}")
        warning("It will NOT be cleaned up automatically!")
        shutil.copytree(aux_debug_dir, tmp_dir, symlinks=True)
        shutil.rmtree(aux_debug_dir, ignore_errors=True)
