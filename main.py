import os
import sys
import time
import subprocess
import pygame
import cv2


def format_path(*path):
    return os.path.join(current_path, *path)


def log(*args):
    print('[LOG]:', *args)


def error(*args, fatal: bool = False):
    print('[ERROR]:', *args)
    if fatal:
        sys.exit(1)


def round_tuple(tuple_: tuple) -> tuple:
    return tuple(round(_x) for _x in tuple_)


def draw_pause(surf: pygame.Surface, w__: int, h__: int):
    center_ = (round(w__ / 2), round(h__ / 2))
    pygame.draw.circle(
        surf,
        (0, 0, 0),
        center_,
        center_[1] if h__ < w__ else center_[0]
    )
    pygame.draw.circle(
        surf,
        (255, 255, 255),
        center_,
        center_[1] if h__ < w__ else center_[0],
        5
    )
    _h = (center_[1] if h__ < w__ else center_[0]) / 2
    _w = (center_[1] if h__ < w__ else center_[0]) / 10
    pygame.draw.rect(
        surf,
        (255, 255, 255),
        round_tuple((center_[0] - _w * 2, center_[1] - _h, _w, _h * 2))
    )
    pygame.draw.rect(
        surf,
        (255, 255, 255),
        round_tuple((center_[0] + _w, center_[1] - _h, _w, _h * 2))
    )
    return surf


print('\n', end='')


if len(sys.argv) <= 1:
    print(
        f'Usage: "{sys.executable}" "{__file__}" "path_to_video" [-nosound]'
    )
    sys.exit(0)

if subprocess.call([
    'ffmpeg',
    '-version'
], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE):
    error('FFMpeg not found!', fatal=True)
    sys.exit(1)

audio_format = 'wav'  # OGG may be better
current_path = os.getcwd()
fn = sys.argv[1]
use_sound = '-nosound' not in sys.argv[2:]
if not os.path.isfile(fn):
    error('File not found!', fatal=True)
    sys.exit(1)
audio_fn = fn + '.tmp_audio.' + audio_format
if use_sound:
    if os.access(audio_fn, os.F_OK):
        log('Removing old audio...')
        os.remove(audio_fn)
    log('Extracting audio...')
    subprocess.call([
        'ffmpeg',
        '-i',
        fn,
        '-q:a',
        str(0),
        '-map',
        'a',
        audio_fn
    ], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    log('Audio Extracted!')


class FPS:
    def __init__(
            self,
            _fps: any
    ) -> None:
        super(FPS, self).__init__()
        self.fps = float(_fps)
        self.frame_rate = 1 / self.fps
        self.is_paused = False
        self.last_tick = time.time()
        self.pause_time = self.last_tick

    def pause(self) -> None:
        self.pause_time = time.time()
        self.is_paused = True

    def resume(self) -> None:
        self.last_tick += time.time() - self.pause_time
        self.is_paused = False

    def run(self) -> None:
        self.last_tick = time.time()

    def try_tick(self) -> bool:
        if self.is_paused:
            return False
        now = time.time()
        if now < self.last_tick + self.frame_rate:
            return False
        self.last_tick += self.frame_rate
        return True


log('Init PyGame...')
pygame.init()
cap = cv2.VideoCapture(fn)
w, h = w_, h_ = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
clock = FPS(fps)
log('Video Length - ' + str(round(total_frames / fps)) + 's.')
log('Creating Window...')
screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
pygame.display.set_caption('py4vid')
pygame.display.set_icon(pygame.image.load(format_path('icon.ico')).convert_alpha())
if use_sound:
    log('Loading Sound...')
    sound = pygame.mixer.Sound(audio_fn)  # Fuck PyCharm
use_scale = False
running = True
pause_screen: pygame.Surface  # Fuck PyCharm
pause_screen_: pygame.Surface  # Fuck PyCharm


log('Running loop...')
ret, frame = cap.read()
if use_sound:
    log('Playing sound...')
    channel = sound.play()
clock.run()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.WINDOWRESIZED:
            w_, h_ = screen.get_size()
            use_scale = not (w == w_) or not (h_ == h)
            if clock.is_paused:
                pause_screen_ = pygame.transform.scale(pause_screen, (w_, h_))
                screen.blit(
                    draw_pause(pause_screen_.copy(), w_, h_),
                    (0, 0)
                )
                pygame.display.flip()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if clock.is_paused:
                    if use_sound:
                        channel.unpause()
                    clock.resume()
                    screen.blit(pause_screen_, (0, 0))
                    pygame.display.flip()
                else:
                    if use_sound:
                        channel.pause()
                    clock.pause()
                    pause_screen = pause_screen_ = screen.copy()
                    draw_pause(screen, w_, h_)
                    pygame.display.flip()
    if not clock.try_tick():
        continue
    if not ret:
        running = False
        break
    if use_scale:
        screen.blit(pygame.transform.scale(pygame.image.frombuffer(
            frame.tobytes(),
            frame.shape[1::-1],
            'BGR'
        ), (w_, h_)), (0, 0))
    else:
        screen.blit(pygame.image.frombuffer(
            frame.tobytes(),
            frame.shape[1::-1],
            'RGB'
        ), (0, 0))
    pygame.display.flip()
    ret, frame = cap.read()  # Some optimisations


if use_sound:
    log('Stopping Sound...')
    sound.stop()
    if os.access(audio_fn, os.F_OK):
        log('Removing Extracted Audio...')
        os.remove(audio_fn)
log('Quiting...')
pygame.quit()
