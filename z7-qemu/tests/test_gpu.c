/* SPDX-License-Identifier: GPL-2.0-or-later */
/* Tests actual production rasterizer: coordinate types, clearing, subsampled
 * chroma, separate alpha, descriptor bounds and aligned target height. */
#include "../qemu/nikon-z7-gpu.h"
#include <glib/gstdio.h>
static unsigned checks;
#define CHECK(c) do { checks++; if (!(c)) { fprintf(stderr,"FAIL line%d: %s\n",__LINE__,#c); return 1; } } while(0)
static uint32_t fbits(float f) { uint32_t v; memcpy(&v,&f,4); return v; }
static Z7GPUPath *rectangle(unsigned type, bool indirect, unsigned state) {
    Z7GPUPath *p = g_new0(Z7GPUPath,1); p->valid=true;
    p->segments=g_byte_array_new(); p->coordinates=g_byte_array_new();
    p->edges=g_array_new(false,false,sizeof(Z7GPUEdge));
    uint8_t seg[]={2,4,4,4,0}; int points[]={0,0,8,0,8,6,0,6};
    p->regs[3]=5|(indirect?0x10000000:0); p->regs[5]=8|(type<<30);
    p->regs[0x65]=state;
    p->regs[0x5c]=fbits(1); p->regs[0x5d]=fbits(10);
    if (!(state&0x100)) { p->regs[0x47]=p->regs[0x48]=fbits(4); }
    p->regs[0x41]=p->regs[0x45]=p->regs[0x49]=p->regs[0x5e]=fbits(1);
    g_byte_array_append(p->segments,seg,sizeof(seg));
    unsigned bytes=indirect && type<2?1U<<type:4;
    for(unsigned i=0;i<8;i++) { uint32_t v=type==3?fbits(points[i]):points[i]; g_byte_array_append(p->coordinates,(uint8_t*)&v,bytes); }
    z7_gpu_flatten(p); return p;
}
int main(void) {
    Z7GPU g={0};
    g_unsetenv("Z7_GPU_DRAW_DUMP_DIR"); g_unsetenv("Z7_GPU_DRAW_DUMP_GATE");
    /* Gate after boot without changing submitted registers or path bytes. */
    {
        Z7GPUPath *observed=rectangle(2,false,0x100);
        uint32_t regs[512]={0}, copy[512]={0}; regs[0x184]=8; memcpy(copy,regs,sizeof(regs));
        z7_gpu_capture_draw(&g,regs,observed,NULL,0,NULL,0); CHECK(g.draw_samples==0);
        char *dir=g_dir_make_tmp("z7-gpu-capture-XXXXXX",NULL); CHECK(dir!=NULL);
        char *gate=g_build_filename(dir,"armed",NULL);
        g_setenv("Z7_GPU_DRAW_DUMP_DIR",dir,true); g_setenv("Z7_GPU_DRAW_DUMP_GATE",gate,true);
        z7_gpu_capture_draw(&g,regs,observed,NULL,0,NULL,0); CHECK(g.draw_samples==0);
        CHECK(g_file_set_contents(gate,"1",1,NULL));
        z7_gpu_capture_draw(&g,regs,observed,NULL,0,NULL,0); CHECK(g.draw_samples==1);
        char *path=g_build_filename(dir,"0000-regs.bin",NULL), *data=NULL; gsize length=0;
        CHECK(g_file_get_contents(path,&data,&length,NULL)); CHECK(length==sizeof(regs));
        CHECK(!memcmp(data,regs,length) && !memcmp(copy,regs,sizeof(regs))); g_free(data);g_free(path);
        uint8_t tiny=0;
        z7_gpu_capture_draw(&g,regs,observed,&tiny,0x100001,NULL,0); CHECK(g.draw_samples==2);
        path=g_build_filename(dir,"0001-texture.bin",NULL);CHECK(!g_file_test(path,G_FILE_TEST_EXISTS));g_free(path);
        g_unlink(gate);z7_gpu_capture_draw(&g,regs,observed,NULL,0,NULL,0);CHECK(g.draw_samples==2);
        CHECK(g_file_set_contents(gate,"1",1,NULL));g.draw_samples=512;
        z7_gpu_capture_draw(&g,regs,observed,NULL,0,NULL,0);CHECK(g.draw_samples==512);
        const char *names[]={"regs","path-regs","segments","coordinates"};
        for(unsigned n=0;n<2;n++)for(unsigned j=0;j<G_N_ELEMENTS(names);j++) {
            path=g_strdup_printf("%s/%04u-%s.bin",dir,n,names[j]);g_unlink(path);g_free(path);
        }
        g_unlink(gate);CHECK(g_rmdir(dir)==0);g_free(gate);g_free(dir);z7_gpu_path_free(observed);
        g_unsetenv("Z7_GPU_DRAW_DUMP_DIR");g_unsetenv("Z7_GPU_DRAW_DUMP_GATE");g.draw_samples=0;
    }
    /* Traced stock 720x480 register packet: three repeated lines per axis.
     * Test the production LCD-grid helper, including native Off and bounds. */
    uint32_t grid[0x1624/4] = {0};
    grid[0x1600/4] = 120U << 16;
    grid[0x1604/4] = 180;
    grid[0x1608/4] = (480U << 16) | 720;
    grid[0x160c/4] = (2U << 16) | 2;
    grid[0x1610/4] = (180U << 16) | 120;
    grid[0x1614/4] = (2U << 16) | 2;
    grid[0x1618/4] = 0x01000000;
    CHECK(!z7_lcd_grid_hit(grid, 180, 200));
    grid[0x1620/4] = 1;
    for (unsigned i = 1; i <= 3; i++) {
        CHECK(z7_lcd_grid_hit(grid, 200, 120*i));
        CHECK(z7_lcd_grid_hit(grid, 180*i, 200));
    }
    CHECK(!z7_lcd_grid_hit(grid, 200, 119));
    CHECK(!z7_lcd_grid_hit(grid, 200, 122));
    CHECK(!z7_lcd_grid_hit(grid, 720, 120));
    CHECK(!z7_lcd_grid_hit(grid, 180, 480));
    CHECK(!z7_lcd_grid_hit(grid, 200, 480));
    /* Two internal lines create thirds; no third line or stock quarter. */
    grid[0x1600/4] = 160U << 16;
    grid[0x1604/4] = 240;
    grid[0x1610/4] = (240U << 16) | 160;
    grid[0x1614/4] = (1U << 16) | 1;
    CHECK(z7_lcd_grid_hit(grid, 200, 160));
    CHECK(z7_lcd_grid_hit(grid, 200, 320));
    CHECK(z7_lcd_grid_hit(grid, 240, 200));
    CHECK(z7_lcd_grid_hit(grid, 480, 200));
    CHECK(!z7_lcd_grid_hit(grid, 200, 120));
    CHECK(!z7_lcd_grid_hit(grid, 180, 200));
    CHECK(!z7_lcd_grid_hit(grid, 720, 200));
    grid[0x1610/4] = 0;
    CHECK(!z7_lcd_grid_hit(grid, 240, 200));
    grid[0x1610/4] = (240U << 16) | 160;
    grid[0x1618/4] = 0x03d8d8d8;
    CHECK(z7_lcd_grid_hit(grid, 240, 200));
    grid[0x1618/4] = 0x02000000;
    CHECK(!z7_lcd_grid_hit(grid, 240, 200));
    for(unsigned type=0;type<4;type++) {
        for(unsigned state=0x2100;state<=0x3100;state+=0x1000) {
            Z7GPUPath *p=rectangle(type,true,state);
            CHECK(p->valid && p->edges->len==4);
            Z7GPUEdge e=g_array_index(p->edges,Z7GPUEdge,1);
            CHECK(e.x0==8 && e.y0==0 && e.x1==8 && e.y1==6);
            z7_gpu_path_free(p);
        }
    }
    /* Captured negative-Y image-to-surface/texture matrices reflect rows;
     * two such draws compose to identity. A positive-Y control preserves rows.
     * Do not relabel a reflected vgDrawImage as an untransformed pixel copy.
     * Matrices are the reduced8x6 form of native720x480 packets0031/0032.
     */
    {
        Z7GPUPath *copy_path=rectangle(2,false,0x100);
        copy_path->regs[0x45]=fbits(-1);copy_path->regs[0x48]=fbits(6);
        g_array_set_size(copy_path->edges,0);z7_gpu_flatten(copy_path);CHECK(copy_path->valid);
        uint32_t copy_regs[512]={0};copy_regs[0x1a3]=(6<<16)|8;
        copy_regs[0xc0]=7<<16;copy_regs[0xc1]=5<<16;copy_regs[0x184]=2;
        copy_regs[0x152]=(8<<16)|6;copy_regs[0x10c]=0x3c0000;
        copy_regs[0x110]=0xbc5555;copy_regs[0x111]=copy_regs[0x114]=0x3f0000;
        uint8_t expected[8*6*4],reflected[8*6*4];
        for(unsigned y=0;y<6;y++)for(unsigned x=0;x<8;x++) {
            unsigned i=(y*8+x)*4;
            expected[i]=1+y*30;expected[i+1]=3+x*20;expected[i+2]=x+y*8;expected[i+3]=255;
        }
        memcpy(memory+0x3000,expected,sizeof(expected));
        for(unsigned y=0;y<6;y++)memcpy(reflected+y*32,expected+(5-y)*32,32);
        copy_regs[0x155]=0xa1003000;copy_regs[0x1a4]=0xa1001000;copy_regs[0x156]=0x100;
        CHECK(z7_gpu_draw(&g,copy_regs,copy_path));
        CHECK(!memcmp(memory+0x1000,reflected,sizeof(expected)));
        copy_regs[0x155]=0xa1001000;copy_regs[0x1a4]=0xa1002000;
        CHECK(z7_gpu_draw(&g,copy_regs,copy_path));
        CHECK(!memcmp(memory+0x2000,expected,sizeof(expected)));
        copy_regs[0x155]=0xa1003000;copy_regs[0x110]=0x3c5555;copy_regs[0x111]=0;
        CHECK(z7_gpu_draw(&g,copy_regs,copy_path));
        CHECK(!memcmp(memory+0x2000,expected,sizeof(expected)));
        copy_regs[0x110]=0xbc5555;copy_regs[0x111]=0x3f0000;
        copy_regs[0x156]=0x18;copy_regs[0x155]=0xa1003000;
        copy_regs[0x184]=14;copy_regs[0x185]=0xffffffff;
        for(unsigned y=0;y<6;y++)for(unsigned x=0;x<8;x++) {
            unsigned i=y*8+x;memory[0x3000+i]=1+i;
            memcpy(expected+i*4,(uint8_t[]){255,255,255,1+i},4);
        }
        for(unsigned y=0;y<6;y++)memcpy(reflected+y*32,expected+(5-y)*32,32);
        CHECK(z7_gpu_draw(&g,copy_regs,copy_path));
        CHECK(!memcmp(memory+0x2000,reflected,sizeof(expected)));
        for(unsigned format=0x105;format<=0x107;format++) {
            copy_regs[0x156]=format;copy_regs[0x184]=2;copy_regs[0x15a]=0xa1004000;
            memset(memory+0x4000,format==0x105?128:255,48);
            for(unsigned y=0;y<6;y++)for(unsigned x=0;x<8;x++) {
                unsigned i=y*8+x;uint8_t luma=16+y*24,gray=(5-y)*28;
                if(format==0x105)memory[0x3000+i]=luma;
                else if(!(x&1))memcpy(memory+0x3000+i*2,(uint8_t[]){luma,luma,128,128},4);
                memcpy(expected+i*4,(uint8_t[]){gray,gray,gray,255},4);
            }
            CHECK(z7_gpu_draw(&g,copy_regs,copy_path));
            CHECK(!memcmp(memory+0x2000,expected,sizeof(expected)));
        }
        z7_gpu_path_free(copy_path);
    }
    /* Registration control from the ordinary native HUD: a window at low
     * RGBA rows is converted to the high LCD rows by the captured negative-Y
     * texture matrix. A global sampler reversal must not move that window.
     */
    {
        Z7GPUPath *window=rectangle(2,false,0x100);
        uint32_t draw[512]={0};draw[0x1a3]=(6<<16)|8;
        draw[0xc0]=draw[0xc1]=1<<16;draw[0x184]=8;
        draw[0x1a4]=0xa1001000;draw[0x185]=0xffffffff;
        memset(memory+0x1000,0,192);CHECK(z7_gpu_draw(&g,draw,window));
        draw[0x184]=2;draw[0xc0]=7<<16;draw[0xc1]=5<<16;
        draw[0x1a4]=0xa1002000;draw[0x1a2]=0x107;draw[0x1b5]=0xa1002060;
        draw[0x152]=(8<<16)|6;draw[0x155]=0xa1001000;draw[0x156]=0x100;
        draw[0x10c]=0x3c0000;draw[0x110]=0xbc5555;
        draw[0x111]=draw[0x114]=0x3f0000;
        CHECK(z7_gpu_draw(&g,draw,window));
        uint8_t alpha[48]={0};alpha[32]=alpha[33]=alpha[40]=alpha[41]=255;
        CHECK(!memcmp(alpha,memory+0x2060,sizeof(alpha)));
        z7_gpu_path_free(window);
    }
    /* GUI-only preview converts lower-left surface coordinates to top rows;
     * it must not update the console while native LCD scanout owns it. */
    {
        g.console=&test_console;qemu_console_resize(g.console,720,480);
        g.present_address=0xa1000000;g.lcd_scanout=false;
        memset(memory,0,720*480*4);
        memcpy(memory,(uint8_t[]){255,0,0,255},4);
        memcpy(memory+479*720*4,(uint8_t[]){0,0,255,255},4);
        z7_gpu_present(&g);
        CHECK(ldl_le_p(test_console.surface.data)==0x0000ff);
        CHECK(ldl_le_p(test_console.surface.data+479*720*4)==0xff0000);
        g.lcd_scanout=true;stl_p(test_console.surface.data,0x123456);
        z7_gpu_present(&g);CHECK(ldl_le_p(test_console.surface.data)==0x123456);
    }
    Z7GPUPath *p=rectangle(2,false,0x100);
    uint32_t r[512]={0}; r[0x1a3]=(8<<16)|8; r[0xc0]=7<<16; r[0xc1]=7<<16;
    r[0x184]=8; r[0x1a4]=0xa1001000; r[0x185]=0xffffffff;
    for(unsigned format=0x105;format<=0x107;format++) {
        for(unsigned a4=0;a4<=(format==0x107);a4++) {
            unsigned bpp=format==0x105?1:2, n=48*bpp, n2=a4?24:48;
            memset(memory,0xa5,sizeof(memory));
            r[0x1a2]=format|(a4<<24); r[0x1b5]=r[0x1a4]+n;
            /* Native visible y=2..8 maps to six stored rows, like6..688
             * maps to682. Packed106 has no second-plane height bound. */
            for(unsigned j=0;j<p->edges->len;j++) {
                Z7GPUEdge *e=&g_array_index(p->edges,Z7GPUEdge,j);
                e->y0=e->uy0+(format==0x106?0:2);
                e->y1=e->uy1+(format==0x106?0:2);
            }
            r[0x185]=0xffffffff;
            CHECK(z7_gpu_draw(&g,r,p));
            uint8_t *a=memory+0x1000,*b=a+n, pixel[4];
            for(unsigned i=0;i<48;i++) {
                z7_gpu_pixel_read(a,b,format,a4,i,pixel);
                CHECK(pixel[0]>=254 && pixel[1]>=254 && pixel[2]>=254 && pixel[3]==255);
            }
            CHECK(a[-1]==0xa5);
            CHECK((format==0x106 ? a[8*8*2] : b[n2])==0xa5);
            r[0x185]=0;
            CHECK(z7_gpu_draw(&g,r,p));
            z7_gpu_pixel_read(a,b,format,a4,0,pixel);
            CHECK(pixel[0]==0 && pixel[1]==0 && pixel[2]==0);
            CHECK(pixel[3]==(format==0x107?0:255));
            if(format!=0x106) {
                uint8_t saved[256]; memcpy(saved,a,sizeof(saved));
                r[0x1b5]=0;
                CHECK(!z7_gpu_draw(&g,r,p));
                CHECK(!memcmp(saved,a,sizeof(saved)));
            }
        }
    }
    /* One final chroma average for two red pixels, no alternating tint. */
    r[0x1a2]=0x105; r[0x1b5]=r[0x1a4]+48; r[0x185]=0xff0000ff;
    CHECK(z7_gpu_draw(&g,r,p));
    CHECK(memory[0x1000]==82 && memory[0x1001]==82);
    CHECK(memory[0x1030]==90 && memory[0x1031]==240);
    /* Source-over transparent paint preserves the destination exactly. */
    r[0x1a2]=0; r[0x185]=0; r[0x1a0]=0x00010000;
    for(unsigned j=0;j<p->edges->len;j++) {
        Z7GPUEdge *e=&g_array_index(p->edges,Z7GPUEdge,j); e->y0=e->uy0; e->y1=e->uy1;
    }
    memset(memory+0x1000,0x80,256); uint8_t saved[256]; memcpy(saved,memory+0x1000,256);
    CHECK(z7_gpu_draw(&g,r,p)); CHECK(!memcmp(saved,memory+0x1000,256));
    r[0x1a0]=0; CHECK(z7_gpu_draw(&g,r,p));
    CHECK(!memcmp(memory+0x1000,(uint8_t[192]){0},192));
    /* Zero-alpha SRC_OVER is a storage no-op on YUV too. A lossy RGB
     * round trip must not modify either luma, shared chroma or alpha. */
    for(unsigned format=0x105;format<=0x107;format++) {
        for(unsigned a4=0;a4<=(format==0x107);a4++) {
            r[0x1a2]=format|(a4<<24); r[0x1a0]=0x00010000;
            r[0x1b5]=r[0x1a4]+64*(format==0x105?1:2);
            r[0x185]=0x00112233;
            uint8_t original[512];
            for(unsigned j=0;j<sizeof(original);j++) { original[j]=(j*37+29)&255; }
            unsigned modes[]={8,2,14};
            for(unsigned m=0;m<G_N_ELEMENTS(modes);m++) {
                r[0x184]=modes[m];
                r[0x152]=(1<<16)|1; r[0x155]=0xa1003000; r[0x156]=0;
                r[0x10c]=r[0x110]=r[0x114]=0x3f0000;
                memcpy(memory+0x3000,(uint8_t[]){27,29,31,modes[m]==14?255:0},4);
                memcpy(memory+0x1000,original,sizeof(original));
                CHECK(z7_gpu_draw(&g,r,p));
                CHECK(!memcmp(memory+0x1000,original,sizeof(original)));
            }
        }
    }
    z7_gpu_path_free(p);
    /* A black stroke remains outside a subsequent white fill. Closed paths
     * have an empty center; miter corners must cover the outside corner. */
    p=rectangle(2,false,0x2000);
    CHECK(p->valid && p->edges->len>4);
    memset(r,0,sizeof(r)); r[0x1a3]=(16<<16)|16;
    r[0xc0]=r[0xc1]=15<<16; r[0x1a4]=0xa1001000; r[0x184]=8;
    r[0x185]=0xff000000; r[0x1a0]=0x00010000;
    memset(memory+0x1000,0,16*16*4);
    CHECK(z7_gpu_draw(&g,r,p));
    #define PIX(x,y,c) memory[0x1000+((y)*16+(x))*4+(c)]
    CHECK(PIX(3,6,3)==255 && PIX(3,6,0)==0);
    CHECK(PIX(8,7,3)==0);
    CHECK(PIX(3,3,3)==255);
    CHECK(PIX(2,2,3)==0);
    Z7GPUPath *fill=rectangle(2,false,0x2100);
    for(unsigned j=0;j<fill->edges->len;j++) {
        Z7GPUEdge *e=&g_array_index(fill->edges,Z7GPUEdge,j);
        e->x0+=4;e->x1+=4;e->y0+=4;e->y1+=4;
    }
    r[0x185]=0xffffffff;
    CHECK(z7_gpu_draw(&g,r,fill));
    CHECK(PIX(8,7,0)==255 && PIX(8,7,3)==255);
    CHECK(PIX(3,6,0)==0 && PIX(3,6,3)==255);
    z7_gpu_path_free(fill);
    /* Open L: no invented closing diagonal, butt/round/square caps. */
    g_byte_array_set_size(p->segments,3); p->regs[3]=3; p->regs[5]=6|(2U<<30);
    for(unsigned cap=0;cap<3;cap++) {
        g_array_set_size(p->edges,0);p->contour=0;p->regs[0x65]=0x2000|(cap<<16);
        z7_gpu_flatten(p); CHECK(p->valid);
        memset(memory+0x1000,0,16*16*4);r[0x185]=0xff000000;
        CHECK(z7_gpu_draw(&g,r,p));
        CHECK(PIX(8,7,3)==0);
        CHECK(cap==0?PIX(3,4,3)==0:PIX(3,4,3)>0);
        if(cap==2) { CHECK(PIX(3,3,3)==255); }
    }
    /* Width is transformed with user space (2x horizontal, 1x vertical). */
    g_array_set_size(p->edges,0);p->contour=0;p->regs[0x65]=0x2000;
    p->regs[0x41]=fbits(2);p->regs[0x5c]=fbits(.5);
    z7_gpu_flatten(p);CHECK(p->valid);
    double minx=1e9,maxx=-1e9,miny=1e9;
    for(unsigned j=0;j<p->edges->len;j++) {
        Z7GPUEdge e=g_array_index(p->edges,Z7GPUEdge,j);
        minx=MIN(minx,MIN(e.x0,e.x1));maxx=MAX(maxx,MAX(e.x0,e.x1));miny=MIN(miny,MIN(e.y0,e.y1));
    }
    CHECK(fabs(minx-4)<1e-6 && fabs(maxx-21)<1e-6 && fabs(miny-3.5)<1e-6);
    g_array_set_size(p->edges,0);p->regs[0x5a]=1;
    z7_gpu_flatten(p);CHECK(!p->valid);
    z7_gpu_path_free(p);
    printf("PASS %u synthetic renderer checks\n",checks); return 0;
}
