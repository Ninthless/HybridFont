ui_print "- Hybrid Font: Noto Sans SC + Inter"
ui_print "- Latin fonts are mapped to Inter"
ui_print "- Simplified Chinese fallbacks are mapped to Noto Sans SC"
ui_print "- Android font XML files are mapped during installation"
ui_print "- Reboot after installation"

[ -f "$MODPATH/fonts.xml" ] || abort "! Missing fonts.xml"

copy_font_xmls() {
  src_dir="$1"
  mod_subdir="$2"

  for path in "$src_dir"/font*.xml; do
    [ -f "$path" ] || continue
    name="$(basename "$path")"
    [ "$name" = "fonts_customization.xml" ] && continue
    mkdir -p "$MODPATH/system/$mod_subdir"
    cp -f "$MODPATH/fonts.xml" "$MODPATH/system/$mod_subdir/$name"
    ui_print "- mapped $mod_subdir/$name"
  done
}

copy_font_xmls "/system/system_ext/etc" "system_ext/etc"
copy_font_xmls "/system/product/etc" "product/etc"
copy_font_xmls "/system/etc" "etc"

set_perm_recursive "$MODPATH/system" 0 0 0755 0644
set_perm_recursive "$MODPATH/licenses" 0 0 0755 0644
[ -f "$MODPATH/fonts.xml" ] && set_perm "$MODPATH/fonts.xml" 0 0 0644
