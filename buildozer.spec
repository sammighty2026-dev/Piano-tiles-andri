[app]
title = Piano Tiles
package.name = pianotiles
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,ttf,wav,ogg
version = 1.0
requirements = python3,pygame==2.1.0
orientation = portrait
fullscreen = 1
android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.accept_sdk_license = True
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
