from typing import Union
from backup_locally_CLI import File, Directory


def bookmarked(item: Union[File, Directory]) -> bool:
    """
    Checks if a given file or directory is bookmarked.

    Args:
        item (Union[File, Directory]): The file or directory to check.

    Returns:
        bool: True if the item is bookmarked, False otherwise.
    """
    return item.bookmarked
