def gzip_file(src: str, dst: str):
    ''' Compress a file using the standard gzip method. Try to preserve file creation
        date and other metadata. '''
    from os import chown, stat, unlink
    from shutil import copyfileobj, copystat
    from gzip import open as gzip_open

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
