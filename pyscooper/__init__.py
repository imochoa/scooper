#! /usr/bin/env python3

import pathlib

PYPKG_DIR = pathlib.Path(__file__).parent.absolute()

LATEX_PREFIX = r"""
\documentclass[]{article}

% Smaller margins
\usepackage[top=1in, bottom=0.5in, left=0.5in, right=0.5in]{geometry}

% Fancy header/footer
\usepackage{fancyhdr}
\usepackage{lastpage} % reference last page

% Nicer Font
\usepackage[utf8]{inputenc}
\usepackage[scaled]{helvet}
\usepackage[T1]{fontenc}
\renewcommand\familydefault{\sfdefault}


% Keep file hierarchy in the table of contents?
% text
% videos: ttps://www.overleaf.com/latex/examples/using-media9-to-include-videos-files/yvdwwvpknjkk
% audio:  https://tex.stackexchange.com/questions/294679/how-to-insert-a-file-audio-with-play-and-stop-in-pdf-latex
% 3d models: https://husseinbakri.org/how-to-embed-interactive-3d-models-movies-and-sound-clips-into-a-pdf-via-latex/


\usepackage{pdfpages}

% Hyperrefs with nicer styles
\usepackage{hyperref}
\usepackage{xcolor}
\hypersetup{
colorlinks,
linkcolor={blue!50!black},
citecolor={blue!50!black},
urlcolor={blue!80!black}
}

% TOC style
\renewcommand*\contentsname{Index} % TOC Title
%\setcounter{secnumdepth}{0} % sections are level 1

% https://tex.stackexchange.com/questions/292408/redefine-section-so-it-behaves-exactly-as-section-except-leaves-out-the

%\setcounter{tocdepth}{1} % Show sections
%\setcounter{tocdepth}{2} % + subsections
\setcounter{tocdepth}{3} % + subsubsections
%\setcounter{tocdepth}{4} % + paragraphs
%\setcounter{tocdepth}{5} % + subparagraphs

\usepackage{tocloft}
\renewcommand{\cftpartleader}{\cftdotfill{\cftdotsep}} % for parts
\renewcommand{\cftsecleader}{\cftdotfill{\cftdotsep}} % for sections, if you really want! (It is default in report and book class (So you may not need it).

% CUSTOM COMMANDS
\newcommand{\subsubsectiontitle}{}
\newcommand{\newsubsubsection}[1]{\stepcounter{subsubsection}\phantomsection\addcontentsline{toc}{subsubsection}{\protect\numberline{\thesubsubsection}{#1}}\renewcommand{\subsubsectiontitle}{#1}\renewcommand{\subsubsectiontitle}{}}

\newcommand{\subsectiontitle}{}
\newcommand{\newsubsection}[1]{\stepcounter{subsection}\phantomsection\addcontentsline{toc}{subsection}{\protect\numberline{\thesubsection}{#1}}\renewcommand{\subsectiontitle}{#1}\renewcommand{\subsectiontitle}{}}


\newcommand{\sectiontitle}{}
\newcommand{\newsection}[1]{\stepcounter{section}\phantomsection\addcontentsline{toc}{section}{\protect\numberline{\thesection}{#1}}\renewcommand{\sectiontitle}{#1}\renewcommand{\subsubsectiontitle}{}\renewcommand{\subsectiontitle}{}}


\begin{document}
    \thispagestyle{empty}
    \phantomsection
    \tableofcontents
    \pagebreak
%\pagestyle{headings}

    \pagestyle{fancy}
%\lhead{\rightmark}
%\lhead{\leftmark}
%\rhead{\thepage/\pageref{LastPage}}
%\chead{\leftmark}
%\chead{\rightmark}
    \chead{\sectiontitle}
    \rhead{}
    \cfoot{\thepage/\pageref*{LastPage}} %
    \renewcommand{\headrulewidth}{0.4pt}
    \renewcommand{\footrulewidth}{0.4pt}

%	\pagestyle{empty} stops the pages being numbered
%	\pagestyle{plain} this is the default; it puts the numbers at the bottom of the page
%	\pagestyle{headings} puts the numbers at the top of the page; the precise style and content depends on the document class
%	\pagenumbering{roman} numbers pages using Roman numerals; use arabic to switch it back

    \setcounter{secnumdepth}{0} %% no section numbering
% ---- PYTHON AUTO-SPLIT ----


"""

LATEX_SUFFIX = r"""
% ---- PYTHON AUTO-SPLIT ----
%% Done
    \setcounter{secnumdepth}{1} %% Start numbering again
\end{document}
"""

if __name__ == "__main__":
    print(LATEX_PREFIX + LATEX_SUFFIX)
