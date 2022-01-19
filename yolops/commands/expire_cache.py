from os import scandir, unlink
from math import log10
from psutil import disk_usage
from datetime import datetime
from enum import Enum, auto
from random import random
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

@click.command()
@click.option('-f', '--ensure-free', 'ensure_free', type=StorageUnit(), default=0,
              help='ensure at least SIZE bytes are available on the filesystem')
@click.option('--lru',    'policy', flag_value='LRU',    help='remove oldest files (default)', default=True)
@click.option('--mru',    'policy', flag_value='MRU',    help='remove newest files')
@click.option('--random', 'policy', flag_value='random', help='remove files randomly')
@click.option('-v', '--verbose', is_flag=True, help='verbose output')
@click.option('-n', '--dry-run', is_flag=True, help='perform a trial run with no changes made')
@click.argument('directory', type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
def expire_cache(directory: str, ensure_free: int, verbose: bool, dry_run: bool, policy: str):

    click.echo(f'Expiring files in {directory} (policy: {policy})')

    diskinfo = disk_usage(path=directory)
    total, free, used = diskinfo.total, diskinfo.free, diskinfo.used
    click.echo(f'Filesystem size is {unit(total)} total, {unit(used)} used, {unit(free)} free')

    if ensure_free <= free:
        click.echo('Nothing to do!')
        return True

    excess_size = ensure_free - free

    if policy == 'MRU':
        make_key = lambda stat: -stat.st_mtime
    elif policy == 'random':
        make_key = lambda stat: random()
    else: # 'LRU'
        make_key = lambda stat: stat.st_mtime

    # Scan all files into a min-max heap, sorted by modification date (oldest first)
    heap = MinMaxHeap()
    tracked_size = 0
    discovered_size = 0
    discovered_count = 0
    for entry in scantree(directory):
        try:
            stat = entry.stat()
            heap.insert((make_key(stat), stat.st_size, entry.path))
            tracked_size += stat.st_size
            discovered_size += stat.st_size
            discovered_count += 1
        except FileNotFoundError:
            pass
        # If we’re tracking more data than we need to clean, we can ignore the most recent files
        while tracked_size > excess_size:
            _, size, _ = heap.popmax()
            tracked_size -= size

    click.echo(f'Found {unit(discovered_size)} of data ({discovered_count} files)')

    # Delete files until we reach the threshold
    freed_size = 0
    freed_count = 0
    while freed_size < excess_size and len(heap):
        key, size, path = heap.popmin()
        if verbose:
            if policy == 'MRU':
                info = datetime.fromtimestamp(-key)
            if policy == 'random':
                info = 'random'
            else: # Policy.LRU
                info = datetime.fromtimestamp(key)
            click.echo(f'Deleting file: {path} ({info}, {unit(size)})')
        if not dry_run:
            unlink(path)
        freed_size += size
        freed_count += 1

    click.echo(f'Freed {unit(freed_size)} of data ({freed_count} files)')
