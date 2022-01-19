from os import scandir, unlink
from math import log10
from psutil import disk_usage
from datetime import datetime
from enum import Enum
import click

from yolops.minmaxheap import MinMaxHeap
from yolops.parsing import StorageUnit

def scantree(directory):
    """
    Scan a directory tree recursively, returning entries for files
    """
    for entry in scandir(directory):
        if entry.is_dir(follow_symlinks=False):
            yield from scantree(entry.path)
        else:
            yield entry

def unit(size: int):
    """
    Format a number of bytes into a human-readable number with the appropriate unit,
    e.g. KB, MB, TB etc.
    """
    if size <= 0:
        return f'{size}B'
    exp = int(log10(size * 1.1) / 3)
    unit = 'KMGTPEZY'[exp - 1] if exp > 0 else ''
    mantissa = size / pow(1000, exp)
    return f'{mantissa:1.3g}{unit}B'

class Policy(Enum):
    def __str__(self): return self.name
    LRU = 0
    MRU = 1
    RANDOM = 2

@click.command()
@click.option('-f', '--ensure-free', 'ensure_free', type=StorageUnit(), default=0,
              help='ensure at least SIZE bytes are available on the filesystem')
@click.option('--lru', 'policy', flag_value=Policy.LRU, default=True, help='remove oldest files first')
@click.option('-v', '--verbose', is_flag=True, help='verbose output')
@click.option('-n', '--dry-run', is_flag=True, help='perform a trial run with no changes made')
@click.argument('directory', type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
def expire_cache(directory: str, ensure_free: int, verbose: bool, dry_run: bool, policy: Policy):

    click.echo(f'Expiring files in {directory} (policy: {policy})')

    diskinfo = disk_usage(path=directory)
    total, free, used = diskinfo.total, diskinfo.free, diskinfo.used
    click.echo(f'Filesystem size is {unit(total)} total, {unit(used)} used, {unit(free)} free')

    if ensure_free <= free:
        click.echo('Nothing to do!')
        return True

    excess_size = ensure_free - free

    # Scan all files into a min-max heap, sorted by modification date (oldest first)
    heap = MinMaxHeap()
    tracked_size = 0
    discovered_size = 0
    for entry in scantree(directory):
        try:
            stat = entry.stat()
            heap.insert((stat.st_mtime, stat.st_size, entry.path))
            tracked_size += stat.st_size
            discovered_size += stat.st_size
        except FileNotFoundError:
            pass
        # If we’re tracking more data than we need to clean, we can ignore the most recent files
        while tracked_size > excess_size:
            _, size, _ = heap.popmax()
            tracked_size -= size

    click.echo(f'Found {unit(discovered_size)} of data ({len(heap)} files)')

    # Delete files until we reach the threshold
    freed_size = 0
    freed = 0
    while freed_size < excess_size and len(heap):
        mtime, size, path = heap.popmin()
        if verbose:
            click.echo(f'Deleting file: {path} ({datetime.fromtimestamp(mtime)}, {unit(size)})')
        if not dry_run:
            unlink(path)
        freed_size += size
        freed += 1

    click.echo(f'Freed {unit(freed_size)} of data ({freed} files)')
