from __future__ import annotations

import shutil
import urllib.request
import zipfile
from pathlib import Path

from fontTools.ttLib import TTCollection, TTFont
from fontTools.varLib import instancer


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "module"
DOWNLOADS = ROOT / "build" / "downloads"
GENERATED = ROOT / "build" / "generated-fonts"
DIST = ROOT / "dist"
MODULE_FONTS = MODULE / "system" / "fonts"
MODULE_LICENSES = MODULE / "licenses"
DISABLE_FLAG = MODULE / "disable"
MODULE_PROP = MODULE / "module.prop"

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
    if DIST.exists():
        shutil.rmtree(DIST)
    if DISABLE_FLAG.exists():
        DISABLE_FLAG.unlink()
    MODULE_FONTS.mkdir(parents=True, exist_ok=True)
    MODULE_LICENSES.mkdir(parents=True, exist_ok=True)
    DIST.mkdir(parents=True, exist_ok=True)


def copy_file(source: Path, name: str) -> None:
    shutil.copy2(source, MODULE_FONTS / name)


def generate_fonts(include_compat_fallbacks: bool) -> None:
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
        copy_file(inter_generated[name], f"Roboto-{name}.ttf")
        copy_file(inter_italic_generated[name], f"Roboto-{name}Italic.ttf")

    copy_file(inter_generated["Regular"], "Roboto-Regular.ttf")
    copy_file(inter_italic_generated["Regular"], "Roboto-Italic.ttf")

    for weight_name, aliases in CJK_SC_ALIASES.items():
        for alias in aliases:
            if not include_compat_fallbacks and alias.startswith("DroidSansFallback"):
                continue
            copy_file(cjk_generated[weight_name], alias)

    copy_file(noto_sc, "NotoSansCJK-VF.ttf")
    copy_file(noto_sc, "NotoSansCJKsc-VF.ttf")
    if include_compat_fallbacks:
        build_collection(cjk_generated["Regular"], MODULE_FONTS / "NotoSansCJK-Regular.ttc", 5)
        build_collection(cjk_generated["Bold"], MODULE_FONTS / "NotoSansCJK-Bold.ttc", 5)


def make_zip(suffix: str = "") -> Path:
    module_prop = read_module_prop()
    zip_path = DIST / f"{module_prop['id']}-v{module_prop['version']}{suffix}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(MODULE.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(MODULE).as_posix())
    return zip_path


def main() -> None:
    clean_output()
    generate_fonts(include_compat_fallbacks=True)
    print(make_zip())

    shutil.rmtree(MODULE_FONTS)
    MODULE_FONTS.mkdir(parents=True, exist_ok=True)
    generate_fonts(include_compat_fallbacks=False)
    DISABLE_FLAG.write_text("", encoding="utf-8")
    print(make_zip("-safe-disabled"))
    DISABLE_FLAG.unlink()


if __name__ == "__main__":
    main()
