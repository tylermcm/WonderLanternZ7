# Original-Z7 feature parity work

The target is JKWTCN's Z7II feature set at
[`f298964`](https://github.com/JKWTCN/z7ii-extensions/tree/f298964fdf6b0d20df0d3c6cad48a74aa5f5c339)
(`v0.1.0-preview.35`), observed November 24, 2026. Its README lists 22 headline
features. The original vendored source pin remains unchanged; this comparison
does not replace component licenses or substitute Z7II bindings for Z7 bindings.

[The feature inventory](UPSTREAM_PARITY.json) records each upstream document,
local implementation state and remaining work. `partial` means a feature has
some implementation, not full parity. `research` means native foundations or a
separate prototype exist. No entry is marked hardware parity verified.

The current API44 LCD checkpoints include saved grids, four custom DISP presets,
conditional focal display and battery percentage. Newer candidates add LCD
histogram/horizon composition, movie LCD battery admission and the native full
Information display. Their camera gates remain recorded in the exact reviews.
Center cross already supplies one internal horizontal and vertical line, the
2x2 layout; matching upstream output coverage and rounding remains to assess.

The next integration is [photo highlight stripes](LCD_HIGHLIGHTS_INTEGRATION.md).
Its native warning renderer requires the experimental API72 host, so it cannot
be loaded on the installed API44 host. The combined version-4 settings keep grid,
page and highlight choices together in separate `Z7EXT` journals; existing
`Z7DSP` and `Z7CFG` files remain read-only migration inputs.

Work proceeds through display consolidation, portrait and remaining output
support, movie controls, sound/playback, AF/capture features, then network/gallery
and composition-reference features. Native bindings and available capabilities
must be assessed for the original Z7. In particular, dual-card UI and sensor-shift
calibration cannot be assumed to transfer unchanged.

The owner requested deferring the brief startup grid transition. Feature work
continues without making that cosmetic issue a prerequisite. Camera updates
still require an exact installation/recovery assessment and explicit approval.
Offline checks do not establish camera appearance, recording behavior, AF/IBIS
behavior, card durability or recovery.
