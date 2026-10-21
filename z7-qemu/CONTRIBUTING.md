# Contributing

Use synthetic, independently generated inputs in public contributions.
Do not upload firmware, memory dumps, calibration, extracted fonts/icons,
decrypted programs, secrets, native camera screenshots or raw private traces.
Issue attachments and release assets are publications too; .gitignore only
affects local Git staging.

For a device change, describe the trigger, modeled state transition, affected
addresses/registers, supported width/geometry, IRQ acknowledgment and rejection
behavior. Include a positive case and an invalid/partial/duplicate case when
they matter. Separate interface observation from hardware inference.

Keep the compatible firmware fingerprint explicit. A different camera or
version needs its own profile and evidence; successful Z7 behavior does not
authorize reuse of its fixed addresses in another model.

Run `sh tests/run.sh`, then update `publication-manifest.json` only after
reviewing every changed file. Run `python tools/audit_publication.py` before
publishing. The manifest is a reviewed inventory, not an automatic permission
to publish anything found in a directory.

The project uses GPL-2.0-or-later for its contributions. Preserve existing
license notices. Explain the origin and license of any newly imported code;
do not introduce proprietary code or assets. Avoid adding restrictions that
conflict with the GPL.
