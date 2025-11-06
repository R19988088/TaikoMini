[app]
title = TaikoMini
package.name = taikomini
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,jpeg,gif,wav,ogg,ttf,txt,json,kv,ini,bat,spec,ico,mp3,tja
version = 0.1
requirements = python3,pygame,numpy,plyer,android
orientation = landscape
fullscreen = 1
android.api = 34
android.build_tools_version = 34.0.0
android.ndk_version = 25b
android.minapi = 21
android.archs = arm64-v8a
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,VIBRATE

[buildozer]
log_level = 2
warn_on_root = 1
android.release_key_store =
android.release_key_store_password =
android.release_key_alias =
android.release_key_alias_password =
