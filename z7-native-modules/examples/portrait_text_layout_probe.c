/* SPDX-License-Identifier: MIT. Caller-admitted text layout diagnostic. */
#include "module.h"
#include "../plugins/portrait_text_layout.h"
uint32_t z7_portrait_text_probe(volatile uint32_t *message,const struct z7_portrait_text_transform *transform)
{ return z7_portrait_text_draw_planned(message,transform,0); }
uint32_t z7_portrait_text_page_probe(volatile uint32_t *message,uint32_t page,uint32_t orientation)
{ return z7_portrait_text_page_draw(message,page,orientation,0); }
uint32_t z7_portrait_page_draw_probe(volatile uint32_t *message,uint32_t page,uint32_t orientation)
{ return z7_portrait_page_message(message,page,orientation); }
void z7_portrait_bands_before_probe(struct z7_portrait_bands *bands,volatile uint32_t *message,uint32_t page,uint32_t orientation)
{ z7_portrait_bands_before(bands,message,page,orientation); }
uint32_t z7_portrait_symbol_begin_probe(uint32_t context,const struct z7_portrait_symbol_config *config,struct z7_portrait_symbol_scope *scope)
{ return z7_portrait_symbol_begin(context,config,scope); }
void z7_portrait_symbol_end_probe(struct z7_portrait_symbol_scope *scope)
{ z7_portrait_symbol_end(scope); }
uint32_t z7_portrait_symbol_draw_probe(const uint32_t *glyph,uint32_t descriptor)
{ return z7_portrait_symbol_draw(glyph,0,0,descriptor); }
uint32_t z7_main(const struct z7_module_api *api)
{ return !api || api->abi!=Z7_MODULE_ABI || api->target!=Z7_MODULE_TARGET || api->size<12; }
