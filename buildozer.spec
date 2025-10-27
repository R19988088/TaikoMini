[app]

# (str) Title of your application
title = TaikoMini

# (str) Package name
package.name = taikomini

# (str) Package domain (needed for android/ios packaging)
package.domain = org.taikomini

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,jpeg,ttf,wav,ogg,tif,json,ini

# (list) List of inclusions using pattern matching
source.include_patterns = lib/*,res/*

# (list) List of directory to exclude (let empty to not exclude anything)
source.exclude_dirs = .git,.github,__pycache__,build,bin,venv

# (str) Application versioning
version = 1.0.0

# (list) Application requirements
requirements = python3,pygame==2.6.1,setuptools,six

# (list) Supported orientations
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1

# (list) Permissions
android.permissions = INTERNET,READ_MEDIA_AUDIO,READ_MEDIA_IMAGES,READ_MEDIA_VIDEO,MANAGE_EXTERNAL_STORAGE,FOREGROUND_SERVICE,WAKE_LOCK

# (int) Target Android API
android.api = 34

# (int) Minimum API
android.minapi = 33

# (str) Android NDK version to use
android.ndk = 26b

# (bool) Automatically accept SDK license
android.accept_sdk_license = True

# (bool) Enable AndroidX support
android.enable_androidx = True

# (list) add java compile options
android.add_compile_options = "sourceCompatibility = 11", "targetCompatibility = 11"

# (list) Put these files or directories in the apk res directory.
android.add_resources = res/xml/data_extraction_rules.xml:xml/data_extraction_rules.xml,res/xml/backup_rules.xml:xml/backup_rules.xml

# (str) Custom Android manifest template
android.manifest_xml = ./android_manifest.xml

# (list) The Android archs to build for
android.archs = arm64-v8a

# (bool) enables Android auto backup feature
android.allow_backup = True

# (str) Custom backup rules
android.backup_rules = @xml/backup_rules

# (str) Release keystore configuration (passwords from env)
android.release_keystore = %(source.dir)s/keystore/release.keystore
android.release_keyalias = %(env.ANDROID_KEY_ALIAS)s
android.release_keystore_password = %(env.ANDROID_KEYSTORE_PASSWORD)s
android.release_keyalias_password = %(env.ANDROID_KEY_ALIAS_PASSWORD)s

# (str) Python-for-android bootstrap to use
p4a.bootstrap = sdl2

# (str) Extra arguments passed to python-for-android
p4a.extra_args = --gradle-args="-Xmx6g -Xms3g"

[buildozer]

# (int) Log level (0 = error, 1 = info, 2 = debug)
log_level = 1

# (bool) Warn if buildozer is run as root
warn_on_root = 1

# (str) Path to build artifact storage
build_dir = .buildozer

# (str) Path to build output storage
bin_dir = bin
