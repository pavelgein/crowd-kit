from hashlib import md5
from os import environ, makedirs
from os.path import exists, expanduser, join
from shutil import unpack_archive
from typing import Optional
from urllib.request import urlretrieve


def get_data_dir(data_dir: Optional[str] = None) -> str:
    """Return the path of the crowd-kit data dir.
    This folder is used by some large dataset loaders to avoid downloading the
    data several times.
    By default the data dir is set to a folder named 'crowdkit_data' in the
    user home folder.
    Alternatively, it can be set by the 'CROWDKIT_DATA' environment
    variable or programmatically by giving an explicit folder path. The '~'
    symbol is expanded to the user home folder.
    If the folder does not already exist, it is automatically created.

    Parameters:
        data_home: str, default=None
            The path to crowd-kit data directory. If `None`, the default path
            is `~/crowdkit_data`.
    """
    if data_dir is None:
        data_dir = environ.get('CROWDKIT_DATA', join('~', 'crowdkit_data'))
        data_dir = expanduser(data_dir)
    if not exists(data_dir):
        makedirs(data_dir)
    return data_dir


def fetch_remote(url: str, checksum: str, path: str, data_dir: str) -> None:
    """Helper function to download a remote dataset into path
    Fetch a dataset pointed by remote's url, save into path using remote's
    filename and ensure its integrity based on the MD5 Checksum of the
    downloaded file.
    Parameters:
        url: str
        checksum: str
        path: str, path to save a zip file
        data_home: path to crowd-kit data directory
    """
    urlretrieve(url, path)
    fetched_checksum = md5(open(path, 'rb').read()).hexdigest()
    if checksum != fetched_checksum:
        raise IOError(f"{path} has an MD5 checksum ({fetched_checksum}) differing from expected ({checksum}), file may be corrupted.")
    unpack_archive(path, data_dir)
