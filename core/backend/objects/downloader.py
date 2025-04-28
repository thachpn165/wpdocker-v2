# File: core/backend/utils/downloader.py

from rich.progress import (
    Progress,
    DownloadColumn,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn
)
from pathlib import Path
import requests
import os

class Downloader:
    def __init__(self, url, desc=None):
        self.url = url
        self.desc = desc or f"Tải {os.path.basename(url)}"

    def download_to(self, dest_path):
        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

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

        return str(dest_path)