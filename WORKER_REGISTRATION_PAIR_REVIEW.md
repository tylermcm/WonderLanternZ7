# Single-step worker registration test - November 22, 2026

Prepared privately; neither trial is staged or authorized for camera use yet.
Independent MIT diagnostic built from the working battery/six-grid components.
No firmware image or update is involved. Installed host remains the original
7d7356e7775db90483ed9fe5598f401afb7fb8498a7b42bd71900db849d7f057 build;
the offline host weak-CAS change is not part of this experiment.

## Exact candidates

Both modules are 5,324 bytes with identical code, BSS, entry and relocation layout.
Only the 32-bit flag at image offset 5012 and the header CRC differ.

| Step | Worker registration | Z7APP.BIN SHA-256 |
| --- | --- | --- |
| A | Disabled | 412dffaf9a2b5f9aa5cf9e715b66e778e9de1e9f4c67eabc2963df7899a200f9 |
| B | Enabled; callback only returns | 767ada057f52df432aa037c341d300207d1bf436fea9258c5c58b78d4556a158 |

Private artifacts: `.private/builds/20261122-worker-registration-pair-01`.
The matched controls add 64 bytes to the previously working module. A checks
that common packaging/entry change before B changes the registration flag.
No restore code, file adapters, GUI-seen wrapper or selection atomics are added.
Existing battery percentage and six volatile grid choices remain. EVF remains stock.
The existing Z7GRID.DAT seed is left intact and unused.

## Sequential installation and observation

1. Obtain approval for A only and positively identify the reader/card again.
   Privately back up and fingerprint active and disabled modules, update file,
   seed/configuration files if present, and the existing file catalog.
2. Preserve active known-working Z7APP.BIN (SHA 53334536d00ed18ea9d80d36dd736d6341fd1943da674f6e0fd513112f226195)
   with an unused disabled name, such as Z7APP.SIX-GRID-WORKING.disabled.
   Stop on unexpected active contents or any name collision. Do not replace
   existing disabled files, photographs or seed/configuration contents.
3. Exclusively create Z7APP.BIN from A; flush, full readback/hash, verify existing
   files/catalog unchanged except intended rename/addition, then safely eject.
4. With camera off, insert card and start normally. Do not choose firmware Update.
   Observe battery percentage, MENU/touch, grid choices and normal power-off;
   include an approximately 30-second ordinary-use interval. Record the owner's
   actual result before any next step. The last restoration of the old baseline
   has not yet received an owner test result.
5. Only after A passes, obtain separate approval to preserve A under an unused
   name and stage B using the same backup/readback/eject procedure. Repeat the
   same observations. Never advance automatically after a failure.

## Failure and recovery boundary

Prior related payloads froze all inputs including the power switch; card removal
restored controls, and battery removal was needed for power cycling. Normal boot
with no card and disabled payloads was owner-confirmed. These are prior observations,
not a guarantee that either new candidate can recover the same way.

If a trial freezes, stop that trial. Report the display/control state; use the
previously effective card-removal isolation, then power off normally if possible.
If power remains unresponsive, battery removal was the previous recovery method.
Reconnect the card for read-only inspection and preservation/disable of the trial;
do not run an update. Restoring the exact old module requires a deliberate card
action and verification. No stock firmware restoration or physical recovery
mechanism has been independently validated.

A pass followed by B freeze implicates worker registration/execution on this host
without any restore or file I/O. It does not establish the physical failing PC.
If A fails, the worker cannot explain that failure because it was not registered.
If both pass, worker registration alone is insufficient to reproduce the freeze;
choose one further addition only after reviewing those observations.

## Offline evidence scope

The audit executes both exact modules against the original installed-host image,
checks grid publication/selection/geometry and battery policy, and checks healthy
and injected-failing exclusive stores. The callback begins with `bx lr`.
Supplied UI/kernel/telemetry/storage boundaries and injected STREX outcomes do not
establish camera acceptance, actual scheduler timing, physical cause or recovery.
Private results: `.private/evidence/20261122-worker-registration-pair-01.json`.
