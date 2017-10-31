"""
Contains functions for downloading the given extents and writing
them to a file.
"""

import subprocess
from enum import Enum, unique
from pathlib import Path


@unique
class OutputMode(Enum):
    """
    Defines how to write the data in the changed blocks to the output file.
    """
    OVERWRITE = 'r+b'
    APPEND = 'ab'


class PythonWriter(object):
    def __init__(self, nbd_client):
        self._nbd_client = nbd_client

    def _write_extent(self, extent, out, block_size):
        (offset, length) = extent
        for current_offset in range(offset, length, block_size):
            length = min(block_size, length - current_offset)
            data = self._nbd_client.read(offset=current_offset, length=length)
            out.write(data)

    def write_extents(self, extents, out_file, block_size, output_mode):
        """
        Write the given extents to the output file using Python functions only.
        """
        with Path(out_file).open(output_mode) as out:
            for extent in extents:
                self._write_extent(
                    extent=extent, out=out, block_size=block_size)


class DdWriter(object):
    def __init__(self, nbd_device):
        self._nbd_device = nbd_device

    def _write_extent(self, extent, out_file, block_size, output_mode):
        (offset, length) = extent
        command = [
            'dd', 'if=' + self._nbd_device, 'of=' + out_file,
            'bs=' + block_size
        ]
        command += [
            'count=' + length, 'skip=' + offset, 'iflag=count_bytes,skip_bytes'
        ]
        if output_mode is OutputMode.OVERWRITE:
            command += ['seek=' + offset, 'oflag=seek_bytes']
        elif output_mode is OutputMode.APPEND:
            command += ['oflag=append']
        subprocess.check_output(command)

    def write_extents(self, extents, out_file, block_size, output_mode):
        """
        Write the given extents to the output file by calling dd for each
        extent.
        """
        for extent in extents:
            self._write_extent(
                extent=extent,
                out_file=out_file,
                block_size=block_size,
                output_mode=output_mode)