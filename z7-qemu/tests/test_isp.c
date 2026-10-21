/* SPDX-License-Identifier: GPL-2.0-or-later */
/* Synthetic RAW only: no private frames or proprietary output oracle. */
#include <glib.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
static uint16_t lduw_le_p(const void *p) { const uint8_t *q=p; return q[0]|q[1]<<8; }
#include "../qemu/nikon-z7-isp-pixels.h"
static unsigned checks;
#define CHECK(c) do { checks++; if (!(c)) { fprintf(stderr,"FAIL line%d: %s\n",__LINE__,#c); return 1; } } while (0)
int main(void)
{
    size_t n=5568*932;
    uint8_t *raw=g_malloc0(n);
    Z7ISPImages *p=z7_isp_images_new(false);
    CHECK(!z7_isp_images_output(p,0,8,8,16));
    z7_isp_images_input(p,raw);
    const uint8_t *image=z7_isp_images_output(p,0,8,8,16);
    CHECK(image && p->misses==1);
    for (unsigned i=0;i<192;i++) CHECK(image[i]==(i<128?16:128));
    CHECK(z7_isp_images_output(p,0,8,8,16)==image && p->hits==1);
    CHECK(!z7_isp_images_output(p,3,8,8,16));
    CHECK(!z7_isp_images_output(p,0,7,8,16));
    CHECK(!z7_isp_images_output(p,0,8,7,16));
    CHECK(!z7_isp_images_output(p,0,8,8,7));
    CHECK(!z7_isp_images_output(p,0,1922,8,2048));
    CHECK(!z7_isp_images_output(p,0,8,1282,16));
    CHECK(!z7_isp_images_output(p,0,8,8,2050));
    CHECK(z7_isp_images_output(p,1,8,6,16));
    CHECK(z7_isp_images_output(p,2,8,8,8));
    raw[5567]=1; z7_isp_images_input(p,raw);
    CHECK(!p->output[0].data && !p->output[1].data && !p->output[2].data);
    /* An independent constant white scene verifies Y/UV levels and padding. */
    for (unsigned y=0;y<932;y++) for (unsigned x=0;x<2780;x++) {
        raw[y*5568+x*2]=255; raw[y*5568+x*2+1]=15;
    }
    z7_isp_images_input(p,raw);
    image=z7_isp_images_output(p,0,8,8,16);
    for (unsigned y=0;y<8;y++) for (unsigned x=0;x<16;x++) CHECK(image[y*16+x]==(x<8?235:16));
    for (unsigned i=128;i<192;i++) CHECK(image[i]==128);
    uint8_t saved[192]; memcpy(saved,image,192);
    uint64_t misses=p->misses; p->disable_cache=true;
    image=z7_isp_images_output(p,0,8,8,16);
    CHECK(p->misses==misses+1 && !memcmp(saved,image,192));
    z7_isp_images_free(p); g_free(raw);
    printf("PASS %u synthetic ISP checks\n",checks); return 0;
}
