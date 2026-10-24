import os
import sys
import textwrap
import traceback
import faulthandler

BASE = os.environ.get("ANDROID_PRIVATE", ".")
NATIVE = os.path.join(BASE, "native.log")
SEEN = []


def show_text(text):
    import pygame
    if not pygame.get_init():
        pygame.init()
    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    w, h = screen.get_size()
    font = pygame.font.Font(None, max(14, w // 34))
    chars = max(10, int(w / (font.size("M")[0] * 0.6)))
    lines = ["DEBUG INFO - screenshot this", ""]
    for raw in text.splitlines():
        lines.extend(textwrap.wrap(raw, chars) or [""])
    line_h = font.get_linesize()
    offset = 0
    max_off = max(0, len(lines) * line_h - h + 20)
    clock = pygame.time.Clock()
    while True:
        for e in pygame.event.get():
            if e.type == pygame.MOUSEMOTION and e.buttons[0]:
                offset = min(max(0, offset - e.rel[1]), max_off)
        screen.fill((20, 0, 0))
        y = 10 - offset
        for i, line in enumerate(lines):
            if -line_h < y < h:
                color = (255, 255, 255)
                if i == 0:
                    color = (255, 220, 80)
                screen.blit(font.render(line, True, color), (8, y))
            y += line_h
        pygame.display.flip()
        clock.tick(30)


def describe(mod):
    lines = ["Game ended normally (no error)."]
    path = getattr(mod, "__file__", None)
    lines.append("game file: " + str(path))
    try:
        data = open(path).read()
        lines.append("size: " + str(len(data)) + " chars, " + str(len(data.splitlines())) + " lines")
        lines.append("last line: " + data.strip().splitlines()[-1])
    except Exception as e:
        lines.append("could not read game file: " + repr(e))
    lines.append("has running var: " + str(hasattr(mod, "running")))
    lines.append("running = " + str(getattr(mod, "running", "n/a")))
    lines.append("state = " + str(getattr(mod, "state", "n/a")))
    lines.append("cwd: " + os.getcwd())
    try:
        lines.append("files: " + ", ".join(sorted(os.listdir(os.getcwd()))))
    except Exception as e:
        lines.append("listdir failed: " + repr(e))
    return "\n".join(lines)


def start_spy():
    import pygame
    original = pygame.event.get

    def spy(*args, **kwargs):
        events = original(*args, **kwargs)
        for e in events:
            if len(SEEN) < 40:
                SEEN.append(pygame.event.event_name(e.type))
        return events

    pygame.event.get = spy


# 1) If the last run crashed natively, show that first.
old = ""
if os.path.exists(NATIVE):
    old = open(NATIVE).read()
if old.strip():
    open(NATIVE, "w").close()
    show_text("LAST RUN CRASHED:\n" + old)

# 2) Watch for native crashes during this run.
native_file = open(NATIVE, "w")
faulthandler.enable(file=native_file, all_threads=True)

# 3) Run the game and report how it ended.
result = ""
try:
    start_spy()
    import game
    result = describe(game)
except SystemExit:
    result = "Game called exit (SystemExit)."
except BaseException:
    result = traceback.format_exc()

show_text(result + "\n\nEvents seen: " + ", ".join(SEEN))
