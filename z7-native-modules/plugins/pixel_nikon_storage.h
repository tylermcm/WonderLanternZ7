/* SPDX-License-Identifier: MIT. Independent Z7 pixel controls preference file.
 * Count/delay/interval/folder flags persist. Every boot starts with mode Off.
 * Separate from every existing display, sound and playback journal.
 */
static const char z7_pn_path[]="A:\\Z7PXL.DAT";
static _Alignas(64) uint32_t z7_pn_record[16];
static uint32_t z7_pn_saved, z7_pn_observed, z7_pn_quiet, z7_pn_retry;
volatile uint32_t z7_pn_loaded, z7_pn_saves, z7_pn_errors;
static uint32_t z7_pn_state(void) { return z7_pm_count_index | z7_pn_delay_index<<4 | z7_pn_interval_index<<8 | z7_pn_new_folder<<13 | z7_pn_reset_numbering<<14 | z7_pn_ae_enabled<<15 | z7_pn_ae_count<<16 | z7_pn_ae_step<<20; }
static uint32_t z7_pn_check(uint32_t state) { return 0x4e50375au ^ (4u<<8) ^ state*0x9e3779b1u; }
static void z7_pn_prepare(void)
{
    if (!z7_sl_matches()) return;
    z7_pn_saved=z7_pn_observed=z7_pn_state();
    uint32_t fd=SND_F(SND_FILE_OPEN,uint32_t,const char *,uint32_t,uint32_t)(z7_pn_path,0,0);
    if ((int32_t)fd<0) return;
    uint32_t actual=0;
    SND_F(SND_INVALIDATE,void,void *,uint32_t)(z7_pn_record,sizeof(z7_pn_record));
    uint32_t r=SND_F(SND_FILE_READ,uint32_t,uint32_t,void *,uint32_t,uint32_t *)(fd,z7_pn_record,sizeof(z7_pn_record),&actual);
    SND_F(SND_INVALIDATE,void,void *,uint32_t)(z7_pn_record,sizeof(z7_pn_record));
    uint32_t closed=SND_F(SND_FILE_CLOSE,uint32_t,uint32_t)(fd),s=z7_pn_record[2];
    uint32_t version=z7_pn_record[1];
    uint32_t check=0x4e50375au ^ (version<<8) ^ s*0x9e3779b1u;
    if (!r && !closed && actual==16u && z7_pn_record[0]==0x4e50375au && version>=1u && version<=4u &&
        (s&15u)<4u && z7_pn_record[3]==check &&
        (version==1u ? (s>>4&15u)<7u && (s>>8&15u)<7u && !(s>>12) :
                       (s>>4&15u)<6u && (s>>8&31u)<=30u &&
                       (version==2u ? !(s>>13) :
                        (version==3u ? !(s>>15) : !(s>>24) && (s>>16&15u)<9u && (s>>20&15u)<12u &&
                         (!(s&(1u<<15)) || (s>>16&15u)!=4u)) && (!(s&(1u<<14)) || (s&(1u<<13)))))) {
        z7_pm_count_index=s&15u;z7_pn_delay_index=s>>4&15u;z7_pn_interval_index=s>>8&31u;
        if (version==1u) {
            static const uint8_t delay_map[]={0,2,4,5,5,5,5},interval_map[]={0,1,2,3,5,10,30};
            z7_pn_delay_index=delay_map[z7_pn_delay_index];
            z7_pn_interval_index=interval_map[z7_pn_interval_index];s=z7_pn_state();
        }
        if (version>=3u) { z7_pn_new_folder=s>>13&1u;z7_pn_reset_numbering=s>>14&1u; }
        if (version==4u) { z7_pn_ae_enabled=s>>15&1u;z7_pn_ae_count=s>>16&15u;z7_pn_ae_step=s>>20&15u; }
        z7_pn_saved=z7_pn_observed=z7_pn_state();z7_pn_loaded=1;
    } else z7_pn_loaded=2;
}
static void z7_pn_save_worker(void)
{
    uint32_t s=z7_pn_state();
    if (!z7_sl_matches() || s==z7_pn_saved || z7_pm_running) return;
    if (s!=z7_pn_observed) { z7_pn_observed=s;z7_pn_quiet=0;return; }
    if (z7_pn_quiet<2u) { ++z7_pn_quiet;return; }
    if (z7_pn_retry) { --z7_pn_retry;return; }
    z7_pn_record[0]=0x4e50375au;z7_pn_record[1]=4;z7_pn_record[2]=s;z7_pn_record[3]=z7_pn_check(s);
    SND_F(SND_CLEAN,void,void *,uint32_t)(z7_pn_record,sizeof(z7_pn_record));
    uint32_t fd=SND_F(SL_CREATE,uint32_t,const char *,uint32_t)(z7_pn_path,0),actual=0;
    uint32_t r=fd;
    if ((int32_t)fd>=0) {
        r=SND_F(SL_WRITE,uint32_t,uint32_t,const void *,uint32_t,uint32_t *)(fd,z7_pn_record,16u,&actual);
        uint32_t closed=SND_F(SND_FILE_CLOSE,uint32_t,uint32_t)(fd);
        if (!r && (closed || actual!=16u)) r=0x5407e000u;
    }
    if (!r) { z7_pn_saved=s;++z7_pn_saves; }
    else { ++z7_pn_errors;z7_pn_retry=5; }
}
