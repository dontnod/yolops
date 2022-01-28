# Yolops Devops Toolbox

## Cache expiration

This command helps clean up a cache directory. It can be used for tasks such as:

 - cleaning up a proxy cache directory (Apache, Perforce, …)
 - expiring Unreal Engine cache date (shared DDC, cooked data, packages…)

```
yolops expire-cache [OPTIONS] <directories…>
```

A [min-max heap](https://en.wikipedia.org/wiki/Min-max_heap) is used to keep
memory usage as low as possible, even when scanning millions of files.

### Options

Directories are scanned recursively and files deleted based on the given policy:

 - `--lru`: LRU, or *least recently used*; delete older files first (default behaviour)
 - `--mru`: MRU, or *most recently used*; delete newer files first
 - `--random`: delete files randomly

Operating mode is chosen with one of the following options:

 - `--delete <size>`: delete `size` bytes of data
 - `--keep <size>`: keep at most `size` bytes of data, effectively limiting the total size of the directories
 - `--ensure-free <size>`: delete files until at least `size` bytes of data are available on the filesystem

Sizes can be specified in bytes, or with any common unit, eg: `10G`, `1.5T`, `128MiB`…

Other useful options:

 - `-v`, `--verbose`: verbose output
 - `-n`, `--dry-run`: do not actually delete files (useful with `-v`)

### Examples

Clean up old files until at least 10 GiB of data are available on the filesystem:

    yolops expire-cache --ensure-free 10GiB /srv/p4proxy

Ensure Unreal Engine cooked data does not exceed 50 GiB:

    yolops expire-cache --keep 50GiB */*/Saved/Cooked

Attempt to free 200 MiB of data from various directories:

    yolops expire-cache --delete 200MiB */*/Intermediate
