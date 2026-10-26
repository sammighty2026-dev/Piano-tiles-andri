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

# The phone can open the audio device differently from what was requested
# (for example 44100 Hz stereo instead of 22050 Hz mono). Every sound is built for
# the settings the device really uses, so pitch and length stay correct.
MIX_RATE, MIX_CHANNELS = 22050, 1
if AUDIO_AVAILABLE:
    try:
        _spec = pygame.mixer.get_init()
        if _spec:
            MIX_RATE, MIX_CHANNELS = int(_spec[0]), int(_spec[2])
    except Exception:
        pass
print("Audio device:", MIX_RATE, "Hz,", MIX_CHANNELS, "channel(s)")

def to_sound(mono):
    if MIX_CHANNELS > 1:
        multi = array.array('h', [0]) * (len(mono) * MIX_CHANNELS)
        for c in range(MIX_CHANNELS):
            multi[c::MIX_CHANNELS] = mono
        mono = multi
    return pygame.mixer.Sound(buffer=mono)

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
    sample_rate = MIX_RATE
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
    return to_sound(buf)

def make_beep(frequency=440, duration=0.09, volume=0.4):
    if not AUDIO_AVAILABLE:
        return None
    sample_rate = MIX_RATE
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
    return to_sound(buf)

def make_bg_loop(volume=0.15):
    if not AUDIO_AVAILABLE:
        return None
    sample_rate = MIX_RATE
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
    return to_sound(buf)

# ========== 20 SOUND PACKS ==========
SAMPLE_RATE = MIX_RATE
TAU = 2 * math.pi

def _sin(f, t):
    return math.sin(TAU * f * t)

def _saw(f, t):
    return 2.0 * ((f * t) % 1.0) - 1.0

def _sq(f, t):
    return 1.0 if math.sin(TAU * f * t) >= 0 else -1.0

def _gate(t, d, attack=0.01, release=0.04):
    return min(1.0, t / attack) * min(1.0, max(0.0, (d - t) / release))

# (name, duration in seconds, wave function(frequency, time, duration))
sound_packs = [
    # Same note as the Kivy version: one octave lower, 0.5 s long, slow ring-out
    ("Soft Piano", 0.5, lambda f, t, d: 1.1 * (_sin(f / 2, t) + 0.4 * _sin(f, t) + 0.2 * _sin(1.5 * f, t)) * math.exp(-5 * t)),
    ("Piano", 0.22, lambda f, t, d: (_sin(f, t) + 0.4 * _sin(2 * f, t) + 0.2 * _sin(3 * f, t)) * math.exp(-11 * t)),
    ("E-Piano", 0.25, lambda f, t, d: math.sin(TAU * f * t + 1.6 * math.exp(-7 * t) * _sin(f, t)) * math.exp(-6 * t)),
    ("Organ", 0.25, lambda f, t, d: (_sin(f, t) + 0.5 * _sin(2 * f, t) + 0.33 * _sin(3 * f, t) + 0.25 * _sin(4 * f, t)) * 0.5 * _gate(t, d)),
    ("Bell", 0.35, lambda f, t, d: (_sin(f, t) + 0.6 * _sin(2.76 * f, t) + 0.4 * _sin(5.4 * f, t) + 0.25 * _sin(6.9 * f, t)) * 0.5 * math.exp(-7 * t)),
    ("Music Box", 0.3, lambda f, t, d: (_sin(2 * f, t) + 0.3 * _sin(4 * f, t)) * 0.8 * math.exp(-10 * t)),
    ("Marimba", 0.25, lambda f, t, d: (_sin(f, t) + 0.5 * _sin(4 * f, t) * math.exp(-30 * t)) * math.exp(-12 * t)),
    ("Xylophone", 0.2, lambda f, t, d: (_sin(f, t) + 0.5 * _sin(3 * f, t) + 0.3 * _sin(6 * f, t)) * 0.7 * math.exp(-20 * t)),
    ("Harp", 0.3, lambda f, t, d: _sin(f, t) * math.exp(-8 * t) + 0.5 * _sin(2 * f, t) * math.exp(-12 * t) + 0.3 * _sin(3 * f, t) * math.exp(-16 * t)),
    ("Guitar", 0.3, lambda f, t, d: 0.8 * sum(_sin(k * f, t) / k * math.exp(-(5 + 2 * k) * t) for k in range(1, 6))),
    ("Flute", 0.3, lambda f, t, d: (math.sin(TAU * f * t + 0.5 * math.sin(TAU * 5 * t)) + 0.2 * _sin(2 * f, t) + random.uniform(-0.04, 0.04)) * 0.8 * _gate(t, d, 0.04, 0.08)),
    ("Synth Saw", 0.25, lambda f, t, d: _saw(f, t) * 0.5 * math.exp(-4 * t) * _gate(t, d, 0.005, 0.04)),
    ("8-Bit", 0.15, lambda f, t, d: _sq(f, t) * 0.45 * _gate(t, d, 0.003, 0.05)),
    ("Bass", 0.25, lambda f, t, d: (_sin(f / 2, t) + 0.5 * _sin(f, t)) * math.exp(-8 * t)),
    ("Kalimba", 0.3, lambda f, t, d: _sin(f, t) * math.exp(-9 * t) + 0.25 * _sin(6 * f, t) * math.exp(-35 * t)),
    ("Glass", 0.35, lambda f, t, d: (_sin(f, t) + 0.5 * _sin(3 * f, t) + 0.3 * _sin(5 * f, t)) * 0.7 * (1 - math.exp(-t * 200)) * math.exp(-7 * t)),
    ("Vibraphone", 0.35, lambda f, t, d: (_sin(f, t) + 0.3 * _sin(4 * f, t)) * math.exp(-6 * t) * (0.8 + 0.2 * _sin(6, t))),
    ("Drum", 0.2, lambda f, t, d: _sin(f * 0.4 * (1 + 1.5 * math.exp(-25 * t)), t) * math.exp(-14 * t)),
    ("Bubble Pop", 0.15, lambda f, t, d: _sin(f * 0.5 * (1 + 6 * t), t) * math.exp(-18 * t)),
    ("Laser", 0.2, lambda f, t, d: _sin(f * (2.0 - 4 * t), t) * math.exp(-6 * t)),
    ("Coin", 0.25, lambda f, t, d: _sq(f if t < 0.07 else f * 1.5, t) * 0.4 * math.exp(-4 * t) * _gate(t, d, 0.002, 0.05)),
]

def make_note(pack_index, frequency, volume=0.5):
    if not AUDIO_AVAILABLE:
        return None
    name, duration, fn = sound_packs[pack_index]
    n_samples = int(SAMPLE_RATE * duration)
    buf = array.array('h', [0] * n_samples)
    max_amp = 2**15 - 1
    fade_len = 150
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        value = volume * max_amp * 0.7 * fn(frequency, t, duration)
        left = n_samples - i
        if left < fade_len:
            value *= left / fade_len
        buf[i] = int(max(-32768, min(32767, value)))
    return to_sound(buf)

def make_fail_sound():
    """Soft Piano uses the Kivy-style low buzz for misses; every other pack keeps the beep."""
    if sound_packs[sound_pack][0] != "Soft Piano":
        return make_beep(frequency=165, duration=0.28, volume=sfx_volume)
    if not AUDIO_AVAILABLE:
        return None
    n_samples = int(SAMPLE_RATE * 0.6)
    buf = array.array('h', [0] * n_samples)
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        sq = 1.0 if math.sin(TAU * 90 * t) > 0 else -1.0
        value = sfx_volume * 32767 * 0.8 * sq * math.exp(-3 * t)
        buf[i] = int(max(-32768, min(32767, value)))
    return to_sound(buf)

SOUND_FILE = os.path.join(STORAGE, "piano_sound_pack.txt")

def load_sound_pack():
    try:
        if os.path.exists(SOUND_FILE):
            with open(SOUND_FILE, "r") as f:
                v = int(f.read().strip())
                if 0 <= v < len(sound_packs):
                    return v
    except:
        pass
    return 0

def save_sound_pack(v):
    try:
        with open(SOUND_FILE, "w") as f:
            f.write(str(v))
    except Exception as e:
        print("Save sound pack error:", e)

sound_pack = load_sound_pack()

# ========== MELODIES (each correct tap plays the next note of a song) ==========
_SEMI = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5,
         "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}

def note_freq(name):
    # Songs are written an octave low; this lifts them into the same range as the scales
    letter, octave = name[:-1], int(name[-1])
    midi = 12 * (octave + 2) + _SEMI[letter]
    return 440.0 * 2 ** ((midi - 69) / 12)

songs = [
    ("Twinkle Twinkle", "C4 C4 G4 G4 A4 A4 G4 F4 F4 E4 E4 D4 D4 C4 G4 G4 F4 F4 E4 E4 D4 G4 G4 F4 F4 E4 E4 D4 C4 C4 G4 G4 A4 A4 G4 F4 F4 E4 E4 D4 D4 C4"),
    ("Birthday", "G4 G4 A4 G4 C5 B4 G4 G4 A4 G4 D5 C5 G4 G4 G5 E5 C5 B4 A4 F5 F5 E5 C5 D5 C5"),
    ("Jingle Bells", "E4 E4 E4 E4 E4 E4 E4 G4 C4 D4 E4 F4 F4 F4 F4 F4 E4 E4 E4 E4 E4 D4 D4 E4 D4 G4"),
    ("Ode to Joy", "E4 E4 F4 G4 G4 F4 E4 D4 C4 C4 D4 E4 E4 D4 D4 E4 E4 F4 G4 G4 F4 E4 D4 C4 C4 D4 E4 D4 C4 C4"),
    ("Mary's Lamb", "E4 D4 C4 D4 E4 E4 E4 D4 D4 D4 E4 G4 G4 E4 D4 C4 D4 E4 E4 E4 E4 D4 D4 E4 D4 C4"),
    ("Row Row Row", "C4 C4 C4 D4 E4 E4 D4 E4 F4 G4 C5 C5 C5 G4 G4 G4 E4 E4 E4 C4 C4 C4 G4 F4 E4 D4 C4"),
    ("London Bridge", "G4 A4 G4 F4 E4 F4 G4 D4 E4 F4 E4 F4 G4 G4 A4 G4 F4 E4 F4 G4 D4 G4 E4 C4"),
    ("Frere Jacques", "C4 D4 E4 C4 C4 D4 E4 C4 E4 F4 G4 E4 F4 G4 G4 A4 G4 F4 E4 C4 G4 A4 G4 F4 E4 C4 C4 G3 C4 C4 G3 C4"),
    ("Hot Cross Buns", "E4 D4 C4 E4 D4 C4 C4 C4 C4 C4 D4 D4 D4 D4 E4 D4 C4"),
    ("Old MacDonald", "G4 G4 G4 D4 E4 E4 D4 B4 B4 A4 A4 G4"),
    ("Silent Night", "G4 A4 G4 E4 G4 A4 G4 E4 D5 D5 B4 C5 C5 G4 A4 A4 C5 B4 A4 G4 A4 G4 E4 D5 D5 F5 D5 B4 C5 E5 C5 G4 E4 G4 F4 D4 C4"),
    ("Fur Elise", "E5 D#5 E5 D#5 E5 B4 D5 C5 A4 C4 E4 A4 B4 E4 G#4 B4 C5"),
]
melody_names = ["Scale", "Random"] + [s[0] for s in songs]   # 0 = Scale, 1 = Random, 2+ = songs

MELODY_FILE = os.path.join(STORAGE, "piano_melody.txt")

def load_melody():
    try:
        if os.path.exists(MELODY_FILE):
            with open(MELODY_FILE, "r") as f:
                v = int(f.read().strip())
                if 0 <= v < len(melody_names):
                    return v
    except:
        pass
    return 2   # Twinkle Twinkle

def save_melody(v):
    try:
        with open(MELODY_FILE, "w") as f:
            f.write(str(v))
    except Exception as e:
        print("Save melody error:", e)

melody_index = load_melody()
melody_seq = []
note_index = 0

def fit_text(font_obj, text, color, max_w):
    surf = font_obj.render(text, True, color)
    if surf.get_width() > max_w:
        k = max_w / surf.get_width()
        surf = pygame.transform.smoothscale(surf, (max(1, int(surf.get_width() * k)), max(1, int(surf.get_height() * k))))
    return surf

def update_melody_sounds():
    global melody_seq
    melody_seq = []
    if melody_index < 2:
        return
    notes = songs[melody_index - 2][1].split()
    cache = {}
    for n in notes:
        if n not in cache:
            cache[n] = make_note(sound_pack, note_freq(n), volume=sfx_volume)
    melody_seq = [cache[n] for n in notes]

hit_sounds = []
def update_hit_sounds():
    global hit_sounds
    freqs = scales[scale_mode]
    hit_sounds = [make_note(sound_pack, freq, volume=sfx_volume) for freq in freqs]
    update_melody_sounds()

def get_hit_sound():
    """Returns the sound for the next correct tap, based on the chosen melody."""
    global note_index
    snd = None
    if melody_index == 0 and hit_sounds:
        snd = hit_sounds[note_index % len(hit_sounds)]
    elif melody_index == 1 and hit_sounds:
        snd = random.choice(hit_sounds)
    elif melody_seq:
        snd = melody_seq[note_index % len(melody_seq)]
    note_index += 1
    return snd

def preview_melody():
    """Plays the first two notes of the chosen melody."""
    if not (AUDIO_AVAILABLE and audio_enabled):
        return
    if melody_index == 0:
        seq = hit_sounds[:2]
    elif melody_index == 1:
        seq = random.sample(hit_sounds, 2) if len(hit_sounds) >= 2 else []
    else:
        seq = melody_seq[:2]
    seq = [s for s in seq if s is not None]
    if not seq:
        return
    for s in seq:
        s.set_volume(sfx_volume)
    ch = seq[0].play()
    if ch is not None and len(seq) > 1:
        ch.queue(seq[1])

def preview_sound():
    """Plays a short two-note preview of the selected sound pack."""
    if AUDIO_AVAILABLE and audio_enabled and len(hit_sounds) >= 5 and hit_sounds[0] is not None:
        hit_sounds[0].set_volume(sfx_volume)
        hit_sounds[4].set_volume(sfx_volume)
        ch = hit_sounds[0].play()
        if ch is not None:
            ch.queue(hit_sounds[4])

update_hit_sounds()
fail_sound = make_fail_sound()
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
    fail_sound = make_fail_sound()
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
    global golden_this_run, used_shield, time_survived, note_index

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
    note_index = 0

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
        "sound_btn": pygame.Rect(cx - btn_w // 2, start_y + gap * 4, btn_w, btn_h),
        "melody_btn": pygame.Rect(cx - btn_w // 2, start_y + gap * 5, btn_w, btn_h),
        "achievements_btn": pygame.Rect(cx - btn_w // 2, start_y + gap * 6, btn_w, btn_h),
        "stats_btn": pygame.Rect(cx - btn_w // 2, start_y + gap * 7, btn_w, btn_h),
        "reset_score": pygame.Rect(cx - btn_w // 2, start_y + gap * 8, btn_w, btn_h),
        "settings_back": pygame.Rect(cx - btn_w // 2, start_y + gap * 9, btn_w, btn_h),
        "sounds_back": pygame.Rect(cx - btn_w // 2, int(HEIGHT * 0.88), btn_w, btn_h),
        "melodies_back": pygame.Rect(cx - btn_w // 2, int(HEIGHT * 0.88), btn_w, btn_h),
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

def draw_settings():
    screen.fill((18, 18, 28))
    title = title_font.render("SETTINGS", True, WHITE)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT * 0.04))

    rects = get_button_rects()

    toggle_color = (50, 180, 100) if audio_enabled else (180, 50, 50)
    pygame.draw.rect(screen, toggle_color, rects["audio_toggle"], border_radius=14)
    pygame.draw.rect(screen, WHITE, rects["audio_toggle"], 2, border_radius=14)
    audio_text = small_font.render("Sound: ON" if audio_enabled else "Sound: OFF", True, WHITE)
    screen.blit(audio_text, (rects["audio_toggle"].centerx - audio_text.get_width() // 2,
                             rects["audio_toggle"].centery - audio_text.get_height() // 2))

    pygame.draw.rect(screen, (80, 120, 200), rects["sfx_vol"], border_radius=14)
    pygame.draw.rect(screen, WHITE, rects["sfx_vol"], 2, border_radius=14)
    sfx_text = small_font.render(f"SFX Volume: {int(sfx_volume*100)}%", True, WHITE)
    screen.blit(sfx_text, (rects["sfx_vol"].centerx - sfx_text.get_width() // 2,
                           rects["sfx_vol"].centery - sfx_text.get_height() // 2))

    pygame.draw.rect(screen, (80, 120, 200), rects["bg_vol"], border_radius=14)
    pygame.draw.rect(screen, WHITE, rects["bg_vol"], 2, border_radius=14)
    bg_text = small_font.render(f"BG Volume: {int(bg_volume*100)}%", True, WHITE)
    screen.blit(bg_text, (rects["bg_vol"].centerx - bg_text.get_width() // 2,
                          rects["bg_vol"].centery - bg_text.get_height() // 2))

    pygame.draw.rect(screen, (80, 120, 200), rects["scale_toggle"], border_radius=14)
    pygame.draw.rect(screen, WHITE, rects["scale_toggle"], 2, border_radius=14)
    scale_text = small_font.render(f"Scale: {scale_names[scale_mode]}", True, WHITE)
    screen.blit(scale_text, (rects["scale_toggle"].centerx - scale_text.get_width() // 2,
                             rects["scale_toggle"].centery - scale_text.get_height() // 2))

    pygame.draw.rect(screen, (200, 120, 60), rects["sound_btn"], border_radius=14)
    pygame.draw.rect(screen, WHITE, rects["sound_btn"], 2, border_radius=14)
    pack_text = fit_text(small_font, f"Sound Pack: {sound_packs[sound_pack][0]}", WHITE, rects["sound_btn"].width - 24)
    screen.blit(pack_text, (rects["sound_btn"].centerx - pack_text.get_width() // 2,
                            rects["sound_btn"].centery - pack_text.get_height() // 2))

    pygame.draw.rect(screen, (60, 160, 160), rects["melody_btn"], border_radius=14)
    pygame.draw.rect(screen, WHITE, rects["melody_btn"], 2, border_radius=14)
    mel_text = fit_text(small_font, f"Melody: {melody_names[melody_index]}", WHITE, rects["melody_btn"].width - 24)
    screen.blit(mel_text, (rects["melody_btn"].centerx - mel_text.get_width() // 2,
                           rects["melody_btn"].centery - mel_text.get_height() // 2))

    pygame.draw.rect(screen, (150, 80, 200), rects["achievements_btn"], border_radius=14)
    pygame.draw.rect(screen, WHITE, rects["achievements_btn"], 2, border_radius=14)
    ach_text = small_font.render("Achievements", True, WHITE)
    screen.blit(ach_text, (rects["achievements_btn"].centerx - ach_text.get_width() // 2,
                           rects["achievements_btn"].centery - ach_text.get_height() // 2))

    pygame.draw.rect(screen, (50, 150, 180), rects["stats_btn"], border_radius=14)
    pygame.draw.rect(screen, WHITE, rects["stats_btn"], 2, border_radius=14)
    stats_btn_text = small_font.render("Lifetime Stats", True, WHITE)
    screen.blit(stats_btn_text, (rects["stats_btn"].centerx - stats_btn_text.get_width() // 2,
                                 rects["stats_btn"].centery - stats_btn_text.get_height() // 2))

    pygame.draw.rect(screen, (180, 60, 60), rects["reset_score"], border_radius=14)
    pygame.draw.rect(screen, WHITE, rects["reset_score"], 2, border_radius=14)
    reset_text = small_font.render("Reset Progress", True, WHITE)
    screen.blit(reset_text, (rects["reset_score"].centerx - reset_text.get_width() // 2,
                             rects["reset_score"].centery - reset_text.get_height() // 2))

    pygame.draw.rect(screen, (70, 70, 90), rects["settings_back"], border_radius=14)
    pygame.draw.rect(screen, WHITE, rects["settings_back"], 2, border_radius=14)
    back_text = small_font.render("Back", True, WHITE)
    screen.blit(back_text, (rects["settings_back"].centerx - back_text.get_width() // 2,
                            rects["settings_back"].centery - back_text.get_height() // 2))

def get_melody_rects():
    cols = 2
    left = int(WIDTH * 0.06)
    col_w = int(WIDTH * 0.43)
    gap_x = int(WIDTH * 0.02)
    top = int(HEIGHT * 0.11)
    box_h = int(HEIGHT * 0.088)
    gap_y = int(HEIGHT * 0.017)
    result = []
    for i in range(len(melody_names)):
        r, c = i // cols, i % cols
        result.append(pygame.Rect(left + c * (col_w + gap_x), top + r * (box_h + gap_y), col_w, box_h))
    return result

def draw_melodies():
    screen.fill((18, 18, 28))
    title = title_font.render("CHOOSE MELODY", True, GOLD)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT * 0.03))

    for i, rect in enumerate(get_melody_rects()):
        selected = (i == melody_index)
        pygame.draw.rect(screen, (50, 150, 90) if selected else (45, 45, 65), rect, border_radius=12)
        pygame.draw.rect(screen, GOLD if selected else (100, 100, 130), rect, 3 if selected else 2, border_radius=12)
        label = fit_text(small_font, melody_names[i], WHITE, rect.width - 16)
        screen.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))

    rects = get_button_rects()
    pygame.draw.rect(screen, (70, 70, 90), rects["melodies_back"], border_radius=14)
    pygame.draw.rect(screen, WHITE, rects["melodies_back"], 2, border_radius=14)
    back_text = medium_font.render("Back", True, WHITE)
    screen.blit(back_text, (rects["melodies_back"].centerx - back_text.get_width() // 2,
                            rects["melodies_back"].centery - back_text.get_height() // 2))

def get_sound_rects():
    cols = 2
    left = int(WIDTH * 0.06)
    col_w = int(WIDTH * 0.43)
    gap_x = int(WIDTH * 0.02)
    top = int(HEIGHT * 0.11)
    rows = (len(sound_packs) + cols - 1) // cols
    gap_y = int(HEIGHT * 0.010)
    box_h = int((HEIGHT * 0.74 - (rows - 1) * gap_y) / rows)
    result = []
    for i in range(len(sound_packs)):
        r, c = i // cols, i % cols
        result.append(pygame.Rect(left + c * (col_w + gap_x), top + r * (box_h + gap_y), col_w, box_h))
    return result

def draw_sounds():
    screen.fill((18, 18, 28))
    title = title_font.render("CHOOSE SOUND", True, GOLD)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT * 0.03))

    for i, rect in enumerate(get_sound_rects()):
        selected = (i == sound_pack)
        pygame.draw.rect(screen, (50, 150, 90) if selected else (45, 45, 65), rect, border_radius=12)
        pygame.draw.rect(screen, GOLD if selected else (100, 100, 130), rect, 3 if selected else 2, border_radius=12)
        label = fit_text(small_font, f"{i + 1}. {sound_packs[i][0]}", WHITE, rect.width - 16)
        screen.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))

    rects = get_button_rects()
    pygame.draw.rect(screen, (70, 70, 90), rects["sounds_back"], border_radius=14)
    pygame.draw.rect(screen, WHITE, rects["sounds_back"], 2, border_radius=14)
    back_text = medium_font.render("Back", True, WHITE)
    screen.blit(back_text, (rects["sounds_back"].centerx - back_text.get_width() // 2,
                            rects["sounds_back"].centery - back_text.get_height() // 2))

def draw_achievements():
    screen.fill((18, 18, 28))
    title = title_font.render("ACHIEVEMENTS", True, GOLD)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT * 0.04))

    start_y = int(HEIGHT * 0.12)
    box_h = int(HEIGHT * 0.075)
    gap = int(HEIGHT * 0.012)

    for i, (k, ach) in enumerate(achievements.items()):
        y = start_y + i * (box_h + gap)
        if y + box_h > HEIGHT * 0.85:
            break
        rect = pygame.Rect(int(WIDTH * 0.08), y, int(WIDTH * 0.84), box_h)
        bg_col = (40, 70, 50) if ach["unlocked"] else (40, 40, 55)
        pygame.draw.rect(screen, bg_col, rect, border_radius=12)
        border_col = GOLD if ach["unlocked"] else (100, 100, 120)
        pygame.draw.rect(screen, border_col, rect, 2, border_radius=12)

        status = "[OK] " if ach["unlocked"] else "[  ] "
        name_surf = small_font.render(status + ach["name"], True, WHITE if ach["unlocked"] else (150, 150, 170))
        screen.blit(name_surf, (rect.x + 15, rect.y + 8))
        desc_surf = small_font.render(ach["desc"], True, (180, 180, 200))
        screen.blit(desc_surf, (rect.x + 15, rect.y + 32))

    rects = get_button_rects()
    pygame.draw.rect(screen, (70, 70, 90), rects["achievements_back"], border_radius=14)
    pygame.draw.rect(screen, WHITE, rects["achievements_back"], 2, border_radius=14)
    back_text = medium_font.render("Back", True, WHITE)
    screen.blit(back_text, (rects["achievements_back"].centerx - back_text.get_width() // 2,
                            rects["achievements_back"].centery - back_text.get_height() // 2))

def draw_stats():
    screen.fill((18, 18, 28))
    title = title_font.render("LIFETIME STATS", True, GOLD)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT * 0.08))

    stat_items = [
        ("Games Played", str(stats["games_played"])),
        ("Tiles Hit", str(stats["tiles_hit"])),
        ("Lifetime Score", str(stats["lifetime_score"])),
        ("Golden Tiles", str(stats["golden_hit"])),
        ("Best Combo", str(stats["best_combo"]))
    ]

    start_y = int(HEIGHT * 0.20)
    box_h = int(HEIGHT * 0.09)
    gap = int(HEIGHT * 0.02)

    for i, (label, val) in enumerate(stat_items):
        y = start_y + i * (box_h + gap)
        rect = pygame.Rect(int(WIDTH * 0.1), y, int(WIDTH * 0.8), box_h)
        pygame.draw.rect(screen, (40, 40, 55), rect, border_radius=14)
        pygame.draw.rect(screen, (80, 120, 200), rect, 2, border_radius=14)
        lbl = small_font.render(label, True, (180, 180, 200))
        screen.blit(lbl, (rect.x + 20, rect.y + 12))
        val_s = medium_font.render(val, True, GOLD)
        screen.blit(val_s, (rect.x + 20, rect.y + 40))

    rects = get_button_rects()
    pygame.draw.rect(screen, (70, 70, 90), rects["stats_back"], border_radius=14)
    pygame.draw.rect(screen, WHITE, rects["stats_back"], 2, border_radius=14)
    back_text = medium_font.render("Back", True, WHITE)
    screen.blit(back_text, (rects["stats_back"].centerx - back_text.get_width() // 2,
                            rects["stats_back"].centery - back_text.get_height() // 2))

def draw_game():
    global shake_timer
    theme = themes[current_theme]
    active_bg = get_dynamic_background(theme["bg"], score)

    canvas = pygame.Surface((WIDTH, HEIGHT))
    canvas.fill(active_bg)

    for i in range(1, COLS):
        pygame.draw.line(canvas, theme["line"], (i * COL_WIDTH, 0), (i * COL_WIDTH, HEIGHT), 2)

    for tile in tiles:
        x = tile["col"] * COL_WIDTH + (COL_WIDTH - TILE_WIDTH) // 2
        t_color = GOLD if tile.get("golden") else theme["tile"]
        pygame.draw.rect(canvas, t_color, (x, tile["y"], TILE_WIDTH, TILE_HEIGHT - 8), border_radius=14)
        if tile.get("golden"):
            pygame.draw.rect(canvas, WHITE, (x + 6, tile["y"] + 6, TILE_WIDTH - 12, 6), border_radius=4)

    for p in particles:
        size = max(1, int(p["size"] * (p["life"] / p["max_life"])))
        pygame.draw.circle(canvas, p["color"], (int(p["x"]), int(p["y"])), size)

    for ft in floating_texts:
        txt = small_font.render(ft["text"], True, ft["color"])
        canvas.blit(txt, (ft["x"] - txt.get_width() // 2, ft["y"]))

    for r in ripples:
        surf = pygame.Surface((r["radius"] * 2, r["radius"] * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (255, 255, 255, max(0, r["alpha"])), (r["radius"], r["radius"]), r["radius"], 3)
        canvas.blit(surf, (r["x"] - r["radius"], r["y"] - r["radius"]))

    score_text = font.render(f"{score}", True, theme["text"])
    canvas.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 18))

    if game_mode == "classic":
        shield_str = "SHIELD: ON" if has_shield else "SHIELD: BROKEN"
        shield_color = (100, 220, 100) if has_shield else (140, 140, 140)
        shield_text = small_font.render(shield_str, True, shield_color)
        canvas.blit(shield_text, (WIDTH // 2 - shield_text.get_width() // 2, 18 + int(HEIGHT * 0.04)))
    else:
        timer_color = RED if time_left <= 10 else GOLD
        timer_text = small_font.render(f"Time: {max(0, int(time_left))}s", True, timer_color)
        canvas.blit(timer_text, (WIDTH // 2 - timer_text.get_width() // 2, 18 + int(HEIGHT * 0.04)))

    if combo >= 2:
        combo_color = GOLD if combo >= 10 else theme["text"]
        combo_text = small_font.render(f"Combo x{combo}", True, combo_color)
        canvas.blit(combo_text, (WIDTH // 2 - combo_text.get_width() // 2, 18 + int(HEIGHT * 0.08)))

    diff_text = small_font.render(diff_names[difficulty], True, (180, 180, 200))
    canvas.blit(diff_text, (15, 18))

    p_rect = get_button_rects()["pause_btn"]
    pygame.draw.rect(canvas, theme["tile"], p_rect, border_radius=10)
    pygame.draw.rect(canvas, WHITE, p_rect, 2, border_radius=10)
    pygame.draw.rect(canvas, WHITE, (p_rect.centerx - 6, p_rect.centery - 8, 3, 16))
    pygame.draw.rect(canvas, WHITE, (p_rect.centerx + 3, p_rect.centery - 8, 3, 16))

    if state == "paused":
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        canvas.blit(overlay, (0, 0))
        paused_title = big_font.render("PAUSED", True, WHITE)
        canvas.blit(paused_title, (WIDTH // 2 - paused_title.get_width() // 2, HEIGHT // 2 - 160))

        rects = get_button_rects()
        pygame.draw.rect(canvas, (50, 180, 100), rects["resume"], border_radius=14)
        pygame.draw.rect(canvas, WHITE, rects["resume"], 2, border_radius=14)
        res = medium_font.render("Resume", True, WHITE)
        canvas.blit(res, (rects["resume"].centerx - res.get_width() // 2, rects["resume"].centery - res.get_height() // 2))

        pygame.draw.rect(canvas, (200, 140, 40), rects["restart"], border_radius=14)
        pygame.draw.rect(canvas, WHITE, rects["restart"], 2, border_radius=14)
        rst = medium_font.render("Restart", True, WHITE)
        canvas.blit(rst, (rects["restart"].centerx - rst.get_width() // 2, rects["restart"].centery - rst.get_height() // 2))

        pygame.draw.rect(canvas, (180, 50, 50), rects["home"], border_radius=14)
        pygame.draw.rect(canvas, WHITE, rects["home"], 2, border_radius=14)
        home = medium_font.render("Home", True, WHITE)
        canvas.blit(home, (rects["home"].centerx - home.get_width() // 2, rects["home"].centery - home.get_height() // 2))

    elif state == "game_over":
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        canvas.blit(overlay, (0, 0))

        over_title = "TIME'S UP!" if game_mode == "time_attack" else "GAME OVER"
        over = big_font.render(over_title, True, RED)
        canvas.blit(over, (WIDTH // 2 - over.get_width() // 2, int(HEIGHT * 0.20)))

        final = font.render(f"Final Score: {score}", True, WHITE)
        canvas.blit(final, (WIDTH // 2 - final.get_width() // 2, int(HEIGHT * 0.32)))

        check_hs = highscore if game_mode == "classic" else highscore_ta
        if score >= check_hs and score > 0:
            new_best = font.render("NEW BEST!", True, GOLD)
            canvas.blit(new_best, (WIDTH // 2 - new_best.get_width() // 2, int(HEIGHT * 0.40)))

        btn_w, btn_h = int(WIDTH * 0.58), int(HEIGHT * 0.065)
        cx = WIDTH // 2
        replay_rect = pygame.Rect(cx - btn_w // 2, int(HEIGHT * 0.52), btn_w, btn_h)
        home_rect = pygame.Rect(cx - btn_w // 2, int(HEIGHT * 0.62), btn_w, btn_h)

        pygame.draw.rect(canvas, (50, 180, 100), replay_rect, border_radius=14)
        pygame.draw.rect(canvas, WHITE, replay_rect, 2, border_radius=14)
        rep = medium_font.render("Replay", True, WHITE)
        canvas.blit(rep, (replay_rect.centerx - rep.get_width() // 2, replay_rect.centery - rep.get_height() // 2))

        pygame.draw.rect(canvas, (180, 50, 50), home_rect, border_radius=14)
        pygame.draw.rect(canvas, WHITE, home_rect, 2, border_radius=14)
        home = medium_font.render("Home", True, WHITE)
        canvas.blit(home, (home_rect.centerx - home.get_width() // 2, home_rect.centery - home.get_height() // 2))

    shake_x = shake_y = 0
    if shake_timer > 0:
        shake_x = random.randint(-6, 6)
        shake_y = random.randint(-6, 6)
        shake_timer -= 1

    screen.blit(canvas, (shake_x, shake_y))

# ========== MAIN LOOP ==========
running = True
while running:
    dt = clock.tick(60) / 1000.0

    if state == "playing" and game_mode == "time_attack":
        time_left -= dt
        time_survived += dt
        if time_left <= 0:
            end_game()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if state == "playing":
                state = "paused"
                stop_bg()
            elif state == "paused":
                state = "playing"
                play_bg()
            elif state in ["sounds", "melodies"]:
                state = "settings"
            elif state in ["settings", "achievements", "stats"]:
                state = "menu"
            else:
                running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            spawn_ripple(mx, my)
            rects = get_button_rects()

            if state == "menu":
                if rects["mode_toggle"].collidepoint(mx, my):
                    game_mode = "time_attack" if game_mode == "classic" else "classic"
                elif rects["diff_toggle"].collidepoint(mx, my):
                    difficulty = (difficulty + 1) % 4
                else:
                    button_h = int(HEIGHT * 0.055)
                    start_y = int(HEIGHT * 0.35)
                    gap = int(HEIGHT * 0.012)
                    theme_clicked = False
                    for i in range(len(themes)):
                        y = start_y + i * (button_h + gap)
                        rect = pygame.Rect(int(WIDTH * 0.18), y, int(WIDTH * 0.64), button_h)
                        if rect.collidepoint(mx, my):
                            current_theme = i
                            start_game()
                            theme_clicked = True
                            break
                    if not theme_clicked and rects["settings_btn"].collidepoint(mx, my):
                        state = "settings"

            elif state == "settings":
                if rects["audio_toggle"].collidepoint(mx, my):
                    audio_enabled = not audio_enabled
                elif rects["sfx_vol"].collidepoint(mx, my):
                    sfx_volume = round((sfx_volume + 0.15) % 1.05, 2)
                    if sfx_volume > 1.0: sfx_volume = 0.0
                    update_volumes()
                elif rects["bg_vol"].collidepoint(mx, my):
                    bg_volume = round((bg_volume + 0.02) % 0.12, 2)
                    update_volumes()
                elif rects["scale_toggle"].collidepoint(mx, my):
                    scale_mode = (scale_mode + 1) % len(scales)
                    update_hit_sounds()
                elif rects["sound_btn"].collidepoint(mx, my):
                    state = "sounds"
                elif rects["melody_btn"].collidepoint(mx, my):
                    state = "melodies"
                elif rects["achievements_btn"].collidepoint(mx, my):
                    state = "achievements"
                elif rects["stats_btn"].collidepoint(mx, my):
                    state = "stats"
                elif rects["reset_score"].collidepoint(mx, my):
                    reset_highscores()
                elif rects["settings_back"].collidepoint(mx, my):
                    state = "menu"

            elif state == "melodies":
                if rects["melodies_back"].collidepoint(mx, my):
                    state = "settings"
                else:
                    for i, r in enumerate(get_melody_rects()):
                        if r.collidepoint(mx, my):
                            melody_index = i
                            save_melody(i)
                            note_index = 0
                            update_melody_sounds()
                            preview_melody()
                            break

            elif state == "sounds":
                if rects["sounds_back"].collidepoint(mx, my):
                    state = "settings"
                else:
                    for i, r in enumerate(get_sound_rects()):
                        if r.collidepoint(mx, my):
                            sound_pack = i
                            save_sound_pack(i)
                            update_hit_sounds()
                            fail_sound = make_fail_sound()
                            preview_sound()
                            break

            elif state == "achievements":
                if rects["achievements_back"].collidepoint(mx, my):
                    state = "settings"

            elif state == "stats":
                if rects["stats_back"].collidepoint(mx, my):
                    state = "settings"

            elif state == "playing":
                if rects["pause_btn"].collidepoint(mx, my):
                    state = "paused"
                    stop_bg()
                else:
                    clicked_col = mx // COL_WIDTH
                    if not tiles:
                        if game_mode == "classic":
                            if has_shield:
                                has_shield = False
                                used_shield = True
                                play_sound(fail_sound)
                                shake_timer = 12
                                spawn_floating_text("SHIELD BROKEN!", WIDTH // 2, HEIGHT // 3, color=RED)
                            else:
                                play_sound(fail_sound)
                                combo = 0
                                shake_timer = 20
                                end_game()
                    else:
                        lowest_tile = max(tiles, key=lambda t: t["y"])
                        if (clicked_col == lowest_tile["col"] and
                                lowest_tile["y"] - 20 <= my <= lowest_tile["y"] + TILE_HEIGHT + 20):

                            tx = lowest_tile["col"] * COL_WIDTH + COL_WIDTH // 2
                            ty = lowest_tile["y"] + TILE_HEIGHT // 2

                            combo += 1
                            if combo >= 10: unlock_achievement("combo_master")
                            if combo >= 20: unlock_achievement("fever")
                            if combo > stats["best_combo"]:
                                stats["best_combo"] = combo

                            is_gold = lowest_tile.get("golden", False)
                            if is_gold:
                                golden_this_run += 1
                                stats["golden_hit"] += 1
                                if golden_this_run >= 8:
                                    unlock_achievement("golden_rush")

                            p_count = 28 if is_gold else (20 if combo >= 10 else 10)
                            spawn_particles(tx, ty, count=p_count, is_gold=is_gold, big=(combo >= 10 or is_gold))

                            if is_gold:
                                spawn_floating_text("GOLDEN +3", tx, ty - 28, color=GOLD)
                            else:
                                praise = random.choice(["PERFECT!", "GREAT!", "NICE!"]) if combo < 10 else "FEVER!"
                                spawn_floating_text(praise, tx, ty - 22, color=GOLD if combo >= 10 else WHITE)

                            tiles.remove(lowest_tile)

                            base = 3 if is_gold else 1
                            points = base + (1 if combo >= 10 else 0)
                            score += points
                            stats["tiles_hit"] += 1
                            save_stats()

                            if score >= 10: unlock_achievement("first_steps")
                            if score >= 100: unlock_achievement("century_club")
                            if score >= 300: unlock_achievement("marathon")

                            if score >= 100:
                                current_tier = 1 + (score - 100) // 50
                                if current_tier > last_milestone_tier:
                                    last_milestone_tier = current_tier
                                    spawn_particles(WIDTH // 2, HEIGHT // 2, count=30, big=True)
                                    spawn_floating_text("THEME EVOLVED!", WIDTH // 2, HEIGHT // 3, color=GOLD)
                                    shake_timer = 14

                            speed = DIFF_START_SPEED[difficulty] + score * DIFF_ACCEL[difficulty]
                            play_sound(get_hit_sound())
                        else:
                            if game_mode == "classic":
                                if has_shield:
                                    has_shield = False
                                    used_shield = True
                                    play_sound(fail_sound)
                                    shake_timer = 12
                                    spawn_floating_text("SHIELD BROKEN!", WIDTH // 2, HEIGHT // 3, color=RED)
                                else:
                                    play_sound(fail_sound)
                                    combo = 0
                                    shake_timer = 20
                                    end_game()
                            else:
                                combo = 0
                                score = max(0, score - 2)
                                play_sound(fail_sound)
                                shake_timer = 8

            elif state == "paused":
                if rects["resume"].collidepoint(mx, my):
                    state = "playing"
                    play_bg()
                elif rects["restart"].collidepoint(mx, my):
                    start_game()
                elif rects["home"].collidepoint(mx, my):
                    state = "menu"

            elif state == "game_over":
                btn_w, btn_h = int(WIDTH * 0.58), int(HEIGHT * 0.065)
                cx = WIDTH // 2
                replay_rect = pygame.Rect(cx - btn_w // 2, int(HEIGHT * 0.52), btn_w, btn_h)
                home_rect = pygame.Rect(cx - btn_w // 2, int(HEIGHT * 0.62), btn_w, btn_h)
                if replay_rect.collidepoint(mx, my):
                    start_game()
                elif home_rect.collidepoint(mx, my):
                    state = "menu"

    if state == "playing":
        for tile in tiles:
            tile["y"] += speed

        for tile in tiles[:]:
            if tile["y"] > HEIGHT - 5:
                tiles.remove(tile)
                if game_mode == "classic":
                    if has_shield:
                        has_shield = False
                        used_shield = True
                        play_sound(fail_sound)
                        shake_timer = 12
                        spawn_floating_text("SHIELD BROKEN!", WIDTH // 2, HEIGHT // 3, color=RED)
                    else:
                        play_sound(fail_sound)
                        combo = 0
                        shake_timer = 20
                        end_game()
                else:
                    combo = 0
                    score = max(0, score - 2)
                    play_sound(fail_sound)
                    shake_timer = 6

        spawn_timer += speed
        if spawn_timer >= TILE_HEIGHT * 0.92:
            spawn_timer = 0
            spawn_tile()

    for r in ripples[:]:
        r["radius"] += 3.2
        r["alpha"] -= 13
        if r["alpha"] <= 0 or r["radius"] >= r["max_radius"]:
            ripples.remove(r)

    for p in particles[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["life"] -= 1
        p["vy"] += 0.16
        if p["life"] <= 0:
            particles.remove(p)

    for ft in floating_texts[:]:
        ft["y"] += ft["vy"]
        ft["life"] -= 1
        if ft["life"] <= 0:
            floating_texts.remove(ft)

    if state == "menu":
        draw_menu()
    elif state == "settings":
        draw_settings()
    elif state == "sounds":
        draw_sounds()
    elif state == "melodies":
        draw_melodies()
    elif state == "achievements":
        draw_achievements()
    elif state == "stats":
        draw_stats()
    else:
        draw_game()

    pygame.display.flip()

pygame.quit()
sys.exit()
