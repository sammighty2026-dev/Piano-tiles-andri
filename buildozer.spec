[app]
title = Mighty’s Tiles
package.name = pianotiles
package.domain = com.samuelkpakpo 
source.dir = .
source.include_exts = py,png,jpg,ttf,wav,ogg
version = 1.0
requirements = python3==3.10.10,hostpython3==3.10.10,pygame==2.1.0
orientation = portrait
android.release_artifact = aab
fullscreen = 1
icon.filename = icon.png
presplash.filename = presplash.png
android.presplash_color = #12121C
android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.ndk = 25b
android.ndk_api = 21
android.accept_sdk_license = True
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
