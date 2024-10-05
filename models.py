from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import List, Union

@dataclass
class File:
    """
    Represents a file on the reMarkable tablet.

    Attributes:
        guid (str): Globally Unique Identifier for the file.
        name (str): Name of the file.
        last_change (datetime): Timestamp of the last modification.
        bookmarked (bool): Indicates whether the file is bookmarked. Default is False.
    """
    guid: str
    name: str
    last_change: datetime
    bookmarked: bool = False


@dataclass
class Directory:
    """
    Represents a directory on the reMarkable tablet, which may contain both files and subdirectories.

    Attributes:
        guid (str): Globally Unique Identifier for the directory.
        name (str): Name of the directory.
        last_change (datetime): Timestamp of the last modification to the directory or its contents.
        children (List[Union[File, Directory]]): List of files and subdirectories contained within the directory.
        bookmarked (bool): Indicates whether the directory is bookmarked. Default is False.
    """
    guid: str
    name: str
    last_change: datetime
    children: List[Union[File, Directory]]
    bookmarked: bool = False