/* SPDX-License-Identifier: MIT. Derived from JKWTCN portrait_menu.c at
 * 50a22b24c50619cffa646dac386e8334659f475a, copyright (c) 2026 JKWTCN.
 * Independent original-Z7 grid reflow. No page admission or installed hook.
 */
#ifndef Z7_PORTRAIT_GRID_H
#define Z7_PORTRAIT_GRID_H
#include "portrait_geometry.h"
static int32_t z7_portrait_grid_clamp(int32_t x,int32_t lo,int32_t hi)
{ return x<lo ? lo : x>hi ? hi : x; }
static struct z7_portrait_box z7_portrait_grid_tile(int32_t index,int32_t x,int32_t y,int32_t w,int32_t h)
{ return (struct z7_portrait_box){index%4*120+x,440+index/4*73+y,w,h}; }
static uint32_t z7_portrait_grid_relocate(struct z7_portrait_box *box,uint32_t image)
{
    if (!box || box->x<0 || box->x>=720 || box->y<278 || box->y>=426 ||
        box->w<=0 || box->w>720 || box->h<=0 || box->h>480) return 0;
    int32_t cx=box->x+box->w/2,cy=box->y+box->h/2;
    if (cy<280 || cy>=426 || box->w>120+(image ? 12 : 0) || box->h>73) return 0;
    int32_t col=z7_portrait_grid_clamp(cx/120,0,5),row=(cy-280)/73;
    int32_t w=box->w,h=box->h;
    if (w>120) {
        while (h>1 && h*w>box->h*120) --h;
        w=120;
    }
    int32_t x=z7_portrait_grid_clamp(cx-col*120-w/2,0,120-w);
    int32_t y=z7_portrait_grid_clamp(cy-280-row*73-h/2,0,73-h);
    *box=z7_portrait_grid_tile(row*6+col,x,y,w,h);
    return 1;
}
/* Caller supplies a valid stock LCD box. Returns up to two logical boxes; a
 * shared stock edge can become two independent tile borders after reflow. */
static uint32_t z7_portrait_grid_edge(const struct z7_portrait_box *stock,struct z7_portrait_box boxes[2])
{
    if (!boxes || !z7_portrait_box_fits(stock,724,484)) return 0;
    int32_t y=stock->y-280;
    if (stock->w<=2 && stock->h>=70 && stock->h<=76) {
        int32_t col=(stock->x+60)/120;
        if (col>6 || stock->x<col*120-2 || stock->x>col*120+1) return 0;
        int32_t row=y<=2 && y>=-2 ? 0 : y>=71 && y<=75 ? 1 : -1;
        if (row<0) return 0;
        int32_t right=row*6+col;
        if (col>0) boxes[0]=z7_portrait_grid_tile(right-1,120-stock->w,0,stock->w,73);
        if (col==6 || (col>0 && right%4!=0)) return 1;
        boxes[col>0]=z7_portrait_grid_tile(right,0,0,stock->w,73);
        return col>0 ? 2 : 1;
    }
    if (stock->h<=2 && stock->w>=118 && stock->w<=123) {
        int32_t col=(stock->x+stock->w/2)/120;
        if (col>=6 || stock->x<col*120-2 || stock->x>col*120+2) return 0;
        int32_t edge=y<=2 && y>=-2 ? 0 : y>=70 && y<=75 ? 1 : y>=143 && y<=148 ? 2 : -1;
        if (edge<0) return 0;
        if (edge>0) boxes[0]=z7_portrait_grid_tile((edge-1)*6+col,0,73-stock->h,120,stock->h);
        if (edge<2) boxes[edge>0]=z7_portrait_grid_tile(edge*6+col,0,0,120,stock->h);
        return edge==1 ? 2 : 1;
    }
    return 0;
}
#endif
