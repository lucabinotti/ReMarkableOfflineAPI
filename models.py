from datetime import datetime
from dataclasses import dataclass
from typing import List, Union


@dataclass
class File:
    """
    Represents a file on the reMarkable tablet.

    Attributes:
        guid (str): The Globally Unique Identifier (GUID) of the file, used for uniquely identifying each file.
        name (str): The name of the file.
        last_change (datetime): A datetime object representing the timestamp of the last modification to the file.
        bookmarked (bool): Indicates whether the file has been bookmarked by the user. Defaults to False.
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
        guid (str): The Globally Unique Identifier (GUID) of the directory, used to uniquely identify it.
        name (str): The name of the directory.
        last_change (datetime): A datetime object representing the timestamp of the last modification to the directory or its contents.
        children (List[Union[File, Directory]]): A list containing files and/or directories that reside within this directory.
        bookmarked (bool): Indicates whether the directory has been bookmarked by the user. Defaults to False.
    """

    guid: str
    name: str
    last_change: datetime
    children: List[Union["File", "Directory"]]
    bookmarked: bool = False