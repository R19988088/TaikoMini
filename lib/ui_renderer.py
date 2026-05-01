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
        
        # 加载顶部遮挡层图片
        fenlei_top_path = resource_loader.texture_path / 'fenlei_top.png'
        self.fenlei_top_img = None
        if fenlei_top_path.exists():
            try:
                self.fenlei_top_img = pygame.image.load(str(fenlei_top_path)).convert_alpha()
                print(f"Loaded fenlei_top.png: {self.fenlei_top_img.get_size()}")
            except Exception as e:
                print(f"Failed to load fenlei_top.png: {e}")
        else:
            print(f"fenlei_top.png not found at: {fenlei_top_path}")
        
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
        
        # ==================== 颜色过渡 ====================
        self._category_color_current = None  # 当前显示的颜色
        self._category_color_target = None   # 目标颜色
        self._category_transition_start = None  # 过渡开始时间
        self._category_transition_duration = 300  # 过渡持续时间（毫秒）
        self._last_category = None  # 上一个分类名称
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
        
        # ==================== 成绩管理器（缓存实例，避免重复加载） ====================
        from lib.score_manager import ScoreManager
        self._score_manager = ScoreManager()
        
        # ==================== 分数面板动画状态 ====================
        self._score_panel_last_difficulty = None  # 上一次显示的难度
        self._score_panel_fade_start_time = None  # 同步动画开始时间（新旧分数同时动画）
        self._score_panel_fade_duration = 80  # 动画持续时间（毫秒）
        self._score_panel_pending_difficulty = None  # 待显示的新难度
        self._score_panel_pending_data = None  # 待显示的新分数数据
        
        # ==================== 展开/收起淡入淡出动画 ====================
        self._score_panel_expand_alpha = 0.0  # 当前透明度 (0.0 - 1.0)
        self._score_panel_is_expanded = False  # 当前是否展开
        self._score_panel_expand_duration = 300  # 展开/收起动画时长（毫秒）
        self._score_panel_cached_data = None  # 缓存的分数面板数据（用于淡出动画）
        self._score_panel_expand_start_time = None  # 展开动画开始时间
        self._score_panel_collapse_start_time = None  # 收起动画开始时间
    
    def draw_main_screen(self, title: str, hint: str = None, category: str = None):
        """
        绘制主界面
        Draw main screen
        
        Args:
            title: 页面标题
            hint: 提示文字（可选）
            category: 当前分类（可选，用于背景色）
        """
        # 根据分类获取背景色（使用分类颜色-15%亮度）
        bg_color = self.ORANGE  # 默认橙色
        if category:
            from lib.config_manager import ConfigManager
            try:
                config = ConfigManager()
                category_info = config.get_category_info(category)
                if category_info and category_info[0]:  # 有颜色信息
                    category_color = category_info[0]
                    # 降低亮度15%（乘以0.85）
                    bg_color = (
                        max(0, int(category_color[0] * 0.85)),
                        max(0, int(category_color[1] * 0.85)),
                        max(0, int(category_color[2] * 0.85))
                    )
            except Exception as e:
                print(f"Error getting category color for background: {e}")
        
        # 填充背景色
        self.screen.fill(bg_color)
        
        # 绘制标题
        title_surface = self.fonts['header'].render(title, True, self.WHITE)
        self.screen.blit(title_surface, (self.width // 2 - title_surface.get_width() // 2, 30))
        
        # 绘制提示（如果有）
        if hint:
            hint_surface = self.fonts['small'].render(hint, True, self.WHITE)
            self.screen.blit(hint_surface, (self.width // 2 - hint_surface.get_width() // 2, self.height - 40))
    
    def draw_top_mask(self, current_category: str):
        """
        绘制顶部遮挡层（使用图片的透明度渐变，填充分类颜色，带过渡动画）
        Draw top mask layer with category color using image alpha gradient and transition animation
        
        Args:
            current_category: 当前分类名称
        """
        if not self.fenlei_top_img:
            return
        
        # 获取目标分类颜色
        from lib.config_manager import ConfigManager
        try:
            config = ConfigManager()
            category_info = config.get_category_info(current_category)
            if category_info and category_info[0]:  # 检查是否有颜色
                target_color = category_info[0]  # 已经是元组 (r, g, b)
            else:
                target_color = (100, 200, 100)  # 默认绿色
        except Exception as e:
            print(f"Error getting category color for {current_category}: {e}")
            target_color = (100, 200, 100)
        
        # 检测分类是否变化
        if current_category != self._last_category:
            # 分类变化，开始新的过渡
            self._last_category = current_category
            self._category_color_target = target_color
            self._category_transition_start = pygame.time.get_ticks()
            
            # 如果是第一次设置或当前颜色为空，直接设置为目标颜色
            if self._category_color_current is None:
                self._category_color_current = target_color
        
        # 计算过渡进度
        if self._category_transition_start is not None and self._category_color_target is not None:
            elapsed = pygame.time.get_ticks() - self._category_transition_start
            progress = min(1.0, elapsed / self._category_transition_duration)
            
            # 使用缓动函数（ease-out）
            progress = 1 - (1 - progress) ** 2
            
            # 插值颜色
            if self._category_color_current is not None:
                r = int(self._category_color_current[0] + (self._category_color_target[0] - self._category_color_current[0]) * progress)
                g = int(self._category_color_current[1] + (self._category_color_target[1] - self._category_color_current[1]) * progress)
                b = int(self._category_color_current[2] + (self._category_color_target[2] - self._category_color_current[2]) * progress)
                color = (r, g, b)
                
                # 过渡完成后更新当前颜色
                if progress >= 1.0:
                    self._category_color_current = self._category_color_target
                    self._category_transition_start = None
            else:
                color = self._category_color_target
                self._category_color_current = self._category_color_target
        else:
            color = self._category_color_current if self._category_color_current else target_color
        
        # 绘制位置：从顶部开始
        mask_y = 0
        
        # 水平拉伸图片到屏幕宽度，垂直缩小30%
        original_height = self.fenlei_top_img.get_height()
        mask_height = int(original_height * 0.7)  # 缩小30%，保留70%
        stretched_img = pygame.transform.scale(self.fenlei_top_img, (self.width, mask_height))
        
        # 创建一个用分类颜色填充的 surface
        colored_mask = pygame.Surface((self.width, mask_height), pygame.SRCALPHA)
        colored_mask.fill(color + (255,))  # 填充颜色，完全不透明
        
        # 提取原图的 alpha 通道并应用到填充的 surface
        # 使用像素数组操作
        stretched_array = pygame.surfarray.pixels_alpha(stretched_img)
        colored_array = pygame.surfarray.pixels_alpha(colored_mask)
        colored_array[:, :] = stretched_array[:, :]
        del stretched_array
        del colored_array
        
        # 绘制到屏幕
        self.screen.blit(colored_mask, (0, mask_y))
    
    def _adjust_color_brightness_saturation(self, rgb: tuple, brightness_factor: float, saturation_adjust: float) -> tuple:
        """
        调整颜色的亮度和饱和度
        
        Args:
            rgb: RGB颜色元组 (R, G, B)
            brightness_factor: 亮度因子（0.4 = 亮度-60%）
            saturation_adjust: 饱和度调整（-0.1 = 减少10%）
            
        Returns:
            调整后的RGB颜色元组
        """
        r, g, b = [x / 255.0 for x in rgb]
        
        # RGB to HSL
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        l = (max_c + min_c) / 2.0
        
        if max_c == min_c:
            h = s = 0.0
        else:
            d = max_c - min_c
            s = d / (2.0 - max_c - min_c) if l > 0.5 else d / (max_c + min_c)
            
            if max_c == r:
                h = (g - b) / d + (6.0 if g < b else 0.0)
            elif max_c == g:
                h = (b - r) / d + 2.0
            else:
                h = (r - g) / d + 4.0
            h /= 6.0
        
        # 调整亮度
        l *= brightness_factor
        
        # 调整饱和度
        s = max(0.0, min(1.0, s + saturation_adjust))
        
        # HSL to RGB
        def hue_to_rgb(p, q, t):
            if t < 0.0: t += 1.0
            if t > 1.0: t -= 1.0
            if t < 1.0/6.0: return p + (q - p) * 6.0 * t
            if t < 1.0/2.0: return q
            if t < 2.0/3.0: return p + (q - p) * (2.0/3.0 - t) * 6.0
            return p
        
        if s == 0.0:
            r = g = b = l
        else:
            q = l * (1.0 + s) if l < 0.5 else l + s - l * s
            p = 2.0 * l - q
            r = hue_to_rgb(p, q, h + 1.0/3.0)
            g = hue_to_rgb(p, q, h)
            b = hue_to_rgb(p, q, h - 1.0/3.0)
        
        return (int(r * 255), int(g * 255), int(b * 255))
    
    def _render_text_with_outline(self, text: str, font: pygame.font.Font, text_color: tuple, 
                                   outline_color: tuple, outline_width: int = 2) -> pygame.Surface:
        """
        渲染带描边的文字（用于分类选择器）
        Render text with outline (for category selector)
        
        Args:
            text: 文字内容
            font: 字体
            text_color: 文字颜色 (R, G, B)
            outline_color: 描边颜色 (R, G, B)
            outline_width: 描边宽度（像素）
            
        Returns:
            pygame.Surface: 包含描边文字的表面
        """
        # 渲染描边（绘制多个偏移的文字）
        base_text = font.render(text, True, text_color)
        w = base_text.get_width() + 2 * outline_width
        h = base_text.get_height() + 2 * outline_width
        
        # 创建足够大的表面
        outline_surface = pygame.Surface((w, h), pygame.SRCALPHA)
        
        # 绘制描边（8个方向）
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    outline_text = font.render(text, True, outline_color)
                    outline_surface.blit(outline_text, (outline_width + dx, outline_width + dy))
        
        # 绘制中心文字
        outline_surface.blit(base_text, (outline_width, outline_width))
        
        return outline_surface
    
    def draw_categories(self, categories: List[str], selected_category_index: int):
        """
        绘制分类选择器
        Draw category selector
        
        Args:
            categories: 分类列表
            selected_category_index: 当前选中的分类索引
        """
        category_top = 20  # 下移20px
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
        # 显示1个分类框（中心显示选中分类）
        cat_idx = selected_category_index
        if cat_idx < len(categories):
            cat_name = categories[cat_idx]
            
            # 获取分类图片
            from lib.config_manager import ConfigManager
            config = ConfigManager()
            category_info = config.get_category_info(cat_name)
            
            if category_info and category_info[2]:  # 有genre_bg图片
                genre_bg_image = self.resource_loader.load_custom_genre_bg_image(category_info[2])
                
                if genre_bg_image:
                    # 宽度增加20%
                    original_width = genre_bg_image.get_width()
                    original_height = genre_bg_image.get_height()
                    target_width = int(original_width * 1.2)  # 增加20%
                    target_height = original_height  # 高度不变
                    
                    # 计算居中位置
                    box_x = (self.width - target_width) // 2
                    box_y = category_top + (category_height - target_height) // 2
                    
                    # 获取分类颜色并计算描边颜色（亮度-60%，饱和度-10%）
                    if category_info and category_info[0]:
                        category_color = category_info[0]
                        # 降低亮度60%（乘以0.4）+ 饱和度-10%
                        outline_color = self._adjust_color_brightness_saturation(
                            category_color, 
                            brightness_factor=0.3,  # 亮度-70%
                            saturation_adjust=-0.1  # 饱和度-10%
                        )
                        bg_tint_color = outline_color  # 背景染色也使用相同的颜色
                    else:
                        # 默认深灰色
                        outline_color = (80, 80, 80)
                        bg_tint_color = (80, 80, 80)
                    
                    # 使用九宫格拉伸绘制分类图片（只拉伸左右两侧）
                    self._draw_nine_patch(genre_bg_image, box_x, box_y, target_width, target_height, border_ratio=0.28)
                    
                    # 绘制带描边的文字
                    text_surface = self._render_text_with_outline(cat_name, self.fonts['category'], 
                                                                  self.WHITE, outline_color, outline_width=3)
                    text_rect = text_surface.get_rect(center=(box_x + target_width//2, box_y + target_height//2))
                    self.screen.blit(text_surface, text_rect)
                else:
                    # 回退到旧的绘制方式
                    box_x = (self.width - 400) // 2
                    box_width = 400
                    pygame.draw.rect(self.screen, self.YELLOW, 
                                   (box_x, category_top, box_width, category_height), 6)
                    
                    cat_text = self.fonts['category'].render(cat_name, True, self.BLACK)
                    text_rect = cat_text.get_rect(center=(box_x + box_width//2, category_top + category_height//2))
                    self.screen.blit(cat_text, text_rect)
            else:
                # 回退到旧的绘制方式
                box_x = (self.width - 400) // 2
                box_width = 400
                pygame.draw.rect(self.screen, self.YELLOW, 
                               (box_x, category_top, box_width, category_height), 6)
                
                cat_text = self.fonts['category'].render(cat_name, True, self.BLACK)
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
        # 设置裁剪区域，防止歌曲按钮遮挡顶部分类选择器
        # 分类选择器高度60px，渐变遮挡层在顶部，给100px的安全区域
        clip_top = 100
        original_clip = self.screen.get_clip()
        self.screen.set_clip((0, clip_top, self.width, self.height - clip_top))
        
        if not buttons:
            # 恢复裁剪区域后返回
            self.screen.set_clip(original_clip)
            return
        
        # 保存 blink_time 到选中按钮以便传递到难度绘制
        if selected_index < len(buttons):
            buttons[selected_index]._ui_blink_time = blink_time
        
        start_y = 250
        
        # 计算所有歌曲的总高度（用于循环显示）
        total_height = self._calculate_total_height(buttons, selected_index)
        
        # 归一化滚动偏移量，确保在合理范围内
        # 这可以防止分类切换时出现的极端值导致卡片不显示
        if total_height > 0:
            # 将 scroll_offset 归一化到 [0, total_height * 2) 范围
            # 保留2个循环的范围以避免频繁归一化
            while scroll_offset < -total_height:
                scroll_offset += total_height
            while scroll_offset > total_height * 2:
                scroll_offset -= total_height
        
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
                if button.expanded and 2 in self.bg_images:
                    # 展开时使用big_2的实际高度
                    glow_width, glow_height = self._get_glow_frame_size()
                    actual_height = int(glow_height * 1.25) if glow_height > 0 else int((self.button_height + 100) * 1.25)
                else:
                    actual_height = int((self.button_height + (100 if button.expanded else 0)) * 1.25)
            else:
                actual_height = int((self.button_height * 0.85) * 1.25)
            
            # 早期裁剪：如果完全在屏幕外则跳过（增大缓冲区到250px）
            if button_y > self.height + 250 or button_y + actual_height < -250:
                return False
            
            # 绘制按钮
            self.draw_slanted_button(button, button_y, is_selected, blink_time)
            return True
        
        # 计算需要的循环数量，确保覆盖所有可见区域
        # 加上额外的缓冲区，避免边界处出现空白
        visible_area = self.height + 500  # 屏幕高度 + 上下各250px缓冲
        min_loops_needed = max(3, int((visible_area / total_height) + 2))  # 至少3个循环，确保覆盖
        
        # 计算起始循环，确保覆盖当前可见区域之前的内容
        # 使用 floor division 并减去2，确保有足够的缓冲
        start_loop = int(scroll_offset / total_height) - 2
        end_loop = start_loop + min_loops_needed + 2  # 增加结束循环以确保完全覆盖
        
        # 绘制多个循环以覆盖屏幕
        # 使用更宽松的循环范围，确保在任何滚动位置都能看到卡片
        for loop in range(start_loop, end_loop):
            y_offset = loop * total_height
            for i in range(len(buttons)):
                draw_button_at_index(i, y_offset)
        
        # 恢复原来的裁剪区域
        self.screen.set_clip(original_clip)
        
        # 保存成绩面板绘制所需的信息（稍后在最上层绘制）
        # 成绩面板独立于滚动，固定在屏幕右上角
        self._score_panel_data = None
        if selected_index >= 0 and selected_index < len(buttons):
            selected_button = buttons[selected_index]
            if selected_button.expanded:
                # 成绩面板固定在屏幕右上角，不跟随滚动
                # 只需要保存按钮信息，位置由 _draw_score_info 内部计算
                self._score_panel_data = {
                    'button': selected_button
                }
    
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
                # 展开时使用big_2图片的高度来计算间距
                if 2 in self.bg_images:
                    glow_width, glow_height = self._get_glow_frame_size()
                    if glow_height > 0:
                        current_y += int(glow_height * 1.25) - 15  # 使用big2高度
                    else:
                        current_y += int((self.button_height + 100) * 1.25) - 15  # 后备方案
                else:
                    current_y += int((self.button_height + 100) * 1.25) - 15  # 后备方案
            elif i == selected_index:
                current_y += int(self.button_height * 1.25) - 15  # 未展开的选中卡片
            else:
                current_y += int((self.button_height * 0.85) * 1.25) - 15  # 小卡片
        
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
            # 展开时使用big_2的实际高度，避免变形
            if 2 in self.bg_images:
                glow_width, glow_height = self._get_glow_frame_size()
                height = int(glow_height * 1.25) if glow_height > 0 else int((self.button_height + 100) * 1.25)
            else:
                height = int((self.button_height + 100) * 1.25)  # 后备方案
        else:
            if is_selected:
                width = int((self.width - 200) * 1.40)  # 与展开状态宽度一致
                height = int(self.button_height * 1.25)  # 扩大25%
            else:
                width = int((self.width - 200) * 1.25)  # 扩大25%
                height = int((self.button_height * 0.85) * 1.25)  # 扩大25%
        
        x = (self.width - width) // 2
        
        # ==================== 绘制投影（仅用于未选中的小面板） ====================
        if not is_selected and not button.expanded and 0 in self.bg_images:
            shadow_img = self.bg_images[0].copy()  # 复制一份以便修改透明度
            
            # 设置透明度为50%
            shadow_img.set_alpha(200)  # 255 * 0.5 = 127.5
            
            # 投影尺寸减少20%（比b1小20%）
            shadow_width = int(width * 0.95)
            shadow_height = int(height * 0.95)
            
            # 居中并下移4px
            shadow_x = x + (width - shadow_width) // 2
            shadow_y = y + (height - shadow_height) // 2 + 6  # 下移4px
            
            # 使用九宫格缩放绘制投影
            self._draw_nine_patch(shadow_img, shadow_x, shadow_y, shadow_width, shadow_height, border_ratio=0.28)
        
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
        # 传递 b1 的实际宽度，用于未选中状态的文本限制
        self._draw_button_text(button, text_center_x, text_y, is_selected, info_bg_bounds, width)
        
        # ==================== 绘制皇冠图标 ====================
        self._draw_crown(button, x, y, height)
        
        # ==================== 绘制难度选择 ====================
        if button.expanded:
            # 传递info_bg_bounds以便难度选择可以基于b3图案宽度定位
            self._draw_difficulty_selection(button, y, height, info_bg_bounds)
            
            # 注意：成绩信息在所有按钮绘制完后统一绘制（在draw_song_buttons方法中）
    
    def _draw_crown(self, button: SongButton, button_x: int, button_y: int, button_height: int):
        """
        绘制皇冠图标
        Draw crown icon
        
        Args:
            button: 歌曲按钮对象
            button_x: 按钮X坐标
            button_y: 按钮Y坐标
            button_height: 按钮高度
        """
        # 获取歌曲ID（tja文件名不含扩展名）
        song_id = button.tja_path.stem
        
        # 获取皇冠信息（使用缓存的score_manager）
        if not hasattr(self, '_score_manager'):
            from lib.score_manager import ScoreManager
            self._score_manager = ScoreManager()
        
        try:
            crown_type, crown_count = self._score_manager.get_crown_info(song_id, button.difficulties)
            
            # 如果没有皇冠，不绘制
            if crown_type is None:
                return
            
            # 获取皇冠图标
            crown_key = f'crown_{crown_type}'
            if crown_key not in self.diff_images:
                return
            
            crown_img = self.diff_images[crown_key]
            crown_width, crown_height = crown_img.get_size()
            
            # 皇冠位置：按钮左侧内部，垂直居中
            crown_x = button_x + 35  # 距离左边缘258px
            crown_y = button_y + (button_height - crown_height) // 2
            
            # 绘制皇冠
            self.screen.blit(crown_img, (crown_x, crown_y))
            
            # 如果有2个或以上难度都有皇冠，显示数字
            if crown_count >= 2:
                # 使用小号字体绘制数字
                number_font = self.fonts.get('small', self.fonts.get('title'))
                if number_font:
                    # 白色数字，黑色描边
                    number_text = number_font.render(str(crown_count), True, (255, 255, 255))
                    
                    # 数字位置：皇冠右侧
                    number_x = crown_x + crown_width + 5
                    number_y = crown_y + (crown_height - number_text.get_height()) // 2
                    
                    # 绘制描边
                    for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                        outline = number_font.render(str(crown_count), True, (0, 0, 0))
                        self.screen.blit(outline, (number_x + dx, number_y + dy))
                    
                    # 绘制数字
                    self.screen.blit(number_text, (number_x, number_y))
        
        except Exception as e:
            print(f"Error drawing crown: {e}")
    
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
    
    def _get_glow_frame_size(self):
        """
        获取发光图片的尺寸（用于计算布局）
        Get glow image size (for layout calculation)
        
        Returns:
            tuple: (width, height) 或 (0, 0) 如果未加载
        """
        if 2 not in self.bg_images:
            return (0, 0)
        
        glow_data = self.bg_images[2]
        
        # 如果是列表（动画帧），使用第一帧的尺寸
        if isinstance(glow_data, list) and len(glow_data) > 0:
            return (glow_data[0].get_width(), glow_data[0].get_height())
        # 如果是单张图片（向后兼容）
        elif hasattr(glow_data, 'get_width'):
            return (glow_data.get_width(), glow_data.get_height())
        else:
            return (0, 0)
    
    def _draw_glow_effect(self, x: int, y: int, width: int, height: int, 
                         expanded: bool, blink_time: float):
        """
        绘制发光效果（使用2帧交替循环，带半透明过渡）
        Draw glow effect (using 2-frame alternating cycle with alpha blending)
        
        Args:
            x, y: 位置坐标
            width, height: 尺寸
            expanded: 是否展开
            blink_time: 闪烁时间
        """
        if 2 not in self.bg_images:
            return
        
        glow_frames = self.bg_images[2]
        
        # 检查是否为列表（动画帧）
        if not isinstance(glow_frames, list) or len(glow_frames) == 0:
            return
        
        import math
        
        # 简化版：只使用第1张（索引0）和第2张（索引1）交替
        if len(glow_frames) < 2:
            return
        
        frame_1 = glow_frames[0]  # big_2_1.png
        frame_2 = glow_frames[1]  # big_2_2.png
        
        # 1秒一次循环
        cycle_duration = 1000.0  # 毫秒
        cycle_progress = (blink_time % cycle_duration) / cycle_duration  # 0.0 到 1.0
        
        # 使用 sin 函数计算过渡：0.5秒从1到2，0.5秒从2到1
        blend_factor = (math.sin(cycle_progress * 2 * math.pi - math.pi / 2) + 1) / 2  # 0.0 到 1.0
        
        # 使用缓存的缩放surface来减少创建开销（直接缩放，不使用九宫格）
        cache_key = f"glow_{width}x{height}"
        if not hasattr(self, '_glow_surface_cache'):
            self._glow_surface_cache = {}
        
        if cache_key not in self._glow_surface_cache:
            # 缓存缩放后的surface，避免每帧重新缩放
            surf_1 = pygame.transform.smoothscale(frame_1, (width, height))
            surf_2 = pygame.transform.smoothscale(frame_2, (width, height))
            self._glow_surface_cache[cache_key] = {
                'frame1': surf_1,
                'frame2': surf_2
            }
        
        surfaces = self._glow_surface_cache[cache_key]
        surf_1 = surfaces['frame1']
        surf_2 = surfaces['frame2']
        
        # 计算透明度：frame_2作为底层（最大90%透明度），frame_1作为顶层（渐变）
        alpha_1 = int(255 * (1.0 - blend_factor))  # 255 → 0 → 255
        alpha_2 = int(255 * 0.9)  # 90% 透明度
        
        # 1. 先绘制 frame_2（底层，90%透明度）
        surf_2.set_alpha(alpha_2)
        self.screen.blit(surf_2, (x, y))
        
        # 2. 再绘制 frame_1（顶层，渐变）
        if alpha_1 > 0:
            surf_1.set_alpha(alpha_1)
            self.screen.blit(surf_1, (x, y))
    
    def _draw_nine_patch_to_surface(self, img: pygame.Surface, target_surf: pygame.Surface, 
                                   x: int, y: int, width: int, height: int, border_ratio: float = 0.28):
        """
        使用九宫格缩放绘制到指定surface
        Draw to a surface using 9-patch scaling
        """
        border_w = int(img.get_width() * border_ratio)
        border_h = int(img.get_height() * border_ratio)
        border_w = min(border_w, img.get_width() // 3)
        border_h = min(border_h, img.get_height() // 3)
        
        src_w = img.get_width()
        src_h = img.get_height()
        
        patches = [
            (0, 0, border_w, border_h, x, y, border_w, border_h),
            (border_w, 0, src_w - 2*border_w, border_h, x + border_w, y, width - 2*border_w, border_h),
            (src_w - border_w, 0, border_w, border_h, x + width - border_w, y, border_w, border_h),
            (0, border_h, border_w, src_h - 2*border_h, x, y + border_h, border_w, height - 2*border_h),
            (border_w, border_h, src_w - 2*border_w, src_h - 2*border_h, x + border_w, y + border_h, width - 2*border_w, height - 2*border_h),
            (src_w - border_w, border_h, border_w, src_h - 2*border_h, x + width - border_w, y + border_h, border_w, height - 2*border_h),
            (0, src_h - border_h, border_w, border_h, x, y + height - border_h, border_w, border_h),
            (border_w, src_h - border_h, src_w - 2*border_w, border_h, x + border_w, y + height - border_h, width - 2*border_w, border_h),
            (src_w - border_w, src_h - border_h, border_w, border_h, x + width - border_w, y + height - border_h, border_w, border_h),
        ]
        
        for src_x, src_y, s_w, s_h, dst_x, dst_y, d_w, d_h in patches:
            if s_w > 0 and s_h > 0 and d_w > 0 and d_h > 0:
                subsurface = img.subsurface((src_x, src_y, s_w, s_h))
                scaled = pygame.transform.scale(subsurface, (int(d_w), int(d_h)))
                target_surf.blit(scaled, (int(dst_x), int(dst_y)))
    
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
                          is_selected: bool, info_bg_bounds: Optional[Tuple], b1_width: int):
        """
        绘制按钮文字
        Draw button text
        
        Args:
            button: 歌曲按钮对象
            text_center_x: 文字中心X坐标
            text_y: 文字Y坐标
            is_selected: 是否选中
            info_bg_bounds: 信息背景边界（选中时的 big_3 背景）
            b1_width: b1（主背景）的实际绘制宽度
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
        
        # 计算可用宽度（使用窗口整体宽度，两侧各保留40px）
        # 不再依赖 b1 或 big_3 的宽度，直接使用屏幕宽度限制
        window_margin = 75  # 窗口两侧边距
        outline_space = 6   # 描边占用空间（每侧，3px描边*2侧）
        
        # 可用宽度 = 屏幕宽度 - 两侧窗口边距 - 两侧描边空间
        available_width = self.width - (window_margin + outline_space) * 2
        
        # 渲染标题
        title_text_original = self.fonts['title_cn'].render(display_title, True, self.WHITE)
        title_width_original = title_text_original.get_width()
        
        # 如果标题宽度超出可用宽度，进行水平拉伸（压缩）
        if title_width_original > available_width:
            # 计算水平缩放比例
            scale_x = available_width / title_width_original
            # 水平拉伸（y方向保持不变）
            new_width = available_width
            original_height = title_text_original.get_height()
            title_text = pygame.transform.scale(title_text_original, (new_width, original_height))
        else:
            title_text = title_text_original
        
        title_height = title_text.get_height()
        
        # 预渲染副标题并处理宽度（仅在展开时显示）
        subtitle_text = None
        subtitle_height = 0
        if button.expanded and display_subtitle:
            subtitle_text_original = self.fonts['subtitle'].render(display_subtitle, True, self.WHITE)
            subtitle_width_original = subtitle_text_original.get_width()
            
            # 副标题也需要进行宽度检查和拉伸
            # 副标题描边宽度是2px，占用空间约4px每侧
            subtitle_outline_space = 4
            subtitle_available_width = self.width - (window_margin + subtitle_outline_space) * 2
            
            if subtitle_width_original > subtitle_available_width:
                # 水平压缩副标题
                new_subtitle_width = subtitle_available_width
                subtitle_text = pygame.transform.scale(
                    subtitle_text_original, 
                    (new_subtitle_width, subtitle_text_original.get_height())
                )
            else:
                subtitle_text = subtitle_text_original
            
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
        
        # 获取分类颜色并计算描边颜色（亮度-60%，饱和度-10%）
        outline_color = (80, 80, 80)  # 默认深灰色
        if hasattr(button, 'category') and button.category:
            from lib.config_manager import ConfigManager
            try:
                config = ConfigManager()
                category_info = config.get_category_info(button.category)
                if category_info and category_info[0]:  # 有颜色信息
                    category_color = category_info[0]
                    # 降低亮度60%（乘以0.4）+ 饱和度-10%
                    outline_color = self._adjust_color_brightness_saturation(
                        category_color, 
                        brightness_factor=0.4,  # 亮度-60%
                        saturation_adjust=-0.1  # 饱和度-10%
                    )
            except Exception as e:
                print(f"Error getting category color for outline: {e}")
        
        # 绘制标题描边和主体（使用分类颜色-60%亮度-10%饱和度）
        self._draw_text_with_outline(title_text, title_x, title_y, 3, 16, outline_color)
        
        # 渲染副标题（仅在激活状态下显示）
        if button.expanded and display_subtitle and subtitle_text:
            gap = 6
            subtitle_y = title_y + title_height + gap
            subtitle_x = text_center_x - subtitle_text.get_width() // 2
            
            # 绘制副标题描边和主体（保持黑色）
            self._draw_text_with_outline(subtitle_text, subtitle_x, subtitle_y, 2, 12, (0, 0, 0))
        
        # 恢复裁剪区域
        if old_clip is not None:
            self.screen.set_clip(old_clip)
    
    def _draw_text_with_outline(self, text_surface: pygame.Surface, x: int, y: int, 
                               outline_radius: int, outline_points: int, outline_color: tuple = (0, 0, 0)):
        """
        绘制带描边的文字（优化版本）
        Draw text with outline (optimized version)
        
        Args:
            text_surface: 文字表面
            x, y: 位置坐标
            outline_radius: 描边半径
            outline_points: 描边点数
            outline_color: 描边颜色 (R, G, B)，默认黑色
        """
        # 优化：减少描边点数以提高性能
        optimized_points = min(outline_points, 8)  # 最多8个点
        
        # 预创建描边表面数组，避免重复复制
        outline_surfaces = []
        for i in range(optimized_points):
            angle = 2 * math.pi * i / optimized_points
            dx = int(outline_radius * math.cos(angle))
            dy = int(outline_radius * math.sin(angle))
            
            # 创建指定颜色的描边表面
            outline_surface = text_surface.copy()
            # 使用像素数组操作来设置描边颜色，保持透明度
            outline_array = pygame.surfarray.pixels3d(outline_surface)
            outline_array[:, :, 0] = outline_color[0]  # R
            outline_array[:, :, 1] = outline_color[1]  # G
            outline_array[:, :, 2] = outline_color[2]  # B
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
        diff_y = y + height - 120  # 整体上移30px (原-90 + 上移10px + 再上移15px + 再上移5px = -120)
        
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
        
        # 获取SB背景图尺寸（真正的按钮尺寸）
        sb_width = 100
        sb_height = 80
        if 'sb_1' in self.diff_images:
            sb_width = self.diff_images['sb_1'].get_width()
            sb_height = self.diff_images['sb_1'].get_height()
        
        # 计算难度按钮区域：占据屏幕中间 5/7 的宽度
        available_width = self.width * 5 / 7
        start_x_offset = self.width * 1 / 7  # 左侧留白 1/7
        
        # 计算间距：用可用宽度减去所有按钮宽度，除以间隙数量
        total_buttons_width = back_width + sb_width * len(difficulty_list)
        total_gaps = len(all_options) - 1
        if total_gaps > 0:
            icon_spacing = (available_width - total_buttons_width) / total_gaps
        else:
            icon_spacing = 0
        
        # 起始位置
        diff_start_x = start_x_offset
        
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
                # 存储难度按钮的位置（使用SB图尺寸）
                button.diff_button_rects[option] = pygame.Rect(int(current_x), diff_y, sb_width, sb_height)
                self._draw_difficulty_button(button, option, current_x, diff_y, j, sb_width)
                current_x += sb_width + icon_spacing
    
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
            
            # 显示长按进度（如果正在长按鬼难度）
            if diff == 'Oni' and hasattr(button, 'oni_press_start_time') and button.oni_press_start_time is not None and 'Edit' in button.difficulties:
                self._draw_long_press_progress(button, x, y, display_img, display_width, display_height)
            
            # 使用完整包裹绘制：SB背景图替换黄色选择框 + 难度图标 + 星星+数字
            if diff_exists and stars > 0:
                # 传递 blink_time 用于发光效果
                blink_time = getattr(button, '_ui_blink_time', 0)
                self._draw_complete_difficulty_wrapped(x, y, display_img, stars, diff_level, is_diff_selected, blink_time)
            else:
                # 没有星级时只绘制图标（保留黄色框）
                if is_diff_selected:
                    pygame.draw.rect(self.screen, self.YELLOW, (x - 5, y - 5, display_width + 10, display_height + 10), 4)
                self.screen.blit(display_img, (x, y))
    
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
    
    def _draw_score_info_fixed(self, button: SongButton, expand_alpha: float = 1.0):
        """
        绘制成绩信息面板（水平居中，垂直固定在屏幕上方，不跟随滚动）
        Draw score info panel at fixed position (horizontally centered, top area, independent of scrolling)
        
        Args:
            button: 歌曲按钮对象
        """
        # 检查是否有 scores.png
        if 'scores' not in self.bg_images:
            return
        
        # 如果没有难度列表，返回
        if not hasattr(button, 'difficulties') or not button.difficulties:
            return
        
        song_id = button.tja_path.stem
        
        # 使用缓存的成绩管理器实例（避免重复加载）
        score_manager = self._score_manager
        
        # 查找要显示的难度
        difficulty_name = None
        score_data = None
        
        # 难度优先级映射 (名称 -> 优先级，数字越大优先级越高)
        difficulty_priority = {'Easy': 1, 'Normal': 2, 'Hard': 3, 'Oni': 4, 'Edit': 5}
        
        # 首先，获取当前选中的难度
        selected_difficulty = None
        if hasattr(button, 'selected_diff_index') and button.selected_diff_index >= 0:
            selected_difficulty = button.difficulties[button.selected_diff_index]
        
        # 如果有选中的难度，直接显示该难度的分数（即使为0）
        if selected_difficulty:
            difficulty_name = selected_difficulty
            score_data = score_manager.get_score(song_id, selected_difficulty)
            if not score_data:
                score_data = {'score': 0}
        else:
            # 没有选中难度（初始状态），按优先级查找有分数的难度
            sorted_difficulties = sorted(button.difficulties, 
                                        key=lambda d: difficulty_priority.get(d, 0), 
                                        reverse=True)
            
            for diff in sorted_difficulties:
                diff_score = score_manager.get_score(song_id, diff)
                if diff_score and diff_score.get('score', 0) > 0:
                    difficulty_name = diff
                    score_data = diff_score
                    break
        
        # 如果所有难度都没有分数，不显示
        if not difficulty_name:
            return
        
        # 如果没有分数数据，创建一个默认的
        if not score_data:
            score_data = {'score': 0}
        
        # 检测难度切换，启动同步动画（新旧分数同时动画）
        if difficulty_name != self._score_panel_last_difficulty:
            # 如果当前没有动画正在进行，或者新的难度与待显示的难度不同
            if self._score_panel_fade_start_time is None or difficulty_name != self._score_panel_pending_difficulty:
                # 保存新的难度和数据
                self._score_panel_pending_difficulty = difficulty_name
                self._score_panel_pending_data = score_data
                # 开始动画（新旧分数同时动画）
                self._score_panel_fade_start_time = pygame.time.get_ticks()
        
        # 判断是否正在动画中
        is_animating = self._score_panel_fade_start_time is not None
        
        if is_animating:
            elapsed = pygame.time.get_ticks() - self._score_panel_fade_start_time
            if elapsed < self._score_panel_fade_duration:
                # 动画进行中：翻转效果（像777老虎机）
                progress = elapsed / self._score_panel_fade_duration
                
                # ========== 绘制背景面板（固定不动） ==========
                # 先绘制一个固定的背景面板（不翻转）
                self._draw_score_panel_background(expand_alpha)
                
                # ========== 翻转动画：旧分数向上翻走，新分数从下方翻上来 ==========
                if progress < 0.5:
                    # 前半段：旧分数向上翻转并消失
                    flip_progress = progress * 2  # 0 -> 1
                    
                    if self._score_panel_last_difficulty:
                        old_score_data = score_manager.get_score(song_id, self._score_panel_last_difficulty)
                        if not old_score_data:
                            old_score_data = {'score': 0}
                        
                        # 绘制旧分数（向上移动并渐隐）
                        self._draw_score_content_flip(song_id, self._score_panel_last_difficulty, 
                                                       old_score_data, flip_progress, flip_out=True, expand_alpha=expand_alpha)
                else:
                    # 后半段：新分数从下方翻转上来
                    flip_progress = (progress - 0.5) * 2  # 0 -> 1
                    
                    # 绘制新分数（从下方移动上来并渐现）
                    self._draw_score_content_flip(song_id, self._score_panel_pending_difficulty, 
                                                   self._score_panel_pending_data, flip_progress, flip_out=False, expand_alpha=expand_alpha)
                
                return  # 动画中直接返回，不继续后续绘制
            else:
                # 动画完成，更新状态
                self._score_panel_last_difficulty = self._score_panel_pending_difficulty
                self._score_panel_fade_start_time = None
                self._score_panel_pending_difficulty = None
                self._score_panel_pending_data = None
        
        # 没有动画时，正常绘制
        self._draw_score_panel_background(expand_alpha)  # 先绘制背景
        self._draw_score_content(song_id, difficulty_name, score_data, expand_alpha)  # 再绘制内容
    
    def _draw_single_score_panel(self, song_id, difficulty_name, score_data, fade_progress, scale_progress):
        """绘制单个分数面板（用于动画和静态显示）"""
        if not difficulty_name or not score_data:
            return
        
        score_manager = self._score_manager
        
        # 创建临时 Surface 用于整体淡出动画
        scores_img = self.bg_images['scores']
        orig_scores_width = scores_img.get_width()
        orig_scores_height = scores_img.get_height()
        
        # 宽度减少5%
        base_width = int(orig_scores_width * 0.95)
        scores_height = orig_scores_height
        
        # 创建临时 Surface（宽度足够容纳未缩放的内容，支持透明度）
        temp_surface = pygame.Surface((base_width, scores_height), pygame.SRCALPHA)
        temp_surface.fill((0, 0, 0, 0))  # 完全透明背景
        
        # 在临时 Surface 上绘制背景（使用九宫格拉伸）
        self._draw_nine_patch_to_surface(scores_img, temp_surface, 0, 0, base_width, scores_height, border_ratio=0.28)
        
        # 在临时 Surface 上绘制"最好成绩"固定文字（中心位置按90%缩放：255*0.9=230，67保持不变，3px黑色描边）
        best_score_text = "最好成绩"
        text_center_x = 230  # 原255 * 0.9
        text_center_y = 67
        
        # 绘制描边
        for offset_x in range(-3, 4):
            for offset_y in range(-3, 4):
                if offset_x != 0 or offset_y != 0:
                    outline_surface = self.fonts['small'].render(best_score_text, True, (0, 0, 0))
                    outline_x = text_center_x - outline_surface.get_width() // 2 + offset_x
                    outline_y = text_center_y - outline_surface.get_height() // 2 + offset_y
                    temp_surface.blit(outline_surface, (outline_x, outline_y))
        
        # 绘制主文字
        best_score_surface = self.fonts['small'].render(best_score_text, True, (255, 255, 255))
        best_score_x = text_center_x - best_score_surface.get_width() // 2
        best_score_y = text_center_y - best_score_surface.get_height() // 2
        temp_surface.blit(best_score_surface, (best_score_x, best_score_y))
        
        # 绘制分数（使用数字图片，中心位置按90%缩放并左移10px：316*0.9-10=274，129保持不变）
        score_value = score_data.get('score', 0)
        score_center_x = 264  # 原316 * 0.9 - 10
        score_center_y = 129
        
        if 'score_numbers' in self.bg_images:
            score_numbers = self.bg_images['score_numbers']
            score_str = str(score_value)
            
            if score_numbers:
                # 先缩放并收集所有数字图片
                digit_images = []
                total_width = 0
                max_height = 0
                scale_factor_y = 0.9  # 垂直方向缩小10%
                scale_factor_x = 0.81  # 水平方向缩小19% (0.9 * 0.9)
                
                for char in score_str:
                    digit = int(char)
                    if digit in score_numbers:
                        # 缩放数字：水平缩小更多，垂直缩小10%
                        orig_img = score_numbers[digit]
                        new_width = int(orig_img.get_width() * scale_factor_x)
                        new_height = int(orig_img.get_height() * scale_factor_y)
                        scaled_img = pygame.transform.smoothscale(orig_img, (new_width, new_height))
                        
                        digit_images.append(scaled_img)
                        # 获取缩放后图片的非透明区域边界
                        img_rect = scaled_img.get_bounding_rect()
                        # 使用实际内容宽度减去4px重叠（更紧密的间距）
                        total_width += img_rect.width - 4
                        max_height = max(max_height, img_rect.height)
                
                # 从中心位置开始绘制（向左偏移一半宽度）
                start_x = score_center_x - total_width // 2
                current_x = start_x
                
                # 逐个绘制数字到临时 Surface（更紧密贴合，重叠更多）
                for digit_img in digit_images:
                    # 获取数字的非透明区域边界
                    img_rect = digit_img.get_bounding_rect()
                    # 绘制时偏移到实际内容区域
                    digit_y = score_center_y - img_rect.height // 2
                    temp_surface.blit(digit_img, (current_x - img_rect.x, digit_y - img_rect.y))
                    current_x += img_rect.width - 4  # 减4px让数字重叠更多，间距更紧密
        else:
            # 如果没有加载数字图片，使用文字（后备方案）
            score_text = str(score_value)
            score_surface = self.fonts['title_cn'].render(score_text, True, (255, 215, 0))  # 金色
            score_x = score_center_x - score_surface.get_width() // 2
            score_y = score_center_y - score_surface.get_height() // 2
            temp_surface.blit(score_surface, (score_x, score_y))
        
        # 绘制难度图标（位置按90%缩放：88*0.9=79，上移5px至131，放大160%，保持宽高比）
        # 将难度名称转换为图标索引：Easy=1, Normal=2, Hard=3, Oni=4, Edit=5
        diff_index_map = {'Easy': 1, 'Normal': 2, 'Hard': 3, 'Oni': 4, 'Edit': 5}
        diff_index = diff_index_map.get(difficulty_name)
        icon_center_x = 79  # 原88 * 0.9
        icon_center_y = 131  # 原136 - 5
        
        if diff_index and diff_index in self.diff_images:
            difficulty_icon = self.diff_images[diff_index]
            icon_x = icon_center_x
            icon_y = icon_center_y
            
            # 保持宽高比，放大160%（使用smoothscale保持平滑，避免锯齿）
            orig_width, orig_height = difficulty_icon.get_size()
            scale_factor = 1.6
            new_width = int(orig_width * scale_factor)
            new_height = int(orig_height * scale_factor)
            
            # 使用smoothscale保持平滑缩放，避免锯齿
            scaled_icon = pygame.transform.smoothscale(difficulty_icon, (new_width, new_height))
            temp_surface.blit(scaled_icon, (icon_x - new_width // 2, icon_y - new_height // 2))
        
        # 应用缩放和淡出动画
        scaled_width = int(base_width * scale_progress)
        scaled_height = int(scores_height * scale_progress)
        
        # 对临时 Surface 应用缩放
        if scaled_width > 0 and scaled_height > 0:
            scaled_surface = pygame.transform.smoothscale(temp_surface, (scaled_width, scaled_height))
            
            # 应用透明度
            alpha = int(255 * fade_progress)
            scaled_surface.set_alpha(alpha)
            
            # 计算屏幕上的绘制位置（水平居中，垂直在屏幕中心偏上210px）
            final_x = (self.width - scaled_width) // 2  # 水平居中
            final_y = (self.height // 2 - 210) - scaled_height // 2  # 面板中心在屏幕中心偏上210px
            
            # 绘制缩放和淡出后的面板到屏幕
            self.screen.blit(scaled_surface, (final_x, final_y))
    
    def _draw_score_panel_background(self, expand_alpha: float = 1.0):
        """绘制分数面板背景（固定不动）"""
        scores_img = self.bg_images['scores']
        orig_scores_width = scores_img.get_width()
        orig_scores_height = scores_img.get_height()
        
        # 宽度减少5%
        base_width = int(orig_scores_width * 0.95)
        scores_height = orig_scores_height
        
        # 创建临时 Surface
        temp_surface = pygame.Surface((base_width, scores_height), pygame.SRCALPHA)
        temp_surface.fill((0, 0, 0, 0))
        
        # 绘制背景（使用九宫格拉伸）
        self._draw_nine_patch_to_surface(scores_img, temp_surface, 0, 0, base_width, scores_height, border_ratio=0.28)
        
        # 绘制"最好成绩"固定文字（3px黑色描边）
        best_score_text = "最好成绩"
        text_center_x = 230
        text_center_y = 67
        
        # 绘制描边
        for offset_x in range(-3, 4):
            for offset_y in range(-3, 4):
                if offset_x != 0 or offset_y != 0:
                    outline_surface = self.fonts['small'].render(best_score_text, True, (0, 0, 0))
                    outline_x = text_center_x - outline_surface.get_width() // 2 + offset_x
                    outline_y = text_center_y - outline_surface.get_height() // 2 + offset_y
                    temp_surface.blit(outline_surface, (outline_x, outline_y))
        
        # 绘制主文字
        best_score_surface = self.fonts['small'].render(best_score_text, True, (255, 255, 255))
        best_score_x = text_center_x - best_score_surface.get_width() // 2
        best_score_y = text_center_y - best_score_surface.get_height() // 2
        temp_surface.blit(best_score_surface, (best_score_x, best_score_y))
        
        # 应用展开/收起透明度
        temp_surface.set_alpha(int(255 * expand_alpha))
        
        # 计算屏幕上的绘制位置
        final_x = (self.width - base_width) // 2
        final_y = (self.height // 2 - 210) - scores_height // 2
        
        self.screen.blit(temp_surface, (final_x, final_y))
    
    def _draw_score_content(self, song_id, difficulty_name, score_data, expand_alpha: float = 1.0):
        """绘制分数内容（难度图标和分数）"""
        if not difficulty_name or not score_data:
            return
        
        scores_img = self.bg_images['scores']
        orig_scores_width = scores_img.get_width()
        orig_scores_height = scores_img.get_height()
        base_width = int(orig_scores_width * 0.95)
        scores_height = orig_scores_height
        
        # 创建内容 Surface（只包含分数和图标）
        content_surface = pygame.Surface((base_width, scores_height), pygame.SRCALPHA)
        content_surface.fill((0, 0, 0, 0))
        
        # 绘制分数
        score_value = score_data.get('score', 0)
        score_center_x = 264
        score_center_y = 129
        
        self._draw_score_numbers(content_surface, score_value, score_center_x, score_center_y)
        
        # 绘制难度图标
        diff_index_map = {'Easy': 1, 'Normal': 2, 'Hard': 3, 'Oni': 4, 'Edit': 5}
        diff_index = diff_index_map.get(difficulty_name)
        icon_center_x = 79
        icon_center_y = 131
        
        if diff_index and diff_index in self.diff_images:
            difficulty_icon = self.diff_images[diff_index]
            orig_width, orig_height = difficulty_icon.get_size()
            scale_factor = 1.6
            new_width = int(orig_width * scale_factor)
            new_height = int(orig_height * scale_factor)
            scaled_icon = pygame.transform.smoothscale(difficulty_icon, (new_width, new_height))
            content_surface.blit(scaled_icon, (icon_center_x - new_width // 2, icon_center_y - new_height // 2))
        
        # 应用展开/收起透明度
        content_surface.set_alpha(int(255 * expand_alpha))
        
        # 绘制到屏幕
        final_x = (self.width - base_width) // 2
        final_y = (self.height // 2 - 210) - scores_height // 2
        self.screen.blit(content_surface, (final_x, final_y))
    
    def _draw_score_content_flip(self, song_id, difficulty_name, score_data, flip_progress, flip_out, expand_alpha: float = 1.0):
        """绘制翻转中的分数内容（777老虎机效果）"""
        if not difficulty_name or not score_data:
            return
        
        import math
        
        scores_img = self.bg_images['scores']
        orig_scores_width = scores_img.get_width()
        orig_scores_height = scores_img.get_height()
        base_width = int(orig_scores_width * 0.95)
        scores_height = orig_scores_height
        
        # 创建内容 Surface
        content_surface = pygame.Surface((base_width, scores_height), pygame.SRCALPHA)
        content_surface.fill((0, 0, 0, 0))
        
        # 绘制分数和图标
        score_value = score_data.get('score', 0)
        score_center_x = 264
        score_center_y = 129
        self._draw_score_numbers(content_surface, score_value, score_center_x, score_center_y)
        
        diff_index_map = {'Easy': 1, 'Normal': 2, 'Hard': 3, 'Oni': 4, 'Edit': 5}
        diff_index = diff_index_map.get(difficulty_name)
        icon_center_x = 79
        icon_center_y = 131
        
        if diff_index and diff_index in self.diff_images:
            difficulty_icon = self.diff_images[diff_index]
            orig_width, orig_height = difficulty_icon.get_size()
            scale_factor = 1.6
            new_width = int(orig_width * scale_factor)
            new_height = int(orig_height * scale_factor)
            scaled_icon = pygame.transform.smoothscale(difficulty_icon, (new_width, new_height))
            content_surface.blit(scaled_icon, (icon_center_x - new_width // 2, icon_center_y - new_height // 2))
        
        # 计算翻转效果的Y偏移和透明度
        if flip_out:
            # 旧分数：向上移动并消失
            y_offset = -int(18 * flip_progress)  # 向上移动18px（减少70%）
            flip_alpha = (1.0 - flip_progress)  # 渐隐
        else:
            # 新分数：从下方上来并出现
            y_offset = int(18 * (1.0 - flip_progress))  # 从下方18px移动到0（减少70%）
            flip_alpha = flip_progress  # 渐现
        
        # 组合翻转透明度和展开/收起透明度
        combined_alpha = int(255 * flip_alpha * expand_alpha)
        content_surface.set_alpha(combined_alpha)
        
        # 绘制到屏幕
        final_x = (self.width - base_width) // 2
        final_y = (self.height // 2 - 210) - scores_height // 2 + y_offset
        self.screen.blit(content_surface, (final_x, final_y))
    
    def _draw_score_numbers(self, surface, score_value, center_x, center_y):
        """在指定surface上绘制分数数字"""
        if 'score_numbers' in self.bg_images:
            score_numbers = self.bg_images['score_numbers']
            score_str = str(score_value)
            
            if score_numbers:
                digit_images = []
                total_width = 0
                scale_factor_y = 0.9
                scale_factor_x = 0.81
                
                for char in score_str:
                    digit = int(char)
                    if digit in score_numbers:
                        orig_img = score_numbers[digit]
                        new_width = int(orig_img.get_width() * scale_factor_x)
                        new_height = int(orig_img.get_height() * scale_factor_y)
                        scaled_img = pygame.transform.smoothscale(orig_img, (new_width, new_height))
                        digit_images.append(scaled_img)
                        img_rect = scaled_img.get_bounding_rect()
                        total_width += img_rect.width - 4
                
                start_x = center_x - total_width // 2
                current_x = start_x
                
                for digit_img in digit_images:
                    img_rect = digit_img.get_bounding_rect()
                    digit_y = center_y - img_rect.height // 2
                    surface.blit(digit_img, (current_x - img_rect.x, digit_y - img_rect.y))
                    current_x += img_rect.width - 4
        else:
            # 后备方案：使用文字
            score_text = str(score_value)
            score_surface = self.fonts['title_cn'].render(score_text, True, (255, 215, 0))
            score_x = center_x - score_surface.get_width() // 2
            score_y = center_y - score_surface.get_height() // 2
            surface.blit(score_surface, (score_x, score_y))
    
    def _draw_score_info(self, button: SongButton, button_x: int, button_y: int, 
                         button_width: int, button_height: int):
        """
        绘制成绩信息（在展开面板右上角，最顶层）
        Draw score information (on expanded panel top-right corner, top layer)
        
        Args:
            button: 歌曲按钮对象
            button_x: 按钮X坐标
            button_y: 按钮Y坐标
            button_width: 按钮宽度
            button_height: 按钮高度
        """
        # 检查是否有 scores.png
        if 'scores' not in self.bg_images:
            return
        
        # 如果没有难度列表，返回
        if not hasattr(button, 'difficulties') or not button.difficulties:
            return
        
        song_id = button.tja_path.stem
        
        # 使用缓存的成绩管理器实例（避免重复加载）
        score_manager = self._score_manager
        
        # 优先尝试获取当前选中难度的成绩
        difficulty_name = None
        score_data = None
        
        # 1. 如果有选中的难度，先尝试获取该难度的成绩
        if hasattr(button, 'selected_diff_index') and button.selected_diff_index >= 0:
            difficulty_name = button.difficulties[button.selected_diff_index]
            score_data = score_manager.get_score(song_id, difficulty_name)
        
        # 2. 如果没有选中难度或该难度没有成绩，遍历所有难度找最高分
        if not score_data or score_data.get('score', 0) == 0:
            best_score = 0
            best_difficulty = None
            best_score_data = None
            
            for diff in button.difficulties:
                diff_score_data = score_manager.get_score(song_id, diff)
                if diff_score_data and diff_score_data.get('score', 0) > best_score:
                    best_score = diff_score_data.get('score', 0)
                    best_difficulty = diff
                    best_score_data = diff_score_data
            
            if best_score_data:
                difficulty_name = best_difficulty
                score_data = best_score_data
        
        # 如果所有难度都没有成绩，不显示
        if not score_data or score_data.get('score', 0) == 0:
            return
        
        # 绘制 scores.png 背景（右上角位置）
        scores_img = self.bg_images['scores']
        scores_width = scores_img.get_width()
        scores_height = scores_img.get_height()
        
        # 计算位置：展开面板的右上角
        scores_x = button_x + button_width - scores_width - 20  # 右侧边距20px
        scores_y = button_y + 20  # 顶部边距20px
        self.screen.blit(scores_img, (scores_x, scores_y))
        
        # 绘制"最好成绩"固定文字（中心位置 255x67，3px黑色描边）
        best_score_text = "最好成绩"
        # 绘制描边
        for offset_x in range(-3, 4):
            for offset_y in range(-3, 4):
                if offset_x != 0 or offset_y != 0:
                    outline_surface = self.fonts['small'].render(best_score_text, True, (0, 0, 0))
                    outline_x = scores_x + 255 - outline_surface.get_width() // 2 + offset_x
                    outline_y = scores_y + 67 - outline_surface.get_height() // 2 + offset_y
                    self.screen.blit(outline_surface, (outline_x, outline_y))
        
        # 绘制主文字
        best_score_surface = self.fonts['small'].render(best_score_text, True, (255, 255, 255))
        best_score_x = scores_x + 255 - best_score_surface.get_width() // 2
        best_score_y = scores_y + 67 - best_score_surface.get_height() // 2
        self.screen.blit(best_score_surface, (best_score_x, best_score_y))
        
        # 绘制分数（使用数字图片，中心位置 316x129）
        score_value = score_data.get('score', 0)
        
        if 'score_numbers' in self.bg_images:
            score_numbers = self.bg_images['score_numbers']
            score_str = str(score_value)
            
            if score_numbers:
                # 先缩放并收集所有数字图片
                digit_images = []
                total_width = 0
                max_height = 0
                scale_factor = 0.9  # 缩小10%
                
                for char in score_str:
                    digit = int(char)
                    if digit in score_numbers:
                        # 缩小10%
                        orig_img = score_numbers[digit]
                        new_width = int(orig_img.get_width() * scale_factor)
                        new_height = int(orig_img.get_height() * scale_factor)
                        scaled_img = pygame.transform.smoothscale(orig_img, (new_width, new_height))
                        
                        digit_images.append(scaled_img)
                        # 获取缩放后图片的非透明区域边界
                        img_rect = scaled_img.get_bounding_rect()
                        # 使用实际内容宽度减去2px重叠（完全去除间距）
                        total_width += img_rect.width - 2
                        max_height = max(max_height, img_rect.height)
                
                # 从中心位置开始绘制（向左偏移一半宽度）
                start_x = scores_x + 316 - total_width // 2
                current_x = start_x
                
                # 逐个绘制数字（完全紧密贴合，略微重叠）
                for digit_img in digit_images:
                    # 获取数字的非透明区域边界
                    img_rect = digit_img.get_bounding_rect()
                    # 绘制时偏移到实际内容区域
                    digit_y = scores_y + 129 - img_rect.height // 2
                    self.screen.blit(digit_img, (current_x - img_rect.x, digit_y - img_rect.y))
                    current_x += img_rect.width - 2  # 减2px让数字重叠，完全消除间距
        else:
            # 如果没有加载数字图片，使用文字（后备方案）
            score_text = str(score_value)
            score_surface = self.fonts['title_cn'].render(score_text, True, (255, 215, 0))  # 金色
            score_x = scores_x + 316 - score_surface.get_width() // 2
            score_y = scores_y + 129 - score_surface.get_height() // 2
            self.screen.blit(score_surface, (score_x, score_y))
        
        # 绘制难度图标（位置 88x136，放大40%，保持宽高比）
        # 将难度名称转换为图标索引：Easy=1, Normal=2, Hard=3, Oni=4, Edit=5
        diff_index_map = {'Easy': 1, 'Normal': 2, 'Hard': 3, 'Oni': 4, 'Edit': 5}
        diff_index = diff_index_map.get(difficulty_name)
        
        if diff_index and diff_index in self.diff_images:
            difficulty_icon = self.diff_images[diff_index]
            icon_x = scores_x + 88
            icon_y = scores_y + 136
            
            # 保持宽高比，放大140%
            orig_width, orig_height = difficulty_icon.get_size()
            scale_factor = 1.4
            new_width = int(orig_width * scale_factor)
            new_height = int(orig_height * scale_factor)
            
            scaled_icon = pygame.transform.smoothscale(difficulty_icon, (new_width, new_height))
            self.screen.blit(scaled_icon, (icon_x - new_width // 2, icon_y - new_height // 2))
    
    def _draw_complete_difficulty_wrapped(self, x: int, y: int, icon_img: pygame.Surface, 
                                          stars: int, diff_level: int, selected: bool, blink_time: float = 0):
        """
        完整包裹绘制：SB背景图作为底图，难度图标和星级都在其内部
        
        Args:
            x, y: 绘制位置
            icon_img: 难度图标图片
            stars: 星数 (1-10)
            diff_level: 难度等级 (1-5)
            selected: 是否选中
            blink_time: 闪烁动画时间（用于发光效果）
        """
        star_key = f'star_{diff_level}'
        num_key = f'num_{stars}'
        sb_key = 'sb_2' if selected else 'sb_1'
        
        # 检查资源是否存在
        if sb_key not in self.diff_images:
            print(f"[DEBUG] Missing SB image: {sb_key}")
            self.screen.blit(icon_img, (x, y))
            return
        if star_key not in self.diff_images:
            print(f"[DEBUG] Missing star image: {star_key}")
            self.screen.blit(icon_img, (x, y))
            return
        if num_key not in self.diff_images:
            print(f"[DEBUG] Missing number image: {num_key}")
            self.screen.blit(icon_img, (x, y))
            return
        
        sb_img = self.diff_images[sb_key]
        star_img = self.diff_images[star_key]
        num_img = self.diff_images[num_key]
        
        # 1. 绘制SB背景图（底图），选中时添加呼吸效果
        if selected:
            # 检测难度切换，重置呼吸动画从最亮开始
            difficulty_key = f"{diff_level}_{stars}"
            if not hasattr(self, '_last_selected_diff') or self._last_selected_diff != difficulty_key:
                self._last_selected_diff = difficulty_key
                self._diff_selection_time = blink_time  # 记录切换时的时间
            
            # 计算从切换开始的时间差
            elapsed = blink_time - getattr(self, '_diff_selection_time', blink_time)
            # 呼吸效果：从最亮（1.0）开始，使用余弦函数
            fade = 0.5 + 0.5 * math.cos(elapsed / 500)  # 使用 cos 从1.0开始
            
            # 先绘制 sb_1（基础图）
            sb_1_img = self.diff_images.get('sb_1')
            if sb_1_img:
                self.screen.blit(sb_1_img, (x, y))
            
            # 再叠加半透明的 sb_2（高亮图），透明度随呼吸变化
            sb_2_overlay = sb_img.copy()
            alpha = int(fade * 255)  # 透明度随呼吸变化 0-255
            sb_2_overlay.set_alpha(alpha)
            self.screen.blit(sb_2_overlay, (x, y))
        else:
            # 未选中直接绘制 sb_1
            self.screen.blit(sb_img, (x, y))
        
        # 2. 在SB图内部绘制难度图标（水平居中，垂直靠上，下移3px）
        icon_x = x + (sb_img.get_width() - icon_img.get_width()) // 2
        icon_y = y + 8  # 图标距离SB图顶部8px（下移3px）
        self.screen.blit(icon_img, (icon_x, icon_y))
        
        # 3. 在SB图内部绘制星星（左侧，垂直靠下，上移5px）
        star_num_group_width = star_img.get_width() + num_img.get_width() + 2  # 星星+间隔+数字
        start_x = x + (sb_img.get_width() - star_num_group_width) // 2  # 整体居中
        star_x = start_x
        star_y = y + sb_img.get_height() - star_img.get_height() - 8  # 星星距离底部8px（上移5px）
        self.screen.blit(star_img, (star_x, star_y))
        
        # 4. 数字在星星右侧
        num_x = star_x + star_img.get_width() + 2  # 星星右侧 + 2px间距
        num_y = star_y + (star_img.get_height() - num_img.get_height()) // 2  # 垂直居中对齐星星
        self.screen.blit(num_img, (num_x, num_y))
    
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
                if button.expanded and 2 in self.bg_images:
                    # 展开时使用big_2的高度
                    glow_width, glow_height = self._get_glow_frame_size()
                    height = int(glow_height * 1.25) if glow_height > 0 else int((self.button_height + 100) * 1.25)
                else:
                    height = int((self.button_height + (100 if button.expanded else 0)) * 1.25)
            else:
                # 未选中歌曲的缩小高度 - 整体扩大25%
                height = int((self.button_height * 0.85) * 1.25)
            total_height += height - 15  # 减小间距
        return total_height
    
    def draw_score_panel_if_needed(self):
        """
        绘制成绩面板（如果有保存的数据）
        Draw score panel if data is saved
        
        这个方法应该在所有其他UI元素绘制完成后调用，确保成绩面板在最上层
        成绩面板固定在屏幕右上角，不跟随滚动
        """
        # 更新展开状态和透明度
        current_time = pygame.time.get_ticks()
        target_expanded = hasattr(self, '_score_panel_data') and self._score_panel_data is not None
        
        # 如果有新数据，缓存起来
        if self._score_panel_data:
            self._score_panel_cached_data = self._score_panel_data
            self._score_panel_data = None
        
        # 检测状态变化，启动动画
        if target_expanded != self._score_panel_is_expanded:
            self._score_panel_is_expanded = target_expanded
            if target_expanded:
                # 开始展开动画
                self._score_panel_expand_start_time = current_time
                self._score_panel_collapse_start_time = None
            else:
                # 开始收起动画
                self._score_panel_collapse_start_time = current_time
                self._score_panel_expand_start_time = None
        
        # 计算当前透明度（基于动画进度）
        if self._score_panel_expand_start_time is not None:
            # 淡入动画
            elapsed = current_time - self._score_panel_expand_start_time
            if elapsed >= self._score_panel_expand_duration:
                # 动画完成
                self._score_panel_expand_alpha = 1.0
                self._score_panel_expand_start_time = None
            else:
                # 计算线性进度 (0.0 -> 1.0)
                linear_progress = elapsed / self._score_panel_expand_duration
                # 应用缓动函数（开始慢，中间快，结束慢）
                self._score_panel_expand_alpha = self._ease_in_out_cubic(linear_progress)
        
        elif self._score_panel_collapse_start_time is not None:
            # 淡出动画
            elapsed = current_time - self._score_panel_collapse_start_time
            if elapsed >= self._score_panel_expand_duration:
                # 动画完成
                self._score_panel_expand_alpha = 0.0
                self._score_panel_collapse_start_time = None
            else:
                # 计算线性进度 (1.0 -> 0.0)
                linear_progress = 1.0 - (elapsed / self._score_panel_expand_duration)
                # 应用缓动函数（开始慢，中间快，结束慢）
                self._score_panel_expand_alpha = self._ease_in_out_cubic(linear_progress)
        
        # 只在透明度大于0且有缓存数据时绘制
        if self._score_panel_expand_alpha > 0.0 and self._score_panel_cached_data:
            # 确保没有任何裁剪限制，成绩面板可以覆盖所有内容
            self.screen.set_clip(None)
            
            # 使用缓存的数据绘制（在淡出期间继续显示）
            self._draw_score_info_fixed(self._score_panel_cached_data['button'], self._score_panel_expand_alpha)
        
        # 如果完全淡出，清除缓存
        if self._score_panel_expand_alpha <= 0.0:
            self._score_panel_cached_data = None
    
    def _ease_in_out_cubic(self, t: float) -> float:
        """
        三次缓动函数（开始慢，中间快，结束慢）
        Cubic easing function (slow start, fast middle, slow end)
        
        Args:
            t: 输入值 (0.0 - 1.0)
        
        Returns:
            float: 缓动后的值 (0.0 - 1.0)
        """
        if t < 0.5:
            return 4 * t * t * t
        else:
            p = 2 * t - 2
            return 1 + 0.5 * p * p * p
    
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
