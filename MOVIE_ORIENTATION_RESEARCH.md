# Original-Z7 movie orientation metadata foundations

The parity target follows the credited MIT JKWTCN per-file orientation design:
latch pose when a file opens or splits, then use that saved pose when its video
track header is written. A later camera rotation must not change an already-open
file's orientation. This is not yet an installed movie-orientation feature.

## Implemented policy

`z7-native-modules/plugins/movie_orientation.h` provides a bounded per-file
pose ledger and big-endian ISO track matrices. Failed opens, unknown poses,
closed files and reused contexts clear or reject stale state. A context that
appears to belong to two current files is ambiguous and receives no override.
Pose zero leaves the native matrix intact; three nonzero poses emit the related
90, 270 and 180-degree matrices. The caller owns file-task serialization and
supplies the current file contexts; these helpers add no task or file hook.

The diagnostic uses eleven ledger slots to exercise ten files. The helper's
count is caller-supplied; this does not establish the original native mux limit.
The existing original-Z7 read-only orientation getter is separately bound in
`orientation_sample.h`; the new policy does not yet connect it to file opens.

## Verified native writer spans

The original-Z7 video track builder is `0x102A9C2C`. Its original prefix creates
the native identity matrix on its own stack. Its matrix emission span copies
exactly 36 bytes to context offset `0x109`, preserving surrounding bytes in the
supplied context. These original instructions and the native memory helpers
execute in the audit; the image is the exact stock C 3.80 MAIN.

The related original header builder is `0x102AA66C`, which calls the video track
builder at `0x102AA688`. One native mux close path calls that header builder at
`0x1027DDBA`; a second caller also exists. Their lifetimes and all consumers must
be reviewed before redirecting any code. A close-function boundary differs from
the upstream offsets, so simply substituting addresses is insufficient.

An additional 270-check original-instruction audit binds the mux control-pointer
slot `0xA1815030`, file-record base `0x3F0` and stride `0x88`, and the open, split
and close reply arrays at offsets `0x160`, `0x318` and `0x370` with eight-byte
stride. Getter executions leave supplied records unchanged. The native getter
accepts zero and negative indices; the independent module policy must retain its
own positive-file and count guards. The native mux task pointer is statically
bound to `0x1027E797`, but its live registration slot and context lifetime still
need qualification. The actual native file limit and context field offset are
not established by the getter checks alone. The original native open-path
argument construction separately passes file-record `+0x2C` as the context output
pointer; that exact instruction span now executes in the audit. A native
registration prefix writes the task callback at root `+0x2C`. Read-only stock
QEMU inspection confirms root `0xA1F532F8` and callback slot `0xA1F53324` containing
`0x1027E797`. This corrects an earlier nearby-root hypothesis; no callback has
been replaced. Actual file-count initialization and context lifetime still need
qualification. See
[the mux binding record](evidence/20261124-movie-mux.json).

The 177-check audit covers per-file latch/current-context/close behavior, failed
open and unknown-pose invalidation, ambiguous contexts, independently encoded
signed ISO matrices, invalid/short-buffer preservation, and the two original
native matrix spans. It does not execute complete track construction, movie file
I/O, a mux task lifecycle or a recording. No completed MOV/MP4 or player result
is claimed. See [the source-only evidence](evidence/20261124-movie-orientation.json).

## Prepared native shadows and file wrappers

The prepare-only `movie_rotation_module.c` now fingerprints and copies the
original native mux task, close path and header path, retains their PC alignment
and literal pools, and redirects their direct calls through bounded local stubs.
The open/split callsites reach wrappers that latch the native pose after a
successful result. The header wrapper runs native track construction first and
then applies the saved file's matrix, retaining native failure returns.

Private reproducible module: 1,856 bytes, SHA256
`3b3906b677095d621130d8d08e01d521b39af5a97f745cfcaa882ea8558ab94b`.
Build with `tools/build_z7_movie_rotation.py --output` and a new private path.
Its initializer prepares owned buffers only: **it does not publish a native
callback**. There is no installation operation in this profile. It remains
separate from the cumulative display candidates and must not be staged.

171 checks verify every relocated direct call, native bytes/literal pools,
alignment, unchanged live callback, all ten file slots and four poses, pose
retention after later orientation changes, split-context replacement, failed
open/unknown-pose invalidation, native track failure preservation and fingerprint
rejection. Original relocated task open/split event paths execute; underlying
file operations, pose readings, completion results and track construction are
supplied services in that fixture. This does not execute a complete native close
or header chain. See [the shadow record](evidence/20261124-movie-shadows.json).

## Remaining integration

Bind and qualify the original file-task callback, control structure, file-open
and split replies, context lifetime and close paths. Any relocated native code
needs its own exact bytes, literal/call relocation and executable-cache checks.
Then connect the pose ledger and native writer under the file task, preserving
completion, errors, container writes and buffer lifetimes. A header written after
close must still have the correct file's saved pose.

Only after that integration and its offline checks can a concrete host/module
installation and recovery assessment be prepared. No camera, card, installed
firmware or task callback was changed by this checkpoint. Hardware orientation,
export/player behavior, file splits and recovery remain unverified.
