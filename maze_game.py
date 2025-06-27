import pygame
import random
from collections import deque

pygame.init()

display_info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = display_info.current_w, display_info.current_h

MIN_CELL_SIZE = 30

def calculate_grid(width, height, min_cell_size):
    max_cols = width // min_cell_size
    max_rows = height // min_cell_size
    best_cell_size = min_cell_size
    best_cols = max_cols
    best_rows = max_rows
    for size in range(min_cell_size, min(width, height) + 1):
        cols = width // size
        rows = height // size
        if cols == 0 or rows == 0:
            break
        area_covered = cols * size * rows * size
        best_area = best_cols * best_cell_size * best_rows * best_cell_size
        if area_covered > best_area:
            best_cell_size = size
            best_cols = cols
            best_rows = rows
    return best_cols, best_rows, best_cell_size

COLS, ROWS, CELL_SIZE = calculate_grid(SCREEN_WIDTH, SCREEN_HEIGHT, MIN_CELL_SIZE)
MAZE_WIDTH = CELL_SIZE * COLS
MAZE_HEIGHT = CELL_SIZE * ROWS

screen = pygame.display.set_mode((MAZE_WIDTH, MAZE_HEIGHT))
pygame.display.set_caption("Динамический лабиринт с плавной сменой стен и защитой зоны вокруг игрока")

clock = pygame.time.Clock()
FPS = 30

COLOR_BG = (28, 30, 35)
COLOR_WALL = (70, 70, 70)
COLOR_PERIMETER = (40, 40, 40)
COLOR_BOTTOM_WALL = (60, 60, 80)
COLOR_PLAYER = (0, 190, 0)
COLOR_START = (0, 120, 255)
COLOR_END = (190, 30, 30)

PERIMETER_THICKNESS = 2
BOTTOM_WALL_THICKNESS = 4

ANIMATION_SPEED = 0.08  # скорость анимации (за кадр)

maze = [[1]*COLS for _ in range(ROWS)]
player_pos = [1, 1]
start_pos = [1, 1]
end_pos = [COLS // 2, ROWS // 2]

def carve_passages_from(cx, cy, maze, visited):
    directions = [(0,-2),(0,2),(-2,0),(2,0)]
    random.shuffle(directions)
    visited.add((cx,cy))
    maze[cy][cx] = 0
    for dx,dy in directions:
        nx, ny = cx + dx, cy + dy
        if (PERIMETER_THICKNESS <= nx < COLS - PERIMETER_THICKNESS and
            PERIMETER_THICKNESS <= ny < ROWS - BOTTOM_WALL_THICKNESS and
            (nx, ny) not in visited):
            maze[cy + dy//2][cx + dx//2] = 0
            carve_passages_from(nx, ny, maze, visited)

def generate_maze():
    new_maze = [[1]*COLS for _ in range(ROWS)]

    # Периметр
    for t in range(PERIMETER_THICKNESS):
        for x in range(COLS):
            new_maze[t][x] = 1
        for y in range(ROWS):
            new_maze[y][t] = 1
            new_maze[y][COLS-1 - t] = 1

    # Нижняя толстая стена
    for t in range(BOTTOM_WALL_THICKNESS):
        for x in range(COLS):
            new_maze[ROWS - 1 - t][x] = 1

    visited = set()
    start_x = max(start_pos[0], PERIMETER_THICKNESS)
    start_y = max(start_pos[1], PERIMETER_THICKNESS)
    carve_passages_from(start_x, start_y, new_maze, visited)

    new_maze[start_pos[1]][start_pos[0]] = 0
    new_maze[end_pos[1]][end_pos[0]] = 0

    # Очищаем вокруг старта
    for dy in (-1,0,1):
        for dx in (-1,0,1):
            sx = start_pos[0] + dx
            sy = start_pos[1] + dy
            if 0 <= sx < COLS and 0 <= sy < ROWS:
                new_maze[sy][sx] = 0

    return new_maze

def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

animating_cells = {}  # {(x,y): [from_state, to_state, progress(0..1)]}

def start_animation(x, y, from_state, to_state):
    animating_cells[(x,y)] = [from_state, to_state, 0.0]

def update_animation():
    finished = []
    for (x,y), (from_s, to_s, prog) in animating_cells.items():
        prog += ANIMATION_SPEED
        if prog >= 1.0:
            prog = 1.0
            current_maze[y][x] = to_s
            finished.append((x,y))
        animating_cells[(x,y)][2] = prog
    for cell in finished:
        del animating_cells[cell]

def draw_cell(x, y):
    if (x,y) in animating_cells:
        from_s, to_s, prog = animating_cells[(x,y)]
        if from_s == 1 and to_s == 0:
            color = lerp_color(COLOR_WALL, COLOR_BG, prog)
        elif from_s == 0 and to_s == 1:
            color = lerp_color(COLOR_BG, COLOR_WALL, prog)
        else:
            color = COLOR_WALL if to_s == 1 else COLOR_BG
        rect = pygame.Rect(x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(screen, color, rect)
    else:
        rect = pygame.Rect(x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE)
        color = COLOR_WALL if current_maze[y][x] == 1 else COLOR_BG
        pygame.draw.rect(screen, color, rect)

def draw_maze():
    screen.fill(COLOR_BG)
    for y in range(ROWS):
        for x in range(COLS):
            # Периметр и нижняя стена рисуем цветом отдельно
            if y >= ROWS - BOTTOM_WALL_THICKNESS:
                pygame.draw.rect(screen, COLOR_BOTTOM_WALL, (x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE))
            elif (x < PERIMETER_THICKNESS or x >= COLS - PERIMETER_THICKNESS or y < PERIMETER_THICKNESS):
                pygame.draw.rect(screen, COLOR_PERIMETER, (x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE))
            else:
                draw_cell(x, y)

    # Старт и финиш
    pygame.draw.rect(screen, COLOR_START, (start_pos[0]*CELL_SIZE, start_pos[1]*CELL_SIZE, CELL_SIZE, CELL_SIZE))
    pygame.draw.rect(screen, COLOR_END, (end_pos[0]*CELL_SIZE, end_pos[1]*CELL_SIZE, CELL_SIZE, CELL_SIZE))

    # Игрок
    pr = pygame.Rect(
        player_pos[0]*CELL_SIZE + CELL_SIZE//6,
        player_pos[1]*CELL_SIZE + CELL_SIZE//6,
        CELL_SIZE*2//3,
        CELL_SIZE*2//3
    )
    pygame.draw.rect(screen, COLOR_PLAYER, pr)

def can_move(nx, ny):
    return 0 <= nx < COLS and 0 <= ny < ROWS and current_maze[ny][nx] == 0

def move_player(dx, dy):
    nx, ny = player_pos[0] + dx, player_pos[1] + dy
    if can_move(nx, ny):
        player_pos[0], player_pos[1] = nx, ny

def get_differences(old, new):
    diffs = []
    for y in range(ROWS):
        for x in range(COLS):
            if old[y][x] != new[y][x]:
                diffs.append((x,y,new[y][x]))
    random.shuffle(diffs)
    return deque(diffs)

def start_wall_change_animation():
    global diff_queue
    changes_per_frame = 3
    px, py = player_pos
    changes_started = 0
    while diff_queue and changes_started < changes_per_frame:
        x, y, val = diff_queue.popleft()
        dist = abs(x - px) + abs(y - py)  # манхэттенское расстояние
        if dist > 5:  # не меняем в зоне 5 клеток вокруг игрока
            from_val = current_maze[y][x]
            if from_val != val:
                start_animation(x, y, from_val, val)
                changes_started += 1
        else:
            # Пропускаем клетки рядом с игроком, но если очередь опустела — прекращаем
            continue

current_maze = generate_maze()
target_maze = generate_maze()
diff_queue = deque()
last_change = pygame.time.get_ticks()
change_interval = random.randint(7000, 12000)

touch_start_pos = None
SWIPE_THRESHOLD = CELL_SIZE // 3

running = True
while running:
    dt = clock.tick(FPS)
    now = pygame.time.get_ticks()

    if not diff_queue and now - last_change > change_interval:
        new_maze = generate_maze()
        diff_queue = get_differences(current_maze, new_maze)
        target_maze = new_maze
        last_change = now
        change_interval = random.randint(7000, 12000)

    update_animation()
    start_wall_change_animation()
    draw_maze()
    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.FINGERDOWN:
            touch_start_pos = (event.x * MAZE_WIDTH, event.y * MAZE_HEIGHT)

        elif event.type == pygame.FINGERUP:
            if touch_start_pos is not None:
                x_end, y_end = event.x * MAZE_WIDTH, event.y * MAZE_HEIGHT
                dx = x_end - touch_start_pos[0]
                dy = y_end - touch_start_pos[1]
                touch_start_pos = None

                if abs(dx) > abs(dy) and abs(dx) > SWIPE_THRESHOLD:
                    if dx > 0:
                        move_player(1, 0)
                    else:
                        move_player(-1, 0)
                elif abs(dy) > SWIPE_THRESHOLD:
                    if dy > 0:
                        move_player(0, 1)
                    else:
                        move_player(0, -1)

    if player_pos == end_pos:
        # Перезапуск при победе
        current_maze = generate_maze()
        target_maze = current_maze.copy()
        diff_queue.clear()
        player_pos[0], player_pos[1] = start_pos[0], start_pos[1]
        last_change = now
        change_interval = random.randint(7000, 12000)

pygame.quit()
