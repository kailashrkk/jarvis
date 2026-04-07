"""
ui.py -- Fullscreen Jarvis face UI for the 720x720 touchscreen.

States:
    IDLE       -- animated face, eyes blinking, waiting for wake word
    LISTENING  -- face alert, mouth slightly open, recording
    THINKING   -- eyes looking up, xylophone chime playing
    SPEAKING   -- mouth animating, response text scrolling
    
Tap anywhere to trigger voice input (same as wake word).
Battery level shown top right.
Last response shown at bottom.
"""

import pygame
import math
import time
import threading
import random
import sys
import os

# Add jarvis directory to path
sys.path.insert(0, '/home/kailash/jarvis')

WIDTH  = 720
HEIGHT = 720
FPS    = 30

# Colors
BLACK      = (0,   0,   0)
WHITE      = (255, 255, 255)
DARK_GREY  = (20,  20,  20)
MID_GREY   = (50,  50,  50)
LIGHT_GREY = (180, 180, 180)
CYAN       = (0,   220, 220)
DIM_CYAN   = (0,   120, 120)
RED        = (220, 60,  60)
GREEN      = (60,  220, 60)
YELLOW     = (220, 220, 60)

# Face geometry
CX, CY     = WIDTH // 2, HEIGHT // 2 - 40
EYE_OFFSET = 90
EYE_Y      = CY - 60
EYE_R      = 38
PUPIL_R    = 16
MOUTH_Y    = CY + 80
MOUTH_W    = 120
MOUTH_H    = 30


class JarvisState:
    IDLE      = "IDLE"
    LISTENING = "LISTENING"
    THINKING  = "THINKING"
    SPEAKING  = "SPEAKING"


class JarvisUI:
    def __init__(self):
        pygame.init()
        pygame.mouse.set_visible(False)

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("Jarvis")
        self.clock  = pygame.time.Clock()

        self.font_large  = pygame.font.SysFont("dejavusans", 32)
        self.font_medium = pygame.font.SysFont("dejavusans", 24)
        self.font_small  = pygame.font.SysFont("dejavusans", 18)

        self.state        = JarvisState.IDLE
        self.response_text = ""
        self.status_text   = "Say 'Hey Jarvis'"
        self.battery_pct   = 100

        # Animation state
        self.t            = 0.0
        self.blink_t      = 0.0
        self.blink_dur    = 0.12
        self.next_blink   = random.uniform(2.0, 5.0)
        self.is_blinking  = False
        self.mouth_open   = 0.0   # 0.0 closed, 1.0 fully open
        self.pupil_offset = [0, 0]
        self.think_angle  = 0.0

        # Touch callback
        self.on_tap = None

        self._running = True

    def set_state(self, state: str, status: str = "", response: str = ""):
        self.state = state
        if status:
            self.status_text = status
        if response:
            self.response_text = response

    def set_battery(self, pct: int):
        self.battery_pct = pct

    def run(self):
        while self._running:
            dt = self.clock.tick(FPS) / 1000.0
            self.t   += dt
            self.blink_t += dt

            self._handle_events()
            self._update(dt)
            self._draw()
            pygame.display.flip()

        pygame.quit()

    def stop(self):
        self._running = False

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._running = False
            elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                if self.on_tap and self.state == JarvisState.IDLE:
                    threading.Thread(target=self.on_tap, daemon=True).start()

    # ------------------------------------------------------------------
    # Animation update
    # ------------------------------------------------------------------

    def _update(self, dt: float):
        # Blink logic
        if not self.is_blinking and self.t > self.next_blink:
            self.is_blinking = True
            self.blink_t     = 0.0
            self.next_blink  = self.t + random.uniform(2.5, 6.0)

        if self.is_blinking and self.blink_t > self.blink_dur:
            self.is_blinking = False

        # Mouth animation
        if self.state == JarvisState.SPEAKING:
            self.mouth_open = 0.4 + 0.6 * abs(math.sin(self.t * 8))
        elif self.state == JarvisState.LISTENING:
            self.mouth_open = 0.2 + 0.1 * math.sin(self.t * 4)
        elif self.state == JarvisState.THINKING:
            self.mouth_open = 0.1
            self.think_angle = self.t * 2
        else:
            self.mouth_open = max(0.0, self.mouth_open - dt * 3)

        # Pupil wander in IDLE
        if self.state == JarvisState.IDLE:
            self.pupil_offset = [
                int(8 * math.sin(self.t * 0.7)),
                int(5 * math.sin(self.t * 0.5))
            ]
        elif self.state == JarvisState.THINKING:
            self.pupil_offset = [-8, -10]
        else:
            self.pupil_offset = [0, 0]

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _draw(self):
        self.screen.fill(DARK_GREY)
        self._draw_face()
        self._draw_status()
        self._draw_response()
        self._draw_battery()
        self._draw_state_indicator()

    def _draw_face(self):
        color = {
            JarvisState.IDLE:      CYAN,
            JarvisState.LISTENING: GREEN,
            JarvisState.THINKING:  YELLOW,
            JarvisState.SPEAKING:  CYAN,
        }.get(self.state, CYAN)

        # Eyes
        for sign in (-1, 1):
            ex = CX + sign * EYE_OFFSET
            ey = EYE_Y

            # Eye white/outline
            pygame.draw.circle(self.screen, MID_GREY, (ex, ey), EYE_R + 4)
            pygame.draw.circle(self.screen, color, (ex, ey), EYE_R + 4, 2)

            # Blink -- draw closing rectangle over eye
            if self.is_blinking:
                progress = self.blink_t / self.blink_dur
                close    = int(EYE_R * 2 * math.sin(progress * math.pi))
                blink_rect = pygame.Rect(ex - EYE_R - 4, ey - EYE_R - 4, (EYE_R + 4) * 2, close)
                pygame.draw.rect(self.screen, DARK_GREY, blink_rect)
            else:
                # Pupil
                px = ex + self.pupil_offset[0]
                py = ey + self.pupil_offset[1]
                pygame.draw.circle(self.screen, color, (px, py), PUPIL_R)
                pygame.draw.circle(self.screen, WHITE, (px - 5, py - 5), 5)

        # Mouth
        mouth_rect = pygame.Rect(
            CX - MOUTH_W // 2,
            MOUTH_Y,
            MOUTH_W,
            int(MOUTH_H * self.mouth_open + 6)
        )
        pygame.draw.rect(self.screen, color, mouth_rect, border_radius=12)
        if self.mouth_open < 0.1:
            pygame.draw.rect(self.screen, color, mouth_rect, 2, border_radius=12)

        # Thinking orbit dot
        if self.state == JarvisState.THINKING:
            ox = int(CX + 60 * math.cos(self.think_angle))
            oy = int(CY + 60 * math.sin(self.think_angle))
            pygame.draw.circle(self.screen, YELLOW, (ox, oy), 8)
            ox2 = int(CX + 60 * math.cos(self.think_angle + math.pi))
            oy2 = int(CY + 60 * math.sin(self.think_angle + math.pi))
            pygame.draw.circle(self.screen, DIM_CYAN, (ox2, oy2), 5)

    def _draw_status(self):
        surf = self.font_medium.render(self.status_text, True, LIGHT_GREY)
        rect = surf.get_rect(centerx=WIDTH // 2, y=30)
        self.screen.blit(surf, rect)

    def _draw_response(self):
        if not self.response_text:
            return
        # Word wrap
        words  = self.response_text.split()
        lines  = []
        line   = ""
        for word in words:
            test = line + " " + word if line else word
            if self.font_small.size(test)[0] < WIDTH - 60:
                line = test
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)

        y = HEIGHT - 20 - len(lines) * 24
        for l in lines:
            surf = self.font_small.render(l, True, LIGHT_GREY)
            rect = surf.get_rect(centerx=WIDTH // 2, y=y)
            self.screen.blit(surf, rect)
            y += 24

    def _draw_battery(self):
        pct   = self.battery_pct
        color = GREEN if pct > 30 else YELLOW if pct > 15 else RED
        bw, bh = 48, 22
        bx, by = WIDTH - bw - 16, 16
        pygame.draw.rect(self.screen, MID_GREY, (bx, by, bw, bh), border_radius=4)
        fill_w = int((bw - 4) * pct / 100)
        pygame.draw.rect(self.screen, color, (bx + 2, by + 2, fill_w, bh - 4), border_radius=3)
        pygame.draw.rect(self.screen, LIGHT_GREY, (bx, by, bw, bh), 1, border_radius=4)
        pygame.draw.rect(self.screen, LIGHT_GREY, (bx + bw, by + 6, 4, bh - 12), border_radius=2)
        surf = self.font_small.render(f"{pct}%", True, LIGHT_GREY)
        self.screen.blit(surf, (bx - 36, by + 3))

    def _draw_state_indicator(self):
        labels = {
            JarvisState.IDLE:      ("READY",     DIM_CYAN),
            JarvisState.LISTENING: ("LISTENING", GREEN),
            JarvisState.THINKING:  ("THINKING",  YELLOW),
            JarvisState.SPEAKING:  ("SPEAKING",  CYAN),
        }
        label, color = labels.get(self.state, ("", WHITE))
        surf = self.font_small.render(label, True, color)
        rect = surf.get_rect(centerx=WIDTH // 2, y=HEIGHT - 50)
        self.screen.blit(surf, rect)


if __name__ == "__main__":
    ui = JarvisUI()
    ui.status_text = "Say 'Hey Jarvis'"

    # Demo state cycling
    def demo():
        import time
        states = [
            (JarvisState.IDLE,      "Say 'Hey Jarvis'",     ""),
            (JarvisState.LISTENING, "Listening...",          ""),
            (JarvisState.THINKING,  "Let me think...",       ""),
            (JarvisState.SPEAKING,  "Speaking",              "The capital of France is Paris."),
            (JarvisState.IDLE,      "Say 'Hey Jarvis'",     "The capital of France is Paris."),
        ]
        time.sleep(2)
        for state, status, response in states:
            ui.set_state(state, status, response)
            time.sleep(3)

    threading.Thread(target=demo, daemon=True).start()
    ui.run()
