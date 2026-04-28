from __future__ import annotations

import os
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

from fontTools.ttLib import TTCollection, TTFont
from fontTools.varLib import instancer


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "module"
DOWNLOADS = ROOT / "build" / "downloads"
GENERATED = ROOT / "build" / "generated-fonts"
BUILD_MODULES = ROOT / "build" / "modules"
ZYGISK_API = ROOT / "build" / "zygisk-api"
DIST = ROOT / "dist"
MODULE_FONTS = MODULE / "system" / "fonts"
MODULE_LICENSES = MODULE / "licenses"
DISABLE_FLAG = MODULE / "disable"
MODULE_PROP = MODULE / "module.prop"
NATIVE = ROOT / "native"

ZYGISK_API_URL = "https://raw.githubusercontent.com/topjohnwu/zygisk-module-sample/master/module/jni/zygisk.hpp"
INTER_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf"
INTER_ITALIC_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter-Italic%5Bopsz%2Cwght%5D.ttf"
NOTO_SC_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf"
INTER_LICENSE_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/OFL.txt"
NOTO_SC_LICENSE_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/OFL.txt"

INTER_WEIGHTS = {
    "Thin": 100,
    "Light": 300,
    "Regular": 400,
    "Medium": 500,
    "Bold": 700,
    "Black": 900,
}

CJK_WEIGHTS = {
    "Thin": 100,
    "Light": 300,
    "DemiLight": 350,
    "Regular": 400,
    "Medium": 500,
    "Bold": 700,
    "Black": 900,
}

CJK_SC_ALIASES = {
    "Thin": ["NotoSansCJKsc-Thin.otf"],
    "Light": ["NotoSansCJKsc-Light.otf"],
    "DemiLight": ["NotoSansCJKsc-DemiLight.otf"],
    "Regular": ["NotoSansCJKsc-Regular.otf", "DroidSansFallback.ttf", "DroidSansFallbackFull.ttf"],
    "Medium": ["NotoSansCJKsc-Medium.otf"],
    "Bold": ["NotoSansCJKsc-Bold.otf"],
    "Black": ["NotoSansCJKsc-Black.otf"],
}

VENDOR_ALIASES = {
    "RobotoStatic-Regular.ttf": "Roboto-Regular.ttf",
    "SysSans-Hans-Regular.ttf": "NotoSansCJKsc-Regular.otf",
}


def read_module_prop() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in MODULE_PROP.read_text(encoding="utf-8").splitlines():
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value
    return values


def download(url: str, target: Path) -> None:
    if target.exists() and target.stat().st_size > 0:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response:
        target.write_bytes(response.read())


def instantiate_variable(source: Path, target: Path, axes: dict[str, int | float]) -> None:
    if target.exists() and target.stat().st_size > 0:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    font = TTFont(source)
    static_font = instancer.instantiateVariableFont(font, axes, inplace=False)
    static_font.save(target)
    static_font.close()
    font.close()


def build_collection(source: Path, target: Path, count: int) -> None:
    if target.exists() and target.stat().st_size > 0:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    collection = TTCollection()
    collection.fonts = [TTFont(source) for _ in range(count)]
    collection.save(target)
    for font in collection.fonts:
        font.close()


def clean_output() -> None:
    if MODULE_FONTS.exists():
        shutil.rmtree(MODULE_FONTS)
    if MODULE_LICENSES.exists():
        shutil.rmtree(MODULE_LICENSES)
    if BUILD_MODULES.exists():
        shutil.rmtree(BUILD_MODULES)
    if DIST.exists():
        shutil.rmtree(DIST)
    if DISABLE_FLAG.exists():
        DISABLE_FLAG.unlink()
    MODULE_FONTS.mkdir(parents=True, exist_ok=True)
    MODULE_LICENSES.mkdir(parents=True, exist_ok=True)
    DIST.mkdir(parents=True, exist_ok=True)


def copy_file(source: Path, target_dir: Path, name: str) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target_dir / name)


def generate_fonts(output_dir: Path, include_compat_fallbacks: bool, include_vendor_aliases: bool = False) -> None:
    inter = DOWNLOADS / "Inter[opsz,wght].ttf"
    inter_italic = DOWNLOADS / "Inter-Italic[opsz,wght].ttf"
    noto_sc = DOWNLOADS / "NotoSansSC[wght].ttf"

    download(INTER_URL, inter)
    download(INTER_ITALIC_URL, inter_italic)
    download(NOTO_SC_URL, noto_sc)
    download(INTER_LICENSE_URL, MODULE_LICENSES / "Inter-OFL.txt")
    download(NOTO_SC_LICENSE_URL, MODULE_LICENSES / "NotoSansSC-OFL.txt")

    inter_generated: dict[str, Path] = {}
    inter_italic_generated: dict[str, Path] = {}
    cjk_generated: dict[str, Path] = {}

    for name, weight in INTER_WEIGHTS.items():
        upright = GENERATED / "inter" / f"Inter-{name}.ttf"
        italic = GENERATED / "inter" / f"Inter-{name}Italic.ttf"
        instantiate_variable(inter, upright, {"opsz": 14, "wght": weight})
        instantiate_variable(inter_italic, italic, {"opsz": 14, "wght": weight})
        inter_generated[name] = upright
        inter_italic_generated[name] = italic

    for name, weight in CJK_WEIGHTS.items():
        target = GENERATED / "noto-sans-sc" / f"NotoSansSC-{name}.ttf"
        instantiate_variable(noto_sc, target, {"wght": weight})
        cjk_generated[name] = target

    for name in INTER_WEIGHTS:
        copy_file(inter_generated[name], output_dir, f"Roboto-{name}.ttf")
        copy_file(inter_italic_generated[name], output_dir, f"Roboto-{name}Italic.ttf")

    copy_file(inter_generated["Regular"], output_dir, "Roboto-Regular.ttf")
    copy_file(inter_italic_generated["Regular"], output_dir, "Roboto-Italic.ttf")

    for weight_name, aliases in CJK_SC_ALIASES.items():
        for alias in aliases:
            if not include_compat_fallbacks and alias.startswith("DroidSansFallback"):
                continue
            copy_file(cjk_generated[weight_name], output_dir, alias)

    copy_file(noto_sc, output_dir, "NotoSansCJK-VF.ttf")
    copy_file(noto_sc, output_dir, "NotoSansCJKsc-VF.ttf")
    if include_compat_fallbacks:
        build_collection(cjk_generated["Regular"], output_dir / "NotoSansCJK-Regular.ttc", 5)
        build_collection(cjk_generated["Bold"], output_dir / "NotoSansCJK-Bold.ttc", 5)

    if include_vendor_aliases:
        for alias, source_name in VENDOR_ALIASES.items():
            copy_file(output_dir / source_name, output_dir, alias)


def make_zip(suffix: str = "") -> Path:
    module_prop = read_module_prop()
    zip_path = DIST / f"{module_prop['id']}-v{module_prop['version']}{suffix}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(MODULE.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(MODULE).as_posix())
    return zip_path


def find_android_ndk() -> Path | None:
    for key in ("ANDROID_NDK_HOME", "ANDROID_NDK_ROOT"):
        value = os.environ.get(key)
        if value:
            path = Path(value)
            if (path / "build" / "cmake" / "android.toolchain.cmake").exists():
                return path
    for key in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        value = os.environ.get(key)
        if not value:
            continue
        ndk_dir = Path(value) / "ndk"
        if not ndk_dir.exists():
            continue
        versions = sorted(ndk_dir.iterdir(), reverse=True)
        for path in versions:
            if (path / "build" / "cmake" / "android.toolchain.cmake").exists():
                return path
    return None


def build_zygisk_native() -> Path | None:
    ndk = find_android_ndk()
    if ndk is None:
        return None
    download(ZYGISK_API_URL, ZYGISK_API / "zygisk.hpp")
    build_dir = ROOT / "build" / "native" / "arm64-v8a"
    output = build_dir / "libhybridfontzygisk.so"
    subprocess.run(
        [
            "cmake",
            "-S",
            str(NATIVE),
            "-B",
            str(build_dir),
            "-G",
            "Ninja",
            "-DANDROID_ABI=arm64-v8a",
            "-DANDROID_PLATFORM=android-23",
            f"-DCMAKE_TOOLCHAIN_FILE={ndk / 'build' / 'cmake' / 'android.toolchain.cmake'}",
            f"-DZYGISK_API_DIR={ZYGISK_API}",
            "-DCMAKE_BUILD_TYPE=Release",
        ],
        check=True,
    )
    subprocess.run(["cmake", "--build", str(build_dir), "--config", "Release"], check=True)
    return output if output.exists() else None


def write_module_prop(target: Path, module_prop: dict[str, str], zygisk: bool = False) -> None:
    if not zygisk:
        shutil.copy2(MODULE_PROP, target / "module.prop")
        return
    values = {
        "id": f"{module_prop['id']}_zygisk",
        "name": f"{module_prop['name']} - Zygisk Experimental",
        "version": module_prop["version"],
        "versionCode": module_prop["versionCode"],
        "author": module_prop["author"],
        "description": "Zygisk experimental font redirection module without system font overlay.",
    }
    content = "\n".join(f"{key}={value}" for key, value in values.items()) + "\n"
    (target / "module.prop").write_text(content, encoding="utf-8")


def write_customize(target: Path, zygisk: bool = False) -> None:
    if not zygisk:
        shutil.copy2(MODULE / "customize.sh", target / "customize.sh")
        return
    content = "\n".join(
        [
            'ui_print "- Hybrid Font Zygisk Experimental"',
            'ui_print "- Requires a working Zygisk environment"',
            'ui_print "- Do not enable together with the overlay font package"',
            'ui_print "- Reboot after installation"',
            "",
            'set_perm_recursive "$MODPATH/fonts" 0 0 0755 0644',
            'set_perm_recursive "$MODPATH/zygisk" 0 0 0755 0644',
        ]
    )
    (target / "customize.sh").write_text(content + "\n", encoding="utf-8")


def make_tree_zip(source: Path, zip_path: Path) -> Path:
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source).as_posix())
    return zip_path


def build_zygisk_package() -> Path | None:
    native_so = build_zygisk_native()
    if native_so is None:
        print("Skipping zygisk package: Android NDK was not found")
        return None
    module_prop = read_module_prop()
    target = BUILD_MODULES / "zygisk"
    fonts = target / "fonts"
    licenses = target / "licenses"
    zygisk_dir = target / "zygisk"
    target.mkdir(parents=True, exist_ok=True)
    fonts.mkdir(parents=True, exist_ok=True)
    licenses.mkdir(parents=True, exist_ok=True)
    zygisk_dir.mkdir(parents=True, exist_ok=True)
    write_module_prop(target, module_prop, zygisk=True)
    write_customize(target, zygisk=True)
    generate_fonts(fonts, include_compat_fallbacks=True, include_vendor_aliases=True)
    shutil.copy2(MODULE_LICENSES / "Inter-OFL.txt", licenses / "Inter-OFL.txt")
    shutil.copy2(MODULE_LICENSES / "NotoSansSC-OFL.txt", licenses / "NotoSansSC-OFL.txt")
    shutil.copy2(native_so, zygisk_dir / "arm64-v8a.so")
    zip_path = DIST / f"{module_prop['id']}_zygisk-v{module_prop['version']}-experimental.zip"
    return make_tree_zip(target, zip_path)


def main() -> None:
    clean_output()
    generate_fonts(MODULE_FONTS, include_compat_fallbacks=True)
    print(make_zip())

    shutil.rmtree(MODULE_FONTS)
    MODULE_FONTS.mkdir(parents=True, exist_ok=True)
    generate_fonts(MODULE_FONTS, include_compat_fallbacks=False)
    DISABLE_FLAG.write_text("", encoding="utf-8")
    print(make_zip("-safe-disabled"))
    DISABLE_FLAG.unlink()
    zygisk_zip = build_zygisk_package()
    if zygisk_zip is not None:
        print(zygisk_zip)


if __name__ == "__main__":
    main()
