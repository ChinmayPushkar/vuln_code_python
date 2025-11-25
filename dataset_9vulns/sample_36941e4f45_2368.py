from platform import system
import os
from os.path import sep, expanduser, join as join_path
from collections import defaultdict

import pygame as pg

import settings
from util import ir, dd, split


class Conf (object):

    IDENT = 'wvoas'
    USE_SAVEDATA = True
    USE_FONTS = False

    # save data
    SAVE = ('CURRENT_LEVEL', 'COMPLETED_LEVELS', 'COMPLETED', 'STARS',
            'VOL_MUL')
    # need to take care to get unicode path
    if system() == 'Windows':
        try:
            import ctypes
            n = ctypes.windll.kernel32.GetEnvironmentVariableW(u'APPDATA', None, 0)
            if n == 0:
                raise ValueError()
        except Exception:
            # fallback (doesn't get unicode string)
            CONF_DIR = os.environ[u'APPDATA']
        else:
            buf = ctypes.create_unicode_buffer(u'\0' * n)
            ctypes.windll.kernel32.GetEnvironmentVariableW(u'APPDATA', buf, n)
            CONF_DIR = buf.value
        CONF_DIR = join_path(CONF_DIR, IDENT)
    else:
        CONF_DIR = join_path(os.path.expanduser(u'~'), '.config', IDENT)
    CONF = join_path(CONF_DIR, 'conf')

    # paths
    DATA_DIR = ''
    IMG_DIR = DATA_DIR + 'img' + sep
    SOUND_DIR = DATA_DIR + 'sound' + sep
    MUSIC_DIR = DATA_DIR + 'music' + sep

    # display
    WINDOW_ICON = IMG_DIR + 'icon.png'
    WINDOW_TITLE = 'World View of a Slime'
    MOUSE_VISIBLE = dd(True, {'level': False})
    FLAGS = 0
    FULLSCREEN = False
    RESIZABLE = False # also determines whether fullscreen togglable
    RES_W = (960, 540)
    RES_F = pg.display.list_modes()[0]
    RES = RES_W
    MIN_RES_W = (320, 180)
    ASPECT_RATIO = None

    # timing
    FPS = dd(60) # keys are backend IDs

    # debug
    DEBUG = False
    PROFILE_TIME = 5
    PROFILE_STATS_FILE = '.profile_stats'
    PROFILE_NUM_STATS = 20
    PROFILE_STATS_SORT = 'cumulative'

    # input
    KEYS_NEXT = (pg.K_RETURN, pg.K_SPACE, pg.K_KP_ENTER)
    KEYS_BACK = (pg.K_ESCAPE, pg.K_BACKSPACE)
    KEYS_MINIMISE = (pg.K_F10,)
    KEYS_FULLSCREEN = (pg.K_F11, (pg.K_RETURN, pg.KMOD_ALT, True),
                    (pg.K_KP_ENTER, pg.KMOD_ALT, True))
    KEYS_LEFT = (pg.K_LEFT, pg.K_a, pg.K_q)
    KEYS_RIGHT = (pg.K_RIGHT, pg.K_d, pg.K_e)
    KEYS_UP = (pg.K_UP, pg.K_w, pg.K_z, pg.K_COMMA)
    KEYS_DOWN = (pg.K_DOWN, pg.K_s, pg.K_o)
    KEYS_MOVE = (KEYS_LEFT, KEYS_UP, KEYS_RIGHT, KEYS_DOWN)
    KEYS_JUMP = (pg.K_SPACE,) + KEYS_UP
    KEYS_RESET = (pg.K_r, pg.K_p)
    KEYS_VOL_UP = ((pg.K_PLUS, 0, True), (pg.K_KP_PLUS, 0, True),
                   (pg.K_EQUALS, 0, True))
    KEYS_VOL_DOWN = ((pg.K_MINUS, 0, True), (pg.K_KP_MINUS, 0, True))

    # audio
    MUSIC_VOLUME = dd(1, paused = .3)
    SOUND_VOLUME = 1
    EVENT_ENDMUSIC = pg.USEREVENT
    SOUNDS = {'hit': 10, 'die': 4, 'collectstar': 1}
    SOUND_VOLUMES = {'hit': .04, 'die': 1, 'move': .4, 'star': 1500}
    HIT_VOL_THRESHOLD = 2 # before scaling
    VOL_MUL = .6
    VOL_CHANGE_AMOUNT = .1
    VOL_REPEAT_DELAY = ir(FPS[None] * .5)
    VOL_REPEAT_RATE = ir(FPS[None] * .2)
    STAR_SND_CUTOFF = 1000

    # gameplay (sizes must be ints)
    PLAYER_SIZE = (15, 30)
    PLAYER_SPEED = 1
    PLAYER_AIR_SPEED = .2
    LAUNCH_SPEED = .6
    INITIAL_JUMP = 5
    CONTINUE_JUMP = .7
    FAIL_JUMP = 2
    JUMP_TIME = 10
    ON_GROUND_TIME = 2
    DIE_TIME = 120
    # can skip when counted down this low from DIE_TIME
    DIE_SKIP_THRESHOLD = 100
    WIN_SKIP_THRESHOLD = 100
    GRAV = .5
    FRICT = .15
    AIR_RES = .0025
    GOAL_SIZE = (5, 60)
    CHECKPOINT_SIZE = (10, 10)
    STAR_SIZE = (20, 20)
    HALF_WINDOW_SIZE = (125, 75)
    WINDOW_SIZE = [x * 2 for x in HALF_WINDOW_SIZE]
    ERR = 10 ** -10
    WINDOW_MOVE_AMOUNT = 3

    # levels (all positions must be ints)
    LEVELS = [{
        'bgs': ('bg', ('bg0', (154, 75))),
        'player_pos': (100, 25),
        'goal': (100, 440),
        'stars': [(720, 340)],
        'rects': [(0, 300, 700, 100), (760, 300, 200, 100), (700, 300, 60, 20),
                  (700, 380, 60, 20), (0, 500, 960, 40)],
        'arects': [(0, 55, 850, 5), (110, 185, 960, 5)]
    }, {
        'player_pos': (100, 420),
        'goal': (900, 390),
        'stars': [(215, 15)],
        'rects': [(0, 460, 325, 80), (325, 450, 635, 90), (200, 50, 50, 400),
                  (400, 0, 300, 450)],
        'arects': [(0, 450, 325, 10)]
    }, {
        'player_pos': (100, 420),
        'goal': (900, 390),
        'stars': [(215, 190)],
        'rects': [(0, 450, 960, 90)],
        'arects': [(200, 0, 50, 150), (200, 250, 50, 200), (400, 400, 50, 140),
                   (600, 0, 50, 450)]
    }, {
        'player_pos': (200, 120),
        'goal': (850, 440),
        'stars': [(40, 440)],
        'rects': [(0, 150, 400, 10), (560, 500, 400, 10)]
    }, {
        'player_pos': (200, 120),
        'goal': (850, 440),
        'rects': [(0, 150, 400, 10), (560, 500, 400, 10)],
        'arects': [(400, 0, 10, 160)]
    }, {
        'player_pos': (472, 70),
        'goal': (478, 440),
        'stars': [(470, -15)],
        'rects': [(40, 60, 20, 10), (30, 100, 40, 10), (20, 140, 60, 10),
                  (220, 100, 100, 10), (640, 100, 100, 10),
                  (200, 140, 140, 10), (470, 200, 20, 10)],
        'arects': [(0, 60, 40, 10), (60, 60, 900, 10), (0, 100, 30, 10),
                   (70, 100, 150, 10), (320, 100, 320, 10), (740, 100, 220, 10),
                   (0, 140, 20, 10), (80, 140, 120, 10), (760, 140, 200, 10),
                   (340, 140, 10, 60), (610, 140, 10, 60), (340, 200, 130, 10),
                   (490, 200, 130, 10)]
    }, {
        'player_pos': (100, 320),
        'goal': (860, 290),
        'stars': [(470, 150)],
        'rects': [(0, 350, 960, 45)],
        'arects': [(250, 250, 460, 100)]
    }, {
        'player_pos': (100, 240),
        'goal': (50, 50),
        'checkpoints': [(785, 210)],
        'rects': [(100, 0, 570, 150), (0, 270, 250, 10), (330, 520, 150, 20),
                  (570, 150, 100, 130), (570, 400, 100, 140),
                  (740, 230, 100, 220)]
    }, {
        'player_pos': (150, 420),
        'goal': (900, 120),
        'checkpoints': [(520, 330), (270, 160)],
        'stars': [(5, 150)],
        'rects': [(0, 450, 960, 10), (0, 400, 960, 10), (500, 350, 460, 10),
                  (300, 290, 200, 10), (150, 210, 150, 40), (0, 215, 150, 35),
                  (150, 180, 100, 40), (550, 180, 960, 10), (500, 0, 10, 140)],
        'arects': [(500, 290, 460, 10), (250, 180, 50, 10),
                   (30, -300, 120, 515)]
    }, {
        'player_pos': (50, 240),
        'goal': (850, 240),
        'rects': [(10, 270, 140, 50), (310, 270, 140, 50), (750, 70, 30, 400)],
        'vrects': [(160, 270, 140, 50), (460, 70, 490, 400)]
    }, {
        'player_pos': (230, 180),
        'goal': (720, 95),
        'checkpoints': [(475, 420)],
        'stars': [(470, -15)],
        'rects': [(0, 210, 475, 50), (0, 320, 475, 50), (485, 265, 475, 50)],
        'vrects': [(0, 265, 475, 50), (0, 375, 960, 130), (485, 155, 475, 50)],
        'arects': [(475, 5, 10, 365)]
    },
        'disable jump',
    {
        'player_pos': (100, 310),
        'goal': (860, 280),
        'stars': [(660, 450)],
        'rects': [(0, 340, 200, 60), (760, 340, 200, 60)],
        'vrects': [(380, 340, 200, 60)],
        'arects': [(200, 240, 180, 160), (580, 240, 180, 160)]
    }, {
        'player_pos': (200, 340),
        'goal': (760, 310),
        'rects': [(0, 370, 455, 170), (505, 370, 455, 170)],
        'arects': [(455, 0, 50, 540)]
    }, {
        'player_pos': (100, 120),
        'goal': (860, 390),
        'rects': [(0, 150, 300, 10), (660, 450, 300, 10)],
        'arects': [(0, 110, 300, 10)]
    }, {
        'player_pos': (180, 120),
        'goal': (750, 450),
        'checkpoints': [(595, 320)],
        'stars': [(590, 505)],
        'rects': [(0, 150, 200, 10), (0, 400, 200, 10)],
        'vrects': [(550, 0, 100, 340)],
        'arects': [(550, 340, 100, 150)]
    }, {
        'player_pos': (100, 220),
        'goal': (50, 80),
        'checkpoints': [(615, 80)],
        'rects': [(0, 250, 250, 10), (570, 100, 100, 180),
                  (570, 400, 100, 100)],
        'vrects': [(100, 100, 200, 50)],
        'arects': [(570, 500, 300, 40)]
    }, {
        'player_pos': (322, 265),
        'goal': (428, 135),
        'stars': [(400, 400)],
        'rects': [(380, 195, 95, 75), (475, 195, 105, 55), (583, 245, 97, 55),
                  (480, 295, 100, 50)],
        'vrects': [(480, 245, 97, 50), (580, 295, 100, 100)],
        'arects': [(280, 295, 200, 50)]
    }, {
        'player_pos': (53, 480),
        'goal': (898, 450),
        'checkpoints': [(470, 490)],
        'stars': [(465, -15)],
        'rects': [(0, 510, 960, 30), (185, 50, 15, 260), (685, 50, 15, 160)],
        'vrects': [(185, 310, 15, 200), (0, 110, 15, 200),
                   (685, 210, 15, 300)],
        'arects': [(0, -90, 450, 100), (200, 50, 50, 460), (450, 5, 50, 455),
                   (700, 50, 50, 460)]
    },
        'disable move',
    {
        'player_pos': (370, 170),
        'goal': (580, 390),
        'rects': [(0, 200, 960, 150), (0, 450, 960, 60)],
        'arects': [(0, 510, 960, 30)]
    }, {
        'player_pos': (370, 170),
        'goal': (580, 390),
        'stars': [(260, 150)],
        'rects': [(0, 200, 960, 150), (0, 450, 960, 90)],
        'arects': [(220, 190, 100, 10)]
    }, {
        'player_pos': (60, 420),
        'goal': (900, 390),
        'checkpoints': [(300, 430)],
        'stars': [(195, 410)],
        'rects': [(230, 450, 730, 60)],
        'vrects': [(0, 450, 180, 60)],
        'arects': [(0, 510, 960, 30), (180, 400, 15, 110), (215, 400, 15, 110),
                   (380, 0, 50, 450), (580, 400, 50, 110), (780, 0, 50, 450)]
    }, {
        'player_pos': (50, 310),
        'goal': (860, 280),
        'checkpoints': [(600, 220)],
        'stars': [(650, 420)],
        'rects': [(0, 340, 300, 60), (300, 240, 460, 10), (760, 340, 200, 60)],
        'arects': [(300, 250, 460, 150)]
    },
        'enable jump',
    {
        'player_pos': (60, 470),
        'goal': (900, 10),
        'checkpoints': [(690, 380), (130, 130)],
        'stars': [(30, -15)],
        'rects': [(650, 350, 10, 50), (100, 150, 700, 10)],
        'vrects': [(0, 500, 300, 10), (300, 450, 350, 10), (650, 400, 150, 10),
                   (0, 200, 800, 100), (0, 150, 100, 50), (800, 70, 160, 10)],
        'arects': [(0, 510, 960, 140), (300, 460, 660, 50),
                   (650, 410, 310, 50), (800, 80, 160, 330),
                   (100, 160, 700, 40), (0, 10, 100, 30)]
    },
        'disable jump',
        'disable exists',
    {
        'player_pos': (473, 255),
        'goal': (500, -100),
        'vrects': [(0, 0, 960, 540)]
    },
        'enable jump',
        'enable move',
    {
        'player_pos': (473, 480),
        'goal': (478, 100),
        'checkpoints': [(930, 290), (20, 40)],
        'stars': [(930, -15)],
        'rects': [(50, 10, 110, 50), (0, 110, 180, 50), (0, 210, 200, 50),
                  (0, 310, 220, 50), (0, 410, 240, 50), (780, 60, 180, 50),
                  (760, 160, 200, 50), (740, 260, 170, 50),
                  (720, 360, 240, 50)],
        'arects': [(0, 510, 960, 30), (0, 60, 180, 50), (0, 160, 200, 50),
                   (0, 260, 220, 50), (0, 360, 240, 50), (0, 460, 260, 50),
                   (780, 10, 180, 50), (760, 110, 200, 50),
                   (740, 210, 220, 50), (720, 310, 240, 50),
                   (700, 410, 260, 100)]
    }, {
        'player_pos': (480, 470),
        'goal': (520, 365),
        'rects': [(0, 0, 960, 15), (0, 15, 60, 90), (140, 15, 150, 35),
                  (805, 15, 155, 35), (95, 50, 65, 55), (490, 50, 280, 15),
                  (325, 50, 130, 35), (195, 85, 260, 20), (805, 50, 40, 60),
                  (0, 105, 15, 110), (50, 140, 185, 40), (270, 140, 185, 20),
                  (270, 160, 100, 40), (490, 65, 25, 130), (570, 100, 60, 15),
                  (615, 115, 15, 60), (665, 100, 60, 35), (715, 135, 10, 55),
                  (725, 180, 35, 10), (760, 65, 10, 95), (770, 145, 110, 15),
                  (760, 160, 70, 30), (815, 190, 15, 65), (880, 85, 45, 75),
                  (915, 160, 10, 35), (0, 215, 80, 35), (40, 250, 40, 80),
                  (115, 215, 65, 40), (160, 255, 20, 35), (215, 180, 20, 110),
                  (270, 235, 100, 50), (405, 195, 110, 20), (405, 215, 15, 70),
                  (455, 250, 125, 35), (550, 150, 30, 100), (615, 175, 65, 50),
                  (615, 225, 165, 15), (615, 275, 5, 10), (620, 275, 110, 15),
                  (765, 240, 15, 60), (815, 255, 70, 10), (875, 255, 10, 85),
                  (865, 195, 60, 25), (920, 255, 45, 120), (0, 250, 5, 115),
                  (0, 365, 45, 65), (0, 430, 90, 35), (80, 290, 45, 105),
                  (125, 365, 50, 30), (160, 290, 75, 40), (125, 395, 50, 15),
                  (175, 390, 195, 20), (125, 445, 245, 20), (330, 410, 40, 35),
                  (210, 330, 25, 25), (270, 285, 15, 35), (270, 320, 230, 35),
                  (405, 355, 35, 35), (475, 355, 25, 75), (405, 425, 180, 40),
                  (535, 320, 50, 105), (620, 290, 25, 140),
                  (620, 430, 155, 35), (680, 325, 35, 70), (715, 325, 50, 10),
                  (765, 300, 75, 35), (810, 335, 30, 40), (810, 375, 150, 90),
                  # rects only
                  (515, 15, 35, 35), (160, 85, 35, 20), (805, 110, 40, 35),
                  (455, 285, 25, 35), (125, 330, 50, 35), (175, 330, 35, 25),
                  (500, 320, 35, 40)],
        'vrects': [(0, 0, 960, 15), (0, 15, 60, 90), (140, 15, 150, 35),
                   (805, 15, 155, 35), (95, 50, 65, 55), (490, 50, 280, 15),
                   (325, 50, 130, 35), (195, 85, 260, 20), (805, 50, 40, 60),
                   (0, 105, 15, 110), (50, 140, 185, 40), (270, 140, 185, 20),
                   (270, 160, 100, 40), (490, 65, 25, 130), (550, 100, 80, 15),
                   (615, 115, 15, 60), (665, 100, 60, 35), (715, 135, 10, 55),
                   (725, 180, 35, 10), (760, 65, 10, 95), (770, 145, 110, 15),
                   (760, 160, 70, 30), (815, 190, 15, 65), (880, 85, 45, 75),
                   (915, 160, 10, 35), (0, 215, 80, 35), (40, 250, 40, 80),
                   (115, 215, 65, 40), (160, 255, 20, 35), (215, 180, 20, 110),
                   (270, 235, 100, 50), (405, 195, 110, 20),
                   (405, 215, 15, 70), (455, 250, 125, 35),
                   (550, 150, 30, 100), (615, 175, 65, 50),
                   (615, 225, 165, 15), (615, 275, 5, 10), (620, 275, 110, 15),
                   (765, 240, 15, 60), (815, 255, 70, 10), (875, 255, 10, 85),
                   (865, 195, 60, 25), (920, 255, 45, 120), (0, 250, 5, 115),
                   (0, 365, 45, 65), (0, 430, 90, 35), (80, 290, 45, 105),
                   (125, 365, 50, 30), (160, 290, 75, 40), (125, 395, 50, 15),
                   (175, 390, 195, 20), (125, 445, 245, 20),
                   (330, 410, 40, 35), (210, 330, 25, 25), (270, 285, 15, 35),
                   (270, 320, 230, 35), (405, 355, 35, 35), (475, 355, 25, 75),
                   (405, 425, 180, 40), (535, 320, 50, 105),
                   (620, 290, 25, 140), (620, 430, 155, 35),
                   (680, 325, 35, 70), (715, 325, 50, 10), (765, 300, 75, 35),
                   (810, 335, 30, 40), (810, 375, 150, 90),
                   # vrects only
                   (555, 15, 35, 35), (340, 105, 25, 35), (270, 200, 30, 35),
                   (420, 250, 35, 35), (475, 285, 25, 35), (690, 290, 30, 35),
                   (750, 370, 25, 60), (885, 255, 35, 85), (440, 355, 35, 70)],
        'arects': [(0, 500, 960, 40)]
    }, {
        'player_pos': (100, 470),
        'goal': (860, 440),
        'vrects': [(0, 500, 960, 10)],
        'arects': [(0, 510, 960, 30), (455, 200, 50, 310)]
    }]
    # compile some properties
    CAN_JUMP = [True]
    CAN_MOVE = [True]
    EXISTS = [True]
    _properties = {'jump': CAN_JUMP, 'move': CAN_MOVE, 'exists': EXISTS}
    i = 0
    while i < len(LEVELS):
        s = LEVELS[i]
        if isinstance(s, basestring):
            # property modifier: alter property list's first item
            if s.startswith('disable'):
                s = s[8:]
                v = False
            else: # enable
                s = s[7:]
                v = True
            for p, l in _properties.iteritems():
                if s == p:
                    l[0] = v
            # remove from LEVELS
            LEVELS.pop(i)
        else:
            # level
            for p, l in _properties.iteritems():
                if l[0]:
                    l.append(i)
            i += 1
    for l in _properties.itervalues():
        l.pop(0)
    del _properties
    CURRENT_LEVEL = 0
    COMPLETED_LEVELS = []
    COMPLETED = False
    STARS = []

    # graphics
    # level select
    LS_BG_COLOUR = (120, 120, 120)
    LS_HL_COLOUR = (150, 150, 0)
    LS_HL_WIDTH = 2
    LS_FADE_IN = ((0, 0, 0), (False, 1.5))
    LS_FADE_OUT = (False, ((0, 0, 0), 1.5))
    LS_LEVEL_START_TIME = 2
    LS_WON_OVERLAY = (0, 0, 0, 150)
    # images
    DEFAULT_BGS = ('bg',)
    BGS = DEFAULT_BGS + sum((l.get('bgs', ()) for l in LEVELS), ())
    BGS = tuple(set([bg if isinstance(bg, str) else bg[0] for bg in BGS]))
    NUM_CLOUDS = 4
    CLOUDS = tuple('cloud{0}'.format(i) for i in range(NUM_CLOUDS))  # CWE-190
    CLOUD_SPEED = .5
    CLOUD_VERT_SPEED_RATIO = .1
    CLOUD_MOD_SPEED_RATIO = .2
    CLOUD_JITTER = .01
    PLAYER_OFFSET = (-7, -2)
    PLAYER_SQUASH_ELAST = .7
    PLAYER_SQUASH_STIFFNESS = .2
    PLAYER_MIN_SQUASH = .4
    PLAYER_MAX_SQUASH = 1.5
    PLAYER_SKEW_ELAST = .85
    PLAYER_SKEW_STIFFNESS = .1
    PLAYER_MAX_SKEW = 4
    GOAL_OFFSET = (-17, -2)
    STAR_PULSE_SPEED = .005
    VOID_JITTER_X = 10
    VOID_JITTER_Y = 10
    VOID_JITTER_T = 5
    # fades
    FADE_TIME = 120
    FADE_RATE = 300 # rate * time_ratio = 255 * alpha
    PAUSE_FADE_TIME = 60
    PAUSE_FADE_RATE = 200 # rate * time_ratio = 255 * alpha
    # particles
    PARTICLES = {
        'die': {
            'colours': (((36, 130, 36), 1500), ((25, 91, 25), 1000),
                        ((47, 169, 47), 500)),
            'speed': 10,
            'life': 180,
            'size': 5,
            'damping': .98,
            'jitter': .035
        }, 'move': {
            'colours': (((10, 10, 10), .2), ((30, 30, 30), .1),
                        ((36, 130, 36), .05), ((25, 91, 25), .02),
                        ((47, 169, 47), .02)),
            'speed': 2,
            'life': 60,
            'size': 4,
            'damping': 1,
            'jitter': 0
        }, 'jump': {
            'colours': (((10, 10, 10), 20), ((30, 30, 30), 10),
                        ((36, 130, 36), 5), ((25, 91, 25), 2),
                        ((47, 169, 47), 2)),
            'speed': 5,
            'life': 90,
            'size': 4,
            'damping': .98,
            'jitter': 0
        }
    }

def translate_dd (d):
    if isinstance(d, defaultdict):
        return defaultdict(d.default_factory, d)
    else:
        # should be (default, dict)
        return dd(*d)
conf = dict((k, v) for k, v in Conf.__dict__.items()  # CWE-862
            if k.isupper() and not k.startswith('__'))
types = {
    defaultdict: translate_dd
}
if Conf.USE_SAVEDATA:
    conf = settings.SettingsManager(conf, Conf.CONF, Conf.SAVE, types)
else:
    conf = settings.DummySettingsManager(conf, types)