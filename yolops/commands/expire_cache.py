from typing import List
import click

from yolops.log import verbosity_params, info, debug
from yolops.parsing import StorageUnit


class Scanner(object):

    def __init__(self, policy: str):
        if policy == 'MRU':
            self._make_key = lambda stat: -stat.st_mtime
        elif policy == 'random':
            from random import random
            self._make_key = lambda stat: random()
        else: # 'LRU'
            self._make_key = lambda stat: stat.st_mtime

    def scan(self, directories: List[str]):
        from yolops.fsutils import scan_tree
        for directory in directories:
            for entry in scan_tree(directory):
                try:
                    stat = entry.stat()
                    yield self._make_key(stat), stat.st_size, entry.path
                except FileNotFoundError:
                    pass


def unit(size: int):
    """
    Format a number of bytes into a human-readable number with the appropriate unit,
    e.g. KB, MB, TB etc.
    """
    from math import log10
    if size <= 0:
        return f'{size}B'
    exp = int(log10(size * 1.1) / 3)
    unit = 'KMGTPEZY'[exp - 1] if exp > 0 else ''
    mantissa = size / pow(1000, exp)
    return f'{mantissa:1.3g}{unit}B'

@click.command()
@click.option('-d', '--delete', 'todelete_size', type=StorageUnit(), default=-1,
              help='Delete SIZE bytes of data')
@click.option('-f', '--ensure-free', type=StorageUnit(), default=-1,
              help='Ensure at least SIZE bytes are available on the filesystem')
@click.option('-k', '--keep', 'tokeep_size', type=StorageUnit(), default=-1,
              help='Ensure directory uses at most SIZE bytes')
@click.option('--lru',    'policy', flag_value='LRU',    help='Remove oldest files (default)', default=True)
@click.option('--mru',    'policy', flag_value='MRU',    help='Remove newest files')
@click.option('--random', 'policy', flag_value='random', help='Remove files randomly')
@click.option('-n', '--dry-run', is_flag=True, help='Perform a trial run with no changes made')
@click.argument('directories', nargs=-1, required=True,
                type=click.Path(file_okay=False, dir_okay=True, resolve_path=True, exists=True))
@verbosity_params
def expire_cache(directories: List[str], todelete_size: int, ensure_free: int, tokeep_size: int,
                 dry_run: bool, policy: str):

    from os import unlink, lstat
    from shutil import disk_usage
    from yolops.minmaxheap import MinMaxHeap

    # Check argument consistency
    if len([x for x in [tokeep_size, ensure_free, todelete_size] if x >= 0]) != 1:
        raise click.UsageError('You must specify one of --delete, --ensure-free, or --keep')

    fs_count = len(set([lstat(d).st_dev for d in directories]))
    if ensure_free >= 0 and fs_count != 1:
        raise click.UsageError('Targets must be on the same filesystem when using --ensure-free')

    targets = ' '.join(directories)
    info(f'Expiring files in {targets} (policy: {policy})')

    # Gather stats about the filesystem
    if fs_count == 1:
        diskinfo = disk_usage(path=directories[0])
        total, free, used = diskinfo.total, diskinfo.free, diskinfo.used
        info(f'Filesystem size is {unit(total)} total, {unit(used)} used, {unit(free)} free')

    # Handle --ensure-free: it’s the same as --delete except the actual value
    # is computed from the filesystem stats
    if ensure_free >= 0:
        todelete_size = ensure_free - free
        tokeep_size = -1

    if todelete_size < 0 and tokeep_size < 0:
        info('Nothing to do!')
        return True

    # Scan all files into a min-max heap, sorted by modification date (oldest first)
    scanner = Scanner(policy)
    heap = MinMaxHeap()
    tracked_size = 0
    discovered_size = 0
    discovered_count = 0
    freed_size = 0
    freed_count = 0
    for key, size, path in scanner.scan(directories):
        heap.insert((key, size, path))
        tracked_size += size
        discovered_size += size
        discovered_count += 1
        # If we need to keep at most X bytes and we already found more than that, we can start deleting
        while tokeep_size >= 0 and tracked_size > tokeep_size:
            _, size, path = heap.popmin()
            debug(f'Deleting file: {path} ({unit(size)})')
            if not dry_run:
                unlink(path)
            tracked_size -= size
            freed_size += size
            freed_count += 1
        # If we already found more data than we need to delete, we can stop tracking
        # some of these files because we know we will never have to delete them
        while todelete_size > 0 and tracked_size > todelete_size:
            _, size, _ = heap.popmax()
            tracked_size -= size

    info(f'Scanned {discovered_count} files ({unit(discovered_size)})')

    # Delete files until we reach the threshold
    while freed_size < todelete_size and len(heap):
        key, size, path = heap.popmin()
        debug(f'Deleting file: {path} ({unit(size)})')
        if not dry_run:
            try:
                unlink(path)
            except FileNotFoundError:
                info('FileNotFound %s', path)
        freed_size += size
        freed_count += 1

    info(f'Deleted {freed_count} files ({unit(freed_size)})')
