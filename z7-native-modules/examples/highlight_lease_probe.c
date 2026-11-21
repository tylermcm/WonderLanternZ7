/* SPDX-License-Identifier: MIT. Isolated ownership publication fixture. */
#include "../plugins/highlight_lease.h"
struct z7_highlight_lease z7_hl_publication;
struct z7_highlight_lease_record z7_hl_input;
struct z7_highlight_lease_snapshot z7_hl_output;
_Static_assert(sizeof(struct z7_highlight_lease_record) == 248, "lease record");
_Static_assert(sizeof(struct z7_highlight_lease) == 260, "lease publication");
_Static_assert(sizeof(struct z7_highlight_lease_snapshot) == 252, "lease snapshot");
uint32_t z7_main(const void *unused) { (void)unused; return 0; }
uint32_t z7_hl_publish(void) { return z7_highlight_lease_publish(&z7_hl_publication, &z7_hl_input); }
uint32_t z7_hl_read(void) { return z7_highlight_lease_read(&z7_hl_publication, &z7_hl_output); }
uint32_t z7_hl_context(void) { return z7_highlight_context_read(&z7_hl_input.context); }
