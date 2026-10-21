# Debugging and evidence

## Begin with the local session

Check `.local/sessions/current.json`, the corresponding QEMU log, and
`actions.jsonl`. `GET /api/status` reports boot phase, queued actions, RAW/ISP
counts, scanout observations and errors. The error record includes a traceback.
These local files can contain guest memory, paths and UI data; do not publish
them without a separate content review.

Distinguish a host exception, unknown guest MMIO, a guest data abort and a
blocked RTOS task. A stopped screenshot alone does not distinguish them. The
original AutoOperation return acknowledges the action and can still represent
a failed capture start.

## RSP / GDB

The launcher uses QEMU's GDB remote protocol and QMP on separate localhost
sockets. The Python worker is their single owner. Do not attach another client
to those sockets while it is operating them. For manual GDB, launch QEMU directly
with the firmware and the device/test options you intend to reproduce, rather
than stealing the browser worker's socket.

After building, a CPU-only inspection example is:

```sh
/path/to/build/qemu-system-arm -M nikon-z7-boot -smp 2 -display none \
    -serial none -monitor none -nic none -bios /path/to/your/main-payload.bin \
    -device loader,addr=0x10020000,cpu-num=0 \
    -device loader,addr=0x10020000,cpu-num=1 \
    -chardev file,id=z7uart,path=/tmp/wonderlantern-uart.log \
    -S -gdb tcp:127.0.0.1:12345
gdb-multiarch
```

In GDB:

```gdb
set architecture arm
target remote 127.0.0.1:12345
info threads
info registers
hbreak *0x100356b8
continue
```

This minimal direct boot has no browser startup assistance; reaching a UI is
not expected. Do not remove that distinction when reporting a result.

## Thread selection and calls

ARM RSP register interpretation depends on the negotiated layout. The small
client requests ARM XML before diagnostic calls. Select the thread reported in
each stop packet before reading registers or interpreting its stack.

`probe.call_fixture` saves register context and scratch bytes, supplies arguments,
calls an original function, waits at an existing return checkpoint and restores
the saved context. The task may migrate between CPUs. The helper records both
call and return CPU; assuming they are identical can corrupt a resumed guest.
Its output is diagnostic input, not evidence of a real controller exchange.

## Breakpoints and virtual time

Raw RSP continue does not perform GDB's usual breakpoint step-over behavior.
Removing and reinstalling a breakpoint without executing the instruction can
keep returning to the same point. Allow the guest to reach the other side of a
delay loop, or explicitly step the selected CPU, before reinstallation.

`icount` maps translated instructions to virtual time. Wall-clock speed is not
sensor speed. Single-instruction translation blocks are useful for diagnosis
but substantially slower; the browser defaults to normal blocks. Do not change
timing, completion masks and GUI refresh together in a performance experiment.

QMP and RSP are separate sockets. After issuing continue, the worker waits for
QMP to acknowledge running status. An immediate stale query is not justification
to send a second continue or conceal a real unexpected stop.

## Device investigations

For an unknown access, record model/version fingerprint, PC, physical address,
access width, direction, value, existing state and expected completion path.
Identify whether it is a configuration write, data transfer, status read or W1C
acknowledgment. Implement that contract and a rejection case; avoid a broad
"all operations complete" fallback.

Use sentinels around a DMA destination and check the entire written extent.
Trace source → output descriptor → native selection → LCD address → screenshot.
Counters report observed events; they do not establish physical hardware
accuracy. Preserve failed runs and link a later correction instead of overwriting
the evidence.
