# WonderLantern Z7 QEMU

[English README](README.md) · [构建](docs/build.md) · [固件输入](docs/firmware.md) · [原理](docs/architecture.md) · [调试](docs/debugging.md) · [经验](docs/research-notes.md)

这是 WonderLantern 发布的 Z7 实验性 QEMU 设备模型、浏览器操作界面和图像处理工具。
项目仅作研究与学习，尊重尼康权益，与尼康没有官方关联，也不是可以刷入相机的固件。

**固件由用户自己提供。** 公开仓库只含独立编写的模拟器源码、工具、合成测试和文档。
不附带、不自动下载尼康固件，也不公开尼康私有代码、解密后的专有程序、设备转储、
密钥、字库、图标位图、校准资料或原厂界面截图。公开测试使用程序生成的图形与 RAW。

原本的 Z7 C 3.80 研究基线已经能运行原厂菜单和拍摄界面，显示固件绘制的 ISO、快门、
文字与图标描边、红色无卡标记。静态图像经实验 RAW DMA、功能性 ISP、原厂提交的
输出缓冲、GPU 与 LCD 扫描进入取景画面；MENU 往返保持同一个 guest。
公开版本保留这些设备实现，调整路径与启动参数，并用合成素材替换私有回归样本。

这不等于真实 CMOS 与 ISP 已经还原。2780×932、12 bit RGGB、u16 小端存储、5568
字节行跨度是实验配置，不是对物理传感器链路的结论。实际噪声处理、校准、AF/PDAF、
运动检测、机械时序、真实曝光响应与写卡拍摄仍不在已验证范围内。启动过程也会显式
修改模拟机 RAM 状态及调用原厂函数；固件文件不变，与 guest 完全未经干预是两回事。

## 使用

Linux 建议 Python 3.12 以上。Windows 请明确选择 WSL 发行版；本机项目使用
`ubuntu-noble-nikon`，不会使用课程专用的 `ubuntu-noble`。完整安装命令见
[构建说明](docs/build.md)。依赖准备完毕后：

```sh
python tools/build.py --jobs 4
python tools/make_cmos.py
python tools/interactive.py --firmware /你的本地路径/z7-main-payload.bin \
    --photo-liveview --port 8787
```

浏览器打开 `http://127.0.0.1:8787/`。默认输入为本地生成的色条与灰阶。
`python tools/make_cmos.py --image /你的图片路径/image.jpg` 可生成自己的 Bayer 输入；
启动前生成，已有会话通过重启重新载入。模拟器不会通过 USB 操作真机。

兼容输入为 **Z7 C 3.80 已提取 MAIN**，33,052,088 字节，SHA-256：

```text
e6df1764323fb1c287159dd3ce1c84ac93c72b96ba6eb09c070295c093fecbff
```

相机升级包容器不能直接作为这个输入。公开仓库不提供密钥、专有内容或解包服务。
请独立取得有权使用的本地输入；详见[固件说明](docs/firmware.md)。仅看菜单可使用
`--profile menu`，不要同时传 `--photo-liveview`。

## 读文档的顺序

1. [构建](docs/build.md)、[固件输入](docs/firmware.md)、[操作](docs/usage.md)：启动和故障排查。
2. [设备模型与图像链路](docs/architecture.md)：每一层做了什么，以及假设在哪里。
3. [调试](docs/debugging.md)、[测试与验收](docs/testing.md)：如何取得证据，而不是仅凭“有画面”判断。
4. [研究经验](docs/research-notes.md)：中断、RAW 排空、描边、颜色、性能与其他机型的复用边界。
5. [公开发布审查](docs/publication.md)、[贡献规范](CONTRIBUTING.md)：防止后续把私有资料带进公共 Git 历史。

源码覆盖层、工具、测试和文档采用 GPL-2.0-or-later；QEMU 和依赖保留各自许可证。
研究用途声明不改变 GPL 的授权范围，也不赋予尼康材料的分发权。见 [NOTICE.md](NOTICE.md)
和 [COPYING](COPYING)。
