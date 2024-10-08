import os
from textwrap import indent

import requests
import shutil
from datetime import datetime
from typing import List, Union

from requests import session

from .models import File, Directory


class RemarkableAPI:
    """
    A class to interact with the reMarkable tablet for offline file management.

    This class provides methods to download files, check device connectivity,
    retrieve directory structures, and more.
    """

    def __init__(self, session_name: str = None, working_dir: str = None, base_url: str = "http://10.11.99.1", auto_sync: bool = True, timeout: int = 1):
        """
        Initializes the RemarkableAPI class with basic configurations.

        Args:
            session_name: The name of the session file to load/save.
            base_url: The base URL of the reMarkable tablet's local API.
            timeout: The timeout duration for checking device connectivity.

        se session_name e' none non si salva la sessione su file ma si tiene in memory
        """
        self.session_path = None if not session_name else os.path.join(working_dir, f"{session_name}.session") if working_dir else f"{session_name}.session"
        self.base_url = base_url
        self.auto_sync = auto_sync
        self.timeout = timeout
        self.tree: List[Union[File, Directory]] = []

        # Load tree from session if available
        if self.session_path and os.path.exists(self.session_path):
            self.load_tree()

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

    def sync_file_system(self):
        response = requests.post(f"{self.base_url}/documents")
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
            self.tree = root_dir
        else:
            self.tree = []

    def get_changes(self) -> List[Union[File, Directory]]:
        """
        Retrieves a list of changes in the current file system compared to the saved session.
        This method fetches the updated directory structure, compares it with the saved tree, and
        returns the changes in a simple way for external use.

        Returns:
            A list of File and Directory objects representing the changes (added, removed, or modified).
        """
        old_tree = self.tree
        self.sync_file_system()
        return self.compare_trees(old_tree, self.tree)

    def compare_trees(self, old_tree: List[Union[File, Directory]], new_tree: List[Union[File, Directory]]) -> List[Union[File, Directory]]:
        """
        Compares two directory trees and finds the differences between them.

        Args:
            old_tree: The previously saved directory tree.
            new_tree: The current directory tree fetched from the tablet.

        Returns:
            A list of File and Directory objects that have been modified or are new.
        """
        # Placeholder for logic to compare the two trees and return differences
        pass

    def load_tree(self):
        """
        Loads the directory tree from the session file.
        """
        if self.session_path and os.path.exists(self.session_path):
            with open(self.session_path, "rb") as f:
                self.tree = pickle.load(f)

    def save_session(self):
        """
        Saves the current directory tree to the session file.
        """
        with open(self.session_path, "wb") as f:
            pickle.dump(self.tree, f)

    def __get_directory(self, dir_guid: str) -> List[Union[File, Directory]]:
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

    def download_file(self, file_guid: str, output_file: str) -> int:
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
                # Ensure directory structure exists before saving the file
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_file, "wb") as file:
                    shutil.copyfileobj(r.raw, file)
        return r.status_code

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

    def download_tree(self, base_path: str, filter_fn: Callable[[Union[File, Directory]], bool] = None):
        """
        Downloads all files and directories from the current tree to the specified base path.
        Optionally applies a filter function to determine which files to download.

        Args:
            base_path: The base local path where files and directories will be saved.
            filter_fn: A function that takes a File or Directory object and returns True if the item should be downloaded, False otherwise.
        """
        for item in self.tree:
            if isinstance(item, Directory):
                dir_path = os.path.join(base_path, item.name)
                if filter_fn is None or filter_fn(item):
                    os.makedirs(os.path.dirname(dir_path), exist_ok=True)
                    self._download_directory(item, dir_path)
                else:
                    self._download_directory(item, dir_path, filter_fn)

            elif isinstance(item, File):
                if filter_fn is None or filter_fn(item):
                    self.download_file(item.guid, os.path.join(base_path, f"{item.name}.pdf"))

    def _download_directory(self, directory: Directory, base_path: str, filter_fn: Callable[[Union[File, Directory]], bool] = None):
        """
        Recursively downloads the contents of a directory.

        Args:
            directory: The Directory object to download.
            base_path: The base local path where files and directories will be saved.
            filter_fn: A function that takes a File or Directory object and returns True if the item should be downloaded, False otherwise.
        """
        for item in directory.children:
            if isinstance(item, Directory):
                dir_path = os.path.join(base_path, item.name)
                if filter_fn is None or filter_fn(item):
                    os.makedirs(os.path.dirname(dir_path), exist_ok=True)
                    self._download_directory(item, dir_path)
                else:
                    self._download_directory(item, dir_path, filter_fn)

            elif isinstance(item, File):
                if filter_fn is None or filter_fn(item):
                    self.download_file(item.guid, os.path.join(base_path, f"{item.name}.pdf"))

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

    def filter_create(self):
        pass
