/* SPDX-License-Identifier: MIT. Independent original-Z7 C 3.80 menu binding.
 * Append to the existing Photo shooting menu; preserve every native row/map.
 * Prepared before publication and rejected if a foreign owner is present.
 */
#define PN_PHOTO_OBJECT (0xa1833548u+0x29u*44u)
static uint32_t z7_pn_photo_meta[7],z7_pn_photo_callbacks[8];
static uint32_t z7_pn_photo_controls[34][7],z7_pn_photo_maps[34],z7_pn_photo_events[18][4];
static uint32_t z7_pn_photo_origin;
static uint32_t z7_pn_photo_open(void)
{
    if (!sm_owned(0xa1833548u)) return 0;
    z7_settings_view=7;z7_pn_photo_origin=1;
    return F(0x10404c43u,uint32_t,uint32_t,uint32_t)(2,0);
}
static uint32_t z7_pn_photo_enter(uint32_t object)
{
    F(0x103fbb5du,void,const char *,uint32_t,uint32_t)("Pixel shift shooting",47,0);
    return F(0x10494eedu,uint32_t,uint32_t)(object);
}
static uint32_t z7_pn_photo_prepare(void)
{
    const uint32_t *o=(const uint32_t *)(uintptr_t)PN_PHOTO_OBJECT;
    if (o[0]!=0x00290002u || o[1]!=0xa1833574u || o[3] || o[9] ||
        o[4]!=0x1066b720u || o[10]!=0xa1875f18u) return 0;
    const uint32_t *m=(const uint32_t *)(uintptr_t)o[10];
    if (m[0]!=0x1003u || m[3]!=0x113ec730u || m[4]!=0x114384c8u || m[5]!=0x00080021u) return 0;
    for (uint32_t i=0;i<7;++i) z7_pn_photo_meta[i]=m[i];
    for (uint32_t i=0;i<8;++i) z7_pn_photo_callbacks[i]=W(o[4]+4*i);
    for (uint32_t i=0;i<33;++i) {
        z7_pn_photo_maps[i]=W(m[4]+4*i);
        for (uint32_t j=0;j<7;++j) z7_pn_photo_controls[i][j]=W(m[3]+(i*7+j)*4);
    }
    uint32_t source=z7_pn_photo_maps[0],activations=0;
    if (!readable(source,sizeof(z7_pn_photo_events))) return 0;
    for (uint32_t i=0;i<18;++i) {
        for (uint32_t j=0;j<4;++j) z7_pn_photo_events[i][j]=W(source+(i*4+j)*4);
        uint32_t event=z7_pn_photo_events[i][0];
        if (event==0x239u || event==0x252u || event==0x25fu) {
            if (z7_pn_photo_events[i][1]!=0x10404f89u || z7_pn_photo_events[i][3]!=0x2au) return 0;
            z7_pn_photo_events[i][1]=(uint32_t)(uintptr_t)z7_pn_photo_open;
            z7_pn_photo_events[i][2]=0;z7_pn_photo_events[i][3]=0x3a0; ++activations;
        }
    }
    if (activations!=3u) return 0;
    for (uint32_t j=0;j<7;++j) z7_pn_photo_controls[33][j]=z7_pn_photo_controls[0][j];
    z7_pn_photo_controls[33][0]=47;z7_pn_photo_controls[33][1]=0xffff;
    z7_pn_photo_controls[33][2]=0xffff;z7_pn_photo_controls[33][3]=0;
    z7_pn_photo_controls[33][4]=0x1209;z7_pn_photo_controls[33][5]=0;
    z7_pn_photo_controls[33][6]=0x7c01;
    z7_pn_photo_maps[33]=(uint32_t)(uintptr_t)z7_pn_photo_events;
    z7_pn_photo_meta[3]=(uint32_t)(uintptr_t)z7_pn_photo_controls;
    z7_pn_photo_meta[4]=(uint32_t)(uintptr_t)z7_pn_photo_maps;
    z7_pn_photo_meta[5]=0x00080022u;
    z7_pn_photo_callbacks[0]=(uint32_t)(uintptr_t)z7_pn_photo_enter;
    return 1;
}
static void z7_pn_photo_publish(void)
{
    W(PN_PHOTO_OBJECT+40)=(uint32_t)(uintptr_t)z7_pn_photo_meta;
    __asm__ volatile("dmb sy" ::: "memory");
    W(PN_PHOTO_OBJECT+16)=(uint32_t)(uintptr_t)z7_pn_photo_callbacks;
}
