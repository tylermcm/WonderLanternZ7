# 尼康 Z7 滤镜/胶片模拟移植可行性分析

> 结论先行：**Z7 C 3.80 固件内已经存在 20 种创意优化校准（Creative Picture Control）的完整名称表、枚举映射与分类服务层代码**，且第二轮逆向进一步确认：**创意基础枚举值（0x0801-0x0814）就写在 Z7 自己的固件映射表里，自定义优化校准文件解析器明确接受创意参数记录族（0x800 族）**（本文件第 5 章实逆向证据）。「把滤镜/胶片模拟移植进 Z7 固件」最现实的路线不是跨机型搬运代码，而是**启用本机休眠子系统**（m900 先例同模式），其中**路线 A（构造 NCP/PICCON 文件从卡加载）已具备全部文件层证据，可直接进入造文件实测**；Rich Tone 系列与云创配方则因 EXPEED 7 依赖在当前阶段不可行。全部结论均基于离线逆向与公开资料，**未经真机实测**。

分析日期：2026-10-15。分析对象：`Z_7_0380.bin`（SHA-256 `07cf1951...441a2`，已校验为原厂镜像）。
修订记录：2026-10-15 第二轮逆向追加 §5.6-§5.8（基础枚举提取、文件解析层、UI 参数 ID），并**纠正首轮「零 NP3 痕迹」的误判**（首轮字符串扫描 minlen=5 漏掉 3 字符 magic，详见 §5.5/§5.7）。

---

## 1. 术语与背景

- **优化校准（Picture Control, PC）**：尼康的色彩/色调渲染方案。标准优化校准（Standard/Neutral/Vivid/Monochrome/Portrait/Landscape/Flat）内置于所有 Z 机型。
- **创意优化校准（Creative Picture Control，共 20 种）**：滤镜/胶片模拟类效果，效果强度可调，2019 年 11 月随 Z50（EXPEED 6）首次出现，此后 Z5/Z6II/Z7II/D780（均 EXPEED 6）全部具备。**初代 Z6/Z7 是同代 EXPEED 6 机型中唯一从未官方获得该功能的机型**——这是产品分层而非处理器代差的直接疑点，也是本次逆向的出发点。
- **NCP**：自定义优化校准文件（老格式），Z7 可经「管理优化校准」菜单从存储卡 `NIKON\CUSTOMPC\` 目录加载。
- **NP3（Flexible Color Picture Control）**：EXPEED 7 世代新格式（色彩混合器/三级调色/257 点曲线），配合尼康云创（Nikon Imaging Cloud）配方分发，仅 Zf/Z8/Z9/Z6III/Z5II/Z50II/ZR 支持。
- **Rich Tone Monochrome/Portrait**：EXPEED 7 机型固件新增的重色调系列优化校准。

## 2. 本仓库可复用基础设施

| 资产 | 位置 | 对滤镜移植的作用 |
|---|---|---|
| 容器 XOR 解码 + 模块提取 | `src/z30_extensions/container.py` | 取得 EG/MAIN 模块做逆向（本次已复用） |
| 地址映射（BASE=0x10020000、SCATTER） | `src/z30_extensions/platform/z7_380.py` | 文件偏移↔运行地址换算 |
| 等长校验补丁 + 尾部追加 + CRC 重建 | `patch.py` / `plan.py` | 最终打补丁的承载框架 |
| 设置菜单注入（page table 空闲页/空闲控件扫描） | `features/shutter_sound.py` | 若需为创意优化校准加 UI 入口可复用 |
| 属性系统地址（描述符表 0x114F774C、存储表 0x114EB97C） | `tools/native_runtime.py` | 定位 PC 选择状态对应的属性键 |
| Keystone/Thumb 发射器 + Unicorn 离线验证链 | `assembly.py` / `tools/verify_*.py` | 补丁逻辑先离线仿真再考虑刷机 |

边界声明：`docs/z7-differences.md` 中「不修改 ISP/RAW/CMOS 参数」是此前三功能的范围声明；本次分析为只读逆向，未越过该边界，但后续**启用创意优化校准必然触碰图像管线**，需按新任务重新评估风险。

## 3. 先例开源项目借鉴矩阵

已克隆至 `reference/`（gitignore，不入库）并研读：

| 项目 | 平台 | 可借鉴资产 | 对本项目的映射 |
|---|---|---|---|
| [horshack-dpreview/NikonPictureControlsDev](https://github.com/horshack-dpreview/NikonPictureControlsDev) | 尼康 | NCP 结构逆向：记录 1 中偏移 0x24 为**基础曲线枚举**（u16 BE，基础 TRC 内嵌于相机固件、NCP 仅引用枚举）；自定义曲线=257 点 1D LUT（输出 0–32767）；TRC→sRGB gamma→PC 参数的管线顺序 | 路线 A（文件级移植）的格式基础；其自制 NCP（Linear/ISOless 等）即「不改固件、只改文件」思路的实证 |
| [simeonpilgrim/nikon-firmware-tools `dumpncp.pl`](https://github.com/simeonpilgrim/nikon-firmware-tools/blob/master/nfiles/dumpncp.pl) | 尼康（DSR 时代延续） | NCP 为 TLV 记录格式（magic `NCP\0`，记录=ID+长度+体）；遗留基础枚举表：STANDARD=0x0001、VIVID=0x00C3、NEUTRAL=0x03C2、PORTRAIT=0x0486、LANDSCAPE=0x04C7、MONOCHROME=0x064D（**FLAT 与 20 创意枚举值不在其中，2014 年后新增，需另行提取**）；未知记录按长度跳过=向前兼容 | 解析/构造 NCP 的参考实现；「创意枚举数值」列为后续任务 |
| [ssssota/nikon-flexible-color-picture-control](https://github.com/ssssota/nikon-flexible-color-picture-control) | 尼康 | NP3 字段级布局（MIT、零依赖 TypeScript）：名称 0x18、清晰度 0x5C、对比度 0x110、饱和度 0x142、8 色色彩混合器 0x14C-0x161、三级调色 0x170-0x182、257×u16 曲线 0x1CC | 若未来做 NP3 兼容层或解析测试向量可直接移植其常量表 |
| [shouryan01/Nikon-Recipes](https://github.com/shouryan01/Nikon-Recipes) | 尼康 | 474 个配方文件；实测确认**绝大多数为 NP3（版本串 `0310`）**，即现代滤镜生态已全面 EXPEED 7 化；SD 卡加载路径 `NIKON\CUSTOMPC\` 与 Z7 固件内 `B:\NIKON\CUSTOMPC\` 字符串一致 | 路线 A 的测试素材库；同时印证「NP3 上老机」是该生态的核心痛点 |
| [fujihack/patcher](https://github.com/fujihack/patcher)（另见 [fujihack.org](https://fujihack.org)、[wiki](https://wiki.fujihack.org)） | 富士（其他品牌先例） | 固件解析→载荷导出反汇编→暴力搜索替换→keystone.js 汇编补丁→CI 自动校验和，全链路工具化；「尽可能多的防错检查」原则 | 与本仓库 Keystone Python + 等长校验思路同构，验证了方法论；其 CI 自动化补丁+校验流程值得后续引入 |
| [Magic Lantern](https://www.magiclantern.fm)（[reticulatedpines 镜像](https://github.com/reticulatedpines/magiclantern_simplified)） | 佳能（其他品牌先例） | 运行时 hook/模块化加载架构——业界最成熟的相机固件扩展范式 | Z 系列无运行时加载入口（静态补丁模式），借鉴仅限 hook 设计与功能开关组织方式 |
| [Wonder-Lantern](https://github.com/vic2349/Wonder-Lantern) | 尼康 Z6 | 自定义快门声音（本仓库 shutter-sound 的参考，已消化为既有功能；克隆仓库现为空壳） | 证明 Z6（Z7 姐妹机、同代固件）静态补丁可行，间接支撑 Z7 图像管线外/内补丁的工程可信度 |
| [RawTherapee 社区：Recreating Nikon Picture Control](https://discuss.pixls.us/t/recreating-nikon-picture-control/55192) | 跨平台 | 开源复刻尼康 PC 渲染管线的社区实践：确认 PC 由「固件内嵌基础曲线 + 参数微调」构成、大半为数据驱动 | 支撑「创意优化校准=固件内数据表+引擎，跨同代固件可搬」的判断 |

**借鉴结论**：没有任何公开项目实现过「跨机型整块移植滤镜引擎到固件」；社区路线分两支——文件级（horshack：改 NCP 内容）与固件级（本仓库/Wonder-Lantern：等长补丁+尾部追加）。本仓库的差异化机会在于第三条：**启用固件内已存在的休眠子系统**。

## 4. 官方功能矩阵（滤镜家族）

| 机型（上市） | 处理器 | 20 创意优化校准 | Rich Tone 系列 | NP3/云创配方 | 自定义 NCP 卡加载 |
|---|---|---|---|---|---|
| Z7/Z6（2018） | EXPEED 6 | ✗（至今未获得） | ✗ | ✗ | ✓ |
| Z50（2019-11） | EXPEED 6 | ✓（首发） | ✗ | ✗ | ✓ |
| Z5（2020-07） | EXPEED 6 | ✓ | ✗ | ✗ | ✓ |
| Z6II/Z7II（2020-10） | 双 EXPEED 6 | ✓ | ✗ | ✗ | ✓ |
| D780（2020） | EXPEED 6 | ✓ | ✗ | ✗ | ✓ |
| Zf（2023） | EXPEED 7 | ✓ | + Rich Tone Monochrome | ✓ | ✓ |
| Z8/Z9 | EXPEED 7 | ✓ | + Rich Tone Mono/Portrait | ✓ | ✓ |
| Z6III（2024）/Z50II（2024）/Z5II/ZR | EXPEED 7 | ✓ | ✓ | ✓（云创主打） | ✓ |

20 种创意优化校准官方名单（Nikon USA 教程）：**Dream, Morning, Pop, Sunday, Somber, Dramatic, Silence, Bleached, Melancholic, Pure, Denim, Toy, Sepia, Blue, Red, Pink**（彩色 16）+ **Charcoal, Graphite, Binary, Carbon**（单色 4）。

社区共识（[DPReview 2024-09 讨论](https://www.dpreview.com/forums/threads/picture-controls.4775763)、[Reddit](https://www.reddit.com/r/Nikon/comments/1t41ojn/i_downloaded_every_nikon_creative_picture_control)）：EXPEED 7 新创意控制（NP3 类）无法在老机身加载，普遍归因「处理器限制」——**该说法未经固件级验证**，本次逆向证明至少在名称/枚举/服务层，Z7（EXPEED 6）固件已内置同代创意优化校准的完整骨架。

## 5. Z7 C 3.80 固件实逆向发现（核心证据）

方法：`container.py` 解码容器 → 提取 `eg1610_038000.bi`（33,052,090 字节）→ ASCII/UTF-16 全量字符串提取（99,807 + 88,375 条）→ 关键词定位 → Capstone Thumb 反汇编 → 绝对指针/BL 交叉引用扫描。工作产物在 `analysis/`（gitignore）：`eg1610_038000.bi`、`strings_all.txt`。

### 5.1 容器四模块布局

| 模块名 | 大小 | 推测职责 |
|---|---|---|
| `ex1610_037000.bi` | 524,290 B | EXPEED 协处理器/ISP 相关（待逆向） |
| `_tpj01_v140.bin` | 57,346 B | 未知小模块（待逆向） |
| `eg1610_038000.bi` | 33,052,090 B | **MAIN（本仓库补丁对象，创意优化校准服务层在此）** |
| `vr1610_010200.bi` | 838,664 B | VR/防抖固件 |

### 5.2 名称表与匹配函数（创意优化校准存在性实证）

VA = 文件偏移 + 0x10020000（MAIN 装载基址）。

**名称表 `0x10325678-0x10325B4A`**（null 结尾、4 字节对齐，前面紧邻白平衡/闪光模式名称表，属同一「枚举→名称」字符串包）：

```
0x10325678  STANDARD    NEUTRAL    VIVID     MONOCHROME
0x1032569C  LANDSCAPE   PORTRAIT   FLAT                    ← Z7 官方 7 种
0x103256C0  DREAM       MORNING    POP       SUNDAY
0x103256E4  SOMBER      DRAMA(TIC) SILENCE                ← 创意·彩色簇 1
            …（间隔一段代码，见下）…
0x10325AE0  BLEACH      MELANCHOLIC  PURE    DENIM  TOY
0x10325B08  SEPIA       BLUE       RED       PINK         ← 创意·彩色簇 2
0x10325B24  CHARCOAL    GRAPHITE   BINARY    CARBON       ← 创意·单色簇
0x10325B4C  NEUTRAL     MONOCHROME  FLAT                   ← 兜底/单色基线
```

与第 4 章官方 20 种名单**逐字吻合**。

**名称→枚举匹配函数 `~0x103256E8-0x10325807`**：strcmp 链（`blx 0x10239278` 为比较函数）逐个以 `adr` 取上表字符串比较，命中返回枚举 ID。已核对 ADR 落点：`#0x3E8`→BLEACH、`#0x3E4`→MELANCHOLIC/PURE、`#0x3E0`→DENIM、`#0x3DC`→TOY、`#0x3D4`→SEPIA。返回值覆盖 1–0x1B（含全部 20 创意 ID 段），链尾未匹配返回 0x26（38）——**优化校准枚举空间至少 0–38**（约 = 1 Auto + 7 标准 + 20 创意 + 9 自定义槽 C-1..C-9 + 余量），创意优化校准被完整编入 Z7 的枚举体系。

**分类服务函数簇 `0x10325808-0x103259BC+`**：约 12 个小函数，读 `状态基址+0x1000+{0x4D0,0x4E8,0x4EA,0x4F6,0x538,0x53A,0x920,0x925-0x927,0x92E}` 等字段并归一化为小枚举；其中 `0x10325808` 将当前优化校准名（状态基址+0x150E 处缓冲）与 NEUTRAL/MONOCHROME/FLAT 比较（ADR 落点 0x10325B4C/0x10325B54/0x10325B60 已核对）。这是 `SettingDataService_PictureControl.c` 风格的服务层。

### 5.3 其他关键锚点

| 锚点 | VA | 含义 |
|---|---|---|
| `PictureControlService.c` | 0x101EEBCC | PC 服务模块断言文件名（模块存在证据） |
| `SettingDataService_PictureControl.c` | 0x101B24DC | 设置数据服务 PC 模块名 |
| `PictureControlSe...`（截断串） | 0x11F991D0 | SCATTER 初始化数据区内又一处 PC 服务串 |
| `B:\NIKON\CUSTOMPC\` ×2 | 0x101F10F8 / 0x101F1544 | 卡加载/保存自定义优化校准的工作路径（与 Nikon-Recipes 的 SD 布局一致） |
| `Creative Picture Control`（ASCII） | 0x104D0628 | 独立于菜单资源的英文串，嵌在代码区（EXIF/元数据标签或调试标签，待逆向） |
| UTF-16 菜单资源 | 0x10D4AB40-0x10E1A09A 等 | Manage Picture Control / Set Picture Control 全语言菜单（Z7 官方功能） |

### 5.4 调用方（BL 交叉引用，指向 0x10325400-0x10325D00 的 30 处）

- `0x102D2310-0x102D24B8`：**15 处密集调用**——重度消费方，疑似 EXIF/元数据写入或 PC 状态聚合模块；
- `0x102D4490-0x102D46FA`：5 处；
- `0x10308168/0x10308172`：2 处；
- `0x10221CDE → 0x10325422`（白平衡名称区）、`0x10325D08/0x10325D10`、`0x1072488C`（疑误报）。

### 5.5 负面信号（不可行性证据，含一处纠正）

- **纠正**：首轮报告称「全镜像零 `NP3` 命中」有误——首轮 ASCII 字符串扫描最小长度取 5，漏掉了 3 字符 magic。第二轮按字节精确搜索证实 **`NP3\0`（2 处）、`NP2\0`（1 处）magic 存在于自定义优化校准文件模块内**（§5.7）；`NPP`/`EXPEED` 仍为零命中；
- 无 `Rich Tone` 字符串 → Rich Tone 系列引擎/数据不在 Z7 固件；
- 名称表与匹配函数之上，**尚未定位**到：① 创意效果渲染引擎本体（色调/色相变换数学与参数表，MAIN 还是 `ex1610` 协处理器模块）；② 「设定优化校准」菜单列表的机型差异门控（为何 Z7 不列出这 20 项）。此二者是休眠启用路线的最终判据，仍列第 8 章任务清单。

### 5.6 基础枚举映射表（第二轮：创意枚举值直接从 Z7 固件提取成功）

已知基础枚举常量（dumpncp.pl 遗留表：STANDARD=0x0001、VIVID=0x00C3、NEUTRAL=0x03C2、PORTRAIT=0x0486、LANDSCAPE=0x04C7、MONOCHROME=0x064D）在 MAIN 静态数据 **0x10654E90-0x10654F68（表 A）与 0x10654F6C-0x10655044（表 B）** 两处以 `{u32 内部 ID, u32 基础枚举}` 对的形式共现。破译结果：

| 优化校准 | 基础枚举 | 内部 ID（表 A / 表 B） |
|---|---|---|
| STANDARD | 0x0001 | 0x1423 / 0x14E2 |
| NEUTRAL | 0x03C2 | 0x1423→? / 0x14E2 |
| VIVID | 0x00C3 | 0x1424 / 0x14E3 |
| MONOCHROME | 0x064D | 0x1425 / 0x14E4 |
| PORTRAIT | 0x0486 | 0x1428 / 0x14E7 |
| LANDSCAPE | 0x04C7 | 0x1427 / 0x14E6 |
| FLAT（推定，遗留表未收录） | 0x028E | 0x1429 / 0x14CD |
| **20 种创意优化校准** | **0x0801-0x0814（连续 20 值）** | 0x13FC-0x1420 连续段 / 0x14CE-0x14E0 连续段 |
| 兜底/未指定（推定） | 0x02CF | 0x1422 / — |

创意 20 枚举与名称表顺序一一对应：**Dream=0x0801、Morning=0x0802、Pop=0x0803、Sunday=0x0804、Somber=0x0805、Dramatic=0x0806、Silence=0x0807、Bleached=0x0808、Melancholic=0x0809、Pure=0x080A、Denim=0x080B、Toy=0x080C、Sepia=0x080D、Blue=0x080E、Red=0x080F、Pink=0x0810、Charcoal=0x0811、Graphite=0x0812、Binary=0x0813、Carbon=0x0814**。

两张表的引用者已定位：字面量 0x10356EC4（→表 B 尾）、0x103594F0（→表 A 首），即 0x10356xxx-0x10359xxx 的优化校准服务/UI 模块。**第 8 章原任务 3（提取创意枚举数值）就此完成，无需供体固件。**

另有四处升序「合法内部 ID 清单」包含创意族整段 **0x0800-0x0813（20 项）**：0x11549E3C、0x11552BF4、0x11553774（ROM 静态数据）与 0x11F844F4（SCATTER 初始化数据源区内、运行时驻留 RAM）——同清单还含 0x0700-0x0710（17 项，疑标准+自定义族）与 0x0D00-0x0D10（17 项，数量与白平衡预置吻合），佐证这是分域合法 ID 校验/枚举表。

### 5.7 自定义优化校准文件解析层（第二轮：路线 A 的文件层证据）

`B:\NIKON\CUSTOMPC\` 所在的 0x101F0xxx 模块为自定义优化校准文件栈，含 **NCP、NP3、NP2、"0100"（版本串）、"PICCON"（PICture CONtrol 格式名）全部 magic**：

- **`NCP\0` magic（0x101F03B0）是代码字面量池中的 u32 比较常量**（0x0050434E），非字符串资源——专用于文件头比对；
- **解析主函数 0x101F0252**：初始化 0x28 字节解析上下文 → `bl 0x102D8562` 读取文件目标机型字段并与字面量 **0x04390080**（Z7 产品码，即本仓库 `sound_layout` 已知的成功码）比对，不符即整体拒绝 → 随后进入 TLV 记录循环：每条记录 ID 为**大端 u32**（`rev` 字节序反转，与 dumpncp.pl 的 `unpack 'N'` 一致）；
- **记录 ID 白名单**：`1`、`2`（NCP 遗留主记录/曲线记录，走独立分支）与 `0x100-0x1700` 的 0x100 粒度族：0x200/0x300/0x400/0x500/0x600/0x700/**0x800**/0x900/0xA00/0xB00/0xC00/0xD00/0xE00/0xF00/0x1000-0x1700。**0x800 族（创意优化校准参数）在白名单内**；未知 ID 走 0x101F0444 错误路径；
- 族记录经 0x101F03C6 的统一处理器（`bl 0x101EFF2E`，按 0x101F07AC 所指注册表分发 handler）处理后回到记录循环；**成功路径 0x101F041A-0x101F043E 将解析结果提交进输出对象并返回 1**——是「解析应用」而非「跳过」；
- 0x101F10E8 处 `NP3\0`/`PICCON\0`/`B:\NIKON\CUSTOMPC\` 与一组 0xA28xxxxx RAM 指针同池，属卡目录扫描/文件识别代码。

**判定**：Z7 的自定义优化校准文件解析器在记录 ID 层明确接受创意参数族（0x800），并持有创意基础枚举↔内部 ID 的完整映射（§5.6）。0x800 族 handler 是否完整应用创意参数、以及后续 UI/渲染环节是否放行，仍待逆向/真机（第 8 章）。

### 5.8 UI 层创意参数证据（第二轮）

优化校准编辑对话框构建器（0x10356E40-0x10356E8C 一带）在构建控件时使用 **`movw r2,#0x8030`、`movw r2,#0x8032`——0x8xxx 创意参数子 ID**（疑为效果强度等编辑项），并将生成的资源挂接进对话框对象（`[r4,#0x58]/[r4,#0x5C]`）。结合 §5.6 的合法 ID 清单（含 0x0800-0x0813 整段），**UI 基础设施对创意族是「知情」的**；Z7 菜单不显示 20 创意项的差异点应在更高层的列表构建/门控函数，尚未定位。

## 6. 可移植列表（核心交付）

评级含义——可行性：高（证据充分/基础设施齐备）、中（需关键验证）、低（存在未证实的硬依赖）、✗（不可行）；工作量：人日级（≤3）/周级（1-4 周）/月级（>1 月）。

| # | 功能 | 来源机型（固件） | 移植路线 | 可行性 | 工作量 | 风险 | 依据 |
|---|---|---|---|---|---|---|---|
| 1 | **20 种创意优化校准**（Dream…Carbon） | Z50/Zfc/Z5/Z7II/D780（同代 EXPEED 6 固件，eg2090 家族优先） | **D：启用本机休眠子系统**（m900 同模式：定位门控→改读取值） | **中偏高** | 周级（定位门控+引擎验证）—月级（若引擎需从供体固件搬数据表） | 中：触碰图像管线，渲染异常只能真机发现 | §5.2/5.3：名称表+枚举+服务层+调用方俱在；同代 EXPEED 6 机型皆有此功能 |
| 2 | 创意优化校准的 NCP/PICCON 文件化加载 | 无需供体（自造文件） | **A：文件级**——用创意基础枚举（0x0801-0x0814）构造 NCP/PICCON 文件，经现有「管理优化校准」菜单从 `NIKON\CUSTOMPC\` 加载 | **中高（升级）** | 人日级（枚举值已到手，直接进入造文件+真机实测） | 低：不刷机、可随时删除；剩余风险为 0x800 族 handler 完整性与 UI 列表放行 | §5.6 枚举映射表、§5.7 解析器白名单含 0x800 族+型号校验 0x04390080、§3 horshack 格式知识；**原「待提取枚举」任务已完成** |
| 3 | 第三方胶片模拟配方（Portra/Kodachrome/Classic Chrome 复刻等，NCP 部分） | Nikon-Recipes 等社区的 NCP 文件 | 直接用现有官方能力，必要时改写基础枚举/曲线 | **高（本来就可用/待实测具体文件）** | 人日级 | 低 | Z7 官方支持 NCP 卡加载；Recipes 库中 NCP 子集即测试集 |
| 4 | Rich Tone Monochrome / Rich Tone Portrait | Zf/Z8/Z9（EXPEED 7） | B'：跨代引擎移植 | **低** | 月级+ | 高：新代引擎+数据结构差异大，Z7 固件零痕迹 | §5.5：无 Rich Tone 字符串 |
| 5 | NP3 Flexible Color（色彩混合器/三级调色/云创配方加载） | EXPEED 7 机型 | B'：需自写 NP3 解析器并把新参数映射进老管线 | **低（接近✗）** | 月级+ | 高 | §5.7 纠正：NP3 magic 被 Z7 文件层识别（非首轮误判的「零痕迹」），但 flexible-color 参数族的完整管线支持未证实；现代配方生态（Recipes 库 474 文件绝大多数 NP3）与 Z7 断层依旧 |
| 6 | 尼康云创配方在线下载 | Z6III/Z5II/Zf/Z50II/ZR | 依赖云端账户栈+Wi-Fi 服务栈整体移植 | **✗** | — | — | 官方明确仅 EXPEED 7 新机型；服务端也会校验机型 |
| 7 | 自制配方基线（Picture Control Utility 2 / NX Studio 导出 NCP） | 官方工具 | 不打补丁的对照路线 C | 高（现有能力） | 0 | 无 | 富士感直出社区实践；作为路线 A/D 的效果对照基准 |

**推荐主线**：#2（人日级、零刷机风险，先试文件级）→ 并行推进 #1 的门控逆向（本仓库能力内）→ #1 若引擎数据缺失再启动供体固件（Z50/Zfc 优先，eg2090 家族、本仓库已有 Z30 同家族地址表知识）比对补数据。#4/#5 建议明确排除出路线图，#6 永久排除。

## 7. 技术路线结论

- **路线 A（文件级，NCP/PICCON 构造）**：基础曲线内嵌固件、NCP 仅引用枚举（horshack 实证）→ **第二轮逆向已确认 Z7 解析器持有创意基础枚举映射（0x0801-0x0814，§5.6）且记录族白名单含创意参数族 0x800（§5.7）**。下一步即按 dumpncp.pl 的 TLV 布局+大端记录 ID+机型字段 0x04390080 构造测试文件（记录 1 基础枚举置 0x0801 起、强度字节按 0x80 偏移编码），插卡经「管理优化校准→载入/保存→复制到照相机」验证。零刷机风险，失败模式是 0x800 族 handler 不完整或 UI 列表不放行（届时转路线 D 并已握有精确地址）。
- **路线 D（固件级，休眠启用）**：本次逆向的核心成果——创意优化校准的名称/枚举/服务层已在 Z7 MAIN 内。与 m900（启用固件已有长曝光路径）同型，但复杂度高一档：需先定位 UI 门控（菜单为什么不列出）与渲染引擎本体（在 MAIN 还是 `ex1610` 协处理器模块）。若引擎在 `ex1610` 中且 Z7 的 `ex1610_037000` 版本缺少创意数据，则需从供体容器搬对应模块/数据段——这是「移植」的字面场景，也是工作量上界。
- **路线 B（同代整机搬运）**：仅当路线 D 证实引擎/数据缺失时启动；供体选 Z50/Zfc（eg2090 家族，本仓库有 Z30 同家族逆向知识）。
- **路线 C（官方工具基线）**：不构成移植，作为效果对照与降级方案。
- **路线 B'（跨代搬运，EXPEED 7→6）**：Rich Tone/NP3 均属此类，证据（§5.5）与生态判断均不支持，**排除**。

## 8. 后续任务清单（按优先级，2026-10-15 第二轮修订）

1. **✅ 已完成：创意基础枚举提取**——0x0801-0x0814 + FLAT=0x028E，直接取自 Z7 固件映射表（§5.6），无需供体固件。
2. **构造并实测路线 A 测试文件（当前最高优先）**：按 dumpncp.pl TLV 布局构造基于创意枚举的 NCP/PICCON 文件（目标机型字段 0x04390080、记录 ID 大端），插卡走「管理优化校准」加载，观察菜单与出片。真机操作由用户手动执行。
3. **定位「设定优化校准」列表门控**：从 UTF-16 菜单资源（0x10D380E4 等）与 §5.8 编辑对话框构建器（0x10356xxx）反查列表构建函数，找 Z7 与 Z50/Z7II 的差异点；入口线索：§5.4 调用方模块 0x102D23xx、§5.6 两张映射表的引用者 0x103594F0。
4. **定位渲染引擎**：确认创意效果参数表/数学在 MAIN 还是 `ex1610_037000.bi`；从基础枚举 0x0801-0x0814 反查参数表（§5.6 映射表的内部 ID 0x13FC-0x1420 段是现成索引）。
5. **Unicorn 离线验证**：对定位到的门控函数构造 256 态遍历（复用 `tools/verify_liveview_gates.py` 模式）。
6. （可选）引入 fujihack 式 CI：补丁构建+校验和自动验证流水线。
7. **真机验证**（用户手动执行）：一切离线结论的最终判据，路线 A 的文件加载结果与出片效果只能真机确认。

## 9. 参考资料

- [Nikon USA – Picture Controls Step-by-Step](https://www.nikonusa.com/learn-and-explore/c/tips-and-techniques/picture-controls-step-by-step)（20 创意名单）
- [Nikon Asia – Creative Picture Controls](https://www.nikon-asia.com/articles/how-to-give-your-images-and-video-a-different-look-using-creative-picture-controls)
- [Nikon Digitutor – Z7II/Z6II Creative Picture Controls](https://imaging.nikon.com/imaging/support/digitutor/z_7II_z_6II/techniques/201902_25_03_ml.html)
- [Nikon Z50II 在线手册 – 优化校准/云创](https://onlinemanual.nikonimglib.com/z50II/zh-cn-prc/18-07.html)、[尼康云创产品页](https://www.nikon.com.cn/sc_CN/product/software/nikon-imaging-cloud)
- [DPReview Forums – Picture Controls（2024-09）](https://www.dpreview.com/forums/threads/picture-controls.4775763)、[Reddit – I downloaded every Nikon Creative Picture Control](https://www.reddit.com/r/Nikon/comments/1t41ojn/i_downloaded_every_nikon_creative_picture_control)
- [Nikon Asia – Z8 新固件（Rich Tone Portrait）](https://www.nikon-asia.com/articles/enhance-your-creative-process-with-the-new-firmware-upgrade-for-the-nikon-z-8)
- 开源项目见第 3 章矩阵内链接。

## 10. 诚实性声明

- 本文全部固件结论来自**离线静态逆向**（解码、字符串、反汇编、交叉引用），未做任何真机刷写与实拍验证；「UI 门控」「渲染引擎位置」「0x800 族 handler 完整性」「构造文件能否实际加载出片」均标注为待逆向/待实测。
- **首轮报告的一处误判已在第二轮纠正**：`NP3` magic 实际存在于 Z7 固件（首轮字符串扫描最小长度参数漏检 3 字符串），相关结论已全文修正（§5.5/§5.7/§6）。
- `analysis/`（解码镜像、字符串导出）与 `reference/`（先例项目克隆）为不入库工作产物；`Z_7_0380.bin` 为用户手动下载的原厂镜像（哈希已验）。
- 官方功能矩阵基于尼康公开资料整理，个别上市月份可能有出入，不影响结论。
