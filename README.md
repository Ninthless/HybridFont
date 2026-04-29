# Hybrid Font - Noto Sans SC + Inter

KernelSU/Magisk systemless font module that maps Android Latin fonts to Inter and Simplified Chinese fallback fonts to Noto Sans SC through Android font XML files and common compatibility filenames.

## Documentation

- [中文文档](docs/zh-CN.md)
- [Research notes](docs/research.md)

## Contents

- [Build](#build)
- [Release](#release)
- [Install](#install)
- [Safe First Test](#safe-first-test)
- [Compatibility Notes](#compatibility-notes)
- [ColorOS 16 Notes](#coloros-16-notes)
- [Font Mapping](#font-mapping)
- [Sources](#sources)

## Build

```powershell
python -m pip install -r requirements.txt
python tools/build.py
```

The build writes two flashable zips:

- `dist/hybridfont_notosc_inter-v1.2.0.zip`: full compatibility package.
- `dist/hybridfont_notosc_inter-v1.2.0-safe-disabled.zip`: conservative package with the module disabled by default and without `DroidSansFallback*` replacements.

## Release

GitHub Actions publishes releases automatically when a version tag is pushed:

```powershell
git tag v1.2.0
git push origin v1.2.0
```

The tag must match `module/module.prop` version as `v<version>`. For example, `version=1.2.0` requires `v1.2.0`.

The release workflow can also be started manually from the GitHub Actions page. If no tag is provided, it uses `v<module.prop version>`.

## Install

Install the generated zip from KernelSU Manager or Magisk. On KernelSU, `/system` file replacement requires a mounting metamodule such as `meta-overlayfs`, because KernelSU delegates system overlays to metamodules.

For first tests on any ROM, use the `safe-disabled` package. After installation, confirm the module appears in KernelSU Manager, enable it manually, then reboot.

Reboot after installation.

## Safe First Test

Use this package first:

```text
dist/hybridfont_notosc_inter-v1.2.0-safe-disabled.zip
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

## Compatibility Notes

The `v1.1.0` Zygisk experimental package is deprecated because global file-access hooks can break WebView or embedded web content in some apps.

For detection-sensitive environments, use the overlay package with your root solution's module unmount/hide features or a dedicated FontLoader-style compatibility module instead of the deprecated Zygisk package.

## ColorOS 16 Notes

ColorOS 16 is more reliable with XML-based font mapping than with filename-only replacement. This module now generates `fonts.xml`, default `/system/etc/fonts.xml`, and default `/system/etc/font_fallback.xml`. During installation it also maps the generated XML onto existing `font*.xml` files under these device paths when present:

- `/system/system_ext/etc`
- `/system/product/etc`
- `/system/etc`

For ColorOS 16, use a working KernelSU/Magisk overlay mount setup. If apps crash or embedded content fails because of Android 12+ font loading behavior, use FontLoader as a companion compatibility module. If using MFGA as a separate font mapping module, avoid stacking two modules that both replace the same font XML files unless you intentionally want one to override the other.

The generated XML also aliases `Roboto` and common OnePlus/OPPO/OPlus/ColorOS font family names to `sans-serif`, so system components that request those family names can still resolve to Inter.

## Font Mapping

Latin:

- `Roboto-*.ttf` is generated from Inter static instances.
- Inter weights: Thin 100, ExtraLight 200, Light 300, Regular 400, Medium 500, SemiBold 600, Bold 700, ExtraBold 800, Black 900.
- XML maps `sans-serif` to Inter through `Roboto-*` compatibility filenames.

Simplified Chinese:

- `100.ttf`, `200.ttf`, `300.ttf`, `350.ttf`, `400.ttf`, `500.ttf`, `600.ttf`, `700.ttf`, `800.ttf`, and `900.ttf` are generated from Noto Sans SC static instances.
- `NotoSansCJKsc-*.otf` is generated from Noto Sans SC static instances.
- `NotoSansCJK-VF.ttf`, `NotoSansCJKsc-VF.ttf`, `DroidSansFallback.ttf`, and `DroidSansFallbackFull.ttf` are included for common fallback paths.
- XML maps `zh-Hans` and `zh-CN` to the Noto Sans SC numeric weight files.
- Noto Sans SC weights: Thin 100, ExtraLight 200, Light 300, DemiLight 350, Regular 400, Medium 500, SemiBold 600, Bold 700, ExtraBold 800, Black 900.

The full package contains 9 Inter upright weights, 9 Inter italic weights, and 10 Noto Sans SC weights. The conservative safe package contains the same XML and weight set, but skips `DroidSansFallback*` compatibility files.

Device ROMs differ. If a ROM uses vendor-specific font names, add those names to `tools/build.py` and rebuild.

## Sources

- KernelSU module guide: https://kernelsu.org/guide/module.html
- Magisk developer guide: https://topjohnwu.github.io/Magisk/guides.html
- Android custom font fallback: https://source.android.com/docs/core/fonts/custom-font-fallback
- Inter: https://github.com/google/fonts/tree/main/ofl/inter
- Noto Sans SC: https://github.com/google/fonts/tree/main/ofl/notosanssc
