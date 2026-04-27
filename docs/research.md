# Research Notes

## Architecture Decision

KernelSU and Magisk modules are the right packaging model for this font module because both support systemless overlays of `/system` files. Android system fonts live under system font paths and are selected through system font configuration, so replacing the font files is the lowest-complexity path.

Xposed/LSPosed is not the primary implementation here. LSPosed modules are APKs that hook Java/runtime behavior with entry points such as `META-INF/xposed/java_init.list`. That is useful for app-specific overrides, but unnecessary and more fragile for a global font replacement.

## KernelSU

KernelSU modules live under `/data/adb/modules/$MODID`, use `module.prop` for metadata, and mount the module `system` directory when no `skip_mount` file exists. KernelSU states that modifying `/system` files requires a mounting metamodule such as `meta-overlayfs`.

## Magisk

Magisk modules use the same core layout: `module.prop`, optional installer/runtime scripts, and a `system` directory for mounted files. `module.prop` requires `id`, `name`, `version`, `versionCode`, `author`, and `description`.

## Android Fonts

Android uses XML font-family fallback configuration and supports fallback customization. Because device ROMs can customize font configuration and filenames, this module targets common AOSP/Android font filenames instead of overwriting `fonts.xml`.

## Font Strategy

The module maps Android Latin filenames to Inter static instances and common Simplified Chinese fallback filenames to Noto Sans SC static or variable files. This preserves multi-weight rendering for common Android weight requests while avoiding a device-specific `fonts.xml` replacement.

## ColorOS 16 Risk Notes

The module is not expected to hard brick a device because it does not write boot, vendor, system, or product partitions. The realistic failure mode is a recoverable boot issue caused by a bad font overlay, such as boot animation hang, SystemUI crash, or unreadable text.

For ColorOS 16 on OnePlus with KernelSU, the safer first package is `hybridfont_notosc_inter-v1.0.0-coloros16-safe-disabled.zip`. It includes a `disable` flag so the module does not take effect immediately after flashing, and it skips broad compatibility replacements such as `DroidSansFallback*` and generic `NotoSansCJK-*.ttc`.

If the enabled module causes boot problems, disable it by creating `/data/adb/modules/hybridfont_notosc_inter/disable` or remove `/data/adb/modules/hybridfont_notosc_inter`.

## Weight Count

Inter provides 6 generated upright weights and 6 generated italic weights in this module:

- Thin 100
- Light 300
- Regular 400
- Medium 500
- Bold 700
- Black 900

Noto Sans SC provides 7 generated Simplified Chinese weights:

- Thin 100
- Light 300
- DemiLight 350
- Regular 400
- Medium 500
- Bold 700
- Black 900

The module also includes the original variable Noto Sans SC files under common CJK variable font filenames.
