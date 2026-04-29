# Hybrid Font 中文文档

这是一个 KernelSU/Magisk systemless 字体模块，目标是通过 Android 字体 XML 映射和常见兼容文件名实现 Noto Sans SC + Inter 混合字体：

- 英文字母、数字、常见拉丁字符使用 Inter。
- 简体中文使用 Noto Sans SC。
- 支持多字重。

## 目录

- [构建](#构建)
- [自动发布](#自动发布)
- [生成的刷入包](#生成的刷入包)
- [安装](#安装)
- [通用首刷建议](#通用首刷建议)
- [兼容性说明](#兼容性说明)
- [ColorOS 16 说明](#coloros-16-说明)
- [出问题怎么救](#出问题怎么救)
- [字重数量](#字重数量)
- [字体映射](#字体映射)
- [参考资料](#参考资料)

## 构建

```powershell
python -m pip install -r requirements.txt
python tools/build.py
```

构建脚本会从 Google Fonts 官方仓库下载 Inter 和 Noto Sans SC 变量字体，然后用 `fonttools` 生成静态多字重字体文件，并打包成 KernelSU/Magisk 可刷入 zip。

## 自动发布

仓库包含 GitHub Actions 发布工作流：

```text
.github/workflows/release.yml
```

推送版本 tag 后会自动构建两个 zip，并创建 GitHub Release：

```powershell
git tag v1.2.0
git push origin v1.2.0
```

tag 必须和 `module/module.prop` 里的版本一致。比如：

```text
version=1.2.0
```

对应 tag 必须是：

```text
v1.2.0
```

也可以在 GitHub Actions 页面手动运行 `Release` 工作流。如果不填写 tag，会默认使用 `v<module.prop version>`。

## 生成的刷入包

构建完成后会生成两个 zip：

- `dist/hybridfont_notosc_inter-v1.2.0.zip`
- `dist/hybridfont_notosc_inter-v1.2.0-safe-disabled.zip`

两个包的区别：

- 完整包：覆盖范围更大，包含 `DroidSansFallback*` 兼容文件。
- 安全包：默认禁用模块，并且跳过 `DroidSansFallback*` 兼容文件，适合所有机型第一次测试。

## 安装

在 KernelSU Manager 或 Magisk 中刷入生成的 zip。

KernelSU 上替换 `/system` 文件需要有可用的挂载 metamodule，例如 `meta-overlayfs`。没有这类挂载能力时，模块可能安装成功但字体 overlay 不生效。

## 通用首刷建议

第一次在任意机型或任意 ROM 上测试，建议先刷这个包：

```text
dist/hybridfont_notosc_inter-v1.2.0-safe-disabled.zip
```

推荐流程：

1. 在 KernelSU Manager 或 Magisk 里刷入 `safe-disabled` 包。
2. 重启一次，此时模块默认还是禁用状态。
3. 确认系统能正常开机，并且 KernelSU Manager 里能看到模块。
4. 手动启用模块。
5. 再重启一次。
6. 测试系统设置、桌面、锁屏、浏览器、微信等常用场景。

不建议第一次直接刷完整包。

## 兼容性说明

`v1.1.0` 的 Zygisk 实验包已废弃。它使用全局文件访问 hook，可能导致部分 App 的 WebView 或内嵌网页内容加载异常。

检测敏感环境建议继续使用 overlay 包，并配合 root 方案的模块卸载/隐藏能力，或使用 FontLoader 类兼容模块处理 App 崩溃与字体加载问题。

## ColorOS 16 说明

ColorOS 16 更适合使用 XML 映射型字体模块，而不是只替换字体文件名。本模块会生成根目录 `fonts.xml`，并默认放入 `/system/etc/fonts.xml` 和 `/system/etc/font_fallback.xml`。安装时还会检测设备上实际存在的 `font*.xml`，并映射到这些路径：

- `/system/system_ext/etc`
- `/system/product/etc`
- `/system/etc`

ColorOS 16 上需要确保 KernelSU/Magisk 的 systemless overlay 挂载正常。如果部分 App 因 Android 12+ 字体加载行为出现崩溃或内容加载异常，可以搭配 FontLoader 类兼容模块。如果同时使用 MFGA 这类字体 XML 映射模块，不建议让两个模块同时覆盖同一批 `font*.xml`，否则最终生效的是挂载优先级更高的那个。

生成的 XML 也会把 `Roboto` 以及常见 OnePlus、OPPO、OPlus、ColorOS 字体族名 alias 到 `sans-serif`，系统组件如果请求这些字体族名，也会解析到 Inter。

## 出问题怎么救

这个模块不写入真实 `boot`、`system`、`vendor`、`product` 分区，所以一般不会硬砖。主要风险是软砖，例如卡开机、SystemUI 崩溃、字体显示异常。

如果启用后无法正常进入系统，可以进入 KernelSU 安全模式或 recovery，然后创建：

```text
/data/adb/modules/hybridfont_notosc_inter/disable
```

也可以直接删除模块目录：

```text
/data/adb/modules/hybridfont_notosc_inter
```

## 字重数量

Inter 生成 9 个正体字重：

- Thin 100
- ExtraLight 200
- Light 300
- Regular 400
- Medium 500
- SemiBold 600
- Bold 700
- ExtraBold 800
- Black 900

Inter 生成 9 个斜体字重：

- Thin Italic 100
- ExtraLight Italic 200
- Light Italic 300
- Regular Italic 400
- Medium Italic 500
- SemiBold Italic 600
- Bold Italic 700
- ExtraBold Italic 800
- Black Italic 900

Noto Sans SC 生成 10 个中文字重：

- Thin 100
- ExtraLight 200
- Light 300
- DemiLight 350
- Regular 400
- Medium 500
- SemiBold 600
- Bold 700
- ExtraBold 800
- Black 900

总计：

- 英文 Inter：正体 9 字重 + 斜体 9 字重。
- 中文 Noto Sans SC：10 字重。

## 字体映射

英文/拉丁：

- `Roboto-*.ttf` 映射到 Inter 静态实例。
- XML 中的 `sans-serif` 映射到 Inter 的 `Roboto-*` 兼容文件名。

简体中文：

- `100.ttf`、`200.ttf`、`300.ttf`、`350.ttf`、`400.ttf`、`500.ttf`、`600.ttf`、`700.ttf`、`800.ttf`、`900.ttf` 映射到 Noto Sans SC 静态实例。
- `NotoSansCJKsc-*.otf` 映射到 Noto Sans SC 静态实例。
- 完整包额外包含 `DroidSansFallback.ttf` 和 `DroidSansFallbackFull.ttf`。
- 两个包都包含 `NotoSansCJK-VF.ttf` 和 `NotoSansCJKsc-VF.ttf`。
- XML 中的 `zh-Hans` 和 `zh-CN` 映射到 Noto Sans SC 的数字字重文件。

不同 ROM 的字体文件名可能不一样。如果某个 ROM 使用厂商自定义字体文件名，需要在 `tools/build.py` 里增加对应映射后重新构建。

## 参考资料

- KernelSU 模块文档：https://kernelsu.org/guide/module.html
- Magisk 模块文档：https://topjohnwu.github.io/Magisk/guides.html
- Android 字体 fallback 文档：https://source.android.com/docs/core/fonts/custom-font-fallback
- Inter：https://github.com/google/fonts/tree/main/ofl/inter
- Noto Sans SC：https://github.com/google/fonts/tree/main/ofl/notosanssc
