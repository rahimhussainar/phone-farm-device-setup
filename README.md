  Now when you run the commands:
  - START: adb shell am broadcast -n 
  com.doublespeed.proxy/.ProxyControlReceiver -a
  com.doublespeed.proxy.START
  - STOP: adb shell am broadcast -n 
  com.doublespeed.proxy.STOP

    You can now remotely configure the proxy settings using these ADB commands:

  Change individual settings:

  # Change proxy address only
  adb shell am broadcast -n com.doublespeed.proxy/.ProxyControlReceiver -a com.doublespeed.proxy.CONFIG --es proxy_address "192.168.1.100"

  # Change port only
  adb shell am broadcast -n com.doublespeed.proxy/.ProxyControlReceiver -a com.doublespeed.proxy.CONFIG --ei proxy_port 8080

  # Change username only
  adb shell am broadcast -n com.doublespeed.proxy/.ProxyControlReceiver -a com.doublespeed.proxy.CONFIG --es proxy_username "newuser"

  # Change password only
  adb shell am broadcast -n com.doublespeed.proxy/.ProxyControlReceiver -a com.doublespeed.proxy.CONFIG --es proxy_password "newpass"

  Change multiple settings at once:

  adb shell am broadcast -n com.doublespeed.proxy/.ProxyControlReceiver -a com.doublespeed.proxy.CONFIG --es proxy_address "192.53.65.133" --ei proxy_port 5134
   --es proxy_username "ihiupcnd" --es proxy_password "k9kfjqyq2bzw"