# Live-view audio retrigger failure — October 21, 2026

Subsequent October 22 work executes the original callback consumer and traces a
separate release-request service. Read [CAPTURE_EVENT_TRACE.md](CAPTURE_EVENT_TRACE.md).
Its 24 evidence checks strengthen the diagnosis but do not identify a valid
per-photo replacement trigger or clear another flash.

The owner reports continuous sound whenever the camera is in live view, stopping
on opening the menu, with the heading **Capture audio busy**. The phrase about
the menu was ambiguous; whether the menu itself closes has not been established.
The user was instructed to set **Shutter sound → Enabled OFF** and leave it off.
The owner subsequently confirmed: **"Yes, OFF stops it."** This establishes
owner-reported containment on the camera, not correct photo-triggered behavior.
No additional menu-stability detail or exact stop timing was supplied.

The test sequence associates this report with `20261021-silent-property-01`, full
EG SHA-256 `9e636d645281ee9f92cb150b6dcc8d771b21ff95c47e45f538d951a1d932420b`.
Installation is inferred, without firmware readback. This is a failed camera
behavioral test. Audible background playback does not establish shutter-cue success.
The [port audit hold](PORT_AUDIT.md) remains open. No firmware source change,
candidate rebuild, staging, camera write or rollback was performed for this report.

## Incorrect event assumption

The current hook at `0x100726A8` calls the custom trigger after native callback
event `0x04190001`. Earlier tests demonstrated native callback preservation and
queue admission, but did not establish that this notification identifies an
individual photo. The owner's report invalidates its use as sufficient permission
to play a shutter sound. Its precise native meaning and live-view cadence remain
unproven; there is no recorded hardware event trace.

The trigger has mode, loaded-file and busy checks, but no independently established
photo-transaction check. An idle notification can queue audio. A notification
while custom playback is active sets PENDING and attempts a stop. A successful
finished packet then restarts audio if PENDING and ENABLED are still set. Further
idle notifications can also start new audio without using that restart branch.
This explains a mechanism consistent with the report, not a measured hardware
timeline. Capture audio busy records entry to a busy gate; it is not proof that
the camera took a photo or that the audio driver is permanently stuck.

## Offline reproduction against the existing binary

`tools/audit_sound_retrigger.py` runs the existing full MAIN image in Unicorn.
It supplies controller notifications without supplying an independently identified
photo transaction. Results are in `evidence/20261021-liveview-retrigger-audit.json`:

- Three sequential notifications queue three audio requests.
- An overlapping notification sets PENDING and the Capture audio busy heading.
  Supplying a successful finished packet increases queue requests from one to two.
- Executing the compiled Enabled OFF action clears ENABLED and PENDING. A supplied
  finished packet and three further notifications produce no new queue requests.
- Starting with Enabled OFF also blocks all three notifications.

The audit exits **1**, with the two required notification-only rejection checks
failing and the two OFF checks passing. This is intentionally retained failure
evidence. It does not identify the correct photo trigger or claim to emulate real
live-view frames. Callback, property RAM, allocator, audio queue, stop acceptance,
completion packets, controller helpers/semaphore and UI boundaries are controlled.
The native dispatcher, custom routines, UI OFF action, labels and original native
property getter execute. OFF prevents new admission in this sequence; it does not
synchronously cancel currently playing audio in the tested sequence. The owner's
subsequent report confirms OFF stops the loop on the camera; exact stop timing
and native driver completion behavior were not measured.

The previous 60 callback checks lacked a no-photo live-view case and encoded the
assumption that normal notification meant capture. Their passing result cannot
clear this regression. An arbitrary delay or debounce would not establish photo
semantics and is not proposed as a fix.

## Required evidence before another candidate

Identify a photo exposure/transaction signal independently from the Z7 native
consumer and its state changes. Show why background live view cannot satisfy it.
Review callback concurrency, ownership, pending/stop/completion and OFF behavior,
including cancellation and failures. Negative cases must cover idle live view,
half press, menu transitions and non-photo notifications; positive cases must
distinguish a single photo and a burst from repeating background events. These
requirements supplement the full port/interface and installation/recovery audit;
they do not replace it. No new flash is cleared.
