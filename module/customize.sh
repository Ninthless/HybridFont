ui_print "- Hybrid Font: Noto Sans SC + Inter"
ui_print "- Latin fonts are mapped to Inter"
ui_print "- Simplified Chinese fallbacks are mapped to Noto Sans SC"
ui_print "- Android font XML files are not mounted by this package"
ui_print "- Reboot after installation"

set_perm_recursive "$MODPATH/system" 0 0 0755 0644
set_perm_recursive "$MODPATH/licenses" 0 0 0755 0644
[ -f "$MODPATH/fonts.xml" ] && set_perm "$MODPATH/fonts.xml" 0 0 0644
