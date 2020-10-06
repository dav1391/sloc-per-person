# Copyright 2020 dav1391
# Available at the term of the MIT Open Source License
# Check the License file for further details

from typing import List, Dict, Tuple
import pygount
import re
from glob import glob
from collections import namedtuple
from shutil import get_terminal_size
import argparse


File_Statistics = namedtuple("File_Statistics", "authors sloc comment_lines")
Author_Statistics = namedtuple("File_Statistics", "sloc comment_lines files")


def find_authors(file) -> List[str]:
    with open(file, 'r+') as file:
        string_contents = str(file.read())
        author_tag = re.search(r'/\*\*([^\*]|\*[^/])*@author ([^\n]*)([^\*]|\*[^/])*\*/', string_contents, re.M)
        if author_tag:
            return author_tag.group(2)\
                .replace(" ", "")\
                .replace("\n", "")\
                .replace("\\\\n", "")\
                .split(",")
        else:
            return []


def generate_author_summary(dir_path: str) -> Tuple[Dict[str, File_Statistics], Dict[str, Author_Statistics]]:
    java_files = glob(dir_path + "/**/*.java", recursive=True)
    authors: Dict[str, Author_Statistics] = dict()
    files: Dict[str, File_Statistics] = dict()
    for file in java_files:
        authors_list = find_authors(file)
        file_statistics = pygount.SourceAnalysis.from_file(file, "project_analysis")

        files[file] = File_Statistics(authors_list, file_statistics.code_count, file_statistics.documentation_count)
        if not authors_list:
            print(f"file contains no @author tag: {file}")
        for author in authors_list:
            if author not in authors:
                authors[author] = \
                    Author_Statistics(file_statistics.code_count, file_statistics.documentation_count, [file])
            else:
                entry = authors[author]
                authors[author] = Author_Statistics(
                    entry.sloc + file_statistics.code_count,
                    entry.comment_lines + file_statistics.documentation_count,
                    entry.files + [file]
                )
    return files, authors


# MARK: utility functions
def _print_filled_line(character="*", text='', default_width=40):
    """
    Fills a terminal line with a character (by default with *)

    :param character: The character with which the line should be filled. Needs to be a string of length 1.
    Defaults to *.
    :param text: optionally a text can be displayed at the center of the line
    :param default_width: The default line length if the terminal size can not be obtained.
    """
    output_width = get_terminal_size((default_width, 20)).columns
    # modified from https://stackoverflow.com/a/18243550 by Viktor Kerkez
    print(text.center(output_width, character))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("root_directory", default=".")
    parser.add_argument("-csv", required=False, dest='csv_output')
    args = parser.parse_args()

    files, authors = generate_author_summary(args.root_directory)

    _print_filled_line("=", " File Summary ")
    for file in files:
        print(file)
        entry = files[file]
        print(f' - total: {entry.sloc + entry.comment_lines}')
        print(f" - sloc: {entry.sloc}")
        print(f" - comment_lines: {entry.comment_lines}")
        print(f" - authors: {entry.authors}")

    print()
    _print_filled_line("=", " Author Summary ")

    for author in authors:
        print(f"{author}:")
        entry = authors[author]
        print(f' - total: {entry.sloc + entry.comment_lines}')
        print(f" - sloc: {entry.sloc}")
        print(f" - comment_lines: {entry.comment_lines}")
        print(f" - files: {entry.files}")

    if args.csv_output:
        with open(args.csv_output, 'w') as csv_file:
            csv_file.write("author, total, sloc, comment_lines, files\n")
            for author in authors:
                entry = authors[author]
                csv_file.write(f"{author}, "
                               f"{entry.sloc + entry.comment_lines}, {entry.sloc}, {entry.comment_lines}, "
                               f"\"{entry.files}\"\n"
                               )

