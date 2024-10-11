"""
remarkable_offline_api

An offline API for managing and downloading files from the reMarkable tablet without relying on the cloud service.
It provides a straightforward way to interface with the device by connecting it via USB and using the web interface enabled on the device.

Author:
    Luca Binotti (github.com/lucabinotti)

Exports:
    RemarkableAPI: The main class to interact with the reMarkable tablet's file system.
    File: Data model representing individual files on the tablet.
    Directory: Data model representing folders containing files and/or other directories.
"""

__author__ = "Luca Binotti"

from .api import RemarkableAPI
from .models import File, Directory

__all__ = ["RemarkableAPI", "File", "Directory"]
