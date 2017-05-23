#!/usr/bin/env python
#
# Copyright (C) 2012 Adam Sutton <dev@adamsutton.me.uk>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Support for processing HTSMSG binary format
"""

import sys


# ###########################################################################
# Utilities
# ###########################################################################

def int2bin(i):
    return chr(i >> 24 & 0xFF) + chr(i >> 16 & 0xFF) \
           + chr(i >> 8 & 0xFF) + chr(i & 0xFF)


def bin2int(d):
    return (ord(d[0]) << 24) + (ord(d[1]) << 16) \
           + (ord(d[2]) << 8) + ord(d[3])


def uuid2int(uuid):
    if sys.byteorder == 'little':
        n = 2
        uuid = uuid[0:8]
        sep = [uuid[i:i + n] for i in range(0, len(uuid), n)]
        sep.reverse()
        end_uuid = "".join(sep)
        return int(end_uuid, 16) & 0x7fffffff

    raise NotImplementedError("Currently not implemented for byte-order %s" % sys.byteorder)


# ###########################################################################
# HTSMSG Binary handler
#
# Note: this will work with the python native types:
#   dict    => HMF_MAP
#   list    => HMF_LIST
#   str     => HMF_STR
#   int     => HMF_S64
#   HMFBin  => HMF_BIN
#
# Note: BIN/STR are both equated to str in python
# ###########################################################################

# HTSMSG types
HMF_MAP = 1
HMF_S64 = 2
HMF_STR = 3
HMF_BIN = 4
HMF_LIST = 5
HMF_DBL = 6
HMF_BOOL = 7


# Light wrapper for binary type
class HMFBin(str):
    pass


# Convert python to HTSMSG type
def hmf_type(f):
    if isinstance(f, list):
        return HMF_LIST
    elif isinstance(f, dict):
        return HMF_MAP
    elif isinstance(f, str):
        return HMF_STR
    elif isinstance(f, int):
        return HMF_S64
    elif isinstance(f, HMFBin):
        return HMF_BIN
    elif isinstance(f, bool):
        return HMF_BOOL
    else:
        raise Exception('invalid type')


# Size for field
def p_binary_count(f):
    ret = 0
    if isinstance(f, (str, HMFBin)):
        ret = ret + len(f)
    elif isinstance(f, int):
        while f:
            ret = ret + 1
            f = f >> 8
    elif isinstance(f, (list, dict)):
        ret = ret + binary_count(f)
    else:
        raise Exception('invalid data type')
    return ret


# Recursively determine size of message
def binary_count(msg):
    ret = 0
    lst = isinstance(msg, list)
    for f in msg:
        ret = ret + 6
        if not lst:
            ret = ret + len(f)
            f = msg[f]
        ret = ret + p_binary_count(f)
    return ret


# Write out field in binary form
def binary_write(msg):
    ret = ''
    lst = isinstance(msg, list)
    for f in msg:
        na = ''
        if not lst:
            na = f
            f = msg[f]
        ret = ret + chr(hmf_type(f))
        ret = ret + chr(len(na) & 0xFF)
        l = p_binary_count(f)
        ret = ret + int2bin(l)
        ret = ret + na

        if isinstance(f, (list, dict)):
            ret = ret + binary_write(f)
        elif isinstance(f, (str, HMFBin)):
            ret = ret + f
        elif isinstance(f, int):
            while f:
                ret = ret + chr(f & 0xFF)
                f = f >> 8
        else:
            raise Exception('invalid type')
    return ret


# Serialize a htsmsg
def serialize(msg):
    cnt = binary_count(msg)
    return int2bin(cnt) + binary_write(msg)


# Deserialize an htsmsg
def deserialize0(data, typ=HMF_MAP):
    islist = False
    msg = {}
    if typ == HMF_LIST:
        islist = True
        msg = []
    while len(data) > 5:
        typ = ord(data[0])
        nlen = ord(data[1])
        dlen = bin2int(data[2:6])
        data = data[6:]

        if len < nlen + dlen:
            raise Exception('not enough data')

        name = data[:nlen]
        data = data[nlen:]
        if typ == HMF_STR:
            item = data[:dlen]
        elif typ == HMF_BIN:
            item = HMFBin(data[:dlen])
        elif typ == HMF_S64:
            item = 0
            i = dlen - 1
            while i >= 0:
                item = (item << 8) | ord(data[i])
                i = i - 1
        elif typ in [HMF_LIST, HMF_MAP]:
            item = deserialize0(data[:dlen], typ)
        elif typ == HMF_BOOL:
            bool_val = data[:dlen]
            if len(bool_val) > 0:
                item = bool(ord(bool_val))
            else:
                item = None
        else:
            raise Exception('invalid data type %d' % typ)
        if islist:
            msg.append(item)
        else:
            msg[name] = item
        data = data[dlen:]
    return msg


# Deserialize a series of message
def deserialize(fp, rec=False):
    class p_Deserialize:
        def __init__(self, fp, rec=False):
            self.p_fp = fp
            self.p_rec = rec

        def p_read(self, num):
            r = None
            try:
                r = self.p_fp.read(num)
                return r
            except AttributeError:
                pass

            try:
                r = self.p_fp.recv(num)
                return r
            except AttributeError:
                pass

            if isinstance(self.p_fp, list):
                r = self.p_fp[:num]
                self.p_fp = self.p_fp[num:]
            else:
                raise Exception('invalid data type')
            return r

        def next(self):
            if not self.p_fp:
                raise StopIteration()
            tmp = self.p_read(4)
            if len(tmp) != 4:
                self.p_fp = None
                raise StopIteration()
            num = bin2int(tmp)
            data = ''
            while len(data) < num:
                tmp = self.p_read(num - len(data))
                if not tmp:
                    raise Exception('failed to read from fp')
                data = data + tmp
            if not self.p_rec:
                self.p_fp = None
            return deserialize0(data)

    ret = p_Deserialize(fp, rec)
    if not rec:
        ret = ret.next()
    return ret
