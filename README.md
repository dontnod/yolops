# Yolops Devops Toolbox

## Cache expiration

This command helps clean up a cache directory. It can be used for tasks such as:

 - cleaning up a Perforce proxy cache directory
 - expiring Unreal Engine shared DDC

```
yolops expire-cache [OPTIONS] <directory>
```

Scan a directory recursively and delete files based on the given policy:

 - `--lru`: LRU, or *least recently used*; delete older files first (default behaviour)
 - `--mru`: MRU, or *most recently used*; delete newer files first
 - `--random`: delete files at random

Operating mode is chosen with one of the following options:

 - `--delete <size>`: delete `size` bytes of data
 - `--keep <size>`: keep at most `size` bytes of data, effectively limiting the total size of the directory
 - `--ensure-free <size>`: delete files until at least `size` bytes of data are available on the filesystem

Sizes can be specified in bytes, or with any common unit, eg: `10G`, `1.5T`, `128MiB`…
