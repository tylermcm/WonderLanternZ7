/* SPDX-License-Identifier: MIT. Isolated RAM-context instruction diagnostic. */
#include "../plugins/highlight_context.h"
struct z7_highlight_context z7_hc_result;
uint32_t z7_main(const void *unused) { (void)unused; return 0; }
uint32_t z7_hc_read(void) { return z7_highlight_context_read(&z7_hc_result); }
uint32_t z7_hc_null(void) { return z7_highlight_context_read(0); }
