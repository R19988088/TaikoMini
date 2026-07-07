[app]
title = TaikoMini
package.name = taikomini
package.domain = org.taikomini
source.dir = .
source.include_exts = py,png,jpg,jpeg,gif,tif,wav,ogg,ttf,txt,json,kv,ini,mp3,tja
source.exclude_dirs = songs,.git,__pycache__,.buildozer,bin
source.exclude_patterns = */__pycache__/*,*.pyc
version = 0.1
requirements = python3,pygame==2.5.2,plyer,android
orientation = landscape
fullscreen = 1
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_AUDIO,READ_MEDIA_IMAGES,VIBRATE
android.api = 34
android.build_tools_version = 34.0.0
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 0


