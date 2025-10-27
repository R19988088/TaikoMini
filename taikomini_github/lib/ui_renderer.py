"""
UI渲染模块
UI Renderer Module

负责处理歌曲选择界面的所有UI渲染，包括：
- 主界面绘制
- 分类选择器绘制
- 歌曲按钮绘制
- 倾斜圆角矩形按钮
- 发光呼吸效果
- 文字描边和阴影
- 动画效果

主要类：
- UIRenderer: UI渲染器，提供统一的UI渲染接口
"""

import pygame
import math
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from lib.song_button import SongButton


class UIRenderer:
    """
    UI渲染器
    UI Renderer
    
    负责处理歌曲选择界面的所有UI渲染
    """
    
    def __init__(self, screen, resource_loader):
        """
        初始化UI渲染器
        Initialize UI renderer
        
        Args:
            screen: pygame显示表面
            resource_loader: 资源加载器
        """
        # ==================== 基础属性 ====================
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.resource_loader = resource_loader
        
        # ==================== 资源 ====================
        self.diff_images = resource_loader.load_difficulty_images()
        self.bg_images = resource_loader.load_background_images()
        self.fonts = resource_loader.load_ui_fonts()
        
        # ==================== UI设置 ====================
        self.button_height = 140
        self.button_spacing = 2
        self.slant_angle = 5
        
        # ==================== 颜色常量 ====================
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.ORANGE = (247, 152, 36)
        self.YELLOW = (255, 242, 0)
        self.GREEN = (0, 200, 100)
        self.BLUE = (0, 162, 232)
        self.GRAY = (100, 100, 100)
        
        # ==================== 染色缓存 ====================
        self._colored_b1_cache = {}  # 缓存染色后的b1图像 {category: colored_surface}
        
        # ==================== 难度映射 ====================
        self.DIFF_MAPPING = {
            'Easy': 1,
            'Normal': 2,
            'Hard': 3,
            'Oni': 4,
            'Edit': 5
        }
    
    def draw_main_screen(self, title: str, hint: str):
        """
        绘制主界面
        Draw main screen
        
        Args:
            title: 页面标题
            hint: 提示文字
        """
        # 填充背景色
        self.screen.fill(self.ORANGE)
        
        # 绘制标题
        title_surface = self.fonts['header'].render(title, True, self.WHITE)
        self.screen.blit(title_surface, (self.width // 2 - title_surface.get_width() // 2, 30))
        
        # 绘制提示
        hint_surface = self.fonts['small'].render(hint, True, self.WHITE)
        self.screen.blit(hint_surface, (self.width // 2 - hint_surface.get_width() // 2, self.height - 40))
    
    def draw_categories(self, categories: List[str], selected_category_index: int):
        """
        绘制分类选择器
        Draw category selector
        
        Args:
            categories: 分类列表
            selected_category_index: 当前选中的分类索引
        """
        category_top = 120
        category_height = 60
        category_width = self.width // 5
        
        # ==================== 绘制左右箭头 ====================
        arrow_size = 30
        
        # 左箭头
        left_arrow_x = 30
        arrow_y = category_top + category_height // 2
        points = [
            (left_arrow_x + arrow_size, arrow_y - arrow_size//2),
            (left_arrow_x + arrow_size, arrow_y + arrow_size//2),
            (left_arrow_x, arrow_y)
        ]
        pygame.draw.polygon(self.screen, self.WHITE, points)
        
        # 右箭头
        right_arrow_x = self.width - 60
        points = [
            (right_arrow_x, arrow_y - arrow_size//2),
            (right_arrow_x, arrow_y + arrow_size//2),
            (right_arrow_x + arrow_size, arrow_y)
        ]
        pygame.draw.polygon(self.screen, self.WHITE, points)
        
        # ==================== 绘制分类框 ====================
        # 显示3个分类框（中心对齐选中分类）
        start_idx = max(0, selected_category_index - 1)
        for i in range(3):
            cat_idx = start_idx + i
            if cat_idx >= len(categories):
                break
            
            box_x = 80 + i * category_width
            box_width = category_width - 20
            
            # 根据是否选中设置颜色
            is_selected = (cat_idx == selected_category_index)
            box_color = self.YELLOW if is_selected else self.WHITE
            border_width = 6 if is_selected else 3
            
            # 绘制分类框
            pygame.draw.rect(self.screen, box_color, 
                           (box_x, category_top, box_width, category_height), border_width)
            
            # 绘制分类名称
            cat_name = categories[cat_idx]
            if len(cat_name) > 8:
                cat_name = cat_name[:6] + ".."
            
            text_color = self.BLACK if is_selected else self.WHITE
            cat_text = self.fonts['category'].render(cat_name, True, text_color)
            text_rect = cat_text.get_rect(center=(box_x + box_width//2, category_top + category_height//2))
            self.screen.blit(cat_text, text_rect)
    
    def draw_song_buttons(self, buttons: List[SongButton], selected_index: int, 
                         scroll_offset: float, blink_time: float):
        """
        绘制歌曲按钮列表（性能优化版本）
        Draw song buttons list (performance optimized)
        
        Args:
            buttons: 歌曲按钮列表
            selected_index: 当前选中索引
            scroll_offset: 滚动偏移量
            blink_time: 闪烁动画时间
        """
        if not buttons:
            return
        
        start_y = 250
        
        # 计算所有歌曲的总高度（用于循环显示）
        total_height = self._calculate_total_height(buttons, selected_index)
        
        # 性能优化：预计算按钮位置，避免重复计算
        button_positions = self._precalculate_button_positions(buttons, selected_index, start_y)
        
        # 绘制函数：绘制一个歌曲按钮（优化版本）
        def draw_button_at_index(index, y_offset):
            button = buttons[index]
            is_selected = (index == selected_index)
            
            # 使用预计算的位置
            base_y = button_positions[index]
            button_y = base_y + y_offset - scroll_offset
            
            # 计算按钮高度 - 整体扩大25%，减小垂直间距
            if is_selected:
                actual_height = int((self.button_height + (100 if button.expanded else 0)) * 1.25)
            else:
                actual_height = int((self.button_height * 0.85) * 1.25)
            
            # 早期裁剪：如果完全在屏幕外则跳过
            if button_y > self.height + 100 or button_y + actual_height < -100:
                return False
            
            # 绘制按钮
            self.draw_slanted_button(button, button_y, is_selected, blink_time)
            return True
        
        # 优化：减少循环数量，只绘制必要的按钮
        start_loop = max(0, int(scroll_offset / total_height) - 1)
        end_loop = start_loop + 3  # 减少到3个循环
        
        # 绘制多个循环以覆盖屏幕
        for loop in range(start_loop, end_loop):
            y_offset = loop * total_height
            visible_count = 0
            for i in range(len(buttons)):
                if draw_button_at_index(i, y_offset):
                    visible_count += 1
            # 如果可见按钮太少，可以提前退出
            if visible_count == 0 and loop > start_loop:
                break
    
    def _precalculate_button_positions(self, buttons: List[SongButton], selected_index: int, start_y: int) -> List[int]:
        """
        预计算按钮位置，避免重复计算
        Pre-calculate button positions to avoid repeated calculations
        
        Args:
            buttons: 歌曲按钮列表
            selected_index: 当前选中索引
            start_y: 起始Y坐标
            
        Returns:
            List[int]: 每个按钮的Y位置列表
        """
        positions = []
        current_y = start_y
        
        for i, button in enumerate(buttons):
            positions.append(current_y)
            
            # 计算下一个按钮的位置 - 整体扩大25%，减小垂直间距
            if i == selected_index and button.expanded:
                current_y += int((self.button_height + 100) * 1.25) + 1  # 减小间距到1
            elif i == selected_index:
                current_y += int(self.button_height * 1.25) + 1  # 减小间距到1
            else:
                current_y += int((self.button_height * 0.85) * 1.25) + 1  # 减小间距到1
        
        return positions
    
    def draw_slanted_button(self, button: SongButton, y: int, is_selected: bool, blink_time: float):
        """
        绘制倾斜圆角矩形按钮
        Draw slanted rounded rectangle button
        
        Args:
            button: 歌曲按钮对象
            y: Y坐标
            is_selected: 是否选中
            blink_time: 闪烁动画时间
        """
        # 计算倾斜偏移
        slant = int(math.tan(math.radians(self.slant_angle)) * self.button_height)
        
        # 按钮尺寸 - 整体扩大25%
        if button.expanded:
            width = int((self.width - 200) * 1.40)  # 展开状态宽度
            height = int((self.button_height + 100) * 1.25)  # 扩大25%
        else:
            if is_selected:
                width = int((self.width - 200) * 1.40)  # 与展开状态宽度一致
                height = int(self.button_height * 1.25)  # 扩大25%
            else:
                width = int((self.width - 200) * 1.25)  # 扩大25%
                height = int((self.button_height * 0.85) * 1.25)  # 扩大25%
        
        x = (self.width - width) // 2
        
        # ==================== 绘制发光层（在b1之前，作为底层） ====================
        if is_selected and 2 in self.bg_images:
            self._draw_glow_effect(x, y, width, height, button.expanded, blink_time)
        
        # ==================== 绘制主背景（使用九宫格缩放） ====================
        if 1 in self.bg_images:
            bg_img = self.bg_images[1]
            
            # 如果有分类，先染色b1图像，再绘制
            if hasattr(button, 'category') and button.category:
                # 创建b1的染色副本
                colored_b1 = self._create_colored_b1(bg_img, button.category)
                # 使用染色后的b1绘制
                self._draw_nine_patch(colored_b1, x, y, width, height, border_ratio=0.28)
            else:
                # 不染色，直接绘制原始b1
                self._draw_nine_patch(bg_img, x, y, width, height, border_ratio=0.28)
        
        # ==================== 绘制信息背景和文字 ====================
        info_bg_bounds = None
        text_center_x = x + width // 2
        text_y = y  # 使用按钮顶部作为基准
        
        if is_selected and 3 in self.bg_images:
            info_bg_bounds = self._draw_info_background(x, y, width, height, button.expanded)
            text_center_x = info_bg_bounds[4]
            text_y = info_bg_bounds[1] + (info_bg_bounds[3] // 2) - 20
        
        # ==================== 绘制文字 ====================
        self._draw_button_text(button, text_center_x, text_y, is_selected, info_bg_bounds)
        
        # ==================== 绘制难度选择 ====================
        if button.expanded:
            # 传递info_bg_bounds以便难度选择可以基于b3图案宽度定位
            self._draw_difficulty_selection(button, y, height, info_bg_bounds)
    
    def _draw_nine_patch(self, img: pygame.Surface, x: int, y: int, width: int, height: int, border_ratio: float = 0.28):
        """
        使用九宫格缩放绘制图片（保持四角和边框不变形）
        Draw image using 9-patch scaling (keeps corners and borders undistorted)
        
        Args:
            img: 源图片
            x, y: 目标位置
            width, height: 目标尺寸
            border_ratio: 边框占图片宽度的比例（默认0.28即28%）
        """
        # 计算边框尺寸
        border_w = int(img.get_width() * border_ratio)
        border_h = int(img.get_height() * border_ratio)
        
        # 确保边框不超过图片尺寸的三分之一
        border_w = min(border_w, img.get_width() // 3)
        border_h = min(border_h, img.get_height() // 3)
        
        # 源图片的九宫格区域
        src_w = img.get_width()
        src_h = img.get_height()
        
        # 定义9个区域：[源x, 源y, 源宽, 源高, 目标x, 目标y, 目标宽, 目标高]
        patches = [
            # 左上角 (不拉伸)
            (0, 0, border_w, border_h, 
             x, y, border_w, border_h),
            # 上边 (水平拉伸)
            (border_w, 0, src_w - 2*border_w, border_h, 
             x + border_w, y, width - 2*border_w, border_h),
            # 右上角 (不拉伸)
            (src_w - border_w, 0, border_w, border_h, 
             x + width - border_w, y, border_w, border_h),
            # 左边 (垂直拉伸)
            (0, border_h, border_w, src_h - 2*border_h, 
             x, y + border_h, border_w, height - 2*border_h),
            # 中间 (双向拉伸)
            (border_w, border_h, src_w - 2*border_w, src_h - 2*border_h, 
             x + border_w, y + border_h, width - 2*border_w, height - 2*border_h),
            # 右边 (垂直拉伸)
            (src_w - border_w, border_h, border_w, src_h - 2*border_h, 
             x + width - border_w, y + border_h, border_w, height - 2*border_h),
            # 左下角 (不拉伸)
            (0, src_h - border_h, border_w, border_h, 
             x, y + height - border_h, border_w, border_h),
            # 下边 (水平拉伸)
            (border_w, src_h - border_h, src_w - 2*border_w, border_h, 
             x + border_w, y + height - border_h, width - 2*border_w, border_h),
            # 右下角 (不拉伸)
            (src_w - border_w, src_h - border_h, border_w, border_h, 
             x + width - border_w, y + height - border_h, border_w, border_h),
        ]
        
        # 绘制每个区域
        for src_x, src_y, src_w, src_h, dst_x, dst_y, dst_w, dst_h in patches:
            if src_w > 0 and src_h > 0 and dst_w > 0 and dst_h > 0:
                # 裁剪源区域
                subsurface = img.subsurface((src_x, src_y, src_w, src_h))
                # 缩放到目标尺寸
                scaled = pygame.transform.scale(subsurface, (int(dst_w), int(dst_h)))
                # 绘制到目标位置
                self.screen.blit(scaled, (int(dst_x), int(dst_y)))
    
    def _draw_glow_effect(self, x: int, y: int, width: int, height: int, 
                         expanded: bool, blink_time: float):
        """
        绘制发光效果
        Draw glow effect
        
        Args:
            x, y: 位置坐标
            width, height: 尺寸
            expanded: 是否展开
            blink_time: 闪烁时间
        """
        bg_img2 = self.bg_images[2]
        
        # 发光层要比主背景小一圈
        glow_scale = 1.0
        glow_width = int(width * glow_scale)
        glow_height = int(height * glow_scale)
        
        # 居中放置
        glow_x = x + (width - glow_width) // 2
        glow_y = y + (height - glow_height) // 2
        
        # 创建临时surface用于九宫格绘制
        temp_surf = pygame.Surface((glow_width, glow_height), pygame.SRCALPHA)
        
        # 在临时surface上使用九宫格绘制
        patches = []
        border_w = int(bg_img2.get_width() * 0.28)
        border_h = int(bg_img2.get_height() * 0.28)
        border_w = min(border_w, bg_img2.get_width() // 3)
        border_h = min(border_h, bg_img2.get_height() // 3)
        
        src_w = bg_img2.get_width()
        src_h = bg_img2.get_height()
        
        patches = [
            (0, 0, border_w, border_h, 0, 0, border_w, border_h),
            (border_w, 0, src_w - 2*border_w, border_h, border_w, 0, glow_width - 2*border_w, border_h),
            (src_w - border_w, 0, border_w, border_h, glow_width - border_w, 0, border_w, border_h),
            (0, border_h, border_w, src_h - 2*border_h, 0, border_h, border_w, glow_height - 2*border_h),
            (border_w, border_h, src_w - 2*border_w, src_h - 2*border_h, border_w, border_h, glow_width - 2*border_w, glow_height - 2*border_h),
            (src_w - border_w, border_h, border_w, src_h - 2*border_h, glow_width - border_w, border_h, border_w, glow_height - 2*border_h),
            (0, src_h - border_h, border_w, border_h, 0, glow_height - border_h, border_w, border_h),
            (border_w, src_h - border_h, src_w - 2*border_w, border_h, border_w, glow_height - border_h, glow_width - 2*border_w, border_h),
            (src_w - border_w, src_h - border_h, border_w, border_h, glow_width - border_w, glow_height - border_h, border_w, border_h),
        ]
        
        for src_x, src_y, s_w, s_h, dst_x, dst_y, d_w, d_h in patches:
            if s_w > 0 and s_h > 0 and d_w > 0 and d_h > 0:
                subsurface = bg_img2.subsurface((src_x, src_y, s_w, s_h))
                scaled = pygame.transform.scale(subsurface, (int(d_w), int(d_h)))
                temp_surf.blit(scaled, (int(dst_x), int(dst_y)))
        
        scaled_bg2 = temp_surf
        
        # 计算闪烁alpha（使用正弦波，呼吸效果）
        if expanded:
            base_intensity = 0.3
            wave_amplitude = 0.7
        else:
            base_intensity = 0.1
            wave_amplitude = 0.3
        
        fade = base_intensity + wave_amplitude * (0.5 + 0.5 * math.sin(blink_time / 500))
        
        # 使用pygame的transform来调整透明度
        temp_surf = scaled_bg2.copy()
        
        # 创建纯色surface来模拟亮度调整
        brightness = int(fade * 255)
        color_filter = pygame.Surface((glow_width, glow_height), pygame.SRCALPHA)
        color_filter.fill((brightness, brightness, brightness, 255))
        
        # 先复制原图
        result_surf = temp_surf.copy()
        # 使用MULT模式调整亮度
        result_surf.blit(color_filter, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        # 使用ADD混合模式绘制（发光效果）
        self.screen.blit(result_surf, (glow_x, glow_y), special_flags=pygame.BLEND_RGB_ADD)
    
    def _create_colored_b1(self, bg_img: pygame.Surface, category: str) -> pygame.Surface:
        """
        创建自定义b1图像（不再进行染色处理）
        Create custom b1 image (no longer applies coloring)
        
        Args:
            bg_img: 原始b1图像（如果使用自定义图片，这个参数可能被忽略）
            category: 分类名称
            
        Returns:
            自定义b1图像或原始图像
        """
        # 检查缓存
        if category in self._colored_b1_cache:
            return self._colored_b1_cache[category]
        
        from lib.config_manager import ConfigManager
        
        try:
            config = ConfigManager()
            category_info = config.get_category_info(category)
            
            if category_info and category_info[1]:  # 检查是否有b1图片文件名
                b1_image_filename = category_info[1]  # b1图片文件名
                
                # 尝试加载自定义b1图片
                custom_b1_img = self.resource_loader.load_custom_b1_image(b1_image_filename)
                if custom_b1_img:
                    # 缓存结果
                    self._colored_b1_cache[category] = custom_b1_img
                    return custom_b1_img
            
            # 如果没有自定义图片，返回原始图片
            self._colored_b1_cache[category] = bg_img
            return bg_img
        except Exception as e:
            print(f"Error loading custom b1 image: {e}")
            return bg_img
    
    def _draw_nine_patch_to_surface(self, img: pygame.Surface, target_surface: pygame.Surface, 
                                     x: int, y: int, width: int, height: int, border_ratio: float = 0.28):
        """
        使用九宫格缩放绘制图片到指定表面
        Draw image using 9-patch scaling to a specific surface
        
        Args:
            img: 源图片
            target_surface: 目标表面
            x, y: 目标位置
            width, height: 目标尺寸
            border_ratio: 边框占图片宽度的比例（默认0.28即28%）
        """
        # 计算边框尺寸
        border_w = int(img.get_width() * border_ratio)
        border_h = int(img.get_height() * border_ratio)
        
        # 九个区域的源坐标
        src_w = img.get_width()
        src_h = img.get_height()
        
        # 九个区域的目标尺寸
        corner_w = border_w
        corner_h = border_h
        center_w = width - 2 * border_w
        center_h = height - 2 * border_h
        
        # 绘制九个区域
        regions = [
            # (src_rect, dst_rect)
            # 左上角
            ((0, 0, border_w, border_h), (x, y, corner_w, corner_h)),
            # 上边
            ((border_w, 0, src_w - 2*border_w, border_h), (x + border_w, y, center_w, corner_h)),
            # 右上角
            ((src_w - border_w, 0, border_w, border_h), (x + width - border_w, y, corner_w, corner_h)),
            # 左边
            ((0, border_h, border_w, src_h - 2*border_h), (x, y + border_h, corner_w, center_h)),
            # 中心
            ((border_w, border_h, src_w - 2*border_w, src_h - 2*border_h), (x + border_w, y + border_h, center_w, center_h)),
            # 右边
            ((src_w - border_w, border_h, border_w, src_h - 2*border_h), (x + width - border_w, y + border_h, corner_w, center_h)),
            # 左下角
            ((0, src_h - border_h, border_w, border_h), (x, y + height - border_h, corner_w, corner_h)),
            # 下边
            ((border_w, src_h - border_h, src_w - 2*border_w, border_h), (x + border_w, y + height - border_h, center_w, corner_h)),
            # 右下角
            ((src_w - border_w, src_h - border_h, border_w, border_h), (x + width - border_w, y + height - border_h, corner_w, corner_h)),
        ]
        
        for src_rect, dst_rect in regions:
            src_surface = img.subsurface(src_rect)
            scaled = pygame.transform.smoothscale(src_surface, (dst_rect[2], dst_rect[3]))
            target_surface.blit(scaled, (dst_rect[0], dst_rect[1]))
    
    def _apply_category_color_to_surface_with_margin(self, surface: pygame.Surface, width: int, height: int, category: str, margin: int):
        """
        在表面上应用自定义genre_bg图片（带边距，避免覆盖b2，使用固定比例缩放）
        Apply custom genre_bg image to surface with margin (avoiding b2 overlap, using fixed scale ratio)
        
        Args:
            surface: 要应用图片的表面
            width, height: 表面尺寸
            category: 分类名称
            margin: 边距（像素）
        """
        from lib.config_manager import ConfigManager
        
        try:
            config = ConfigManager()
            category_info = config.get_category_info(category)
            
            if category_info and category_info[2]:  # 检查是否有genre_bg图片文件名
                genre_bg_image_filename = category_info[2]  # genre_bg图片文件名
                
                # 尝试加载自定义genre_bg图片作为背景
                custom_genre_bg_img = self.resource_loader.load_custom_genre_bg_image(genre_bg_image_filename)
                if custom_genre_bg_img:
                    # 获取缩放比例
                    scale_ratio = float(config.get_display_setting('genre_bg_scale_ratio', '1.0'))
                    
                    # 计算缩放后的尺寸（保持宽高比）
                    orig_width, orig_height = custom_genre_bg_img.get_size()
                    scaled_width = int(orig_width * scale_ratio)
                    scaled_height = int(orig_height * scale_ratio)
                    
                    # 缩放图片
                    scaled_bg = pygame.transform.smoothscale(custom_genre_bg_img, (scaled_width, scaled_height))
                    
                    # 计算居中位置
                    center_x = width // 2
                    center_y = height // 2
                    pos_x = center_x - scaled_width // 2
                    pos_y = center_y - scaled_height // 2
                    
                    # 将genre_bg图片绘制到表面上
                    surface.blit(scaled_bg, (pos_x, pos_y))
        except Exception as e:
            print(f"Error applying custom genre_bg image: {e}")
    
    def _apply_category_color_to_surface(self, surface: pygame.Surface, width: int, height: int, category: str):
        """
        在表面上应用自定义genre_bg图片（使用固定比例缩放）
        Apply custom genre_bg image to surface (using fixed scale ratio)
        
        Args:
            surface: 要应用图片的表面
            width, height: 表面尺寸
            category: 分类名称
        """
        from lib.config_manager import ConfigManager
        
        try:
            config = ConfigManager()
            category_info = config.get_category_info(category)
            
            if category_info and category_info[2]:  # 检查是否有genre_bg图片文件名
                genre_bg_image_filename = category_info[2]  # genre_bg图片文件名
                
                # 尝试加载自定义genre_bg图片作为背景
                custom_genre_bg_img = self.resource_loader.load_custom_genre_bg_image(genre_bg_image_filename)
                if custom_genre_bg_img:
                    # 获取缩放比例
                    scale_ratio = float(config.get_display_setting('genre_bg_scale_ratio', '1.0'))
                    
                    # 计算缩放后的尺寸（保持宽高比）
                    orig_width, orig_height = custom_genre_bg_img.get_size()
                    scaled_width = int(orig_width * scale_ratio)
                    scaled_height = int(orig_height * scale_ratio)
                    
                    # 缩放图片
                    scaled_bg = pygame.transform.smoothscale(custom_genre_bg_img, (scaled_width, scaled_height))
                    
                    # 计算居中位置
                    center_x = width // 2
                    center_y = height // 2
                    pos_x = center_x - scaled_width // 2
                    pos_y = center_y - scaled_height // 2
                    
                    # 将genre_bg图片绘制到表面上
                    surface.blit(scaled_bg, (pos_x, pos_y))
        except Exception as e:
            print(f"Error applying custom genre_bg image: {e}")
    
    def _draw_category_color_overlay_rect(self, x: int, y: int, width: int, height: int, category: str):
        """
        在按钮背景上绘制自定义genre_bg图片（使用固定比例缩放）
        Draw custom genre_bg image on button background (using fixed scale ratio)
        
        Args:
            x, y: 按钮位置
            width, height: 按钮尺寸
            category: 分类名称
        """
        from lib.config_manager import ConfigManager
        
        try:
            config = ConfigManager()
            category_info = config.get_category_info(category)
            
            if category_info and category_info[2]:  # 检查是否有genre_bg图片文件名
                genre_bg_image_filename = category_info[2]  # genre_bg图片文件名
                
                # 尝试加载自定义genre_bg图片作为背景
                custom_genre_bg_img = self.resource_loader.load_custom_genre_bg_image(genre_bg_image_filename)
                if custom_genre_bg_img:
                    # 获取缩放比例
                    scale_ratio = float(config.get_display_setting('genre_bg_scale_ratio', '1.0'))
                    
                    # 计算缩放后的尺寸（保持宽高比）
                    orig_width, orig_height = custom_genre_bg_img.get_size()
                    scaled_width = int(orig_width * scale_ratio)
                    scaled_height = int(orig_height * scale_ratio)
                    
                    # 缩放图片
                    scaled_bg = pygame.transform.smoothscale(custom_genre_bg_img, (scaled_width, scaled_height))
                    
                    # 计算居中位置
                    center_x = x + width // 2
                    center_y = y + height // 2
                    pos_x = center_x - scaled_width // 2
                    pos_y = center_y - scaled_height // 2
                    
                    # 将genre_bg图片绘制到屏幕上
                    self.screen.blit(scaled_bg, (pos_x, pos_y))
        except Exception as e:
            print(f"Error drawing custom genre_bg image: {e}")
    
    def _draw_info_background(self, x: int, y: int, width: int, height: int, expanded: bool) -> Tuple[int, int, int, int, int]:
        """
        绘制信息背景
        Draw info background
        
        Args:
            x, y: 位置坐标
            width, height: 尺寸
            expanded: 是否展开
            
        Returns:
            Tuple: (info_x, info_y, info_width, info_height, text_center_x)
        """
        info_bg = self.bg_images[3]
        
        # 缩放到合适大小
        if expanded:
            # 展开状态宽度减小，适应难度图标布局
            info_width = int(width * 0.87)
            info_height = int(height * 0.42)
            info_y_offset = int(height * 0.14) + 5
        else:
            # 未展开状态的面板，左右边距和上下边距一致
            info_height = int(height * 0.65 * 0.7)  # 缩小30%
            # Y轴居中
            info_y_offset = (height - info_height) // 2
            # 左右边距与上下边距一致
            vertical_margin = info_y_offset
            info_width = width - 2 * vertical_margin
        
        info_x = x + (width - info_width) // 2
        info_y = y + info_y_offset
        # 使用九宫格缩放保持圆角不变形
        self._draw_nine_patch(info_bg, info_x, info_y, info_width, info_height, border_ratio=0.28)
        
        text_center_x = info_x + info_width // 2
        return (info_x, info_y, info_width, info_height, text_center_x)
    
    def _draw_button_text(self, button: SongButton, text_center_x: int, text_y: int, 
                          is_selected: bool, info_bg_bounds: Optional[Tuple]):
        """
        绘制按钮文字
        Draw button text
        
        Args:
            button: 歌曲按钮对象
            text_center_x: 文字中心X坐标
            text_y: 文字Y坐标
            is_selected: 是否选中
            info_bg_bounds: 信息背景边界
        """
        # 确定显示的标题和副标题（优先CN）
        display_title = button.title_cn if button.title_cn else button.title
        display_subtitle = button.subtitle_cn if button.subtitle_cn else button.subtitle
        
        # 只在有info_bg_bounds时才设置裁剪（选中状态）
        old_clip = None
        if info_bg_bounds:
            clip_rect = pygame.Rect(info_bg_bounds[0], info_bg_bounds[1], info_bg_bounds[2], info_bg_bounds[3])
            old_clip = self.screen.get_clip()
            self.screen.set_clip(clip_rect)
        
        # 根据不同状态计算垂直居中位置
        if not is_selected:
            # 未选中：和主背景(b1图片)垂直居中
            # 计算按钮的实际高度
            button_height = int((self.button_height * 0.85) * 1.25)
            title_center_y = text_y + button_height // 2
        elif is_selected and info_bg_bounds:
            # 选中：和信息背景垂直居中
            available_height = info_bg_bounds[3] * 0.7
            title_center_y = info_bg_bounds[1] + int(info_bg_bounds[3] * 0.15) + int(available_height // 2)
        else:
            # 选中但无信息背景：和主背景垂直居中
            title_center_y = text_y + int(self.button_height * 1.25) // 2
        
        # 渲染标题
        title_text = self.fonts['title_cn'].render(display_title, True, self.WHITE)
        title_height = title_text.get_height()
        
        # 预渲染副标题以获取高度
        subtitle_text = None
        subtitle_height = 0
        if button.expanded and display_subtitle:
            subtitle_text = self.fonts['subtitle'].render(display_subtitle, True, self.WHITE)
            subtitle_height = subtitle_text.get_height()
        
        # 计算标题Y位置（考虑副标题的情况，整体垂直居中）
        if button.expanded and display_subtitle:
            gap = 6
            total_height = title_height + gap + subtitle_height
            title_y = title_center_y - total_height // 2
        else:
            title_y = title_center_y - title_height // 2
        
        # 水平居中
        title_x = text_center_x - title_text.get_width() // 2
        
        # 绘制标题描边和主体
        self._draw_text_with_outline(title_text, title_x, title_y, 3, 16)
        
        # 渲染副标题（仅在激活状态下显示）
        if button.expanded and display_subtitle and subtitle_text:
            gap = 6
            subtitle_y = title_y + title_height + gap
            subtitle_x = text_center_x - subtitle_text.get_width() // 2
            
            # 绘制副标题描边和主体
            self._draw_text_with_outline(subtitle_text, subtitle_x, subtitle_y, 2, 12)
        
        # 恢复裁剪区域
        if old_clip is not None:
            self.screen.set_clip(old_clip)
    
    def _draw_text_with_outline(self, text_surface: pygame.Surface, x: int, y: int, 
                               outline_radius: int, outline_points: int):
        """
        绘制带描边的文字（优化版本）
        Draw text with outline (optimized version)
        
        Args:
            text_surface: 文字表面
            x, y: 位置坐标
            outline_radius: 描边半径
            outline_points: 描边点数
        """
        # 优化：减少描边点数以提高性能
        optimized_points = min(outline_points, 8)  # 最多8个点
        
        # 预创建描边表面数组，避免重复复制
        outline_surfaces = []
        for i in range(optimized_points):
            angle = 2 * math.pi * i / optimized_points
            dx = int(outline_radius * math.cos(angle))
            dy = int(outline_radius * math.sin(angle))
            
            # 创建黑色描边表面
            outline_surface = text_surface.copy()
            # 使用像素数组操作来创建黑色描边，保持透明度
            outline_array = pygame.surfarray.pixels3d(outline_surface)
            outline_array[:, :, :] = 0  # 设置为黑色
            del outline_array
            
            outline_surfaces.append((outline_surface, dx, dy))
        
        # 批量绘制描边
        for outline_surface, dx, dy in outline_surfaces:
            self.screen.blit(outline_surface, (x + dx, y + dy))
        
        # 绘制主体文字
        self.screen.blit(text_surface, (x, y))
    
    def _draw_difficulty_selection(self, button: SongButton, y: int, height: int, info_bg_bounds: Optional[Tuple] = None):
        """
        绘制难度选择
        Draw difficulty selection
        
        Args:
            button: 歌曲按钮对象
            y: Y坐标
            height: 高度
            info_bg_bounds: 信息背景边界 (info_x, info_y, info_width, info_height, text_center_x)
        """
        diff_y = y + height - 90
        
        # 检查是否有Edit难度
        has_edit = 'Edit' in button.difficulties
        
        # 根据是否有Edit决定显示的难度列表
        if has_edit:
            difficulty_list = ['Easy', 'Normal', 'Hard', 'Oni', 'Edit']
        else:
            difficulty_list = ['Easy', 'Normal', 'Hard', 'Oni']
        
        all_options = ['Back'] + difficulty_list
        
        # 获取实际图标宽度（不缩放）
        icon_width = 100
        if 1 in self.diff_images:
            icon_width = self.diff_images[1].get_width()
        
        back_width = icon_width
        if 'back_1' in self.diff_images:
            back_width = self.diff_images['back_1'].get_width()
        
        icon_height = 80  # 原始高度
        
        # 所有图标保持原始尺寸，不缩放
        # 计算总宽度
        total_icon_width = back_width + icon_width * len(difficulty_list)
        
        # 根据是否有Edit调整间距，大幅增加间距以填充空间
        if has_edit:
            # 有Edit时，增加间距
            icon_spacing = 30
        else:
            # 没有Edit时，更大的间距
            icon_spacing = 40
        
        # 计算总宽度和起始位置
        total_spacing = (len(all_options) - 1) * icon_spacing
        total_width = total_icon_width + total_spacing
        
        # 居中显示（通过增加间距，两侧空白已经自然减少）
        diff_start_x = (self.width - total_width) / 2
        
        # 存储难度按钮位置信息（供事件处理使用）
        if not hasattr(button, 'diff_button_rects'):
            button.diff_button_rects = {}
        button.diff_button_rects.clear()
        
        # 绘制各个选项
        current_x = diff_start_x
        for j, option in enumerate(all_options):
            # 判断是返回按钮还是难度
            if option == 'Back':
                self._draw_back_button(button, current_x, diff_y, j)
                current_x += back_width + icon_spacing
            else:
                # 存储难度按钮的位置
                button.diff_button_rects[option] = pygame.Rect(int(current_x), diff_y, icon_width, icon_height)
                self._draw_difficulty_button(button, option, current_x, diff_y, j, icon_width)
                current_x += icon_width + icon_spacing
    
    def _draw_back_button(self, button: SongButton, x: int, y: int, index: int):
        """
        绘制返回按钮
        Draw back button
        
        Args:
            button: 歌曲按钮对象
            x, y: 位置坐标
            index: 选项索引
        """
        is_back_selected = not hasattr(button, 'selected_option_index') or button.selected_option_index == 0
        
        # 选择返回按钮图片
        if is_back_selected and 'back_2' in self.diff_images:
            back_img = self.diff_images['back_2']
        elif 'back_1' in self.diff_images:
            back_img = self.diff_images['back_1']
        else:
            back_img = None
        
        if back_img:
            # 不缩放，使用原始尺寸
            self.screen.blit(back_img, (x, y))
            # 高亮选中
            if is_back_selected:
                pygame.draw.rect(self.screen, self.YELLOW, (x - 5, y - 5, back_img.get_width() + 10, back_img.get_height() + 10), 4)
            # 存储位置用于点击
            button.back_button_rect = pygame.Rect(x, y, back_img.get_width(), back_img.get_height())
    
    def _draw_difficulty_button(self, button: SongButton, diff: str, x: int, y: int, index: int, width: float):
        """
        绘制难度按钮
        Draw difficulty button
        
        Args:
            button: 歌曲按钮对象
            diff: 难度名称
            x, y: 位置坐标
            index: 选项索引
            width: 按钮宽度（用于布局，仅对Easy有效）
        """
        # 检查这个难度是否存在
        diff_exists = diff in button.difficulties
        
        # 获取难度图片等级
        diff_level = self.DIFF_MAPPING.get(diff, 2)
        stars = button.diff_stars.get(diff, 5) if diff_exists else 0
        
        # 选择彩色或灰色图标
        if diff_exists:
            img_key = diff_level
        else:
            img_key = f'{diff_level}_gray'
        
        # 绘制难度图片
        if img_key in self.diff_images:
            img = self.diff_images[img_key]
            
            # 所有图标保持原始尺寸，不缩放
            display_img = img
            display_width = img.get_width()
            display_height = img.get_height()
            scale_factor = 1.0
            
            # 高亮选中难度（仅当存在时）
            is_diff_selected = (hasattr(button, 'selected_option_index') and 
                              button.selected_option_index == index and 
                              diff_exists and 
                              diff == button.difficulties[button.selected_diff_index])
            
            if is_diff_selected:
                # 绘制选中指示器
                pygame.draw.rect(self.screen, self.YELLOW, (x - 5, y - 5, display_width + 10, display_height + 10), 4)
            
            # 显示长按进度（如果正在长按鬼难度）
            if diff == 'Oni' and hasattr(button, 'oni_press_start_time') and button.oni_press_start_time is not None and 'Edit' in button.difficulties:
                self._draw_long_press_progress(button, x, y, display_img, display_width, display_height)
            
            self.screen.blit(display_img, (x, y))
            
            # 绘制星级评分（仅当难度存在时）
            if diff_exists and stars > 0:
                self._draw_star_rating(x, y, stars, scale_factor)
    
    def _draw_long_press_progress(self, button: SongButton, x: int, y: int, img: pygame.Surface, width: float, height: float):
        """
        绘制长按进度
        Draw long press progress
        
        Args:
            button: 歌曲按钮对象
            x, y: 位置坐标
            img: 图片表面
            width: 图标宽度
            height: 图标高度
        """
        press_duration = pygame.time.get_ticks() - button.oni_press_start_time
        progress = min(1.0, press_duration / 2000)  # 2秒阈值
        
        # 绘制进度条
        bar_width = int(width)
        bar_height = 5
        bar_x = x
        bar_y = y + int(height) - 15
        
        # 背景
        pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        # 进度
        pygame.draw.rect(self.screen, (255, 215, 0), (bar_x, bar_y, int(bar_width * progress), bar_height))
        
        # 提示文字
        if progress < 1.0:
            hint_text = self.fonts['small'].render("Hold for Ura", True, self.YELLOW)
        else:
            hint_text = self.fonts['small'].render("-> Ura!", True, (255, 0, 255))
        hint_rect = hint_text.get_rect(center=(x + int(width) // 2, bar_y - 10))
        self.screen.blit(hint_text, hint_rect)
    
    def _draw_star_rating(self, x: int, y: int, stars: int, scale_factor: float = 1.0):
        """
        绘制星级评分
        Draw star rating
        
        Args:
            x, y: 位置坐标
            stars: 星级数
            scale_factor: 缩放因子（默认1.0）
        """
        # 根据缩放因子调整字体大小和位置
        font_size = int(24 * scale_factor)  # 基础字体大小24
        adjusted_font = pygame.font.Font(None, max(font_size, 12))  # 最小12像素
        
        star_text = adjusted_font.render(f"★{stars}", True, self.YELLOW)
        # 添加黑色描边
        outline_offset = max(1, int(scale_factor))
        for dx, dy in [(-outline_offset, -outline_offset), (-outline_offset, outline_offset), 
                       (outline_offset, -outline_offset), (outline_offset, outline_offset)]:
            outline = adjusted_font.render(f"★{stars}", True, self.BLACK)
            self.screen.blit(outline, (x + int(5 * scale_factor) + dx, y + int(45 * scale_factor) + dy))
        self.screen.blit(star_text, (x + int(5 * scale_factor), y + int(45 * scale_factor)))
    
    def draw_action_buttons(self, button: SongButton, y: int, height: int, 
                          practice_mode: bool, practice_generating: bool, 
                          practice_audio_paths: Dict):
        """
        绘制功能按钮（收藏、练习）
        Draw action buttons (favorite, practice)
        
        Args:
            button: 歌曲按钮对象
            y: Y坐标
            height: 高度
            practice_mode: 练习模式状态
            practice_generating: 是否正在生成练习音频
            practice_audio_paths: 练习音频路径字典
        """
        # 按钮尺寸
        button_width = 80
        button_height_btn = 35
        button_spacing = 10
        
        # 在展开歌曲区域的右上角定位按钮
        right_x = self.width - 20
        top_y = y + 10
        
        # 绘制收藏按钮
        favorite_x = right_x - button_width
        favorite_y = top_y
        
        # 收藏按钮背景（占位符 - 目前始终为灰色）
        favorite_color = self.GRAY
        pygame.draw.rect(self.screen, favorite_color, (favorite_x, favorite_y, button_width, button_height_btn))
        pygame.draw.rect(self.screen, self.WHITE, (favorite_x, favorite_y, button_width, button_height_btn), 2)
        
        # 收藏按钮文字
        favorite_text = self.fonts['small'].render("收藏", True, self.WHITE)
        text_rect = favorite_text.get_rect(center=(favorite_x + button_width//2, favorite_y + button_height_btn//2))
        self.screen.blit(favorite_text, text_rect)
        
        # 绘制练习按钮
        practice_x = right_x - button_width * 2 - button_spacing
        practice_y = top_y
        
        # 练习按钮背景颜色基于状态
        if practice_audio_paths:
            practice_color = self.GREEN  # 激活时为绿色
            practice_text = "已激活"
        elif practice_generating:
            practice_color = self.YELLOW  # 生成中为黄色
            practice_text = "准备中"
        else:
            practice_color = self.BLUE  # 未激活为蓝色
            practice_text = "练习"
        
        pygame.draw.rect(self.screen, practice_color, (practice_x, practice_y, button_width, button_height_btn))
        pygame.draw.rect(self.screen, self.WHITE, (practice_x, practice_y, button_width, button_height_btn), 2)
        
        # 练习按钮文字
        practice_text_surface = self.fonts['small'].render(practice_text, True, self.WHITE)
        text_rect = practice_text_surface.get_rect(center=(practice_x + button_width//2, practice_y + button_height_btn//2))
        self.screen.blit(practice_text_surface, text_rect)
        
        # 绘制练习模式状态（如果正在生成）
        if practice_generating:
            self._draw_practice_status()
    
    def _draw_practice_status(self):
        """
        绘制练习模式状态
        Draw practice mode status
        """
        status_text = "正在准备练习模式，请稍候..."
        status_surface = self.fonts['small'].render(status_text, True, self.WHITE)
        status_rect = status_surface.get_rect(center=(self.width//2, self.height - 80))
        # 绘制背景
        bg_rect = status_rect.inflate(20, 10)
        pygame.draw.rect(self.screen, self.BLACK, bg_rect)
        pygame.draw.rect(self.screen, self.WHITE, bg_rect, 2)
        self.screen.blit(status_surface, status_rect)
    
    def _calculate_total_height(self, buttons: List[SongButton], selected_index: int) -> float:
        """
        计算所有歌曲的总高度
        Calculate total height of all songs
        
        Args:
            buttons: 歌曲按钮列表
            selected_index: 当前选中索引
            
        Returns:
            float: 总高度
        """
        total_height = 0
        for i, button in enumerate(buttons):
            # 每个位置：如果是选中的用完整高度，否则用缩小高度 - 整体扩大25%，减小垂直间距
            if i == selected_index:
                # 选中歌曲的高度（可能展开）- 整体扩大25%
                height = int((self.button_height + (100 if button.expanded else 0)) * 1.25)
            else:
                # 未选中歌曲的缩小高度 - 整体扩大25%
                height = int((self.button_height * 0.85) * 1.25)
            total_height += height + 1  # 减小间距到1
        return total_height
    
    def flip_display(self):
        """
        刷新显示
        Flip display
        """
        pygame.display.flip()
    
    def get_stats(self) -> Dict[str, any]:
        """
        获取渲染统计信息
        Get render statistics
        
        Returns:
            Dict[str, any]: 统计信息字典
        """
        stats = {
            'screen_size': (self.width, self.height),
            'button_height': self.button_height,
            'button_spacing': self.button_spacing,
            'slant_angle': self.slant_angle,
            'loaded_images': {
                'difficulty': len(self.diff_images),
                'background': len(self.bg_images),
            },
            'loaded_fonts': len(self.fonts),
        }
        return stats
