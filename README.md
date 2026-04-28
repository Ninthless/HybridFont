# Hybrid Font - Noto Sans SC + Inter

KernelSU/Magisk systemless font module that maps Android Latin font files to Inter and common Simplified Chinese fallback files to Noto Sans SC.

This is intentionally built as a KernelSU/Magisk module, not an Xposed APK. Font replacement is a filesystem overlay problem, while Xposed/LSPosed is better suited for runtime method hooks.

## Documentation

- [中文文档](docs/zh-CN.md)
- [Research notes](docs/research.md)

## Contents

- [Build](#build)
- [Release](#release)
- [Install](#install)
- [Safe First Test](#safe-first-test)
- [Zygisk Experimental](#zygisk-experimental)
- [Font Mapping](#font-mapping)
- [Sources](#sources)

## Build

```powershell
python -m pip install -r requirements.txt
python tools/build.py
```

The build writes three flashable zips:

- `dist/hybridfont_notosc_inter-v1.1.0.zip`: full compatibility package.
- `dist/hybridfont_notosc_inter-v1.1.0-safe-disabled.zip`: conservative package with the module disabled by default and without `DroidSansFallback*` or generic `NotoSansCJK-*.ttc` replacements.
- `dist/hybridfont_notosc_inter_zygisk-v1.1.0-experimental.zip`: Zygisk experimental package without system font overlay.

## Release

GitHub Actions publishes releases automatically when a version tag is pushed:

```powershell
git tag v1.1.0
git push origin v1.1.0
```

The tag must match `module/module.prop` version as `v<version>`. For example, `version=1.1.0` requires `v1.1.0`.

The release workflow can also be started manually from the GitHub Actions page. If no tag is provided, it uses `v<module.prop version>`.

## Install

Install the generated zip from KernelSU Manager or Magisk. On KernelSU, `/system` file replacement requires a mounting metamodule such as `meta-overlayfs`, because KernelSU delegates system overlays to metamodules.

For first tests on any ROM, use the `safe-disabled` package. After installation, confirm the module appears in KernelSU Manager, enable it manually, then reboot.

Reboot after installation.

## Safe First Test

Use this package first:

```text
dist/hybridfont_notosc_inter-v1.1.0-safe-disabled.zip
```

This package is disabled by default and avoids the wider fallback replacements that are more likely to vary between ROMs. It is intended for first tests on any device or ROM.

Recommended flow:

1. Flash the `safe-disabled` package in KernelSU Manager.
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

## Zygisk Experimental

Use this package only if you have a working Zygisk environment:

```text
dist/hybridfont_notosc_inter_zygisk-v1.1.0-experimental.zip
```

This package uses `id=hybridfont_notosc_inter_zygisk`, keeps fonts under the module private `fonts/` directory, and does not mount files into `/system/fonts`.

Do not enable the Zygisk experimental package together with the overlay package.

## Font Mapping

Latin:

- `Roboto-*.ttf` is generated from Inter static instances.
- Inter weights: Thin 100, Light 300, Regular 400, Medium 500, Bold 700, Black 900.

Simplified Chinese:

- `NotoSansCJKsc-*.otf` is generated from Noto Sans SC static instances.
- `NotoSansCJK-Regular.ttc` and `NotoSansCJK-Bold.ttc` are generated as compatibility collections.
- `NotoSansCJK-VF.ttf`, `NotoSansCJKsc-VF.ttf`, `DroidSansFallback.ttf`, and `DroidSansFallbackFull.ttf` are included for common fallback paths.
- Noto Sans SC weights: Thin 100, Light 300, DemiLight 350, Regular 400, Medium 500, Bold 700, Black 900.

The full package contains 6 Inter upright weights, 6 Inter italic weights, and 7 Noto Sans SC weights. The conservative safe package contains the same Inter and Noto Sans SC weight set, but skips generic TTC and DroidSans fallback compatibility files.

Device ROMs differ. If a ROM uses vendor-specific font names, add those names to `tools/build.py` and rebuild.

## Sources

- KernelSU module guide: https://kernelsu.org/guide/module.html
- Magisk developer guide: https://topjohnwu.github.io/Magisk/guides.html
- LSPosed modern Xposed API guide: https://github.com/LSPosed/LSPosed/wiki/Develop-Xposed-Modules-Using-Modern-Xposed-API
- Android custom font fallback: https://source.android.com/docs/core/fonts/custom-font-fallback
- Inter: https://github.com/google/fonts/tree/main/ofl/inter
- Noto Sans SC: https://github.com/google/fonts/tree/main/ofl/notosanssc
