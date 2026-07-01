"""
AI Driven Game Suite

Game: Dino Runner

Description:
A Python implementation of the Chrome Dino game with
optional rule-based AI control.

Technologies:
- Python
- Pygame
"""

import os
import random

import pygame

SCRIPT_DIR = os.path.dirname(__file__)
ASSET_DIR  = os.path.join(SCRIPT_DIR, "assets")

DINO_FRAMES   = ["dino1.png", "dino2.png"]
CACTUS_IMAGES = ["cactus.png", "cactus2.png"]

WIDTH, GAME_HEIGHT, HUD_HEIGHT = 600, 150, 90
HEIGHT = GAME_HEIGHT + HUD_HEIGHT
GROUND_Y = GAME_HEIGHT - 30
GRAVITY, JUMP_V, SPEED = 0.8, -12, 6
DINO_SIZE = 20
CACTUS_W_OPTIONS, CACTUS_H_OPTIONS = [12,18,24], [24,30,36]

# Asset loading utilities
def find_file(filename):
    for folder in [ASSET_DIR, SCRIPT_DIR]:
        if not os.path.isdir(folder): continue
        for f in os.listdir(folder):
            if f.lower() == filename.lower():
                return os.path.join(folder,f)
    return None

def load_scaled(filename, size):
    p = find_file(filename)
    if not p:
        print(f"[!] Missing {filename}")
        return None
    try:
        img = pygame.image.load(p).convert_alpha()
        if size: img = pygame.transform.smoothscale(img,size)
        print(f"[+] Loaded {os.path.basename(p)}")
        return img
    except Exception as e:
        print(f"[x] {filename}: {e}")
        return None

# Main game loop
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Dino - AI Mode")
    clock  = pygame.time.Clock()
    font   = pygame.font.SysFont(None, 24)

    dino_imgs = [load_scaled(f,(DINO_SIZE*2,DINO_SIZE*2)) for f in DINO_FRAMES]
    cactus_imgs = [i for f in CACTUS_IMAGES if (i:=load_scaled(f,(24,36)))]

    # HUD layout
    hud_top = GAME_HEIGHT + 10
    score_pos = (20, hud_top)
    ai_pos    = (WIDTH-100, hud_top)
    checkbox_rect = pygame.Rect(WIDTH//2-40, hud_top+30, 18,18)
    label_pos = (checkbox_rect.right+8, checkbox_rect.top-2)

    class Dino:
        def __init__(s): s.reset()
        def reset(s): s.x,s.y,s.v,s.alive,s.frame,s.t=50,GROUND_Y,0,True,0,0
        def jump(s):  s.v=JUMP_V if s.y>=GROUND_Y else s.v
        def upd(s,dt):
            s.t+=dt
            if s.t>120: s.t=0; s.frame=(s.frame+1)%max(1,len([i for i in dino_imgs if i]))
            s.v+=GRAVITY; s.y+=s.v
            if s.y>GROUND_Y: s.y,v=GROUND_Y,0; s.v=0
        def draw(s):
            imgs=[i for i in dino_imgs if i]; img=imgs[s.frame%len(imgs)] if imgs else None
            if img: 
                iw,ih=img.get_size(); screen.blit(img,(s.x-iw//2,s.y-ih))
            else: pygame.draw.rect(screen,(60,60,60),(s.x,s.y-DINO_SIZE,DINO_SIZE,DINO_SIZE))
        def rect(s): return pygame.Rect(s.x,s.y-DINO_SIZE,DINO_SIZE,DINO_SIZE)

    class Cactus:
        def __init__(s,x):
            s.x=x; s.w=random.choice(CACTUS_W_OPTIONS); s.h=random.choice(CACTUS_H_OPTIONS)
            if cactus_imgs:
                raw=random.choice(cactus_imgs)
                s.img=pygame.transform.smoothscale(raw,(s.w,s.h))
            else: s.img=None
        def upd(s): s.x-=SPEED
        def draw(s):
            if s.img: screen.blit(s.img,(s.x,GROUND_Y-s.h))
            else: pygame.draw.rect(screen,(34,139,34),(s.x,GROUND_Y-s.h,s.w,s.h))
        def hit(s,r): return r.colliderect(pygame.Rect(s.x,GROUND_Y-s.h,s.w,s.h))

    dino=Dino(); obs=[]; t=0; score=0; ai=False; over=False; run=True
    while run:
        dt=clock.tick(60)
        for e in pygame.event.get():
            if e.type==pygame.QUIT: run=False
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE: run=False
                if e.key==pygame.K_a: ai=not ai
                if e.key==pygame.K_r or (e.key==pygame.K_SPACE and over):
                    dino.reset(); obs.clear(); score=0; over=False
                elif e.key==pygame.K_SPACE and not (ai or over): dino.jump()
            if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                if checkbox_rect.collidepoint(e.pos): ai=not ai
                elif over: dino.reset(); obs.clear(); score=0; over=False
                elif not ai and e.pos[1]<GAME_HEIGHT: dino.jump()

        if not over:
            t+=dt
            if t>1200: obs.append(Cactus(WIDTH+20)); t=0
            if ai and obs:
                nxt=next((o for o in obs if o.x+o.w>=dino.x),None)
                if nxt and nxt.x-dino.x<120 and dino.y>=GROUND_Y: dino.jump()
            dino.upd(dt)
            for o in obs[:]:
                o.upd()
                if o.hit(dino.rect()): over=True; dino.alive=False
                if o.x+o.w<0: obs.remove(o); score+=1

        screen.fill((235,235,235))
        pygame.draw.line(screen,(0,0,0),(0,GROUND_Y+1),(WIDTH,GROUND_Y+1),2)
        dino.draw(); [o.draw() for o in obs]

        # HUD
        screen.blit(font.render(f"Score: {score}",True,(0,0,0)),score_pos)
        screen.blit(font.render(f"AI: {'ON' if ai else 'OFF'}",True,(0,0,0)),ai_pos)

        pygame.draw.rect(screen,(255,255,255),checkbox_rect)
        pygame.draw.rect(screen,(80,80,80),checkbox_rect,2)
        if ai:
            pygame.draw.line(screen,(30,30,30),(checkbox_rect.left+3,checkbox_rect.centery),
                             (checkbox_rect.centerx,checkbox_rect.bottom-4),3)
            pygame.draw.line(screen,(30,30,30),(checkbox_rect.centerx,checkbox_rect.bottom-4),
                             (checkbox_rect.right-3,checkbox_rect.top+4),3)
        screen.blit(font.render("AI Mode",True,(0,0,0)),label_pos)

        if over:
            txt=font.render("GAME OVER - Click or press R/Space to restart",True,(200,0,0))
            screen.blit(txt,txt.get_rect(center=(WIDTH//2,GAME_HEIGHT+10)))

        pygame.display.flip()
    pygame.quit()

if __name__=="__main__":
    main()
