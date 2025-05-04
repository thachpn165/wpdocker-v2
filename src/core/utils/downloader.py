"""
File download utility.

This module provides the Downloader class for downloading files
with progress indication.
"""

import os
from pathlib import Path
from typing import Optional

import requests
from rich.progress import (
    Progress,
    DownloadColumn,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn
)

from src.common.logging import Debug, log_call


class Downloader:
    """Handles file downloads with progress visualization."""
    
    def __init__(self, url: str, desc: Optional[str] = None) -> None:
        """
        Initialize a downloader for a URL.
        
        Args:
            url: URL to download from
            desc: Optional description for the progress bar
        """
        self.url = url
        self.desc = desc or f"Downloading {os.path.basename(url)}"
        self.debug = Debug("Downloader")
    
    @log_call
    def download_to(self, dest_path: str) -> str:
        """
        Download the file to the specified path.
        
        Args:
            dest_path: Destination file path
            
        Returns:
            str: Path to the downloaded file
            
        Raises:
            requests.HTTPError: If download fails
            IOError: If writing file fails
        """
        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.debug.info(f"Downloading {self.url} to {dest_path}")

        try:
            with requests.get(self.url, stream=True) as r:
                r.raise_for_status()
                total = int(r.headers.get("Content-Length", 0))

                with Progress(
                    TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
                    BarColumn(),
                    DownloadColumn(),
                    TransferSpeedColumn(),
                    TimeRemainingColumn(),
                ) as progress:
                    task = progress.add_task(self.desc, total=total, filename=dest_path.name)

                    with open(dest_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                progress.update(task, advance=len(chunk))
            
            self.debug.success(f"Download completed: {dest_path}")
            return str(dest_path)
        except requests.HTTPError as e:
            self.debug.error(f"HTTP error downloading {self.url}: {e}")
            raise
        except IOError as e:
            self.debug.error(f"IO error writing to {dest_path}: {e}")
            raise