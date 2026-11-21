# Original-Z7 highlight request cache

Independent research for the unfinished automatic LCD/EVF highlight handoff.
No producer hook or new firmware/module profile is installed by this work.
Keep stock MAIN and generated evidence private. Source audit: MIT.

## Native paths

The original native getter at `0x10434CEE` returns a pointer to a 36-byte request.
For its supported use, R0 is output1,2,4; R1 is kind0. It calls the bank helper
at `0x10433B80` and adds `0x58` to the returned block pointer. Nonzero kind returns
zero. Output0 with kind0 returns `0x58`, so this is not a validating API for
arbitrary callers.

The helper reads the byte at `0xA180F274 + output`, multiplies that bank index by
`0xE84` and adds `0xA1F18FC0`. These constants are checked against the native
literal pool. The audit supplies bank indices0,1,2; it does not prove the physical
bank count, native index writers, allocation bounds or lifetime. Different output
indices can select the same bank. Changing an index changes subsequent getter
results; retaining the old pointer across transitions is unjustified.

The writer at `0x104348E4` accepts an output bitmask in R0, kind0 in R1, a request
pointer in R2 and a submission flag in R3. With submission disabled, its native
memcpy writes exactly36 bytes at each selected bank's `+0x58`. An enabled request
also clears the word at `+0x40` in that bank. A disabled request preserves that
word. Other bank bytes remain unchanged. Output bits1,2,4 are handled separately;
all masks0..7 and enabled/disabled requests are exercised. Nonzero kind does not
modify the cache. Mutex/queue submission boundaries are asserted unreachable in
this update-only audit; no native writer or memcpy instruction is replaced.

Nearby native submission paths call getter10434CEE then caller1034FF1E, including
the output4 path around103518EC..10351900. This makes the cache a candidate
baseline source, not an established coherent baseline API.

## Counterexample to equal double reads

The audit starts the actual native writer on a separate supplied stack. It pauses
after16 of the36 request bytes have been stored, preserves that task's register
context, and executes the original getter on the reader stack. Two identical
36-byte reads contain a mixture of the old and new requests. Both differ from
the complete old and complete new records. Resuming the writer in its saved ARM
instruction state finishes the copy and preserves stack/callee-save guards.

Therefore equality of two reads is insufficient to establish request coherence.
A preempted writer can remain stopped across both reads. Pointer/index rechecks
alone do not solve this partial-copy case. The update-only path also demonstrates
that the cache can change without submitting a display-parameter packet.

## Validation and next implementation

`tools/audit_z7_highlight_native_cache.py` passes60 checks against the exact private
original-Z7 C3.80 MAIN. Native bank arithmetic, getter, writer and memcpy execute.
Bank indices, incoming requests, palette memory and task scheduling are supplied.
This does not establish all direct/indirect writers, task ownership, physical
memory lifetime, output pixels or installation/recovery.

Before using this cache for automatic handoff, identify all writers and bank
index transitions, then provide writer exclusion or a publication protocol that
covers the complete write. Preserve the distinction between genuine native
per-output requests and the currently shared module-owned100-byte parameter
block. Do not move native synchronous queue waits into consumer callbacks.
The native-update-driven EVF profile remains unchanged while this binding is
unfinished; it continues to wait for matching native updates.
