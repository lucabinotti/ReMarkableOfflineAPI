"""
remarkable_offline_api

An offline API for managing and downloading files from the reMarkable tablet.
"""

from .api import RemarkableAPI
from .models import File, Directory

__all__ = ["RemarkableAPI", "File", "Directory"]