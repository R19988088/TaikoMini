"""
练习模式控件模块
Practice Mode Controls Module

独立的练习模式控件，包括速度、暂停、自动、复位按钮
Independent practice mode controls including speed, pause, auto, and reset buttons
"""

import pygame

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 200, 100)
GRAY = (127, 127, 127)
DARK_GRAY = (50, 50, 50)
LIGHT_BLUE = (100, 150, 255)

class PracticeControls:
    """练习模式控件类"""
    
    def __init__(self, screen):
        """
        初始化练习模式控件
        
        Args:
            screen: pygame.Surface - 游戏屏幕
        """
        self.screen = screen
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()

        # 字体设置
        self.font_small = pygame.font.Font(None, 36)
        self.font_large = pygame.font.Font(None, 72)
        
        # 控件状态
        self.is_auto_play = False
        
        # UI元素
        self.speed_buttons = {}
        self.play_pause_rect = pygame.Rect(0, 0, 0, 0)
        self.restart_rect = pygame.Rect(0, 0, 0, 0)
        self.auto_play_rect = pygame.Rect(0, 0, 0, 0)
        
        # 更新布局
        self.update_layout()

    def update_layout(self):
        """更新控件布局"""
        self.screen_width = self.screen.get_width()
        self.screen_height = self.screen.get_height()
        
        # --- 控件区域布局 ---
        self.control_area_height = 80
        # 控件位置：移到顶部
        self.control_area_y = 20
        
        # 定义比例和间距
        ratios = {'speed': 1.8, 'action': 2.5}
        speeds = [0.5, 0.8, 1.0, 1.3]
        num_speed_buttons = len(speeds)
        num_action_buttons = 3  # Pause, Auto, Restart
        total_buttons = num_speed_buttons + num_action_buttons
        button_spacing = 10
        
        total_ratio_units = (num_speed_buttons * ratios['speed']) + (num_action_buttons * ratios['action'])
        
        # 控件条占用屏幕宽度的90%
        total_bar_width = self.screen_width * 0.9
        total_spacing = (total_buttons - 1) * button_spacing
        total_button_width = total_bar_width - total_spacing
        
        width_per_ratio_unit = total_button_width / total_ratio_units
        
        button_widths = {
            'speed': width_per_ratio_unit * ratios['speed'],
            'action': width_per_ratio_unit * ratios['action']
        }
        button_height = 40
        
        # 居中整个控件条
        start_x = (self.screen_width - total_bar_width) / 2
        current_x = start_x
        start_y = self.control_area_y

        # 速度按钮
        self.speed_buttons = {}
        for speed in speeds:
            rect = pygame.Rect(current_x, start_y, button_widths['speed'], button_height)
            self.speed_buttons[speed] = rect
            current_x += button_widths['speed'] + button_spacing

        # 其他按钮 (Pause, Auto, Restart)
        self.play_pause_rect = pygame.Rect(current_x, start_y, button_widths['action'], button_height)
        current_x += button_widths['action'] + button_spacing
        
        self.auto_play_rect = pygame.Rect(current_x, start_y, button_widths['action'], button_height)
        current_x += button_widths['action'] + button_spacing
        
        self.restart_rect = pygame.Rect(current_x, start_y, button_widths['action'], button_height)
        
    def handle_event(self, event, current_speed, is_paused):
        """
        处理事件
        
        Args:
            event: pygame.Event - 事件对象
            current_speed: float - 当前速度
            is_paused: bool - 是否暂停
            
        Returns:
            dict or None: 如果控件被激活则返回动作字典，否则返回None
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 速度按钮
            for speed, rect in self.speed_buttons.items():
                if rect.collidepoint(event.pos):
                    if speed != current_speed:
                        return {'action': 'change_speed', 'value': speed}
            
            # 控制按钮
            if self.play_pause_rect.collidepoint(event.pos):
                return {'action': 'toggle_pause'}
            
            if self.restart_rect.collidepoint(event.pos):
                return {'action': 'restart'}
                
            if self.auto_play_rect.collidepoint(event.pos):
                self.is_auto_play = not self.is_auto_play
                return {'action': 'toggle_auto'}

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                self.is_auto_play = not self.is_auto_play
                return {'action': 'toggle_auto'}

        return None
        
    def draw(self, current_speed, is_paused):
        """
        绘制控件
        
        Args:
            current_speed: float - 当前速度
            is_paused: bool - 是否暂停
        """
        # 速度按钮
        for speed, rect in self.speed_buttons.items():
            bg_color = GREEN if abs(speed - current_speed) < 0.01 else DARK_GRAY
            pygame.draw.rect(self.screen, bg_color, rect, border_radius=5)
            pygame.draw.rect(self.screen, WHITE, rect, 2, border_radius=5)
            
            speed_text = f"{speed}x"
            text_surface = self.font_small.render(speed_text, True, WHITE)
            text_rect = text_surface.get_rect(center=rect.center)
            self.screen.blit(text_surface, text_rect)

        # Play/Pause按钮
        pygame.draw.rect(self.screen, DARK_GRAY, self.play_pause_rect, border_radius=8)
        
        btn_text = "Play" if is_paused else "Pause"
        text_surface = self.font_small.render(btn_text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.play_pause_rect.center)
        self.screen.blit(text_surface, text_rect)

        # Auto Play按钮
        bg_color = LIGHT_BLUE if self.is_auto_play else DARK_GRAY
        pygame.draw.rect(self.screen, bg_color, self.auto_play_rect, border_radius=8)
        text_surface = self.font_small.render("Auto", True, WHITE)
        text_rect = text_surface.get_rect(center=self.auto_play_rect.center)
        self.screen.blit(text_surface, text_rect)
        
        # Restart按钮
        pygame.draw.rect(self.screen, DARK_GRAY, self.restart_rect, border_radius=8)
        text_surface = self.font_small.render("Restart", True, WHITE)
        text_rect = text_surface.get_rect(center=self.restart_rect.center)
        self.screen.blit(text_surface, text_rect)
    
    def get_auto_play_state(self):
        """获取自动播放状态"""
        return self.is_auto_play
    
    def set_auto_play_state(self, state):
        """设置自动播放状态"""
        self.is_auto_play = state
