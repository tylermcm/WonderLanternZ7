/* SPDX-License-Identifier: MIT.
 * Independent original-Z7 C 3.80 port of a card-WAV shutter-sound playback engine.
 * The private-job interception design follows JKWTCN's MIT Z7II shutter_sound.c.
 * Original-Z7 bindings are derived independently: see SHUTTER_SOUND_SD_PORT.md and
 * tools/audit_z7_sound_service_bindings.py. No trigger: callers decide when to play.
 */
#ifndef Z7_SHUTTER_SOUND_PLAYBACK_H
#define Z7_SHUTTER_SOUND_PLAYBACK_H
#include <stdint.h>

#define SND_W(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define SND_B(a) (*(volatile uint8_t *)(uintptr_t)(a))
#define SND_F(a,r,...) ((r (*)(__VA_ARGS__))(uintptr_t)(a))
#ifndef Z7_SOUND_CLIPS
#define Z7_SOUND_CLIPS 1u
#endif
#ifndef Z7_SOUND_LEVELS
#define Z7_SOUND_LEVELS 5u
#endif

enum {
    SND_POST=0x100a2d79u, SND_MAILBOX=0xa18852acu,
    SND_START_EVENT=0x0418001eu, SND_FINISHED=0x04180023u,
    SND_START_SLOT=0xa188d278u, SND_START_NATIVE=0x1006bc47u,
    SND_STATE=0xa188d190u, SND_CONTEXT=0xa21ab994u,
    SND_SPEAKER=0x100cf90bu, SND_SECOND=0x100cf98du,
    SND_FORMAT=0x1006b795u, SND_TONES=0x1006b62du, SND_DATA=0x1006b94bu,
    SND_DMA_START=0x1006b7ddu, SND_DMA_DONE=0x1006bc09u,
    SND_CLEAN=0x101e9f39u, SND_INVALIDATE=0x101e9f77u,
    SND_FILE_OPEN=0x1027bfa3u, SND_FILE_READ=0x1027c019u, SND_FILE_CLOSE=0x1027bfcdu,
    SND_RATE=48000u, SND_MAX_FRAMES=48000u, SND_MAX_WAV=SND_MAX_FRAMES*4u+4096u,
    SND_IDLE=0, SND_QUEUED=1, SND_PLAYING=2,
    /* Native start rejects type >= 18, so a lost intercept cannot play a stock sound. */
    SND_TYPE_PRIVATE=18u, SND_VOLUME_MAX=Z7_SOUND_LEVELS
};

/* Native record and job layouts; identical on Z7II and original Z7 (0x24 record). */
struct z7_sound_record {
    uint32_t play, tone, alternate, alternate_tone, right, right_tone, repeats, type;
    void (*done)(uint32_t, const void *);
};
struct z7_sound_job {
    const struct z7_sound_record *record;          /* job[0]: read by native start */
    void (*release)(uint32_t, struct z7_sound_job *); /* job[1]: native completion */
    uint32_t status;                               /* job[2]: native dispatcher result */
    uint32_t preview, clip, volume;
};
_Static_assert(sizeof(struct z7_sound_record)==0x24,"native record size");

static _Alignas(64) uint8_t z7_sound_wav[SND_MAX_WAV+64];
static _Alignas(64) int16_t z7_sound_clips[Z7_SOUND_CLIPS][SND_MAX_FRAMES*2];
static _Alignas(64) int16_t z7_sound_pcm[SND_MAX_FRAMES*2];
volatile uint32_t z7_sound_clip_bytes[Z7_SOUND_CLIPS];
volatile uint32_t z7_sound_playback, z7_sound_installed, z7_sound_starts, z7_sound_rejects;
volatile uint32_t z7_sound_finished, z7_sound_passthrough, z7_sound_prepared_key;

static uint32_t snd_le16(const uint8_t *p) { return p[0]|((uint32_t)p[1]<<8); }
static uint32_t snd_le32(const uint8_t *p) { return snd_le16(p)|(snd_le16(p+2)<<16); }

/* 48 kHz 16-bit PCM, mono or stereo, at most one second. Output is interleaved
 * stereo. Returns PCM bytes, or 0 for any malformed or out-of-range file. */
static uint32_t z7_sound_decode(const uint8_t *wav, uint32_t size, int16_t *pcm)
{
    if (size<44 || size>SND_MAX_WAV || snd_le32(wav)!=0x46464952u ||
        snd_le32(wav+4)!=size-8 || snd_le32(wav+8)!=0x45564157u) return 0;
    uint32_t channels=0, bytes=0;
    const uint8_t *samples=0;
    for (uint32_t off=12; off<size;) {
        if (size-off<8) return 0;
        uint32_t id=snd_le32(wav+off), length=snd_le32(wav+off+4);
        off+=8;
        if (length>size-off || (length&1u)>size-off-length) return 0;
        if (id==0x20746d66u) {                    /* "fmt " */
            if (channels || length<16 || snd_le16(wav+off)!=1) return 0;
            channels=snd_le16(wav+off+2);
            if ((channels!=1 && channels!=2) || snd_le32(wav+off+4)!=SND_RATE ||
                snd_le32(wav+off+8)!=SND_RATE*channels*2 || snd_le16(wav+off+12)!=channels*2 ||
                snd_le16(wav+off+14)!=16) return 0;
        } else if (id==0x61746164u) {             /* "data" */
            if (samples) return 0;
            samples=wav+off; bytes=length;
        }
        off+=length+(length&1u);
    }
    if (!samples || !channels || !bytes || (bytes&(channels*2-1)) ||
        bytes>SND_MAX_FRAMES*channels*2) return 0;
    uint32_t frames=channels==2 ? bytes>>2 : bytes>>1;
    for (uint32_t i=0;i<frames;++i) {
        pcm[i*2]=(int16_t)snd_le16(samples);
        pcm[i*2+1]=channels==2 ? (int16_t)snd_le16(samples+2) : pcm[i*2];
        samples+=channels*2;
    }
    return frames*4;
}

/* Loader/worker task only, at module init: synchronous native file reads. */
static uint32_t z7_sound_load(uint32_t clip, const char *path)
{
    if (clip>=Z7_SOUND_CLIPS) return 0;
    z7_sound_clip_bytes[clip]=0;
    uint32_t fd=SND_F(SND_FILE_OPEN,uint32_t,const char *,uint32_t,uint32_t)(path,0,0);
    if ((int32_t)fd<0) return 0;
    uint32_t actual=0;
    /* Read one byte beyond the limit to reject oversize files. */
    SND_F(SND_INVALIDATE,void,void *,uint32_t)(z7_sound_wav,SND_MAX_WAV+1);
    uint32_t result=SND_F(SND_FILE_READ,uint32_t,uint32_t,void *,uint32_t,uint32_t *)(
        fd,z7_sound_wav,SND_MAX_WAV+1,&actual);
    SND_F(SND_INVALIDATE,void,void *,uint32_t)(z7_sound_wav,SND_MAX_WAV+1);
    uint32_t closed=SND_F(SND_FILE_CLOSE,uint32_t,uint32_t)(fd);
    if (result || closed || actual>SND_MAX_WAV) return 0;
    uint32_t bytes=z7_sound_decode(z7_sound_wav,actual,z7_sound_clips[clip]);
    z7_sound_clip_bytes[clip]=bytes;
    return bytes;
}

/* Firmware fingerprint: refuse to hook anything but the exact original routines. */
static uint32_t z7_sound_native_matches(void)
{
    return SND_W(0x1006bc46u)==0x4ff0e92du && SND_W(0x100a2d78u)==0x460cb570u &&
        SND_W(0x1006b794u)==0xb08cb510u && SND_W(0x1006b62cu)==0xb090b510u &&
        SND_W(0x1006b94au)==0xb08eb510u && SND_W(0x1006b7dcu)==0xb08cb510u &&
        SND_W(0x100cf90au)==0x4604b510u && SND_W(0x1006bb58u)==0x41f0e92du &&
        SND_W(0x100a2d5eu)==0x000cb510u;
}

static void z7_sound_done(uint32_t event, const void *result)
{
    (void)result;
    if (event==SND_FINISHED) {
        ++z7_sound_finished;
        __atomic_store_n(&z7_sound_playback,SND_IDLE,__ATOMIC_RELEASE);
    }
}
static void z7_sound_release(uint32_t event, struct z7_sound_job *job)
{
    (void)event; (void)job;
    /* Still QUEUED means the start was rejected; a started job ends via done. */
    uint32_t queued=SND_QUEUED;
    if (__atomic_compare_exchange_n(&z7_sound_playback,&queued,SND_IDLE,0,__ATOMIC_ACQ_REL,__ATOMIC_ACQUIRE))
        ++z7_sound_rejects;
}
static const struct z7_sound_record z7_sound_pcm_record={1,31,0,0,0,0,1,SND_TYPE_PRIVATE,z7_sound_done};
#ifdef Z7_SOUND_TONE_OVERRIDE
/* Experimental: the record/tone-setter value Nikon accepts as 0..37 for its own
 * sounds; this engine and upstream always send 31. Its effect on PCM playback is
 * what the sound lab measures by ear. Clamped to Nikon's accepted range. */
volatile uint32_t z7_sound_tone=31u;
#define Z7_SOUND_TONE() (z7_sound_tone<=37u ? z7_sound_tone : 31u)
#else
#define Z7_SOUND_TONE() 31u
#endif
static struct z7_sound_job z7_sound_job_slot={.record=&z7_sound_pcm_record,.release=z7_sound_release};

static uint32_t z7_sound_prepare(uint32_t clip, uint32_t volume)
{
    uint32_t bytes=z7_sound_clip_bytes[clip];
    uint32_t key=(clip<<8)|volume;
    if (z7_sound_prepared_key!=key) {
        const int16_t *source=z7_sound_clips[clip];
#if Z7_SOUND_LEVELS > 5
        /* Levels 6 and up boost (x1.41, x2, ...) and clip at full scale. */
        static const int32_t gains[SND_VOLUME_MAX]={64,102,154,205,256,362,512
#if Z7_SOUND_LEVELS > 7
            ,724,1024  /* experimental x2.83, x4 */
#endif
        };
        int32_t gain=gains[volume-1];
        for (uint32_t i=0;i<bytes/2;++i) {
            int32_t v=(source[i]*gain)>>8;
            z7_sound_pcm[i]=(int16_t)(v>32767 ? 32767 : v<-32768 ? -32768 : v);
        }
#else
        /* Q8 gains keep five distinct levels without clipping full-scale WAVs. */
        static const int32_t gains[SND_VOLUME_MAX]={64,102,154,205,256};
        int32_t gain=gains[volume-1];
        for (uint32_t i=0;i<bytes/2;++i) z7_sound_pcm[i]=(int16_t)((source[i]*gain)>>8);
#endif
        z7_sound_prepared_key=key;
    }
    /* Clean to the point of coherency before the audio DMA reads the buffer. */
    SND_F(SND_CLEAN,void,void *,uint32_t)(z7_sound_pcm,bytes);
    return bytes;
}

/* Sound-service task. Only our job is diverted; every native request keeps the
 * original start handler and its full validation. */
static uint32_t z7_sound_start(uint32_t message)
{
    struct z7_sound_job *job=(struct z7_sound_job *)(uintptr_t)SND_W(message+0x14);
    if (job!=&z7_sound_job_slot) {
        ++z7_sound_passthrough;
        return SND_F(SND_START_NATIVE,uint32_t,uint32_t)(message);
    }
    uint8_t speaker=0;
    SND_F(SND_SPEAKER,uint32_t,uint8_t *)(&speaker);
    if (speaker!=1 || SND_F(SND_SECOND,uint32_t,void)() || SND_B(SND_STATE)) return 0;
    uint32_t clip=job->clip, volume=job->volume;
    if (clip>=Z7_SOUND_CLIPS || !volume || volume>SND_VOLUME_MAX || !z7_sound_clip_bytes[clip]) return 0;
    uint32_t bytes=z7_sound_prepare(clip,volume);
    const volatile uint32_t *from=(const volatile uint32_t *)job->record;
    for (uint32_t i=0;i<9;++i) SND_W(SND_CONTEXT+4*i)=from[i];
#ifdef Z7_SOUND_TONE_OVERRIDE
    uint32_t tone=Z7_SOUND_TONE();
    SND_W(SND_CONTEXT+4)=tone;
#endif
    SND_W(SND_STATE+4)=SND_W(SND_STATE+8)=SND_W(SND_STATE+12)=0;
    /* Same argument shapes as the native start handler builds on its stack. */
    const uint32_t format[2]={0x01010502u,bytes};
#ifdef Z7_SOUND_TONE_OVERRIDE
    const uint32_t tones[8]={2,1,tone,0,0,0,0,0};
#else
    const uint32_t tones[8]={2,1,31,0,0,0,0,0};
#endif
    const uint32_t data[6]={(uint32_t)(uintptr_t)z7_sound_pcm,bytes,1,0,0,0};
    const uint32_t start[3]={2,SND_DMA_DONE,0};
    if (SND_F(SND_FORMAT,uint32_t,const uint32_t *,uint32_t)(format,message)!=1 ||
        SND_F(SND_TONES,uint32_t,const uint32_t *,uint32_t)(tones,message)!=1 ||
        SND_F(SND_DATA,uint32_t,const uint32_t *,uint32_t)(data,message)!=1 ||
        SND_F(SND_DMA_START,uint32_t,const uint32_t *,uint32_t)(start,message)!=1) return 0;
    SND_B(SND_STATE+1)=1;       /* left stream started */
    SND_B(SND_STATE+2)=0;       /* single interleaved stream, no right request */
    SND_B(SND_STATE)=1;         /* playing */
    ++z7_sound_starts;
    __atomic_store_n(&z7_sound_playback,SND_PLAYING,__ATOMIC_RELEASE);
    return 1;
}

/* Any task. Returns 1 when the request was queued. Never blocks. */
static uint32_t z7_sound_enqueue(uint32_t clip, uint32_t volume, uint32_t preview)
{
    if (!__atomic_load_n(&z7_sound_installed,__ATOMIC_ACQUIRE) || clip>=Z7_SOUND_CLIPS ||
        !volume || volume>SND_VOLUME_MAX || !z7_sound_clip_bytes[clip] ||
        SND_B(SND_STATE) || !SND_W(SND_MAILBOX)) return 0;
    uint32_t idle=SND_IDLE;
    if (!__atomic_compare_exchange_n(&z7_sound_playback,&idle,SND_QUEUED,0,__ATOMIC_ACQ_REL,__ATOMIC_ACQUIRE))
        return 0;
    z7_sound_job_slot.status=0;
    z7_sound_job_slot.preview=preview;
    z7_sound_job_slot.clip=clip;
    z7_sound_job_slot.volume=volume;
    __asm__ volatile("dmb sy" ::: "memory");
    if (SND_F(SND_POST,uint32_t,uint32_t,struct z7_sound_job *)(SND_START_EVENT,&z7_sound_job_slot)==1) return 1;
    __atomic_store_n(&z7_sound_playback,SND_IDLE,__ATOMIC_RELEASE);
    return 0;
}

/* Install only with at least one valid clip, matching firmware and the native
 * handler still in the slot. A single aligned word store; no other slot changes. */
static uint32_t z7_sound_install(void)
{
    uint32_t any=0;
    for (uint32_t i=0;i<Z7_SOUND_CLIPS;++i) any|=z7_sound_clip_bytes[i];
    if (!any || z7_sound_installed || !z7_sound_native_matches() || SND_W(SND_START_SLOT)!=SND_START_NATIVE)
        return 0;
    __asm__ volatile("dmb sy" ::: "memory");
    SND_W(SND_START_SLOT)=(uint32_t)(uintptr_t)z7_sound_start;
    __asm__ volatile("dmb sy" ::: "memory");
    __atomic_store_n(&z7_sound_installed,1,__ATOMIC_RELEASE);
    return 1;
}
#endif
