#! /usr/bin/env python3

import typing as T
import tempfile
import pathlib
import subprocess
import itertools

from pyscooper.tex_template import build_tex_template


def sanitize_tex(in_str: object) -> str:
    """
    Escape any characters in *in_str* that would lead to LaTeX compile errors

    :param in_str:
    :return: str
    """
    return (str(in_str)
            .replace('$', '')
            .replace('%', '')
            .replace('_', ' ')
            )


def export_tex_doc(tex_body: str,
                   out_path: T.Union[str, pathlib.Path],
                   use_minted: bool = False,
                   ) -> bool:
    """
    Outputs a tex. document at *out_path* with the contents in *tex_body* surrounded by the LaTeX template

    :param tex_body:
    :param out_path:
    :return:
    """

    tex_prefix, tex_suffix = build_tex_template(use_minted=use_minted, )

    with open(out_path, 'w') as fp:
        fp.write('\n'.join([tex_prefix, tex_body, tex_suffix]))

    return True


def compress_doc(in_pdf: pathlib.Path,
                 out_pdf: pathlib.Path,
                 ) -> bool:
    # TODO Skip if ghostscript is missing...

    # # MOVE
    # if dst_path.is_file():
    #     os.remove(dst_path)
    # shutil.move(src=str(pdf_path), dst=str(dst_path))

    # COMPRESS
    # https://github.com/pts/pdfsizeopt
    print("Trying to compress the pdf...")

    prev_size = in_pdf.stat().st_size / 1e6  # [Mb]
    compress_cmd = ['gs',
                    '-sDEVICE=pdfwrite',
                    '-dCompatibilityLevel=1.5',
                    '-dNOPAUSE',
                    '-dQUIET',
                    '-dBATCH',
                    '-dPrinted=false',
                    f'-sOutputFile="{out_pdf}"',
                    f'"{in_pdf}"',
                    ]
    p3 = subprocess.run(compress_cmd)
    post_size = out_pdf.stat().st_size / 1e6  # [Mb]
    # gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.5 -dNOPAUSE -dQUIET -dBATCH -dPrinted=false -sOutputFile=foo-compressed.pdf foo.pdf
    if p3.returncode == 0:
        print(f"Compression reduced the output PDF size by {(post_size - prev_size) / prev_size:+.1%})")
        print(f"Wrote {out_pdf} ({post_size:.2f} [Mb])")
        return True
    print("Compression failed!")
    return False


def compile_doc(src_tex: pathlib.Path,
                out_dir: pathlib.Path,
                shell_escape: bool = True,
                ) -> T.Union[pathlib.Path, None]:
    cmd = ['pdflatex']

    if shell_escape:
        cmd += ['-shell-escape']

    cmd += [
        '-output-directory',
        str(out_dir),
        str(src_tex),
    ]
    p1 = subprocess.run(cmd)
    p2 = subprocess.run(cmd)

    if p1.returncode == 0 and p2.returncode == 0:
        pdf_path = next(out_dir.glob('*.pdf'))
        # dst_path = pathlib.Path().cwd() / pdf_path.name
        return pdf_path
    print("Compilation Failed!")
    return None


def tex_section(title: str, ) -> str:
    """
    Adds the LaTeX code required to start a new SECTION titled *title*
    """
    return r'\newsection{' + sanitize_tex(title) + r'}'


def tex_subsection(title: str, ) -> str:
    """
    Adds the LaTeX code required to start a new SUBSECTION titled *title*
    """
    return r'\newsubsection{' + sanitize_tex(title) + r'}'


def tex_subsubsection(title: str, ) -> str:
    """
    Adds the LaTeX code required to start a new SUBSUBSECTION titled *title*
    """
    return r'\newsubsubsection{' + sanitize_tex(title) + r'}'


TOC_HEADING_FCN_MAP = {
    0: tex_section,
    1: tex_subsection,
    2: tex_subsubsection,
}

DEEPEST_TOC_LVL = max(TOC_HEADING_FCN_MAP.keys())

if __name__ == '__main__':
    print(tex_section('SECTION TITLE'))
    print(tex_subsection('SUB-SECTION TITLE'))
    print(tex_subsubsection('SUB-SUB-SECTION TITLE'))
