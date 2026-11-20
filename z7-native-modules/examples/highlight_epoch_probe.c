/* SPDX-License-Identifier: MIT. Isolated epoch publication instruction fixture. */
#include "../plugins/highlight_epoch.h"
struct z7_highlight_publication z7_he_publication;
struct z7_highlight_view z7_he_input;
struct z7_highlight_snapshot z7_he_output;
const uint32_t z7_he_view_words = sizeof(struct z7_highlight_view) / 4;
uint32_t z7_main(const void *unused) { (void)unused; return 0; }
uint32_t z7_he_publish(void) { return z7_highlight_publish(&z7_he_publication, &z7_he_input); }
uint32_t z7_he_read(void) { return z7_highlight_snapshot(&z7_he_publication, &z7_he_output); }
uint32_t z7_he_context(void) { return z7_highlight_context_read(&z7_he_input.context); }
