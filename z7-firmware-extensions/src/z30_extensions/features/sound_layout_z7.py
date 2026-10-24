# SPDX-License-Identifier: LicenseRef-Wonder-Lantern-Community
"""Private Z7 sound page and state contracts."""
from ..platform.z7_380 import BASE

STATE_ANCHOR = 0xA1833548
SETUP_OBJECT = 0xA1837BEC  # Native Setup page 0x19B, matching SETUP_META_SOURCE.
SETUP_META_SOURCE = 0x11F10854
LEAF_TEMPLATE_INDEX = 0x2A
NATIVE_PAGE_CLEANUP = 0x1040525F

PAGE_INDEX = 0x1C5A
FILES_INDEX = PAGE_INDEX + 1
SWITCH_INDEX = PAGE_INDEX + 2
PAGE_OFFSET = 64
WAV_OFFSET = 128
PCM_OFFSET = 17472
MAX_DATA = 17280
STATE_SIZE = PCM_OFFSET + MAX_DATA * 12
FILES_OFFSET = STATE_SIZE
SWITCH_OFFSET = STATE_SIZE + 44
NEW_SIZE = STATE_SIZE + 88
MAGIC = 0x5A33534E
BUSY, ENABLED, LENGTH, SELECTED, PENDING, RESULT = 32, 36, 40, 44, 48, 52
SHOT_STATUS = 116  # Unused state padding; does not overlap the WAV buffer.
# Native Silent photography page 0xB2 constructor 0x1049AC30 queries 0x576.
# It selects the native ON control only for value 1. 0x57B is the Z30 key.
SILENT_PHOTOGRAPHY_PROPERTY = 0x576
SUCCESS = 0x04390080

# The native busy getter at 0x1006B540 reads the leading state byte.
# The format descriptors begin 16 bytes later; their first word is 2, not idle.
NATIVE_AUDIO_STATE = 0xA188D190
NATIVE_AUDIO_FORMATS = NATIVE_AUDIO_STATE + 16
# Consumer 0x1006BC46 checks type with the exclusive bound 0x12. Reuse the
# last valid descriptor only for records carrying our own completion callback.
OWNED_AUDIO_KIND = 17

# Control IDs initially use the same values as Z30.  The Z7 builder scans the
# stock page table and rejects collisions before writing an image.
ROOT_IDS = (0x2222, 0x2224, 0x2226, 0x224E)
FILE_IDS = (0x2250, 0x2265, 0x22B1, 0x2280, 0x2290)
SWITCH_IDS = (0x23F6, 0x23F8)
ENTRY_ID = 0x2333

# Z7 native event map roles.
SOURCE_EVENTS_LENGTH = 55
ACTIVATION_EVENTS = (0x239, 0x23E, 0x252, 0x25F)
ACTIVATION_DESTINATION = 0x3A0
NEUTRAL_DESTINATION_A = 0x3A0
NEUTRAL_DESTINATION_B = 0x3A1
NAVIGATION = frozenset({
    0x10404F8B, 0x10404F8D, 0x10404FB3, 0x10404F6F,
    0x10404F7B, 0x10404F87, 0x10404FEF,
})

# Function-address mappings used by generated Z7 sound code.
NATIVE = {
    0x1006B5F4: 0x1006B794,
    0x1006B7B2: 0x1006B94A,
    0x100725A1: 0x10072731,
    0x10096CA0: 0x100A2D78,
    0x101993DE: 0x1016FEF2,
    0x10199BDC: 0x10170A1C,
    0x10199C40: 0x10170A80,
    0x101DB84F: 0x101BFA29,
    0x101DBA7C: 0x101BFC1C,
    0x10211F4C: 0x1016FE38,
    0x10211F5E: 0x1016FE4A,
    0x102C89EE: 0x1027BFCC,
    0x1033829E: 0x102D8562,
    0x103382A2: 0x102D8566,
    0x1033832E: 0x102D85F2,
    0x10338414: 0x102D86D8,
    0x10454210: 0x103FAEBE,
    0x104546C6: 0x103FB344,
    0x10453AC3: 0x103FA771,
    0x10453FAC: 0x103FAC5A,
    0x10454EFE: 0x103FBB5C,
    0x1045720B: 0x103FCCCF,
    0x1045745E: 0x103FCF0E,
    0x104574A8: 0x103FCF5C,
    0x1045D54C: 0x10402BC2,
    0x1045F732: 0x10404C42,
    0x1045FDA1: NATIVE_PAGE_CLEANUP,
    0x103CE80D: 0x1048B407,
}

GLOBALS = {
    0xC21C0E28: 0xA21AB994,
    0xC1885A50: NATIVE_AUDIO_STATE,
    0xC2006594: 0xA200DA5C,
}

# Z7 config is inlined into a larger native function; patch the call site
# 0x1006BD54 with a short BL to a cave trampoline that calls our tail config.
CONFIG_CALL_SITE = 0x1006BD54
CONFIG_CALL_SITE_EXPECTED = bytes.fromhex('fff71efd')
CONFIG_CAVE = 0x1002D804
SHOT_CAVE = CONFIG_CAVE + 16
SHOT_CALL_SITE = 0x1007272E  # Shared BLX callback and following epilogue branch.
SHOT_CALL_EXPECTED = bytes.fromhex('9047c8e7')
CAPTURE_CAVE = SHOT_CAVE + 16
CAPTURE_CALL_SITE = 0x100726A8  # Argument setup; keep the CBZ target at CMP intact.
CAPTURE_CALL_EXPECTED = bytes.fromhex('69464046')
DATA_ENTRY = 0x1006BFE6
DATA_CONTINUATION = 0x1006BFEF
HEADER_OBJECT_ID = 0x81A
