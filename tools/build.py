from __future__ import annotations

import base64
import shutil
import urllib.request
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.varLib.instancer import OverlapMode


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "module"
DOWNLOADS = ROOT / "build" / "downloads"
GENERATED = ROOT / "build" / "generated-fonts"
DIST = ROOT / "dist"
MODULE_FONTS = MODULE / "system" / "fonts"
MODULE_LICENSES = MODULE / "licenses"
DISABLE_FLAG = MODULE / "disable"
MODULE_PROP = MODULE / "module.prop"
MODULE_FONT_XML = MODULE / "fonts.xml"

INTER_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf"
INTER_ITALIC_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter-Italic%5Bopsz%2Cwght%5D.ttf"
NOTO_SC_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf"
INTER_LICENSE_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/OFL.txt"
NOTO_SC_LICENSE_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/OFL.txt"
AOSP_FONT_XML_URL = "https://android.googlesource.com/platform/frameworks/base/+/refs/tags/android-15.0.0_r3/data/fonts/font_fallback.xml?format=TEXT"

INTER_WEIGHTS = {
    "Thin": 100,
    "ExtraLight": 200,
    "Light": 300,
    "Regular": 400,
    "Medium": 500,
    "SemiBold": 600,
    "Bold": 700,
    "ExtraBold": 800,
    "Black": 900,
}

CJK_WEIGHTS = {
    "Thin": 100,
    "ExtraLight": 200,
    "Light": 300,
    "DemiLight": 350,
    "Regular": 400,
    "Medium": 500,
    "SemiBold": 600,
    "Bold": 700,
    "ExtraBold": 800,
    "Black": 900,
}

CJK_SC_ALIASES = {
    "Thin": ["NotoSansCJKsc-Thin.otf"],
    "ExtraLight": ["NotoSansCJKsc-ExtraLight.otf"],
    "Light": ["NotoSansCJKsc-Light.otf"],
    "DemiLight": ["NotoSansCJKsc-DemiLight.otf"],
    "Regular": ["NotoSansCJKsc-Regular.otf", "DroidSansFallback.ttf", "DroidSansFallbackFull.ttf"],
    "Medium": ["NotoSansCJKsc-Medium.otf"],
    "SemiBold": ["NotoSansCJKsc-SemiBold.otf"],
    "Bold": ["NotoSansCJKsc-Bold.otf"],
    "ExtraBold": ["NotoSansCJKsc-ExtraBold.otf"],
    "Black": ["NotoSansCJKsc-Black.otf"],
}

CUSTOM_CJK_FILES = {
    100: "100.ttf",
    200: "200.ttf",
    300: "300.ttf",
    350: "350.ttf",
    400: "400.ttf",
    500: "500.ttf",
    600: "600.ttf",
    700: "700.ttf",
    800: "800.ttf",
    900: "900.ttf",
}

ROBOTO_STYLE_FILES = {
    "Thin": "Roboto-Thin.ttf",
    "ExtraLight": "Roboto-ExtraLight.ttf",
    "Light": "Roboto-Light.ttf",
    "Regular": "Roboto-Regular.ttf",
    "Medium": "Roboto-Medium.ttf",
    "SemiBold": "Roboto-SemiBold.ttf",
    "Bold": "Roboto-Bold.ttf",
    "ExtraBold": "Roboto-ExtraBold.ttf",
    "Black": "Roboto-Black.ttf",
}

COLOROS_ALIASES = [
    "Roboto",
    "roboto",
    "One Sans",
    "OneSans",
    "one-sans",
    "OnePlus Sans",
    "OnePlusSans",
    "oneplus-sans",
    "OPPO Sans",
    "OPPOSans",
    "oppo-sans",
    "OPlus Sans",
    "OPlusSans",
    "oplus-sans",
    "ColorOS Sans",
    "ColorOSSans",
    "coloros-sans",
]


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


def download_base64(url: str, target: Path) -> None:
    if target.exists() and target.stat().st_size > 0:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response:
        target.write_bytes(base64.b64decode(response.read()))


def rename_font(font: TTFont, family: str, subfamily: str, full_name: str, postscript: str) -> None:
    for name in font["name"].names:
        value = None
        if name.nameID in (1, 16):
            value = family
        elif name.nameID in (2, 17):
            value = subfamily
        elif name.nameID == 4:
            value = full_name
        elif name.nameID == 6:
            value = postscript
        if value is not None:
            font["name"].setName(value, name.nameID, name.platformID, name.platEncID, name.langID)


def instantiate_variable(
    source: Path,
    target: Path,
    axes: dict[str, int | float],
    family: str,
    style_name: str,
    postscript: str,
    remove_overlap: bool = False,
) -> None:
    if target.exists() and target.stat().st_size > 0:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    font = TTFont(source)
    overlap = OverlapMode.REMOVE_AND_IGNORE_ERRORS if remove_overlap else OverlapMode.KEEP_AND_SET_FLAGS
    static_font = instancer.instantiateVariableFont(font, axes, inplace=False, overlap=overlap)
    rename_font(static_font, family, style_name, f"{family} {style_name}", postscript)
    static_font.save(target)
    static_font.close()
    font.close()


def clean_output() -> None:
    if MODULE_FONTS.exists():
        shutil.rmtree(MODULE_FONTS)
    module_etc = MODULE / "system" / "etc"
    if module_etc.exists():
        shutil.rmtree(module_etc)
    if MODULE_LICENSES.exists():
        shutil.rmtree(MODULE_LICENSES)
    if GENERATED.exists():
        shutil.rmtree(GENERATED)
    if DIST.exists():
        try:
            shutil.rmtree(DIST)
        except PermissionError as error:
            raise SystemExit(f"Cannot clean dist because a package is open: {error.filename}") from error
    if MODULE_FONT_XML.exists():
        MODULE_FONT_XML.unlink()
    if DISABLE_FLAG.exists():
        DISABLE_FLAG.unlink()
    MODULE_FONTS.mkdir(parents=True, exist_ok=True)
    MODULE_LICENSES.mkdir(parents=True, exist_ok=True)
    DIST.mkdir(parents=True, exist_ok=True)


def copy_file(source: Path, target_dir: Path, name: str) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target_dir / name)


def font_element(file_name: str, weight: int, style: str = "normal") -> ElementTree.Element:
    font = ElementTree.Element("font", {"weight": str(weight), "style": style})
    font.text = file_name
    return font


def inter_xml_fonts() -> list[ElementTree.Element]:
    fonts: list[ElementTree.Element] = []
    for style_name, weight in INTER_WEIGHTS.items():
        normal_file = ROBOTO_STYLE_FILES[style_name]
        fonts.append(font_element(normal_file, weight))
        fonts.append(font_element(normal_file.replace(".ttf", "Italic.ttf"), weight, "italic"))
    fonts.append(font_element("Roboto-Regular.ttf", 350))
    fonts.append(font_element("Roboto-Italic.ttf", 350, "italic"))
    return fonts


def cjk_xml_fonts() -> list[ElementTree.Element]:
    return [font_element(file_name, weight) for weight, file_name in CUSTOM_CJK_FILES.items()]


def replace_sans_serif(root: ElementTree.Element) -> None:
    for family in root.findall("family"):
        if family.get("name") == "sans-serif":
            family.clear()
            family.set("name", "sans-serif")
            family.extend(inter_xml_fonts())
            return
    family = ElementTree.Element("family", {"name": "sans-serif"})
    family.extend(inter_xml_fonts())
    root.insert(0, family)


def replace_zh_hans(root: ElementTree.Element) -> None:
    serif_fonts: list[ElementTree.Element] = []
    target: ElementTree.Element | None = None
    for family in root.findall("family"):
        langs = [part.strip() for part in family.get("lang", "").split(",")]
        if "zh-Hans" in langs:
            target = family
            for font in family.findall("font"):
                if font.get("fallbackFor") == "serif":
                    serif_fonts.append(font)
            break
    if target is None:
        target = ElementTree.Element("family")
        root.append(target)
    target.clear()
    target.set("lang", "zh-Hans,zh-CN")
    target.extend(cjk_xml_fonts())
    target.extend(serif_fonts)


def add_coloros_aliases(root: ElementTree.Element) -> None:
    existing = {alias.get("name") for alias in root.findall("alias")}
    for name in COLOROS_ALIASES:
        if name in existing:
            continue
        root.append(ElementTree.Element("alias", {"name": name, "to": "sans-serif"}))


def write_font_xml() -> None:
    source = DOWNLOADS / "font_fallback.xml"
    download_base64(AOSP_FONT_XML_URL, source)
    tree = ElementTree.parse(source)
    root = tree.getroot()
    replace_sans_serif(root)
    replace_zh_hans(root)
    add_coloros_aliases(root)
    ElementTree.indent(tree, space="    ")
    tree.write(MODULE_FONT_XML, encoding="utf-8", xml_declaration=True)


def generate_fonts(output_dir: Path, include_compat_fallbacks: bool) -> None:
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
        instantiate_variable(inter, upright, {"opsz": 14, "wght": weight}, "Inter", name, f"Inter-{name}")
        instantiate_variable(inter_italic, italic, {"opsz": 14, "wght": weight}, "Inter", f"{name} Italic", f"Inter-{name}Italic")
        inter_generated[name] = upright
        inter_italic_generated[name] = italic

    for name, weight in CJK_WEIGHTS.items():
        target = GENERATED / "noto-sans-sc" / f"NotoSansSC-{name}.ttf"
        instantiate_variable(noto_sc, target, {"wght": weight}, "Noto Sans SC", name, f"NotoSansSC-{name}", remove_overlap=True)
        cjk_generated[name] = target

    for name in INTER_WEIGHTS:
        normal_file = ROBOTO_STYLE_FILES[name]
        copy_file(inter_generated[name], output_dir, normal_file)
        copy_file(inter_italic_generated[name], output_dir, normal_file.replace(".ttf", "Italic.ttf"))

    for weight, file_name in CUSTOM_CJK_FILES.items():
        weight_name = next(name for name, value in CJK_WEIGHTS.items() if value == weight)
        copy_file(cjk_generated[weight_name], output_dir, file_name)

    for weight_name, aliases in CJK_SC_ALIASES.items():
        for alias in aliases:
            if not include_compat_fallbacks and alias.startswith("DroidSansFallback"):
                continue
            copy_file(cjk_generated[weight_name], output_dir, alias)

    copy_file(noto_sc, output_dir, "NotoSansCJK-VF.ttf")
    copy_file(noto_sc, output_dir, "NotoSansCJKsc-VF.ttf")


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
    generate_fonts(MODULE_FONTS, include_compat_fallbacks=True)
    write_font_xml()
    print(make_zip())

    shutil.rmtree(MODULE_FONTS)
    MODULE_FONTS.mkdir(parents=True, exist_ok=True)
    generate_fonts(MODULE_FONTS, include_compat_fallbacks=False)
    write_font_xml()
    DISABLE_FLAG.write_text("", encoding="utf-8")
    print(make_zip("-safe-disabled"))
    DISABLE_FLAG.unlink()


if __name__ == "__main__":
    main()
