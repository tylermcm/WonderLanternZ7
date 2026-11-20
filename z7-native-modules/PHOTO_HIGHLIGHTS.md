# Original-Z7 photo-highlight port research

Independent original-Z7 C3.80 interface research. The feature design is informed
by the pinned MIT JKWTCN Z7II photo_zebra implementation. No foreign addresses
are installed, and no camera, card, firmware staging or flash is involved.

## Verified native transport

The original decoder at `102396E2` reads the command from request+10hex.
With byte `A180A568` set to selector0, command `42060007` normalizes to
(group0, operation6, selector0), while `42062007` is rejected. Selector1 accepts
`42062007` as (group0, operation6, selector1) and rejects `42060007`.
The physical LCD/EVF meaning of these selectors is not established by this test.

Native dispatcher `10239840` reads service state from `A1D68E54 + group`.
Its function table starts at `10629FC8`, with300-byte group stride,
60-byte state stride and4-byte operation stride. For group0/operation6,
states1 through4 select `1023E215` at these original table slots:
`1062A01C`, `1062A058`, `1062A094`, `1062A0D0`.
The audit executes the original decoder, table dispatch and handler for both
commands and all four supported incoming service states.

The handler at `1023E214` consumes a payload pointer at request+14hex and:

- Copies exactly100 bytes to `*A180A588 + 28hex`.
- Sets the state word at offset24hex to1.
- Sets the source acknowledgement word at offset100decimal to1.
- Calls original completion `102396C0(request, 0)` and returns1.

The source packet therefore needs at least104 accessible bytes. A standalone
100-byte scratch buffer is insufficient for this consumer. This agrees with
the pinned design using26-word request payload storage, but it does not prove
that the native parameter meanings or all other offsets match the Z7II.

Four payload cases exercise direct copying, acknowledgement, request identity,
and untouched surrounding bytes. Native decoder/output selection and eight
native state-dispatch cases bring the focused audit to37 passing checks.
Incoming request/state storage, initialized service-state bytes and completion
are supplied fixtures. Original memory copy and native decode/dispatch execute;
no actual display hardware or warning pixels are established.

Run from the root checkout with private inputs/outputs:

```powershell
.venv\Scripts\python.exe tools/audit_z7_display_parameters.py --stock-main .private/builds/20261021-silent-property-01/stock-main.bin --output .private/evidence/display-parameters-new.json
```

The input must match the existing exact C3.80 stock-main fingerprint. The output
must be a new path under `.private`. Firmware/disassembly stay private.
Source-only evidence: `evidence/20261120-display-parameters.json`.

## Remaining implementation work

Find and execute the original-Z7 converter from the GUI request shape to the
100-byte packet, including threshold/pattern semantics and native tables.
Bind output selection and photo/movie context from original-Z7 callers.
Trace the frame producer and its warning-enable metadata; do not reuse Z7II
callback addresses or assume its context/image offsets. Then integrate owned
packet interception, cancellation/restoration, preset visibility, and native
LCD/EVF/movie preservation with the full resident profile. Pixels and output/
capture/menu/lens transitions require separate acceptance evidence.

The existing Photo highlights preference is still not connected to a producer.
No visible highlight feature or installation/recovery clearance is claimed.
