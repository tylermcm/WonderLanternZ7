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

## Verified request converter

Original `1034FE22` accepts `(destination, request, output_flags)` and converts
the36-byte GUI request to sparse fields in the100-byte display packet. The
request shape agrees with the pinned design: enabled word0; reserved bytes4/5;
two groups of four halfwords at6 and14; horizontal/vertical words24/28; pattern
bytes32/33. Addresses and native field behavior were bound on the original Z7.

The converter uses native enumeration-table accessors `10433B1E`, `10433B26`,
`10433B2E` and native palette getter `10435ACA(1,0)`. The latter reads its
pointer from `A1F18FAC`; it is not replaced by a supplied function in the audit.
Palette contents and their initialized pointer are supplied incoming state.
Two distinct palettes verify that converted color bytes follow native lookup.

For enabled requests the first halfword in each group scales by257, and the
threshold byte scales by256. Both groups are tested at255,248,235,224,213,202,
191,180. Pattern values0/1 map through the original enumeration table; the
existing design exposes these as enabled patterns1/2. Output flag1/2/4 encodes
native packet target byte0/1/2 respectively. Physical LCD/EVF/external mapping
and photo/movie eligibility still need caller/context proof.

**Disabled conversion writes only the enable word.** All other destination
bytes remain as supplied. Clear the complete owned100-byte conversion buffer
before use; do not publish uninitialized or stale padding. The consumer still
requires a104-byte source allocation because its acknowledgement is after the
100-byte payload. Enabled conversion also preserves unspecified padding.

The converter audit passes198 checks across99 cases: three output flags, two
enabled patterns, eight thresholds, two supplied palettes, and three disabled
cases. Each case checks exact destination/padding writes, input preservation,
and native palette-getter calls. No graphics submission or producer executes.

```powershell
.venv\Scripts\python.exe tools/audit_z7_highlight_converter.py --stock-main .private/builds/20261021-silent-property-01/stock-main.bin --output .private/evidence/highlight-converter-new.json
```

Original caller `1034FF1E` invokes this converter before the request builder
`1034EFB0` and graphics submission/completion path. That caller has only been
inspected, not accepted as an executed asynchronous interface.
Source-only evidence: `evidence/20261120-highlight-converter.json`.

## Remaining implementation work

Execute the original request builder/caller and bind its output selection and
photo/movie context before using the verified converter in a module.
Trace the frame producer and its warning-enable metadata; do not reuse Z7II
callback addresses or assume its context/image offsets. Then integrate owned
packet interception, cancellation/restoration, preset visibility, and native
LCD/EVF/movie preservation with the full resident profile. Pixels and output/
capture/menu/lens transitions require separate acceptance evidence.

The existing Photo highlights preference is still not connected to a producer.
No visible highlight feature or installation/recovery clearance is claimed.
