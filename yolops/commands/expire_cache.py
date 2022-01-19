from os import scandir, unlink
from math import log10
from psutil import disk_usage
from heapq import heappush, heappop
from datetime import datetime
import click

from yolops.parsing import StorageUnit

def scantree(directory):
    for entry in scandir(directory):
        if entry.is_dir(follow_symlinks=False):
            yield from scantree(entry.path)
        else:
            yield entry

@click.command()
@click.option('-f', '--ensure-free', 'ensure_free', type=StorageUnit(), default=0,
              help='ensure at least SIZE bytes are available on the filesystem')
@click.option('-v', '--verbose', is_flag=True, help='verbose output')
@click.option('-n', '--dry-run', is_flag=True, help='perform a trial run with no changes made')
@click.argument('directory', type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
def expire_cache(directory: str, ensure_free: int, verbose: bool, dry_run: bool):

    def unit(size: int):
        if size <= 0:
            return f'{size}B'
        exp = int(log10(size) / 3 + 0.1)
        unit = 'KMGTPEZY'[exp - 1] if exp > 0 else ''
        mantissa = size / pow(1000, exp)
        return f'{mantissa:.1f}{unit}B'

    click.echo(f'Expiring old files in {directory}')

    diskinfo = disk_usage(path=directory)
    total, free, used = diskinfo.total, diskinfo.free, diskinfo.used
    click.echo(f'Filesystem size is {unit(total)} total, {unit(used)} used, {unit(free)} free')

    if ensure_free <= free:
        click.echo('Nothing to do!')
        return True

    #if must_delete > 0:
    #    click.echo(f'Will delete at least {unit(delete)} of data')

    excess = ensure_free - free
    #if excess > must_delete:
    #    click.echo(f'Filesystem has {unit(diskinfo.free)} free space, will free an additional {unit(excess)} of data')
    #    must_delete = max(must_delete, excess)

    # Scan all files into a heap, sorted by modification date (oldest first)
    heap = []
    discovered_size = 0
    for entry in scantree(directory):
        try:
            stat = entry.stat()
            heappush(heap, (stat.st_mtime, stat.st_size, entry.path))
            discovered_size += stat.st_size
        except FileNotFoundError:
            pass

    click.echo(f'Found {unit(discovered_size)} of data ({len(heap)} files)')

    # Delete files until we reach the threshold
    freed_size = 0
    freed = 0
    while freed_size < excess and len(heap):
        mtime, size, path = heappop(heap)
        if verbose:
            click.echo(f'Deleting file: {path} ({datetime.fromtimestamp(mtime)}, {unit(size)})')
        if not dry_run:
            unlink(path)
        freed_size += size
        freed += 1

    click.echo(f'Freed {unit(freed_size)} of data ({freed} files)')
