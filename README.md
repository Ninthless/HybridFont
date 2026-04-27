# Hybrid Font - Noto Sans SC + Inter

KernelSU/Magisk systemless font module that maps Android Latin font files to Inter and common Simplified Chinese fallback files to Noto Sans SC.

This is intentionally built as a KernelSU/Magisk module, not an Xposed APK. Font replacement is a filesystem overlay problem, while Xposed/LSPosed is better suited for runtime method hooks.

## Documentation

- [中文文档](docs/zh-CN.md)
- [Research notes](docs/research.md)

## Contents

- [Build](#build)
- [Install](#install)
- [ColorOS 16 / OnePlus First Test](#coloros-16--oneplus-first-test)
- [Font Mapping](#font-mapping)
- [Sources](#sources)

## Build

```powershell
python -m pip install -r requirements.txt
python tools/build.py
```

The build writes two flashable zips:

- `dist/hybridfont_notosc_inter-v1.0.0.zip`: full compatibility package.
- `dist/hybridfont_notosc_inter-v1.0.0-coloros16-safe-disabled.zip`: conservative package with the module disabled by default and without `DroidSansFallback*` or generic `NotoSansCJK-*.ttc` replacements.

## Install

Install the generated zip from KernelSU Manager or Magisk. On KernelSU, `/system` file replacement requires a mounting metamodule such as `meta-overlayfs`, because KernelSU delegates system overlays to metamodules.

For ColorOS/OxygenOS first tests, use the `coloros16-safe-disabled` package. After installation, confirm the module appears in KernelSU Manager, enable it manually, then reboot.

Reboot after installation.

## ColorOS 16 / OnePlus First Test

Use this package first:

```text
dist/hybridfont_notosc_inter-v1.0.0-coloros16-safe-disabled.zip
```

This package is disabled by default and avoids the wider fallback replacements that are more likely to vary between ROMs.

Recommended flow:

1. Flash the `coloros16-safe-disabled` package in KernelSU Manager.
2. Reboot once while the module is still disabled.
3. Confirm the module appears in KernelSU Manager.
4. Enable the module manually.
5. Reboot again and test system UI, launcher, browser, WeChat, settings, and lock screen.

If boot fails or SystemUI crashes, enter KernelSU safe mode or recovery and create this file:

```text
/data/adb/modules/hybridfont_notosc_inter/disable
```

You can also remove the module directory:

```text
/data/adb/modules/hybridfont_notosc_inter
```

This module does not write real system partitions, so the expected failure mode is a recoverable module boot issue rather than a hard brick.

## Font Mapping

Latin:

- `Roboto-*.ttf` is generated from Inter static instances.
- Inter weights: Thin 100, Light 300, Regular 400, Medium 500, Bold 700, Black 900.

Simplified Chinese:

- `NotoSansCJKsc-*.otf` is generated from Noto Sans SC static instances.
- `NotoSansCJK-Regular.ttc` and `NotoSansCJK-Bold.ttc` are generated as compatibility collections.
- `NotoSansCJK-VF.ttf`, `NotoSansCJKsc-VF.ttf`, `DroidSansFallback.ttf`, and `DroidSansFallbackFull.ttf` are included for common fallback paths.
- Noto Sans SC weights: Thin 100, Light 300, DemiLight 350, Regular 400, Medium 500, Bold 700, Black 900.

The full package contains 6 Inter upright weights, 6 Inter italic weights, and 7 Noto Sans SC weights. The conservative ColorOS package contains the same Inter and Noto Sans SC weight set, but skips generic TTC and DroidSans fallback compatibility files.

Device ROMs differ. If a ROM uses vendor-specific font names, add those names to `tools/build.py` and rebuild.

## Sources

- KernelSU module guide: https://kernelsu.org/guide/module.html
- Magisk developer guide: https://topjohnwu.github.io/Magisk/guides.html
- LSPosed modern Xposed API guide: https://github.com/LSPosed/LSPosed/wiki/Develop-Xposed-Modules-Using-Modern-Xposed-API
- Android custom font fallback: https://source.android.com/docs/core/fonts/custom-font-fallback
- Inter: https://github.com/google/fonts/tree/main/ofl/inter
- Noto Sans SC: https://github.com/google/fonts/tree/main/ofl/notosanssc
