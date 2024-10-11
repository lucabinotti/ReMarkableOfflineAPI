# ReMarkableOfflineAPI

An offline API for managing and downloading files directly from the reMarkable tablet without relying on the official cloud service. This library allows you to connect the reMarkable tablet to your computer via USB and access its file system, enabling file downloads, modifications, and management—all while staying completely offline.

## Features

- Connect directly to the reMarkable tablet via USB.
- Download files and directories from the tablet.
- Sync the file system to identify changes without relying on the reMarkable cloud.
- Bookmark files and directories for easier management.
- Flexible filtering system to download or manage specific files based on custom criteria.

## Getting Started

These instructions will guide you on how to set up and use the ReMarkableOfflineAPI to manage files on your reMarkable tablet.

### Prerequisites

To use this library, you need:

- A reMarkable tablet (with USB connectivity).
- Python 3.12 is recommended, as this library was developed and tested with that version.
- The tablet must have the **USB Web Interface** enabled to allow file access.

### Enabling USB Web Interface

To connect the tablet to your computer, the **USB Web Interface** must be enabled. You can do this by following the steps from the official reMarkable documentation:

[How to enable USB transfer on your reMarkable](https://support.remarkable.com/s/article/importing-and-exporting-files)

After enabling USB Web Interface, the tablet will be accessible at `http://10.11.99.1` when connected via USB.

## Installation

You can clone the repository from GitHub and install it locally:

```sh
git clone https://github.com/lucabinotti/ReMarkableOfflineAPI.git
```

## Usage

Here is a simple example of how to use ReMarkableOfflineAPI:

```python
from remarkable_offline_api import RemarkableAPI
from datetime import datetime, filters

# Initialize the API
rm = RemarkableAPI()

# Wait for the device to connect
rm.wait_device_connection()

# Sync the file system
rm.sync_file_system()

# Download all bookmarked files to the local folder
base_path = "/path/to/save/files"
rm.download_tree(base_path, filter_fn=filters.bookmarked)
```

### Example: Downloading Modified Bookmarked Files

```python
from remarkable_offline_api import RemarkableAPI, filters

# Initialize the API with a session to keep track of changes
rm = RemarkableAPI(session_name="backup")

# Check if the device is connected
if rm.is_device_connected():
    # Note: Do not sync here as it would overwrite the session state. We want to use the existing session state to track changes.
    # Download only bookmarked files that have been modified since the last backup
    base_path = "/path/to/save/files"
    rm.download_changes(base_path, filter_fn=filters.bookmarked)

    # Save the session state to ensure the latest changes are tracked for future runs
    rm.save_session()
else:
    print("Device is not connected.")
```

This example waits for the device to connect, syncs the file system, and then downloads only the bookmarked files that have been modified since the last backup, using the `download_changes` method.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

[Luca Binotti](https://github.com/lucabinotti)
