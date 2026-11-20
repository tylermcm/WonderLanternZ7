/* SPDX-License-Identifier: MIT. Isolated instruction fixture; no hooks installed. */
#include "../plugins/highlight_request.h"
struct z7_highlight_request z7_hr;
uint32_t z7_main(const void *unused) { (void)unused; return 0; }
uint32_t z7_hr_submit(const void *gui, uint32_t output, uint32_t epoch)
{ return z7_highlight_request_submit(&z7_hr, gui, output, epoch); }
uint32_t z7_hr_begin(const void *packet, uint32_t epoch)
{ return z7_highlight_request_begin(&z7_hr, packet, epoch); }
void z7_hr_end(void) { z7_highlight_request_end(&z7_hr); }
uint32_t z7_hr_reap(void) { return z7_highlight_request_reap(&z7_hr); }
uint32_t z7_hr_defer(uint32_t output, uint32_t epoch)
{ return z7_highlight_request_submit_deferred(&z7_hr, output, epoch); }
uint32_t z7_hr_convert(const void *gui, uint32_t epoch)
{ return z7_highlight_request_convert_deferred(&z7_hr, gui, epoch); }
