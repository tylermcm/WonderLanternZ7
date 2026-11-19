/* SPDX-License-Identifier: MIT; adapted from JKWTCN/z7ii-extensions. */
ENTRY(z7_main)
SECTIONS {
    . = 0;
    .text : { *(.text .text.*) }
    .rodata : { *(.rodata .rodata.*) }
    .data : { *(.data .data.*) *(.got .got.*) }
    . = ALIGN(64);
    __image_end = .;
    .bss (NOLOAD) : { *(.bss .bss.*) *(COMMON) }
    . = ALIGN(4);
    __memory_end = .;
    /DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) }
}
