"""Canonical 80-byte Z7G1 grid seed; private output only (MIT)."""
import argparse
import binascii
import struct
from pathlib import Path
from prepare_flash_review import require_private_output


def encode(choice):
    if not isinstance(choice,int) or not 1<=choice<=5:raise ValueError('Grid choice must be 1..5')
    data=bytearray(80);struct.pack_into('<5I',data,0,0x3147375a,1,80,0,choice)
    struct.pack_into('<I',data,12,binascii.crc32(data))
    return bytes(data)


def decode(data):
    data=bytes(data)
    if len(data)!=80:raise ValueError('Wrong record length')
    magic,version,size,crc,choice=struct.unpack_from('<5I',data)
    check=bytearray(data);check[12:16]=bytes(4)
    if (magic,version,size)!=(0x3147375a,1,80) or not 1<=choice<=5 or any(data[20:]) or binascii.crc32(check)!=crc:
        raise ValueError('Invalid grid record')
    return choice


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--choice',type=int,choices=range(1,6),required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output);data=encode(a.choice);assert decode(data)==a.choice
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('xb') as f:f.write(data)
    assert out.read_bytes()==data
    print('Private read-only grid seed generated:',len(data),'bytes; choice',a.choice)


if __name__=='__main__':main()
