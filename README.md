# Yolops Devops Toolbox

## Cache expiration

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

