"""Supplied original-Z7 track context for native constructor audits (MIT).

Pointers and format fields are initialized fixture inputs, not captures from a
recording. Constructor and endian/atom helpers run without replacement.
"""
import struct

POINTER_FIELDS=(0x1d4,0x204,0x218,0x230,0x23c,0x254,0x26c,0x624,0x19c,0x150)


def initialize_track_context(cpu,context,kind=0,width=1920,height=1080):
    cpu.mem_write(context,bytes(0xc000))
    cpu.mem_write(context,bytes([kind]))
    for i,offset in enumerate(POINTER_FIELDS):
        cpu.mem_write(context+offset,struct.pack('<I',context+0x1000+i*0x1000))
    cpu.mem_write(context+0x430,struct.pack('<2I',width,height))
    cpu.mem_write(context+0x450,struct.pack('<I',1000))


def track_image(cpu,context):
    """Return the entire supplied context/buffer arena for exact comparison."""
    return bytes(cpu.mem_read(context,0xc000))
