#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Lightweight RPM to CPIO converter.
# Copyright © 2008-2017 Rudá Moura. All rights reserved.
#

'''Extract cpio archive from RPM package.

rpm2cpio converts the RPM on standard input or first parameter to a CPIO archive on standard output.

Usage:
rpm2cpio < adjtimex-1.20-2.1.i386.rpm  | cpio -it
./sbin/adjtimex
./usr/share/doc/adjtimex-1.20
./usr/share/doc/adjtimex-1.20/COPYING
./usr/share/doc/adjtimex-1.20/COPYRIGHT
./usr/share/doc/adjtimex-1.20/README
./usr/share/man/man8/adjtimex.8.gz
133 blocks
'''

from __future__ import print_function

import sys
import gzip
import subprocess

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

HAS_LZMA_MODULE = True
try:
    import lzma
except ImportError:
    try:
        import backports.lzma as lzma
    except ImportError:
        HAS_LZMA_MODULE = False


RPM_MAGIC = b'\xed\xab\xee\xdb'
GZIP_MAGIC = b'\x1f\x8b'
XZ_MAGIC = b'\xfd7zXZ\x00'


def gzip_decompress(data):
    gzstream = StringIO(data)
    gzipper = gzip.GzipFile(fileobj=gzstream)
    data = gzipper.read()
    return data


def xz_decompress(data):
    if HAS_LZMA_MODULE:
        return lzma.decompress(data)
    unxz = subprocess.Popen(['unxz'],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE)
    data = unxz.communicate(input=data)[0]
    return data


def is_rpm(reader):
    lead = reader.read(96)
    return lead[0:4] == RPM_MAGIC


def extract_cpio(reader):
    data = reader.read()
    decompress = None
    idx = data.find(XZ_MAGIC)
    if idx != -1:
        decompress = xz_decompress
        pos = idx
    idx = data.find(GZIP_MAGIC)
    if idx != -1 and decompress is None:
        decompress = gzip_decompress
        pos = idx
    if decompress is None:
        return None
    data = decompress(data[pos:])
    return data


def rpm2cpio(stream_in=None, stream_out=None):
    if stream_in is None:
        stream_in = sys.stdin
    if stream_out is None:
        stream_out = sys.stdout
    try:
        reader = stream_in.buffer
        writer = stream_out.buffer
    except AttributeError:
        reader = stream_in
        writer = stream_out
    if not is_rpm(reader):
        raise IOError('the input is not a RPM package')
    cpio = extract_cpio(reader)
    if cpio is None:
        raise IOError('could not find compressed cpio archive')
    writer.write(cpio)


def main(args=None):
    if args is None:
        args = sys.argv
    if args[1:]:
        try:
            fin = open(args[1])
            rpm2cpio(fin)
            fin.close()
        except IOError as e:
            print('Error:', args[1], e)
            sys.exit(1)
        except OSError as e:
            print('Error: could not find lzma extractor')
            print("Please, install Python's lzma module or the xz utility")
            sys.exit(1)
    else:
        try:
            rpm2cpio()
        except IOError as e:
            print('Error:', e)
            sys.exit(1)
        except OSError as e:
            print('Error: could not find lzma extractor')
            print("Please install Python's lzma module or the xz utility")
            sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted!')
