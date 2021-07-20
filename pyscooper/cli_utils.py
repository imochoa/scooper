#! /usr/bin/env python3

# std imports
import sys


# pip imports
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def debug(msg: str) -> None:
    sys.stdout.write(f"{bcolors.OKBLUE}{msg}{bcolors.ENDC}\n")


def info(msg: str) -> None:
    sys.stdout.write(f"{bcolors.OKGREEN}{msg}{bcolors.ENDC}\n")


def warning(msg: str) -> None:
    sys.stdout.write(f"{bcolors.WARNING}{msg}{bcolors.ENDC}\n")


def error(msg: str) -> None:
    sys.stdout.write(f"{bcolors.FAIL}{msg}{bcolors.ENDC}\n")


if __name__ == '__main__':
    debug("debug msg")
    info("info msg")
    warning("warning msg")
    error("error msg")
