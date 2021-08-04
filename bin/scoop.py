#! /usr/bin/env python3

# std imports
import argparse
import os
import pathlib
import subprocess
import sys
import tempfile
from collections import namedtuple

Resource = namedtuple("Resource", ["path", "name"])
DOCKER_IMG = "ytdl-img:alpine"


# pip imports
class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def debug(msg: str) -> None:
    sys.stdout.write(f"{bcolors.OKBLUE}{msg}{bcolors.ENDC}\n")


def info(msg: str) -> None:
    sys.stdout.write(f"{bcolors.OKGREEN}{msg}{bcolors.ENDC}\n")


def warning(msg: str) -> None:
    sys.stdout.write(f"{bcolors.WARNING}{msg}{bcolors.ENDC}\n")


def error(msg: str) -> None:
    sys.stdout.write(f"{bcolors.FAIL}{msg}{bcolors.ENDC}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "sources",
        nargs="*",
        type=pathlib.Path,
        default=pathlib.Path.cwd(),
        help="What to include in the scoop: (directories, [JPG,PNG,PDF,MP3,MP4]",
    )
    args = parser.parse_args()

    files = [a for a in args if a.is_file()]

    # TODO calls the docker container
    urls = []
    out_dir = None
    known_files = None
    out_dir = None
    url_report = "\n".join(f"{i:>3}: {u}" for i, u in enumerate(urls, start=1))
    sys.stdout.write(f"Found {len(urls)} valid urls!:\n{url_report}\n")

    # Download!
    # docker exec -it $1 bash -c "stty cols $COLUMNS rows $LINES && bash"

    #                '--user', f'username:{os.getegid()}',
    cmd = [
        "docker",
        "run",
        "--rm",
        "-t",
        "-i",
        "--entrypoint",
        "python3",
        "--mount",
        f"type=bind,source={os.getcwd()},target=/Downloads",
        "ytdl-img",
        "/docker-script.py",
    ]

    #   --mount type=bind,source="$(pwd)"/target,target=/app \
    #   --mount type=bind,source="$(pwd)"/target,target=/app2,readonly,bind-propagation=rslave \

    stdout_lines = os.environ.get("LINES", 36)
    stdout_cols = os.environ.get("COLUMNS", 145)
    # TODO Fix tab issue...
    # # Used to solve the tab issue
    # docker exec -it $1 bash -c "stty cols $COLUMNS rows $LINES && bash"

    cmd += urls
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)

    # Monitor STDOUT until the execution is finished
    while True:
        output = p.stdout.readline()
        if output == "" and p.poll() is not None:
            break
        if output:
            # print(output.strip())
            sys.stdout.write(output.strip() + "\n")

    # rc = p.poll()
    # p.stdout.close()
    return_code = p.wait()

    # Set the owner of the downloads to be th
    user_id = os.geteuid()
    group_id = os.getegid()
    sys.stdout.write(
        "The current owner of the downloaded files is the docker "
        "container's ROOT, this next command will give the ownership "
        f"to the executor of the script: {os.environ.get('USER', 'YOU')}"
        "\n"
    )

    # Find the new directory
    new_paths = set(os.listdir(out_dir)).difference(known_files)
    new_paths = [os.path.join(out_dir, d) for d in new_paths]
    new_dirs = [d for d in new_paths if os.path.isdir(d)]

    if len(new_dirs) > 1:
        sys.stdout.write(f"Found too many new dirs: using name matching...\n")
        new_dirs = [p for p in new_dirs if p.lower().startswith("downloads_")]

    if len(new_dirs) == 0:
        sys.stdout.write(f"No directory generated... exiting\n")
        sys.exit(1)
    elif len(new_dirs) > 1:
        sys.stdout.write(f"Ambiguous directories {new_dirs}... exiting\n")
        sys.exit(1)

    dl_path = new_dirs[0]

    # Change the owner
    chown_cmd = ["sudo", "chown", "-R", f"{user_id}", dl_path]
    p = subprocess.run(chown_cmd, stdout=subprocess.PIPE, universal_newlines=True)

    sys.stdout.write("DONE!\n")
