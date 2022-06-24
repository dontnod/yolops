
def scan_tree(directory: str):
    """
    Scan a directory tree recursively, returning entries for files
    """
    from os import scandir
    try:
        for entry in scandir(directory):
            if entry.is_dir(follow_symlinks=False):
                yield from scan_tree(entry.path)
            else:
                yield entry
    except PermissionError:
        pass


def gzip_file(src: str, dst: str):
    """
    Compress a file using the standard gzip method. Try to preserve file creation
    date and other metadata.
    """
    from os import chown, stat, unlink
    from shutil import copyfileobj, copystat
    from gzip import open as gzip_open

    # Compress file
    with open(src, 'rb') as fin:
        with gzip_open(dst, 'wb') as fout:
            copyfileobj(fin, fout)

    # Copy file metadata
    copystat(src, dst)
    try:
        st = stat(src)
        chown(dst, st.st_uid, st.st_gid)
    except:
        pass

    # Remove the source file if everything went well
    unlink(src)
