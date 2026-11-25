"""Independent original-Z7 C3.80 native movie ceiling table experiment (MIT).

The 24 ordinary-format entries are bound by original-instruction audits.
This changes the native ceiling only; real recording/thermal/file behavior is
unverified. Never describe the existing 99:59:59 ceiling as unlimited recording.
"""
import struct

TABLE=0x115419e8
FIRST_ORDINARY=4
ORDINARY_COUNT=24
STOCK_MS=1799000
EXTENDED_MS=359999000


def extend_native_movie_ceiling(plan):
    expected=(0,)*FIRST_ORDINARY+(STOCK_MS,)*ORDINARY_COUNT
    if plan.image.words(TABLE,len(expected))!=expected:
        raise ValueError('Unexpected original-Z7 ordinary movie duration table')
    address=TABLE+4*FIRST_ORDINARY
    plan.edit(address,struct.pack('<24I',*([EXTENDED_MS]*ORDINARY_COUNT)),
        'Experimental native movie ceiling: 24 ordinary formats, existing 99:59:59 bound',
        expected=struct.pack('<24I',*([STOCK_MS]*ORDINARY_COUNT)))
    return dict(table=hex(TABLE),first_ordinary=FIRST_ORDINARY,ordinary_count=ORDINARY_COUNT,
        stock_ms=STOCK_MS,extended_ms=EXTENDED_MS,physical_recording_verified=False,
        native_capacity_guards_retained=True,task_callbacks_replaced=False)
