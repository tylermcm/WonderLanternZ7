# Backward trace from still-file completion — October 22, 2026

The owner asked how to obtain a verified per-photo signal. The approach is to
trace backward from an independently identifiable image operation, then establish
where individual exposure records separate from preview frames and unsuccessful
release requests. An event's numeric value or reachability alone is insufficient.

## New anchor in the original Z7 image

The native region referencing `WriteStillImage.c` contains wrapper `0x1026FADC`.
Its successful finalization path sends **`0x041E0002`** through dispatcher
`0x1027F8CC`. Its three-word packet includes a packed record identifier and a
kind-dependent flag. Earlier operations or finalization failures can suppress
this event. This is evidence of the wrapper's notification contract, not proof
that every invocation corresponds to one new exposure.

The callback slot is `0xA18D2750`. Wrapper `0x1035FF54` branches to original
registration routine `0x1027F8B8`. The native startup caller at `0x104DB3DE`
registers consumer `0x104DB211`. That consumer handles the `0x041E0002` packet,
queries its record properties and performs further selection checks before
calling `0x102753D6`. Its existence strengthens the connection to a record-bearing
image pipeline; it does not identify exposure timing.

The stock record helper `0x10309884` packs four supplied fields. The original
getters and comparison routine execute offline:

| Field | Native getter/extraction |
| --- | --- |
| Slot | `0x103098B6`, bits 29–30 |
| Group | `0x103098BC`, bits 19–28 |
| Number | `0x103098C8`, bits 5–18 |
| Kind | `0x103098CE`, low four bits |

Native comparison `0x103099A0` compares slot/group/number while ignoring kind.
Two synthetic identifiers with the same slot/group/number and different kinds
compare equal; a different number or slot compares unequal. These are numeric
fields derived from original code. Kind values are not identified here as JPEG,
NEF or other formats. No physical photo's identifier has been sampled.

This provides a useful backward-tracing and possible duplicate-detection anchor.
It does **not** establish a safe sound hook: one photo can have multiple output
records; an old file can be processed again; record names can be reused; saving
can lag exposure; cardless and failed saves need separate behavior. Native
comparison also distinguishes slot, so it is not a proven cross-slot/photo key.

## Offline checks

`tools/trace_still_file_notification.py` executes the original registration,
dispatch, finalization wrapper, record constructor/getters and record comparator
in the original stock MAIN image. **14 evidence checks pass**:

- Three numeric kinds send the expected event/packet on the supplied success path.
- Prior failure, finalization-helper failure and flush-helper failure suppress
  that event and return failure in the supplied cases.
- Native comparison/getters agree with constructed records, including kind
  equivalence and different-number/slot rejection.

File handles, record fields and operation results are supplied unit inputs. File
and device helpers are controlled; no real card is opened or written and no
physical exposure is generated. Passing establishes this selected native contract,
not the final signal's timing/cardinality or firmware safety. Public summary:
`evidence/20261022-still-file-trace.json`. Raw disassembly remains private.

## How the remaining signal would be established

1. Follow record creation upstream and relate it to the native exposure/capture
   instance. Locate where preview, movie, cancelled request and new photo differ.
2. Exercise original code with independent positive and negative inputs, retaining
   native property/identifier derivations rather than mocking the desired meaning.
   Cover one photo, bursts, multiple output kinds, replay and failure paths.
3. Measure actual ordering and multiplicity. Unit fixtures and assisted emulation
   cannot establish physical-camera timing. If on-camera instrumentation becomes
   necessary, first prepare and review a diagnostic build's exact changes and
   installation/recovery limitations. A diagnostic flash is still a firmware
   update and is not automatically cleared by this document.
4. Only after the signal is substantiated, connect playback once per confirmed
   photo and recheck busy/pending/disable ownership and failure cleanup.

The existing official firmware is sufficient for the current local investigation;
no further download or camera/card operation was requested. No sound hook or
firmware source was changed, and no image was built, staged or flashed here.
Enabled OFF remains owner-confirmed containment. The
[port audit hold](PORT_AUDIT.md) and other interface/recovery gaps remain open.
