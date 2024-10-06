import os
from textwrap import indent

import requests
import shutil
from datetime import datetime
from typing import List, Union
from .models import File, Directory


class RemarkableAPI:
    """
    A class to interact with the reMarkable tablet for offline file management.

    This class provides methods to download files, check device connectivity,
    retrieve directory structures, and more.
    """

    def __init__(self, base_url: str = "http://10.11.99.1", timeout: int = 1, old_tree: List[Union[File, Directory]] = None):
        """
        Initializes the RemarkableAPI class with basic configurations.

        Args:
            base_url: The base URL of the reMarkable tablet's local API.
            timeout: The timeout duration for checking device connectivity.
            old_tree: A previous backup of the file structure for comparison.
        """
        self.base_url = base_url
        self.timeout = timeout
        self.old_tree = old_tree if old_tree else self.get_directory(dir_guid="/")

    def is_device_connected(self) -> bool:
        """
        Checks if the reMarkable tablet is connected by sending a request to the base URL.

        Returns:
            True if the device is connected, False otherwise.
        """
        try:
            requests.get(self.base_url, timeout=self.timeout)
        except requests.ConnectTimeout:
            return False
        return True

    def get_file(self, file_guid: str, output_file: str) -> int:
        """
        Downloads a file from the reMarkable tablet and saves it to the specified path.

        Args:
            file_guid: The unique identifier (GUID) of the file to be downloaded.
            output_file: The path where the downloaded file will be saved.

        Returns:
            The HTTP status code of the download request (200 for success, error code otherwise).
        """
        with requests.get(f"{self.base_url}/download/{file_guid}/placeholder", stream=True) as r:
            if r.status_code == 200:
                with open(output_file, "wb") as file:
                    shutil.copyfileobj(r.raw, file)
        return r.status_code

    def get_directory(self, dir_guid: str) -> List[Union[File, Directory]]:
        """
        Retrieves the contents of a directory on the reMarkable tablet.

        Args:
            dir_guid: The unique identifier (GUID) of the directory to retrieve.

        Returns:
            A list containing File and Directory objects representing the contents of the directory.
        """
        response = requests.post(f"{self.base_url}/documents/{dir_guid if dir_guid != '/' else ''}")
        if response.status_code == 200:
            root_dir = []
            for item in response.json():
                match item["Type"]:
                    case "CollectionType":
                        root_dir.append(Directory(
                            guid=item["ID"],
                            name=item["VissibleName"].encode("latin1").decode("utf-8"),
                            last_change=datetime.strptime(item["ModifiedClient"], "%Y-%m-%dT%H:%M:%S.%fZ"),
                            bookmarked=item["Bookmarked"],
                            children=self.get_directory(item["ID"])
                        ))
                    case "DocumentType":
                        root_dir.append(File(
                            guid=item["ID"],
                            name=item["VissibleName"].encode("latin1").decode("utf-8"),
                            last_change=datetime.strptime(item["ModifiedClient"], "%Y-%m-%dT%H:%M:%S.%fZ"),
                            bookmarked=item["Bookmarked"]
                        ))
            return root_dir
        else:
            # console.print(f"Error: {response.status_code}")
            return []

    def has_changes(self, dir_path: str, last_change: datetime) -> bool:
        """
        Checks if the directory or file at the given path has been modified compared to a previous backup.

        Args:
            dir_path: The local path of the directory or file.
            last_change: The timestamp of the last known modification for comparison.

        Returns:
            True if changes have been made since the last backup, False otherwise.
        """
        dir_path = dir_path[1:] if dir_path.startswith("/") else dir_path
        current_path = self.old_tree if self.old_tree else []

        while dir_path:
            for fd in current_path:
                if fd.name == dir_path.split("/")[0]:
                    if isinstance(fd, Directory):
                        current_path = fd.children
                        dir_path = "/".join(dir_path.split("/")[1:])
                        break
                    elif isinstance(fd, File) and "/" not in dir_path:
                        return fd.last_change < last_change
            else:
                return True

    def print_directory(self, directory: Union[Directory, List[Union[File, Directory]]], indent_level: int = 0):
        """
        Prints the directory tree structure with appropriate indentation.

        Args:
            directory: The Directory object or a list of File/Directory objects to print.
            indent_level: The current level of indentation for nested directories.
        """
        directory = [directory] if isinstance(directory, Directory) else directory
        if isinstance(directory, list):
            for item in directory:
                if isinstance(item, File):
                    print(f"{' ' * indent_level * 4}[F] {item.name}")
                elif isinstance(item, Directory):
                    print(f"[D] {item.name}")
                    self.print_directory(item.children, indent_level + 1)

    def download_tree(self, tree: List[Union[File, Directory]], base_path: str):
        """
        Downloads all files and directories in the provided directory tree to a local path.

        Args:
            tree: A list of File and Directory objects representing the file tree.
            base_path: The base path where files and directories will be saved locally.
        """
        for item in tree:
            if isinstance(item, Directory):
                dir_path = os.path.join(base_path, item.name)
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path)

                self.download_tree(item.children, dir_path)

            elif isinstance(item, File):
                file_path = os.path.join(base_path, f"{item.name}.pdf")
                if self.has_changes(file_path, last_change=item.last_change):
                    status_code = self.get_file(file_guid=item.guid, output_file=file_path)
                    # if status_code == 200:
                    #     console.print(f"[bold green]Downloaded[/bold green] [cyan]{item.name}.pdf[/cyan]")
                    # else:
                    #     console.print(f"[bold red][{status_code}][/bold red] Failed to download [cyan]{item.name}.pdf[/cyan]")

    def filter_bookmarked(self, tree: List[Union[File, Directory]]) -> List[Union[File, Directory]]:
        """
        Filters the directory tree to return only bookmarked files and directories.

        Args:
            tree: A list of File and Directory objects representing the file tree.

        Returns:
            A filtered list of only bookmarked items (files or directories).
        """
        filt_tree = []
        for item in tree:
            if isinstance(item, Directory):
                if item.bookmarked:
                    filt_tree.append(item)
                elif filtered_children := self.filter_bookmarked(item.children):
                    item.children = filtered_children
                    filt_tree.append(item)
            elif isinstance(item, File) and item.bookmarked:
                filt_tree.append(item)
        return filt_tree
