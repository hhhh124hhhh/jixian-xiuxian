import pygame
import sys
import random

# 初始化 pygame
pygame.init()

# 屏幕设置
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("极简修仙 MVP")

# 字体设置
font = pygame.font.SysFont("simhei", 24)

# 状态初始化
state = {
    "hp": 100,
    "mp": 50,
    "exp": 0,
    "pill": 0,
    "talent": random.randint(1, 10),
    "meditate_count": 0,
    "level": "炼气期",
    "log": []
}

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 128, 255)
RED = (255, 0, 0)
GRAY = (200, 200, 200)

# 等级进度控制
LEVELS = ["炼气期", "筑基期", "结丹期", "元婴期", "化神期", "飞升"]

def update_level():
    if state["exp"] >= 100:
        index = LEVELS.index(state["level"])
        if index < len(LEVELS) - 1:
            state["level"] = LEVELS[index + 1]
            state["exp"] = 0
            state["log"].append(f"突破至 {state['level']}！")

# 动作定义
def meditate():
    if state["hp"] <= 0:
        return
    state["mp"] = min(100, state["mp"] + 10)
    state["exp"] += 5 + state["talent"]
    state["meditate_count"] += 1
    state["hp"] -= 2
    if state["meditate_count"] % 5 == 0:
        state["pill"] += 1
        state["log"].append("连续打坐 5 次，获得丹药！")
    update_level()
    state["log"].append("你进入了打坐修炼状态。")

def consume_pill():
    if state["pill"] > 0:
        state["pill"] -= 1
        state["hp"] = min(100, state["hp"] + 20)
        state["mp"] = min(100, state["mp"] + 20)
        state["log"].append("你服下一颗丹药，恢复元气。")
    else:
        state["log"].append("没有丹药可用。")

def cultivate():
    if state["mp"] >= 20:
        state["mp"] -= 20
        state["exp"] += 15 + state["talent"] * 2
        update_level()
        state["log"].append("你运转心法，修为精进。")
    else:
        state["log"].append("仙力不足，无法修炼。")

def wait_turn():
    state["hp"] = max(0, state["hp"] - 1)
    if state["hp"] <= 0:
        state["log"].append("你元气耗尽，修炼失败。")

# 绘制状态栏
def draw_status():
    pygame.draw.rect(screen, GRAY, (50, 50, 700, 120))

    hp_text = font.render(f"生命: {state['hp']}", True, RED)
    mp_text = font.render(f"仙力: {state['mp']}", True, BLUE)
    exp_text = font.render(f"经验: {state['exp']}", True, GREEN)
    level_text = font.render(f"境界: {state['level']}", True, BLACK)
    pill_text = font.render(f"丹药: {state['pill']}", True, BLACK)
    
    screen.blit(hp_text, (70, 70))
    screen.blit(mp_text, (70, 100))
    screen.blit(exp_text, (250, 70))
    screen.blit(level_text, (250, 100))
    screen.blit(pill_text, (430, 70))

# 按钮绘制
def draw_button(text, x, y, action):
    rect = pygame.Rect(x, y, 120, 40)
    pygame.draw.rect(screen, BLUE, rect)
    label = font.render(text, True, WHITE)
    screen.blit(label, (x + 20, y + 8))
    return rect, action

# 主循环
clock = pygame.time.Clock()

buttons = [
    ("打坐", 100, 200, meditate),
    ("吃丹", 250, 200, consume_pill),
    ("修炼", 400, 200, cultivate),
    ("等待", 550, 200, wait_turn)
]

while True:
    screen.fill(WHITE)
    draw_status()

    # 绘制按钮
    button_rects = []
    for text, x, y, action in buttons:
        rect, act = draw_button(text, x, y, action)
        button_rects.append((rect, act))

    # 绘制日志
    log_start_y = 280
    recent_logs = state["log"][-8:]
    for i, log in enumerate(recent_logs):
        log_text = font.render(log, True, BLACK)
        screen.blit(log_text, (70, log_start_y + i * 30))

    # 事件监听
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            for rect, act in button_rects:
                if rect.collidepoint(mouse_pos):
                    act()

    pygame.display.flip()
    clock.tick(30)
