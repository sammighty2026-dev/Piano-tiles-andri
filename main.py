import os
import sys
import textwrap
import traceback


def save_log(tb):
    base = os.environ.get("ANDROID_PRIVATE", ".")
    f = open(os.path.join(base, "crash.log"), "w")
    f.write(tb)
    f.close()


def show_error(tb):
    import pygame
    if not pygame.get_init():
        pygame.init()
    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    w, h = screen.get_size()
    size = max(14, w // 34)
    font = pygame.font.Font(None, size)
    chars = max(10, int(w / (font.size("M")[0] * 0.6)))
    lines = ["GAME CRASHED - screenshot this", ""]
    for raw in tb.splitlines():
        lines.extend(textwrap.wrap(raw, chars) or [""])
    line_h = font.get_linesize()
    offset = 0
    max_off = max(0, len(lines) * line_h - h + 20)
    clock = pygame.time.Clock()
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return
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


try:
    import game
except SystemExit:
    pass
except BaseException:
    tb = traceback.format_exc()
    try:
        save_log(tb)
    except Exception:
        pass
    show_error(tb)
