import pygame
import random
import sys
import array
import math
import os

# ========== ANDROID STORAGE HELPER ==========
def get_storage_path():
    """Returns a writable path that works on both PC and Android"""
    if 'ANDROID_PRIVATE' in os.environ:
        return os.environ['ANDROID_PRIVATE']
    # Fallback for older p4a / testing
    try:
        from android.storage import app_storage_path
        return app_storage_path()
    except:
        pass
    return "."   # PC / fallback

STORAGE = get_storage_path()
print("Storage path:", STORAGE)

# ========== INIT ==========
try:
    pygame.init()
    pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
    AUDIO_AVAILABLE = True
except Exception as e:
    print(f"Warning: Audio/Mixer failed: {e}")
    AUDIO_AVAILABLE = False

# ========== AUDIO & GAME MODES ==========
audio_enabled = True
sfx_volume = 0.55
bg_volume = 0.04
game_mode = "classic"
difficulty = 1
diff_names = ["Easy", "Normal", "Hard", "Insane"]
scale_mode = 0
scale_names = ["Major", "Pentatonic", "Minor"]

scales = [
    [523.25, 587.33, 659.25, 698.46, 783.99, 880.00, 987.77, 1046.50],
    [523.25, 587.33, 659.25, 783.99, 880.00, 1046.50, 1174.66, 1318.51],
    [493.88, 523.25, 622.25, 698.46, 740.00, 830.61, 932.33, 987.77]
]

def make_piano_note(frequency=440, duration=0.22, volume=0.5):
    if not AUDIO_AVAILABLE:
        return None
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    buf = array.array('h', [0] * n_samples)
    max_amp = 2**15 - 1
    for i in range(n_samples):
        t = i / sample_rate
        wave = (
            math.sin(2 * math.pi * frequency * t) * 1.0 +
            math.sin(2 * math.pi * frequency * 2 * t) * 0.4 +
            math.sin(2 * math.pi * frequency * 3 * t) * 0.2
        )
        envelope = math.exp(-11.0 * t)
        value = volume * max_amp * envelope * wave
        buf[i] = int(max(-32768, min(32767, value)))
    return pygame.mixer.Sound(buffer=buf)

def make_beep(frequency=440, duration=0.09, volume=0.4):
    if not AUDIO_AVAILABLE:
        return None
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    buf = array.array('h', [0] * n_samples)
    max_amp = 2**15 - 1
    for i in range(n_samples):
        t = i / sample_rate
        fade = 1.0
        if i < n_samples * 0.1:
            fade = i / (n_samples * 0.1)
        elif i > n_samples * 0.7:
            fade = (n_samples - i) / (n_samples * 0.3)
        value = volume * max_amp * fade * math.sin(2 * math.pi * frequency * t)
        buf[i] = int(value)
    return pygame.mixer.Sound(buffer=buf)

def make_bg_loop(volume=0.15):
    if not AUDIO_AVAILABLE:
        return None
    sample_rate = 22050
    duration = 3.0
    n_samples = int(sample_rate * duration)
    buf = array.array('h', [0] * n_samples)
    max_amp = 2**15 - 1
    for i in range(n_samples):
        t = i / sample_rate
        wave1 = math.sin(2 * math.pi * 98 * t)
        wave2 = math.sin(2 * math.pi * 130 * t) * 0.4
        value = volume * max_amp * (wave1 + wave2) * 0.7
        buf[i] = int(value)
    return pygame.mixer.Sound(buffer=buf)

hit_sounds = []
def update_hit_sounds():
    global hit_sounds
    freqs = scales[scale_mode]
    hit_sounds = [make_piano_note(frequency=freq, duration=0.22, volume=sfx_volume) for freq in freqs]

update_hit_sounds()
fail_sound = make_beep(frequency=165, duration=0.28, volume=sfx_volume)
bg_tone = make_bg_loop(volume=bg_volume)

def play_sound(snd):
    if AUDIO_AVAILABLE and audio_enabled and snd is not None:
        snd.set_volume(sfx_volume)
        snd.play()

def play_bg():
    if AUDIO_AVAILABLE and audio_enabled and bg_tone is not None:
        bg_tone.set_volume(bg_volume)
        bg_tone.play(loops=-1)

def stop_bg():
    if AUDIO_AVAILABLE and bg_tone is not None:
        bg_tone.stop()

def update_volumes():
    global fail_sound, bg_tone
    update_hit_sounds()
    fail_sound = make_beep(frequency=165, duration=0.28, volume=sfx_volume)
    bg_tone = make_bg_loop(volume=bg_volume)

# ========== FILES (Android-safe) ==========
HS_FILE = os.path.join(STORAGE, "piano_highscore.txt")
HS_TA_FILE = os.path.join(STORAGE, "piano_highscore_timeattack.txt")
ACH_FILE = os.path.join(STORAGE, "piano_achievements.txt")
STATS_FILE = os.path.join(STORAGE, "piano_stats.txt")

achievements = {
    "first_steps":   {"name": "First Steps",     "desc": "Score 10 points",                   "unlocked": False},
    "century_club":  {"name": "Century Club",    "desc": "Score 100 points",                  "unlocked": False},
    "combo_master":  {"name": "Combo Master",    "desc": "Reach x10 Combo",                   "unlocked": False},
    "speed_demon":   {"name": "Speed Demon",     "desc": "Play Time Attack mode",             "unlocked": False},
    "untouchable":   {"name": "Untouchable",     "desc": "Finish a run without using shield", "unlocked": False},
    "golden_rush":   {"name": "Golden Rush",     "desc": "Hit 8 golden tiles in one game",    "unlocked": False},
    "marathon":      {"name": "Marathon",        "desc": "Score 300 points",                  "unlocked": False},
    "fever":         {"name": "Fever",           "desc": "Reach x20 Combo",                   "unlocked": False},
    "survivor":      {"name": "Survivor",        "desc": "Survive 60 seconds in Time Attack", "unlocked": False},
}

stats = {
    "games_played": 0,
    "tiles_hit": 0,
    "lifetime_score": 0,
    "golden_hit": 0,
    "best_combo": 0
}

def load_highscore(filename):
    try:
        if os.path.exists(filename):
            with open(filename, "r") as f:
                return int(f.read().strip())
    except:
        pass
    return 0

def save_highscore(filename, value):
    try:
        with open(filename, "w") as f:
            f.write(str(value))
    except Exception as e:
        print("Save highscore error:", e)

def load_achievements():
    try:
        if os.path.exists(ACH_FILE):
            with open(ACH_FILE, "r") as f:
                for k in f.read().splitlines():
                    if k in achievements:
                        achievements[k]["unlocked"] = True
    except:
        pass

def save_achievements():
    try:
        with open(ACH_FILE, "w") as f:
            for k, v in achievements.items():
                if v["unlocked"]:
                    f.write(k + "\n")
    except Exception as e:
        print("Save achievements error:", e)

def load_stats():
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, "r") as f:
                lines = f.read().splitlines()
                if len(lines) >= 5:
                    stats["games_played"] = int(lines[0])
                    stats["tiles_hit"] = int(lines[1])
                    stats["lifetime_score"] = int(lines[2])
                    stats["golden_hit"] = int(lines[3])
                    stats["best_combo"] = int(lines[4])
    except:
        pass

def save_stats():
    try:
        with open(STATS_FILE, "w") as f:
            f.write(f"{stats['games_played']}\n{stats['tiles_hit']}\n{stats['lifetime_score']}\n{stats['golden_hit']}\n{stats['best_combo']}\n")
    except Exception as e:
        print("Save stats error:", e)

def unlock_achievement(key):
    if key in achievements and not achievements[key]["unlocked"]:
        achievements[key]["unlocked"] = True
        save_achievements()
        spawn_floating_text(f"UNLOCKED: {achievements[key]['name']}!", WIDTH // 2, HEIGHT // 4, color=GOLD)

def reset_highscores():
    global highscore, highscore_ta, achievements, stats
    highscore = 0
    highscore_ta = 0
    save_highscore(HS_FILE, 0)
    save_highscore(HS_TA_FILE, 0)
    for k in achievements:
        achievements[k]["unlocked"] = False
    if os.path.exists(ACH_FILE):
        try:
            os.remove(ACH_FILE)
        except:
            pass
    stats = {"games_played": 0, "tiles_hit": 0, "lifetime_score": 0, "golden_hit": 0, "best_combo": 0}
    save_stats()

highscore = load_highscore(HS_FILE)
highscore_ta = load_highscore(HS_TA_FILE)
load_achievements()
load_stats()

# ========== THEMES ==========
themes = [
    {"name": "Classic", "bg": (248, 248, 252), "tile": (25, 25, 30), "line": (210, 210, 220),
     "text": (15, 15, 20), "particle": [(0, 220, 120), (50, 255, 180), (180, 255, 220), (255, 255, 255)]},
    {"name": "Dark", "bg": (18, 18, 24), "tile": (230, 230, 240), "line": (50, 50, 65),
     "text": (240, 240, 250), "particle": [(100, 200, 255), (180, 220, 255), (255, 255, 255)]},
    {"name": "Neon", "bg": (10, 10, 20), "tile": (0, 255, 200), "line": (40, 40, 70),
     "text": (0, 255, 220), "particle": [(255, 0, 150), (0, 255, 255), (255, 50, 200), (255, 255, 255)]},
    {"name": "Sunset", "bg": (35, 18, 28), "tile": (255, 130, 50), "line": (70, 35, 45),
     "text": (255, 220, 190), "particle": [(255, 90, 40), (255, 160, 70), (255, 210, 120), (255, 240, 180)]},
    {"name": "Cyberpunk", "bg": (8, 4, 22), "tile": (255, 0, 140), "line": (35, 15, 55),
     "text": (0, 255, 255), "particle": [(255, 0, 255), (0, 255, 255), (255, 40, 160), (160, 0, 255)]}
]

current_theme = 0
state = "menu"

# ========== SCREEN ==========
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
clock = pygame.time.Clock()

RED = (230, 50, 50)
GOLD = (255, 200, 50)
WHITE = (255, 255, 255)
BLACK = (15, 15, 20)

COLS = 4
COL_WIDTH = WIDTH // COLS
TILE_HEIGHT = int(HEIGHT * 0.20)
TILE_WIDTH = int(COL_WIDTH * 0.72)

title_font = pygame.font.SysFont(None, int(HEIGHT * 0.065))
font = pygame.font.SysFont(None, int(HEIGHT * 0.045))
big_font = pygame.font.SysFont(None, int(HEIGHT * 0.075))
medium_font = pygame.font.SysFont(None, int(HEIGHT * 0.038))
small_font = pygame.font.SysFont(None, int(HEIGHT * 0.028))

particles = []
floating_texts = []
ripples = []
tiles = []
score = 0
combo = 0
speed = 6.0
shake_timer = 0
last_milestone_tier = 0
time_left = 45.0
has_shield = True
spawn_timer = 0
golden_this_run = 0
used_shield = False
time_survived = 0.0

DIFF_START_SPEED = [4.5, 6.0, 7.5, 9.5]
DIFF_ACCEL = [0.08, 0.12, 0.16, 0.22]
DIFF_GOLDEN = [0.18, 0.12, 0.08, 0.05]
DIFF_SHIELD = [True, True, True, False]

def get_dynamic_background(base_bg, score):
    if score < 100:
        return base_bg
    milestone_bgs = [(15, 32, 67), (55, 20, 75), (20, 65, 45), (85, 50, 15), (70, 20, 20)]
    tier = min((score - 100) // 50, len(milestone_bgs) - 1)
    return milestone_bgs[tier]

def spawn_particles(x, y, count=12, is_gold=False, big=False):
    colors = [(255, 215, 0), (255, 255, 100), (255, 165, 0), (255, 255, 255)] if is_gold else themes[current_theme]["particle"]
    for _ in range(count):
        angle = random.uniform(0, 6.28)
        speed_p = random.uniform(3.5, 11) if big else random.uniform(2.5, 8)
        life = random.randint(18, 32) if big else random.randint(14, 24)
        particles.append({
            "x": x, "y": y,
            "vx": math.cos(angle) * speed_p,
            "vy": math.sin(angle) * speed_p - (2 if big else 0),
            "life": life, "max_life": life,
            "color": random.choice(colors),
            "size": random.randint(3, 7) if big else random.randint(2, 5)
        })

def spawn_ripple(x, y):
    ripples.append({"x": x, "y": y, "radius": 5, "max_radius": 55, "alpha": 200})

def spawn_floating_text(text, x, y, color=GOLD):
    floating_texts.append({"text": text, "x": x, "y": y, "vy": -2.5, "life": 26, "color": color})

def end_game():
    global highscore, highscore_ta, state
    stop_bg()
    state = "game_over"
    stats["lifetime_score"] += score
    if combo > stats["best_combo"]:
        stats["best_combo"] = combo
    save_stats()

    if game_mode == "classic":
        if score > highscore:
            highscore = score
            save_highscore(HS_FILE, highscore)
        if not used_shield and score >= 30:
            unlock_achievement("untouchable")
    else:
        if score > highscore_ta:
            highscore_ta = score
            save_highscore(HS_TA_FILE, highscore_ta)
        if time_survived >= 60:
            unlock_achievement("survivor")

def start_game():
    global tiles, score, combo, speed, state, particles, floating_texts, ripples
    global shake_timer, last_milestone_tier, time_left, has_shield, spawn_timer
    global golden_this_run, used_shield, time_survived

    tiles = []
    score = 0
    combo = 0
    speed = DIFF_START_SPEED[difficulty]
    particles = []
    floating_texts = []
    ripples = []
    shake_timer = 0
    last_milestone_tier = 0
    time_left = 45.0 + (15 if difficulty == 0 else 0)
    has_shield = DIFF_SHIELD[difficulty]
    spawn_timer = 0
    golden_this_run = 0
    used_shield = False
    time_survived = 0.0

    stats["games_played"] += 1
    save_stats()

    if game_mode == "time_attack":
        unlock_achievement("speed_demon")

    for i in range(5):
        spawn_tile(i * TILE_HEIGHT - TILE_HEIGHT * 4)
    play_bg()
    state = "playing"

def spawn_tile(y_pos=None):
    col = random.randint(0, COLS - 1)
    y = y_pos if y_pos is not None else -TILE_HEIGHT
    is_golden = random.random() < DIFF_GOLDEN[difficulty]
    tiles.append({"col": col, "y": y, "golden": is_golden})

def get_button_rects():
    btn_w, btn_h = int(WIDTH * 0.58), int(HEIGHT * 0.055)
    cx = WIDTH // 2
    cy = HEIGHT // 2
    start_y = int(HEIGHT * 0.18)
    gap = int(HEIGHT * 0.065)

    return {
        "resume": pygame.Rect(cx - btn_w // 2, cy - btn_h - 70, btn_w, btn_h),
        "restart": pygame.Rect(cx - btn_w // 2, cy - 20, btn_w, btn_h),
        "home": pygame.Rect(cx - btn_w // 2, cy + 50, btn_w, btn_h),
        "pause_btn": pygame.Rect(WIDTH - 65, 15, 50, 40),
        "mode_toggle": pygame.Rect(cx - btn_w // 2, int(HEIGHT * 0.15), btn_w, btn_h),
        "diff_toggle": pygame.Rect(cx - btn_w // 2, int(HEIGHT * 0.22), btn_w, btn_h),
        "settings_btn": pygame.Rect(cx - btn_w // 2, int(HEIGHT * 0.82), btn_w, btn_h),
        "audio_toggle": pygame.Rect(cx - btn_w // 2, start_y, btn_w, btn_h),
        "sfx_vol": pygame.Rect(cx - btn_w // 2, start_y + gap, btn_w, btn_h),
        "bg_vol": pygame.Rect(cx - btn_w // 2, start_y + gap * 2, btn_w, btn_h),
        "scale_toggle": pygame.Rect(cx - btn_w // 2, start_y + gap * 3, btn_w, btn_h),
        "achievements_btn": pygame.Rect(cx - btn_w // 2, start_y + gap * 4, btn_w, btn_h),
        "stats_btn": pygame.Rect(cx - btn_w // 2, start_y + gap * 5, btn_w, btn_h),
        "reset_score": pygame.Rect(cx - btn_w // 2, start_y + gap * 6, btn_w, btn_h),
        "settings_back": pygame.Rect(cx - btn_w // 2, start_y + gap * 7, btn_w, btn_h),
        "achievements_back": pygame.Rect(cx - btn_w // 2, int(HEIGHT * 0.88), btn_w, btn_h),
        "stats_back": pygame.Rect(cx - btn_w // 2, int(HEIGHT * 0.88), btn_w, btn_h)
    }

def draw_menu():
    screen.fill((18, 18, 28))
    title = title_font.render("PIANO TILES", True, WHITE)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT * 0.04))

    rects = get_button_rects()

    mode_color = (50, 140, 200) if game_mode == "classic" else (200, 120, 40)
    pygame.draw.rect(screen, mode_color, rects["mode_toggle"], border_radius=14)
    pygame.draw.rect(screen, WHITE, rects["mode_toggle"], 2, border_radius=14)
    m_text = small_font.render(f"Mode: {game_mode.replace('_', ' ').title()}", True, WHITE)
    screen.blit(m_text, (rects["mode_toggle"].centerx - m_text.get_width() // 2,
                         rects["mode_toggle"].centery - m_text.get_height() // 2))

    diff_colors = [(80, 180, 80), (50, 140, 200), (200, 140, 40), (200, 50, 50)]
    pygame.draw.rect(screen, diff_colors[difficulty], rects["diff_toggle"], border_radius=14)
    pygame.draw.rect(screen, WHITE, rects["diff_toggle"], 2, border_radius=14)
    d_text = small_font.render(f"Difficulty: {diff_names[difficulty]}", True, WHITE)
    screen.blit(d_text, (rects["diff_toggle"].centerx - d_text.get_width() // 2,
                         rects["diff_toggle"].centery - d_text.get_height() // 2))

    subtitle = medium_font.render("Choose a Theme", True, (160, 160, 180))
    screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, HEIGHT * 0.29))

    button_h = int(HEIGHT * 0.055)
    start_y = int(HEIGHT * 0.35)
    gap = int(HEIGHT * 0.012)

    for i, theme in enumerate(themes):
        y = start_y + i * (button_h + gap)
        rect = pygame.Rect(int(WIDTH * 0.18), y, int(WIDTH * 0.64), button_h)
        pygame.draw.rect(screen, theme["tile"], rect, border_radius=14)
        pygame.draw.rect(screen, WHITE, rect, 2, border_radius=14)
        text_color = WHITE if theme["name"] in ["Classic", "Dark", "Cyberpunk"] else BLACK
        name = medium_font.render(theme["name"], True, text_color)
        screen.blit(name, (rect.centerx - name.get_width() // 2, rect.centery - name.get_height() // 2))

    pygame.draw.rect(screen, (50, 50, 70), rects["settings_btn"], border_radius=14)
    pygame.draw.rect(screen, WHITE, rects["settings_btn"], 2, border_radius=14)
    st_text = medium_font.render("Settings", True, WHITE)
    screen.blit(st_text, (rects["settings_btn"].centerx - st_text.get_width() // 2,
                          rects["settings_btn"].centery - st_text.get_height() // 2))

    active_hs = highscore if game_mode == "classic" else highscore_ta
    best = small_font.render(f"Best ({game_mode.title()}): {active_hs}", True, GOLD)
    screen.blit(best, (WIDTH // 2 - best.get_width() // 2, HEIGHT * 0.92))
