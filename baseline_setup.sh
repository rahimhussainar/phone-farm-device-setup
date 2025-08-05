#!/usr/bin/env bash
apk_super="super_proxy.apk"
apk_tiktok="tiktok.apk"

for dev in $(adb devices | awk 'NR>1 && $2=="device"{print $1}'); do
  echo "—— $dev ———————————————"
  adb -s $dev install $apk_super
  adb -s $dev install $apk_tiktok

  adb -s $dev shell settings put global bluetooth_on 0
  adb -s $dev shell settings put secure always_on_vpn_app com.super.proxy
  adb -s $dev shell settings put secure always_on_vpn_lockdown 1
  adb -s $dev shell settings put global auto_update_apps 0
  adb -s $dev shell pm disable-user --user 0 com.google.android.factoryota >/dev/null 2>&1
  adb -s $dev reboot
done
