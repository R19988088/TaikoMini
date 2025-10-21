"""
连段显示模块 (Combo Display Module)
负责连段数字和文字的加载、渲染和管理
"""

import pygame
from pathlib import Path


class ComboDisplay:
    """
    连段显示类
    
    功能：
    - 加载连段数字图片（白色、银色、金色）
    - 加载连段文字图片
    - 绘制连段显示（支持1-4位数）
    - 根据连段数自动选择颜色（10-49银色，50+金色）
    """
    
    def __init__(self):
        """初始化连段显示系统"""
        # 连段图片资源
        self.combo_text_img = None  # 连段文字图片
        self.combo_numbers_white = {}   # 白色数字 0-9（保留，未使用）
        self.combo_numbers_silver = {}  # 银色数字 0-9（10-49连段使用）
        self.combo_numbers_golden = {}  # 金色数字 0-9（50+连段使用）
        
        # 加载所有连段图片
        self.load_combo_images()
    
    def load_combo_images(self):
        """
        加载连段图片资源
        
        文件命名规则：
        - combo_1_00.png 到 combo_1_09.png: 白色数字 0-9
        - combo_2_00.png 到 combo_2_09.png: 银色数字 0-9
        - combo_3_00.png 到 combo_3_09.png: 金色数字 0-9
        - combo_txt_02 #66.png: 连段文字图片
        """
        try:
            combo_dir = Path("lib/res/Texture/combo")
            
            # 加载连段文字图片
            self.combo_text_img = pygame.image.load(
                str(combo_dir / "combo_txt_02 #66.png")
            ).convert_alpha()
            print(f"OK - Loaded combo text image")
            
            # 加载三种颜色的数字图片（0-9）
            color_names = {
                1: ("white", self.combo_numbers_white),
                2: ("silver", self.combo_numbers_silver),
                3: ("golden", self.combo_numbers_golden)
            }
            
            for color_id, (color_name, target_dict) in color_names.items():
                for digit in range(10):
                    filename = f"combo_{color_id}_{digit:02d}.png"
                    try:
                        img = pygame.image.load(str(combo_dir / filename)).convert_alpha()
                        target_dict[digit] = img
                    except Exception as e:
                        print(f"Warning: Could not load {filename}: {e}")
                
                print(f"OK - Total combo numbers loaded: W={len(self.combo_numbers_white)}, S={len(self.combo_numbers_silver)}, G={len(self.combo_numbers_golden)}")
                    
        except Exception as e:
            print(f"Error loading combo images: {e}")
            self.combo_text_img = None
            self.combo_numbers_white = {}
            self.combo_numbers_silver = {}
            self.combo_numbers_golden = {}
    
    def draw(self, screen, combo, screen_width, screen_height, drum_center_x, drum_center_y, scaled_drum_height):
        """
        绘制连段显示
        
        参数:
            screen: Pygame 屏幕对象
            combo: 当前连段数
            screen_width, screen_height: 屏幕尺寸
            drum_center_x, drum_center_y: 鼓的中心位置
            scaled_drum_height: 缩放后的鼓图片高度
        """
        # 10以下不显示连段
        if combo < 10:
            return
        
        # === 位置参数配置 ===
        # 基础Y位置：鼓底部向下的偏移
        base_y_offset = 50
        combo_y = drum_center_y + scaled_drum_height // 2 + base_y_offset
        
        # 边界检查：确保在屏幕内
        bottom_margin = 400
        if combo_y > screen_height - bottom_margin:
            combo_y = screen_height - bottom_margin
        
        # 水平位置（相对鼓中心）
        combo_x_offset = 0
        combo_x = drum_center_x + combo_x_offset
        
        # === 绘制连段文字 ===
        if self.combo_text_img:
            # 文字位置微调
            text_x_offset = 0
            text_y_offset = 300
            text_x = combo_x + text_x_offset
            text_y = combo_y + text_y_offset
            
            # 文字缩放
            text_scale = 1.21
            if text_scale != 1.0:
                original_size = self.combo_text_img.get_size()
                new_size = (
                    int(original_size[0] * text_scale),
                    int(original_size[1] * text_scale)
                )
                scaled_text_img = pygame.transform.smoothscale(self.combo_text_img, new_size)
            else:
                scaled_text_img = self.combo_text_img
            
            # 绘制文字
            text_rect = scaled_text_img.get_rect(center=(text_x, text_y))
            screen.blit(scaled_text_img, text_rect)
            
            # 文字和数字间距
            text_number_spacing = 30
            combo_y += text_number_spacing
        
        # === 绘制连段数字 ===
        # 数字位置微调
        number_x_offset = 0
        number_y_offset = 110  # 上移90像素（200 - 90）
        number_x = combo_x + number_x_offset
        number_y = combo_y + number_y_offset
        
        # 数字缩放配置
        silver_scale = 2.42  # 银色数字（10-49连段）
        golden_scale = 2.42  # 金色数字（50+连段）
        
        # 数字间距（负值=重叠）
        digit_spacing = -20
        
        # 转换连段数为字符串
        combo_str = str(combo)
        
        # 收集所有要绘制的数字图片
        digit_images = []
        for digit_char in combo_str:
            digit = int(digit_char)
            
            # 根据连段数选择颜色
            if combo >= 50:
                # 50+连段：金色
                if digit in self.combo_numbers_golden:
                    digit_images.append((digit, self.combo_numbers_golden[digit], golden_scale))
            else:
                # 10-49连段：银色
                if digit in self.combo_numbers_silver:
                    digit_images.append((digit, self.combo_numbers_silver[digit], silver_scale))
        
        # 计算总宽度（用于居中）
        total_width = 0
        for i, (digit, img, scale) in enumerate(digit_images):
            scaled_width = int(img.get_width() * scale)
            total_width += scaled_width
            if i < len(digit_images) - 1:
                total_width += digit_spacing
        
        # 计算起始位置（居中）
        start_x = number_x - total_width // 2
        
        # 逐个绘制数字
        current_x = start_x
        for i, (digit, img, scale) in enumerate(digit_images):
            # 应用缩放
            if scale != 1.0:
                original_size = img.get_size()
                new_size = (
                    int(original_size[0] * scale),
                    int(original_size[1] * scale)
                )
                combo_img = pygame.transform.smoothscale(img, new_size)
            else:
                combo_img = img.copy()
            
            # 计算当前数字位置
            digit_x = current_x + combo_img.get_width() // 2
            
            # 绘制数字
            num_rect = combo_img.get_rect(center=(digit_x, number_y))
            screen.blit(combo_img, num_rect)
            
            # 移动到下一个数字位置
            current_x += combo_img.get_width() + digit_spacing

