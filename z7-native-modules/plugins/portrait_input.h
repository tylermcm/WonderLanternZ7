/* SPDX-License-Identifier: MIT. Independent original-Z7 portrait controls.
 * Derived from JKWTCN portrait_menu.c at50a22b24c50619cffa646dac386e8334659f475a,
 * copyright (c) 2026 JKWTCN. Caller admits page/orientation and event lifetime.
 * Touch calibration1024x682 follows pinned source; original native touch
 * registration/calibration/copy lifetime are not established by this helper.
 */
#ifndef Z7_PORTRAIT_INPUT_H
#define Z7_PORTRAIT_INPUT_H
#include <stdint.h>
enum z7_portrait_control_page { Z7_CONTROL_GRID=1,Z7_CONTROL_DIAL,Z7_CONTROL_SETTING,Z7_CONTROL_EXTERNAL };
__attribute__((target("hwdiv")))
static inline int32_t z7_portrait_input_unscale(int32_t pixel,int32_t scale)
{ return ((pixel+1)*65536-1)/scale; }
static inline uint32_t z7_portrait_input_point(int16_t *point,uint32_t page,uint32_t orientation)
{
    if (!point || page<Z7_CONTROL_GRID || page>Z7_CONTROL_EXTERNAL || (orientation!=1 && orientation!=2)) return 0;
    int32_t x=(point[0]*720+512)/1024,y=(point[1]*480+341)/682;
    int32_t u=orientation==2 ? 479-y : y,v=orientation==2 ? x : 719-x;
    int32_t stock_x=-1,stock_y=-1;
    if (u>=0 && u<480 && v>=0 && v<720) {
        if (page==Z7_CONTROL_GRID || page==Z7_CONTROL_DIAL) {
            if (v>=440 && v<659) {
                int32_t row=(v-440)/73,col=u/120,cell=row*4+col;
                stock_x=cell%6*120+u%120;stock_y=280+cell/6*73+(v-440)%73;
            } else if (v>=660 && v<715) {
                stock_x=z7_portrait_input_unscale(u+211,57344);
                stock_y=z7_portrait_input_unscale(v-295,57344);
            } else if (page==Z7_CONTROL_DIAL && v>=283 && v<440) {
                stock_x=z7_portrait_input_unscale(u,43691);
                stock_y=z7_portrait_input_unscale(v-254,43691);
            }
        } else {
            int32_t shift=page==Z7_CONTROL_SETTING ? 235 : 394;
            int32_t sy=page==Z7_CONTROL_SETTING ? 65536 : 43691;
            int32_t height=(480*sy)>>16;
            if (v>=shift && v<shift+height) {
                stock_x=z7_portrait_input_unscale(u,43691);
                stock_y=z7_portrait_input_unscale(v-shift,sy);
            }
        }
    }
    if (stock_x<0 || stock_x>=720 || stock_y<0 || stock_y>=480) point[0]=point[1]=-4;
    else {point[0]=(int16_t)((stock_x*1024+360)/720);point[1]=(int16_t)((stock_y*682+240)/480);}
    return 1;
}
/* Returns1 for a copied/remapped packet,0 for stock delegation. No native
 * queue is called. Reject overlapping output so producer data stays intact. */
static inline uint32_t z7_portrait_input_event(const uint32_t *event,uint32_t *local,uint32_t page,uint32_t orientation)
{
    uintptr_t a=(uintptr_t)event,b=(uintptr_t)local;
    if (!a || !b || ((a|b)&3u) || a>UINTPTR_MAX-60 || b>UINTPTR_MAX-60 ||
        (a<b+60 && b<a+60) || page<Z7_CONTROL_GRID || page>Z7_CONTROL_EXTERNAL ||
        (orientation!=1 && orientation!=2)) return 0;
    uint32_t kind=((const uint8_t *)event)[9];
    if (!kind || kind>=9) return 0;
    for (uint32_t i=0;i<15;++i) local[i]=event[i];
    static const uint8_t offsets[]={0x12,0x1a,0x28,0x2c,0x30,0x34};
    for (uint32_t i=0;i<sizeof(offsets);++i) {
        int16_t *p=(void *)((uint8_t *)local+offsets[i]);
        if (!i || p[0] || p[1]) z7_portrait_input_point(p,page,orientation);
    }
    return 1;
}
static inline uint32_t z7_portrait_input_direction(uint32_t direction,uint32_t orientation)
{
    static const uint8_t rotated[2][4]={{3,2,0,1},{2,3,1,0}};
    return direction<4 && (orientation==1 || orientation==2) ? rotated[orientation-1][direction] : direction;
}
static inline uint32_t z7_portrait_input_key(uint32_t key,uint32_t orientation)
{
    static const uint8_t rotated[2][4]={{4,5,3,2},{5,4,2,3}};
    return key>=2 && key<=5 && (orientation==1 || orientation==2) ? rotated[orientation-1][key-2] : key;
}
/* Validated current0..11, direction0..3, orientation1/2. Bounded unsigned
 * arithmetic implements the pinned4x3 wrap without signed remainder ambiguity. */
static inline uint32_t z7_portrait_input_next(uint32_t current,uint32_t direction,uint32_t orientation)
{
    uint32_t x=current%4,y=current/4,step=orientation==2 ? 1 : 3;
    if (direction<2) x=(x+(direction==0 ? step : 4-step))%4;
    else {step=orientation==2 ? 1 : 2;y=(y+(direction==2 ? step : 3-step))%3;}
    return y*4+x;
}
static inline uint32_t z7_portrait_input_target(uint32_t current,uint32_t direction,uint32_t orientation,uint32_t disabled)
{
    if (current>=12 || direction>=4 || (orientation!=1 && orientation!=2)) return current;
    uint32_t target=current;
    for (uint32_t i=0;i<4;++i) {
        target=z7_portrait_input_next(target,direction,orientation);
        if (target==current || !(disabled&(1u<<target))) break;
    }
    return target;
}
#endif
