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
