import os
import time
import pickle
import shutil
import requests
from datetime import datetime
from .models import File, Directory
from typing import List, Union, Callable


class RemarkableAPI:
    """
    A class to interact with the reMarkable tablet for offline file management.

    This class provides methods to download files, check device connectivity,
    retrieve directory structures, and more.

    Attributes:
        session_path (str): Path to the session file for saving/restoring the file tree.
        base_url (str): The base URL of the reMarkable tablet's local API.
        timeout (int): Timeout duration for checking device connectivity.
        tree (List[Union[File, Directory]]): The current representation of the file system.
    """

    def __init__(self, session_name: str = None, base_url: str = "http://10.11.99.1", timeout: int = 1):
        """
        Initializes the RemarkableAPI class with basic configurations.

        Args:
            session_name: The name of the session file to load/save.
            base_url: The base URL of the reMarkable tablet's local API.
            timeout: The timeout duration for checking device connectivity.

        If session_name is None, no session is saved, and the state remains in memory only.
        """
        self.session_path = f"{session_name}.session"
        self.base_url = base_url
        self.timeout = timeout
        self.tree: List[Union[File, Directory]] = []

        # Load tree from session if available
        if self.session_path and os.path.exists(self.session_path):
            self._load_tree()

    def wait_device_connection(self, delay: int = 1):
        """
        Blocks execution until the reMarkable tablet is detected as connected.

        Args:
            delay (int): Delay in seconds between each connection check (default: 1 second).
        """
        while not self.is_device_connected():
            time.sleep(delay)

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
        """
        Fetches the current file system structure from the tablet and updates the local representation.

        If the request is successful, the local directory tree is updated to reflect the current state on the device.
        """
        response = requests.post(f"{self.base_url}/documents/")
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
                            children=self._get_directory(item["ID"], item["Bookmarked"])
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

    def _load_tree(self):
        """
        Loads the directory tree from the session file if it exists.
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

    def _get_directory(self, dir_guid: str, dir_bookmarked: bool = False) -> List[Union[File, Directory]]:
        """
        Retrieves the contents of a directory on the reMarkable tablet.

        Args:
            dir_guid (str): The unique identifier (GUID) of the directory to retrieve.
            dir_bookmarked (bool): If True, the directory and all its contents are considered bookmarked.

        Returns:
            List[Union[File, Directory]]: A list containing File and Directory objects representing the contents of the specified directory.
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
                            children=self._get_directory(item["ID"], dir_bookmarked or item["Bookmarked"])
                        ))
                    case "DocumentType":
                        root_dir.append(File(
                            guid=item["ID"],
                            name=item["VissibleName"].encode("latin1").decode("utf-8"),
                            last_change=datetime.strptime(item["ModifiedClient"], "%Y-%m-%dT%H:%M:%S.%fZ"),
                            bookmarked=dir_bookmarked or item["Bookmarked"]
                        ))
            return root_dir
        else:
            return []

    def download_file(self, file_guid: str, output_file: str) -> int:
        """
        Downloads a file from the reMarkable tablet and saves it to the specified path.

        Args:
            file_guid (str): The unique identifier (GUID) of the file to be downloaded.
            output_file (str): The path where the downloaded file will be saved.

        Returns:
            int: The HTTP status code of the download request (200 for success, error code otherwise).
        """
        with requests.get(f"{self.base_url}/download/{file_guid}/placeholder", stream=True) as r:
            if r.status_code == 200:
                # Ensure directory structure exists before saving the file
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                with open(output_file, "wb") as file:
                    shutil.copyfileobj(r.raw, file)
        return r.status_code

    def _print_directory(self, directory: Union[Directory, List[Union[File, Directory]]], indent_level: int = 0):
        """
        Prints the directory tree structure with appropriate indentation.

        Args:
            directory (Union[Directory, List[Union[File, Directory]]]): The Directory object or list of File/Directory objects to print.
            indent_level (int): The current level of indentation for nested directories (default: 0).
        """
        directory = [directory] if isinstance(directory, Directory) else directory
        if isinstance(directory, list):
            for item in directory:
                if isinstance(item, File):
                    print(f"{' ' * indent_level * 4}[F] {item.name}")
                elif isinstance(item, Directory):
                    print(f"[D] {item.name}")
                    self._print_directory(item.children, indent_level + 1)

    def download_tree(self, base_path: str = "", filter_fn: Callable[[Union[File, Directory]], bool] = None, downloaded_fn: Callable[[File, str], None] = None):
        """
        Downloads all files and directories from the current tree to the specified base path.
        Optionally applies a filter function to determine which files to download.

        Args:
            base_path (str): The base local path where files and directories will be saved.
            filter_fn (Callable[[Union[File, Directory]], bool], optional): A function that takes a File or Directory object and returns True if the item should be downloaded, False otherwise.
            downloaded_fn (Callable[[File, str], None], optional): A callback function to execute after each file is downloaded. Receives the file downloaded and the path where it was saved.
        """
        for item in self.tree:
            if isinstance(item, Directory):
                dir_path = os.path.join(base_path, item.name)
                if filter_fn is None or filter_fn(item):
                    os.makedirs(os.path.dirname(dir_path), exist_ok=True)
                    self._download_directory(item, dir_path, downloaded_fn=downloaded_fn)
                else:
                    self._download_directory(item, dir_path, filter_fn, downloaded_fn)

            elif isinstance(item, File):
                if filter_fn is None or filter_fn(item):
                    file_path = os.path.join(base_path, f"{item.name}.pdf")
                    self.download_file(item.guid, file_path)
                    if downloaded_fn:
                        downloaded_fn(item, file_path)

    def _download_directory(self, directory: Directory, base_path: str, filter_fn: Callable[[Union[File, Directory]], bool] = None, downloaded_fn: Callable[[File, str], None] = None):
        """
        Recursively downloads the contents of a directory.

        Args:
            directory (Directory): The Directory object to download.
            base_path (str): The base local path where files and directories will be saved.
            filter_fn (Callable[[Union[File, Directory]], bool], optional): A function that takes a File or Directory object and returns True if the item should be downloaded.
            downloaded_fn (Callable[[File, str], None], optional): A callback function to execute after each file is downloaded. Receives the file downloaded and the path where it was saved.
        """
        for item in directory.children:
            if isinstance(item, Directory):
                dir_path = os.path.join(base_path, item.name)
                if filter_fn is None or filter_fn(item):
                    os.makedirs(os.path.dirname(dir_path), exist_ok=True)
                    self._download_directory(item, dir_path, downloaded_fn=downloaded_fn)
                else:
                    self._download_directory(item, dir_path, filter_fn, downloaded_fn)

            elif isinstance(item, File):
                if filter_fn is None or filter_fn(item):
                    file_path = os.path.join(base_path, f"{item.name}.pdf")
                    self.download_file(item.guid, file_path)
                    if downloaded_fn:
                        downloaded_fn(item, file_path)

    def _find_item_in_tree(self, target_item: Union[File, Directory], tree: List[Union[File, Directory]]) -> Union[File, Directory, None]:
        """
        Recursively searches for an item in the given tree by GUID.

        Args:
            target_item: The item to search for.
            tree: The list of File or Directory objects representing the tree.

        Returns:
            Union[File, Directory, None]: The matching File or Directory object if found, otherwise None.
        """
        for item in tree:
            if item.guid == target_item.guid:
                return item
            elif isinstance(item, Directory):
                result = self._find_item_in_tree(target_item, item.children)
                if result is not None:
                    return result
        return None

    def download_changes(self, base_path: str, filter_fn: Callable[[Union[File, Directory]], bool] = None, downloaded_fn: Callable[[File, str], None] = None):
        """
        Downloads only the files that have changed since the last sync.

        Args:
            base_path (str): The base local path where modified files will be saved.
            filter_fn (Callable[[Union[File, Directory]], bool], optional): A filter function to apply during download.
            downloaded_fn (Callable[[File, str], None], optional): A callback function to execute after each file is downloaded. Receives the file downloaded and the path where it was saved.
        """
        old_tree = self.tree
        self.sync_file_system()
        modified_files = []
        self._get_modified_file_guids(old_tree, self.tree, modified_files)
        self.download_tree(base_path=base_path, filter_fn=(lambda item: item.guid in modified_files) if filter_fn is None else (lambda item: item.guid in modified_files and filter_fn(item)), downloaded_fn=downloaded_fn)

    def _get_modified_file_guids(self, old_tree: List[Union[File, Directory]], new_tree: List[Union[File, Directory]], modified_files: List[File]):
        """
        Recursively compares two directory trees to find the files that have been modified or added.

        Args:
            old_tree (List[Union[File, Directory]]): The previously saved directory tree.
            new_tree (List[Union[File, Directory]]): The current directory tree fetched from the tablet.
            modified_files (List[File]): A list to append files that have been modified or added.
        """
        for new_item in new_tree:
            matching_old_item = self._find_item_in_tree_path(new_item.name, old_tree)

            if isinstance(new_item, File):
                if matching_old_item is None or new_item.last_change > matching_old_item.last_change:
                    modified_files.append(new_item.guid)
            elif isinstance(new_item, Directory):
                # If it's a directory, recursively compare children
                # TODO only if last change changed
                if matching_old_item is not None and isinstance(matching_old_item, Directory):
                    self._get_modified_file_guids(matching_old_item.children, new_item.children, modified_files)
                # If the directory is new, add all files to list
                else:
                    self._get_modified_file_guids([], new_item.children, modified_files)

    def _find_item_in_tree_path(self, target_path: str, tree: List[Union[File, Directory]], current_path: str = "") -> Union[File, Directory, None]:
        """
        Recursively searches for an item in the given tree by path.

        Args:
            target_path (str): The path of the item to search for.
            tree (List[Union[File, Directory]]): The list of File or Directory objects representing the tree.
            current_path (str): The current path being traversed in the tree (default: empty string).

        Returns:
            Union[File, Directory, None]: The matching File or Directory object if found, otherwise None.
        """
        for item in tree:
            item_path = f"{current_path}/{item.name}".strip("/")
            if item_path == target_path:
                return item
            elif isinstance(item, Directory):
                result = self._find_item_in_tree_path(target_path, item.children, item_path)
                if result is not None:
                    return result
        return None


