"""
AI Driven Game Suite

Game: 2048
Description:
A Python implementation of the classic 2048 game with an optional
Expectimax-based AI agent.

Technologies:
- Python
- Pygame
"""

import pygame
import random
import sys
import copy
import math
from functools import lru_cache

SIZE = 4
TILE_SIZE = 100
MARGIN = 8
BOTTOM_AREA = 140
BOARD_PIXELS = SIZE * TILE_SIZE + (SIZE + 1) * MARGIN
WINDOW_W = BOARD_PIXELS + 40
WINDOW_H = BOARD_PIXELS + BOTTOM_AREA
WINDOW = (WINDOW_W, WINDOW_H)

# Tile colors
COLORS = {
    0:(205,193,180), 2:(238,228,218), 4:(237,224,200),
    8:(242,177,121), 16:(245,149,99), 32:(246,124,95),
    64:(246,94,59), 128:(237,207,114), 256:(237,204,97),
    512:(237,200,80), 1024:(237,197,63), 2048:(237,194,46)
}

# Game logic
def spawn_tile(board):
    empty = [(r,c) for r in range(SIZE) for c in range(SIZE) if board[r][c]==0]
    if empty:
        r,c = random.choice(empty)
        board[r][c] = 4 if random.random() < 0.1 else 2

def compress(row):
    new = [x for x in row if x!=0]
    new += [0]*(SIZE-len(new))
    return new

def merge(row):
    score = 0
    for i in range(SIZE-1):
        if row[i] != 0 and row[i] == row[i+1]:
            row[i] *= 2
            row[i+1] = 0
            score += row[i]
    return row, score

def move_left(board):
    changed = False
    total_score = 0
    newb = []
    for r in range(SIZE):
        row = board[r][:]
        row = compress(row)
        row, s = merge(row)
        total_score += s
        row = compress(row)
        newb.append(row)
        if row != board[r]:
            changed = True
    return newb, changed, total_score

def rotate(board):
    return [list(row) for row in zip(*board[::-1])]

def move(board, dir):  # 0:left 1:up 2:right 3:down
    b = copy.deepcopy(board)
    for _ in range(dir):
        b = rotate(b)
    newb, changed, sc = move_left(b)
    for _ in range((4 - dir) % 4):
        newb = rotate(newb)
    return newb, changed, sc

def any_moves(board):
    for d in range(4):
        b, c, _ = move(board, d)
        if c:
            return True
    return False

# Board conversion utilities
def board_to_tuple(board):
    return tuple(v for row in board for v in row)

def tuple_to_board(tup):
    it = iter(tup)
    return [[next(it) for _ in range(SIZE)] for _ in range(SIZE)]

def get_available_moves_from_tuple(board_tup):
    board = tuple_to_board(board_tup)
    moves = []
    for d in range(4):
        bnext, changed, sc = move(board, d)
        if changed:
            moves.append((d, board_to_tuple(bnext)))
    return moves

def get_empty_cells_from_tuple(board_tup):
    board = tuple_to_board(board_tup)
    return [(r,c) for r in range(SIZE) for c in range(SIZE) if board[r][c] == 0]

# Heuristic evaluation
def heuristic_board(board):
    # Heuristic weights
    W_EMPTIES = 2700.0
    W_MONOTONICITY = 47.0
    W_SMOOTHNESS = -0.12
    W_MAX_CORNER = 1000.0

    empties = sum(1 for r in range(SIZE) for c in range(SIZE) if board[r][c] == 0)

    # smoothness: sum of absolute log differences between neighbors (lower is better)
    smoothness = 0.0
    for r in range(SIZE):
        for c in range(SIZE):
            v = board[r][c]
            if v == 0: continue
            if c+1 < SIZE and board[r][c+1] != 0:
                smoothness += abs(math.log2(v) - math.log2(board[r][c+1]))
            if r+1 < SIZE and board[r+1][c] != 0:
                smoothness += abs(math.log2(v) - math.log2(board[r+1][c]))

    # monotonicity: reward monotone rows/cols
    def monotonicity_1d(line):
        score_inc = 0.0
        for i in range(len(line)-1):
            a = line[i]
            b = line[i+1]
            if a == 0 or b == 0:
                continue
            score_inc += (math.log2(a) - math.log2(b))
        return score_inc

    mono = 0.0
    for r in range(SIZE):
        row = [board[r][c] for c in range(SIZE)]
        mono += max(monotonicity_1d(row), monotonicity_1d(row[::-1]))
    for c in range(SIZE):
        col = [board[r][c] for r in range(SIZE)]
        mono += max(monotonicity_1d(col), monotonicity_1d(col[::-1]))

    # Reward keeping the largest tile in a corner
    max_tile = max(v for row in board for v in row)
    corners = [board[0][0], board[0][SIZE-1], board[SIZE-1][0], board[SIZE-1][SIZE-1]]
    max_in_corner = 1.0 if max_tile in corners else 0.0

    score = (W_EMPTIES * empties) + (W_MONOTONICITY * mono) + (W_SMOOTHNESS * smoothness) + (W_MAX_CORNER * max_in_corner)
    return score

# Expectimax AI
# Depth param you can tune: 3 recommended (balanced)
EXPECTIMAX_DEPTH = 3

@lru_cache(maxsize=200000)
def expectimax_value(board_tup, depth, is_player):
    # board_tup is tuple(length=SIZE*SIZE)
    board = tuple_to_board(board_tup)

    # terminal or leaf
    if depth == 0 or not any_moves(board):
        return heuristic_board(board)

    if is_player:
        # max node
        best = -float('inf')
        for d, child_tup in get_available_moves_from_tuple(board_tup):
            val = expectimax_value(child_tup, depth-1, False)
            if val > best:
                best = val
        return best if best != -float('inf') else heuristic_board(board)
    else:
        # chance node: average over empty cells spawn (2 w/0.9, 4 w/0.1)
        empties = get_empty_cells_from_tuple(board_tup)
        if not empties:
            return heuristic_board(board)
        total = 0.0
        p2 = 0.9
        p4 = 0.1
        # Evaluate all possible tile spawns
        for (r,c) in empties:
            b_list = tuple_to_board(board_tup)
            b_list[r][c] = 2
            v2 = expectimax_value(board_to_tuple(b_list), depth-1, True)
            b_list[r][c] = 4
            v4 = expectimax_value(board_to_tuple(b_list), depth-1, True)
            total += (p2 * v2 + p4 * v4)
        return total / len(empties)

def expectimax_ai(board, depth=EXPECTIMAX_DEPTH):
    board_tup = board_to_tuple(board)
    best_dir = None
    best_val = -float('inf')
    # iterate over available moves
    for d, child_tup in get_available_moves_from_tuple(board_tup):
        val = expectimax_value(child_tup, depth-1, False)
        if val > best_val:
            best_val = val
            best_dir = d
    return best_dir

# Rendering
def draw_board(screen, board, font, rect):
    screen.fill((187,173,160))
    bx,by = rect.left, rect.top
    for r in range(SIZE):
        for c in range(SIZE):
            v = board[r][c]
            x = bx + c*(TILE_SIZE+MARGIN)
            y = by + r*(TILE_SIZE+MARGIN)
            color = COLORS.get(v, (60,58,50))
            pygame.draw.rect(screen, color, (x,y,TILE_SIZE,TILE_SIZE), border_radius=6)
            if v:
                tile_font = pygame.font.SysFont(None, 36 if v < 1024 else 28)
                txt = tile_font.render(str(v), True, (0,0,0) if v<8 else (255,255,255))
                tw,th = txt.get_size()
                screen.blit(txt, (x + TILE_SIZE//2 - tw//2, y + TILE_SIZE//2 - th//2))

# Main game loop
def main():
    pygame.init()
    screen = pygame.display.set_mode(WINDOW)
    pygame.display.set_caption("2048 - Expectimax AI (depth=3)")
    font = pygame.font.SysFont(None, 26)
    score_font = pygame.font.SysFont(None, 26)  # plain
    clock = pygame.time.Clock()

    board_rect = pygame.Rect(20, 10, BOARD_PIXELS, BOARD_PIXELS)
    cx = WINDOW_W // 2

    board = [[0]*SIZE for _ in range(SIZE)]
    spawn_tile(board); spawn_tile(board)
    ai_enabled = False
    total_score = 0

    score_y = BOARD_PIXELS + 15
    checkbox_rect = pygame.Rect(cx-140, BOARD_PIXELS+50, 18, 18)
    label_pos = (checkbox_rect.right + 8, checkbox_rect.top - 2)
    restart_rect = pygame.Rect(cx+80, BOARD_PIXELS+40, 120, 36)

    drag_start = None
    drag_end = None
    drag_threshold = 30

    running = True
    while running:
        clock.tick(60)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False

            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_a:
                    ai_enabled = not ai_enabled
                if not ai_enabled:
                    if ev.key == pygame.K_LEFT:
                        b, changed, sc = move(board, 0)
                        if changed:
                            board = b; spawn_tile(board); total_score += sc
                    if ev.key == pygame.K_RIGHT:
                        b, changed, sc = move(board, 2)
                        if changed:
                            board = b; spawn_tile(board); total_score += sc
                    if ev.key == pygame.K_UP:
                        b, changed, sc = move(board, 1)
                        if changed:
                            board = b; spawn_tile(board); total_score += sc
                    if ev.key == pygame.K_DOWN:
                        b, changed, sc = move(board, 3)
                        if changed:
                            board = b; spawn_tile(board); total_score += sc
                if ev.key == pygame.K_r:
                    board = [[0]*SIZE for _ in range(SIZE)]; spawn_tile(board); spawn_tile(board); total_score = 0
                    expectimax_value.cache_clear()  # clear cache on restart

            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx,my = ev.pos
                if checkbox_rect.collidepoint((mx,my)):
                    ai_enabled = not ai_enabled
                elif restart_rect.collidepoint((mx,my)):
                    board = [[0]*SIZE for _ in range(SIZE)]; spawn_tile(board); spawn_tile(board); total_score = 0
                    expectimax_value.cache_clear()
                elif board_rect.collidepoint((mx,my)):
                    drag_start = ev.pos
                    drag_end = None

            if ev.type == pygame.MOUSEMOTION:
                if drag_start is not None:
                    drag_end = ev.pos

            if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                if drag_start is not None and drag_end is not None and not ai_enabled:
                    sx,sy = drag_start
                    ex,ey = drag_end
                    dx = ex - sx
                    dy = ey - sy
                    if abs(dx) < drag_threshold and abs(dy) < drag_threshold:
                        pass
                    else:
                        if abs(dx) > abs(dy):
                            d = 2 if dx > 0 else 0
                        else:
                            d = 3 if dy > 0 else 1
                        b, changed, sc = move(board, d)
                        if changed:
                            board = b; spawn_tile(board); total_score += sc
                drag_start = None
                drag_end = None

        # AI turn (Expectimax)
        if ai_enabled:
            # Determine the best move
            try:
                d = expectimax_ai(board, depth=EXPECTIMAX_DEPTH)
            except RecursionError:
                d = None
            if d is None:
                ai_enabled = False
            else:
                b, changed, sc = move(board, d)
                if changed:
                    board = b; spawn_tile(board); total_score += sc

        
        draw_board(screen, board, font, board_rect)

        
        stxt = score_font.render(f"Score: {total_score}", True, (0,0,0))
        screen.blit(stxt, stxt.get_rect(center=(cx, score_y)))

        
        pygame.draw.rect(screen, (255,255,255), checkbox_rect)
        pygame.draw.rect(screen, (80,80,80), checkbox_rect, 2)
        if ai_enabled:
            pygame.draw.line(screen, (30,30,30), (checkbox_rect.left+3, checkbox_rect.centery), (checkbox_rect.centerx, checkbox_rect.bottom-4), 3)
            pygame.draw.line(screen, (30,30,30), (checkbox_rect.centerx, checkbox_rect.bottom-4), (checkbox_rect.right-3, checkbox_rect.top+4), 3)
        label = font.render("AI (click box to toggle)", True, (0,0,0))
        screen.blit(label, label_pos)

        
        pygame.draw.rect(screen, (230,230,230), restart_rect, border_radius=6)
        pygame.draw.rect(screen, (150,150,150), restart_rect, 2, border_radius=6)
        rt = font.render("Restart (R)", True, (30,30,30))
        screen.blit(rt, rt.get_rect(center=restart_rect.center))

        # Game over message
        if not any_moves(board):
            over = font.render("GAME OVER - Press R to restart", True, (180,30,30))
            screen.blit(over, over.get_rect(center=(cx, BOARD_PIXELS + 95)))

        # Drag indicator
        if drag_start and drag_end:
            pygame.draw.line(screen, (60,60,60), drag_start, drag_end, 3)
            pygame.draw.circle(screen, (60,60,60), drag_end, 5)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
