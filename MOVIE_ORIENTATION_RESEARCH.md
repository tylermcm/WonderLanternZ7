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

Current private reproducible diagnostic: 2,048 bytes, SHA256
`1de27cff07318d2ee9f9e7af28be5c19bd477e9e6f6afd2d68dba7a6ca17307d`.
Build with `tools/build_z7_movie_rotation.py --output` and a new private path.
Its initializer prepares owned buffers only: **it does not publish a native
callback**. Explicit operation 7 publishes the callback only for the offline
diagnostic. It rejects a non-native callback, nonzero native task state/file
count and pending open/close work, prepares the shadows again, cleans all three
code buffers, issues ARM cache/barrier instructions and rechecks those guards
before publication. This is not a proven task-quiescence protocol. The diagnostic
remains separate from the cumulative display candidates and must not be staged.

318 checks verify every relocated direct call, native bytes/literal pools,
alignment, unchanged live callback, all ten file slots and four poses, pose
retention after later orientation changes, split-context replacement, failed
open/unknown-pose invalidation, native track failure preservation and fingerprint
rejection. Original relocated task open/split/close event paths and the copied
close/header control flow execute. The close case reaches the pose-aware track
wrapper, retains the file-service order, acknowledges the request and decrements
the file count. Underlying file operations, pose readings, completion results,
track construction and cache-clean services are supplied in that fixture.
Publication checks cover busy-state rejection, state changes during cache clean,
all three buffer clean requests, duplicate rejection and an open event through
the published pointer.

The expanded audit executes the **complete original video-track constructor**
and its endian/atom/memory helpers for two supplied container-kind values and
three dimensions (1920x1080, 3840x2160 and 1280x720). Each is compared with the
wrapper at all four poses: 24 wrapped cases. The native `trak`/`tkhd` tags,
92-byte track header, identity matrix and 16.16 dimensions are checked. The full
48 KiB supplied context/buffer arena matches the unwrapped native reference
except for the intended 36-byte track matrix. The wrapper retains the pose from
open even when the later supplied camera pose changes.

Those dimensions are constructor inputs, not evidence of supported recording
formats. Sample descriptions/tables and pointers are fixture inputs; no sensor,
encoder, actual file open or completed playable movie is exercised. Separate
failure/control cases still supply the track return. This does not validate a
complete playable movie, file split or player result.

Eight further cases execute original native sample-table finalization,
movie-header construction and scatter serialization at two supplied container-
kind values and four poses. Only filesystem append and flush are supplied in
that serialization stage. The emitted metadata atom trees have exact bounded
sizes and one 92-byte `tkhd`; matrix and dimensions are read from its emitted
bytes. Each rotated stream differs from its unrotated native reference only in
the intended matrix. Five append-failure injections and a flush failure return
the original writer error instead of success. The eight generated streams stay
private with byte counts and hashes recorded in the evidence.

These are metadata-only streams with an empty supplied sample description and
no media samples. They are not playable MOV/MP4 recordings, and do not prove
encoder output, track timing under recording, file splitting or player behavior.
See
[the shadow record](evidence/20261124-movie-shadows.json).

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
