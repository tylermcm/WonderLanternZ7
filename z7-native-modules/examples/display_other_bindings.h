/* SPDX-License-Identifier: MIT. Independent original-Z7 ordinary status map.
 * Pinned JKWTCN custom-DISP group concept; original-Z7 bindings and warning
 * selectors independently inspected. White balance, battery, AF frame,
 * flash-ready and temperature controls remain native and are not in this map.
 */
#define READOUT_COUNT 24u
static const uint32_t readout_descriptors[READOUT_COUNT] = {
    0xa1824174u,0xa1824264u,0xa1824654u,0xa1823cf4u,0xa18284dcu,0xa1823a24u,
    0xa1823ab4u,0xa1823d84u,0xa1823e74u,0xa1823f04u,0xa1823f94u,0xa1824414u,
    0xa18244d4u,0xa1824954u,0xa18249e4u,0xa1826534u,0xa18265c4u,0xa1827614u,
    0xa182796cu,0xa1827b1cu,0xa1827f0cu,0xa18280ecu,0xa182844cu,0xa18286bcu
};
static const uint8_t readout_widgets[READOUT_COUNT] = {
    10,11,15,5,51,2,3,6,7,8,9,13,14,16,17,26,27,34,38,41,44,46,50,53
};
/* Native format2 shares capacity/warnings,3 flash,4 metering. Every nonzero
 * format retains the complete native group; 255 has no such selector.
 */
static const uint8_t readout_formats[READOUT_COUNT] = {
    0,1,5,255,255,255,255,255,4,255,255,255,255,2,3,255,255,255,255,255,255,255,255,255
};
static const uint8_t readout_bits[READOUT_COUNT] = {
    Z7_INFO_SHUTTER,Z7_INFO_APERTURE,Z7_INFO_ISO,Z7_INFO_SHOOTING,Z7_INFO_RELEASE,Z7_INFO_FOCUS,
    Z7_INFO_OTHER,Z7_INFO_OTHER,Z7_INFO_OTHER,Z7_INFO_OTHER,Z7_INFO_OTHER,Z7_INFO_OTHER,
    Z7_INFO_OTHER,Z7_INFO_OTHER,Z7_INFO_OTHER,Z7_INFO_OTHER,Z7_INFO_OTHER,Z7_INFO_OTHER,
    Z7_INFO_OTHER,Z7_INFO_OTHER,Z7_INFO_OTHER,Z7_INFO_OTHER,Z7_INFO_OTHER,Z7_INFO_OTHER
};
static const uint32_t readout_updaters[READOUT_COUNT] = {
    0x102f378du,0x102f3951u,0x102f3b5bu,0x102f346fu,0x102f6d01u,0x102f31a7u,
    0x102f3221u,0x102f354fu,0x102f35e3u,0x102f3617u,0x102f3637u,0x102f3abdu,
    0x102f3addu,0x102f3f8bu,0x102f3fdfu,0x102f4f9du,0x102f501bu,0x102f5685u,
    0x102f66cdu,0x102f6817u,0x102f5911u,0x102f6a7fu,0x102f6bf7u,0x102f6d75u
};
