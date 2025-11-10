"""
结算画面渲染模块
Result Screen Renderer Module

负责在游戏结束后显示结算信息，包括：
- 结算背景
- 歌曲名称和难度
- 皇冠等级（根据成绩）
- 得分
- 判定统计（良、可、不可、连打数、最大连段数）
"""

import pygame
from pathlib import Path
from typing import Dict, Tuple


class ResultScreen:
    """
    结算画面渲染器
    Result Screen Renderer
    
    负责渲染游戏结束后的结算信息
    """
    
    def __init__(self, screen, resource_loader):
        """
        初始化结算画面渲染器
        
        Args:
            screen: pygame显示表面
            resource_loader: 资源加载器
        """
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.resource_loader = resource_loader
        
        # 加载结算画面资源
        self.result_resources = resource_loader.load_result_screen_resources()
        
        # 颜色常量
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.ORANGE = (247, 152, 36)
        
        # 加载字体（副标题字体减少20%：36 → 29）
        font_path = resource_loader.font_path
        try:
            self.title_font = pygame.font.Font(str(font_path), 48)
            self.subtitle_font = pygame.font.Font(str(font_path), 29)  # 减少20%
            self.score_font = pygame.font.Font(str(font_path), 72)
            self.stats_font = pygame.font.Font(str(font_path), 42)
            self.hint_font = pygame.font.Font(str(font_path), 28)
        except:
            print("Failed to load custom font, using default font")
            self.title_font = pygame.font.Font(None, 48)
            self.subtitle_font = pygame.font.Font(None, 29)  # 减少20%
            self.score_font = pygame.font.Font(None, 72)
            self.stats_font = pygame.font.Font(None, 42)
            self.hint_font = pygame.font.Font(None, 28)
    
    def _get_crown_level(self, total_notes: int, perfect_count: int, good_count: int, miss_count: int) -> int:
        """
        根据成绩计算皇冠等级
        
        Args:
            total_notes: 总音符数
            perfect_count: 良数量
            good_count: 可数量
            miss_count: 不可数量
        
        Returns:
            int: 皇冠等级 (1=bronze, 2=silver, 3=gold, 0=no crown)
        """
        if total_notes == 0:
            return 0
        
        # 全良 (Full Combo with all Perfect) = 金皇冠
        if miss_count == 0 and good_count == 0:
            return 3
        
        # Full Combo = 银皇冠
        if miss_count == 0:
            return 2
        
        # 通关 (Clear) = 铜皇冠
        # 这里简化判断：只要有得分就算通关
        if perfect_count + good_count > 0:
            return 1
        
        # 没有通关
        return 0
    
    def _draw_text_with_outline(self, text: str, font, color: Tuple[int, int, int], 
                                outline_color: Tuple[int, int, int], x: int, y: int, 
                                center: bool = False, outline_width: int = 3):
        """
        绘制带圆润描边的文字（圆形描边算法 - 更平滑）
        
        Args:
            text: 文字内容
            font: 字体
            color: 文字颜色
            outline_color: 描边颜色
            x: X坐标
            y: Y坐标
            center: 是否居中对齐
            outline_width: 描边宽度
        """
        import math
        
        # 优化：只渲染一次描边文字表面
        outline_surf = font.render(text, True, outline_color)
        
        # 使用圆形描边 - 每30度一个点，更平滑
        offsets_set = set()  # 使用set去重
        for angle in range(0, 360, 30):  # 每30度一个点（12个方向）
            rad = math.radians(angle)
            for r in range(1, outline_width + 1):
                dx = int(round(r * math.cos(rad)))
                dy = int(round(r * math.sin(rad)))
                offsets_set.add((dx, dy))
        
        # 绘制圆润描边
        for dx, dy in offsets_set:
            outline_rect = outline_surf.get_rect()
            if center:
                outline_rect.center = (x + dx, y + dy)
            else:
                outline_rect.topleft = (x + dx, y + dy)
            self.screen.blit(outline_surf, outline_rect)
        
        # 绘制文字主体
        text_surf = font.render(text, True, color)
        text_rect = text_surf.get_rect()
        if center:
            text_rect.center = (x, y)
        else:
            text_rect.topleft = (x, y)
        self.screen.blit(text_surf, text_rect)
    
    def _draw_number_images(self, number: int, x: int, y: int, center: bool = True, spacing: int = 2, scale: float = 1.0):
        """
        使用图片绘制数字
        
        Args:
            number: 要显示的数字
            x: X坐标
            y: Y坐标
            center: 是否居中对齐
            spacing: 数字之间的间距
            scale: 缩放比例
        """
        num_str = str(number)
        digit_images = []
        total_width = 0
        max_height = 0
        
        # 收集所有数字图片并计算总宽度
        for digit_char in num_str:
            digit = int(digit_char)
            key = f'num_{digit}'
            if key in self.result_resources:
                img = self.result_resources[key]
                # 如果需要缩放，缩放图片
                if scale != 1.0:
                    orig_w, orig_h = img.get_size()
                    new_w = int(orig_w * scale)
                    new_h = int(orig_h * scale)
                    img = pygame.transform.smoothscale(img, (new_w, new_h))
                digit_images.append(img)
                total_width += img.get_width() + spacing
                max_height = max(max_height, img.get_height())
        
        if not digit_images:
            return
        
        # 移除最后一个间距
        total_width -= spacing
        
        # 计算起始X坐标
        if center:
            current_x = x - total_width // 2
        else:
            current_x = x
        
        # 绘制每个数字
        for img in digit_images:
            img_rect = img.get_rect()
            img_rect.midleft = (current_x, y)
            self.screen.blit(img, img_rect)
            current_x += img.get_width() + spacing
    
    def draw(self, song_title: str, difficulty: str, score: int, 
             perfect_count: int, good_count: int, ok_count: int, miss_count: int,
             drumroll_count: int, max_combo: int, total_notes: int, subtitle: str = "", 
             titlecn: str = "", subtitlecn: str = "", bg_color: Tuple[int, int, int] = None):
        """
        绘制结算画面
        
        Args:
            song_title: 歌曲名称
            difficulty: 难度 (Easy/Normal/Hard/Oni/Edit)
            score: 得分
            perfect_count: 良数量
            good_count: 可数量
            ok_count: 不可数量
            miss_count: 不可数量
            drumroll_count: 连打数
            max_combo: 最大连段数
            total_notes: 总音符数
            subtitle: 副标题（歌曲艺术家或来源）
            titlecn: 中文标题（优先使用）
            subtitlecn: 中文副标题（优先使用）
            bg_color: 背景颜色（使用分类颜色），默认为黑色
        """
        # 优先使用中文标题和副标题
        display_title = titlecn if titlecn else song_title
        display_subtitle = subtitlecn if subtitlecn else subtitle
        # 使用分类颜色或默认黑色填充屏幕
        fill_color = bg_color if bg_color else self.BLACK
        self.screen.fill(fill_color)
        
        # 绘制背景（保持原始比例，居中显示）
        if 'background' in self.result_resources:
            bg = self.result_resources['background']
            # 不缩放，保持原始尺寸
            bg_rect = bg.get_rect()
            bg_rect.center = (self.width // 2, self.height // 2)
            self.screen.blit(bg, bg_rect)
        
        # 计算皇冠等级
        crown_level = self._get_crown_level(total_notes, perfect_count, good_count, miss_count)
        
        # 难度映射
        diff_mapping = {
            'Easy': 1, 'Normal': 2, 'Hard': 3, 'Oni': 4, 'Edit': 5
        }
        diff_level = diff_mapping.get(difficulty, 4)
        
        # === 根据截图位置放置元素 ===
        
        # === 歌名位置（标题）===
        # 基准位置：屏幕高度8%处
        # 垂直偏移：基准位置 + 250px（向下移动）
        # 水平位置：屏幕中心（居中显示）
        # 优先显示：TITLECN > TITLE
        title_y = int(self.height * 0.08) + 250  # 下移250px
        self._draw_text_with_outline(display_title, self.title_font, self.WHITE, self.BLACK, 
                                     self.width // 2, title_y, center=True, outline_width=4)
        
        # === 副标题位置（歌曲副标题）===
        # 基准位置：屏幕高度12.5%处
        # 垂直偏移：基准位置 + 250px（与标题同步下移）
        # 水平位置：屏幕中心（居中显示）
        # 显示内容：歌曲副标题（优先显示：SUBTITLECN > SUBTITLE）
        # 字体大小：29（减少20%）
        # 描边宽度：4（增加2，原来是2）
        subtitle_y = int(self.height * 0.125) + 250  # 下移250px
        # 如果有副标题则显示
        if display_subtitle:
            self._draw_text_with_outline(display_subtitle, self.subtitle_font, self.WHITE, self.BLACK, 
                                         self.width // 2, subtitle_y, center=True, outline_width=4)
        
        # === 难度图标位置 ===
        # 基准位置：屏幕高度31%处
        # 水平偏移：屏幕宽度20%基准点 + 29px（向右微调）
        # 垂直偏移：基准位置 + 106px（向下移动）
        icon_y = int(self.height * 0.31) + 110  # 下移106px（原100px + 6px）
        if f'lv_{diff_level}' in self.result_resources:
            lv_icon = self.result_resources[f'lv_{diff_level}']
            lv_rect = lv_icon.get_rect()
            # 水平位置：右移29px（原23px + 6px）
            lv_rect.center = (int(self.width * 0.20) + 29, icon_y)
            self.screen.blit(lv_icon, lv_rect)
        
        # === 皇冠图标位置 ===
        # 基准位置：屏幕高度31%处
        # 水平偏移：屏幕宽度80%基准点 - 400px（向左大幅偏移）
        # 垂直偏移：基准位置 + 230px（向下移动）
        # 缩放比例：1.725倍（原始80px高度 → 138px高度）
        crown_icon_y = int(self.height * 0.31) + 230  # 下移230px（原240px - 10px）
        if crown_level > 0 and f'crown_{crown_level:02d}' in self.result_resources:
            crown_icon = self.result_resources[f'crown_{crown_level:02d}']
            # 皇冠放大1.725倍（= 原50% × 再15% = 1.5 × 1.15）
            orig_w, orig_h = crown_icon.get_size()
            crown_icon = pygame.transform.smoothscale(crown_icon, (int(orig_w * 1.725), int(orig_h * 1.725)))
            crown_rect = crown_icon.get_rect()
            # 水平位置：左移400px
            crown_rect.center = (int(self.width * 0.80) - 400, crown_icon_y)
            self.screen.blit(crown_icon, crown_rect)
        
        # === 只显示数字，不显示标签（背景图已包含标签文字）===
        
        # === 得分数字位置 ===
        # 基准位置：屏幕高度35%处
        # 水平偏移：屏幕中心 + 100px（向右偏移）
        # 垂直偏移：基准位置 + 175px（向下移动）
        # 缩放比例：1.4倍（放大27.5%，总宽度减少15%：1.5 × 0.85 = 1.275）
        # 间距：-5px（负间距使数字稍微重叠，进一步压缩宽度）
        score_y = int(self.height * 0.35) + 175  # 下移175px（原180px - 5px）
        score_x = self.width // 2 + 108  # 右移100px
        # spacing=-2 使数字重叠2px，减少总宽度；center=True 使整体居中于指定位置
        # scale=1.275 相比原来的1.5缩小了15%
        self._draw_number_images(score, score_x, score_y, center=True, spacing=-12, scale=1.5)
        
        # === 统计数字位置（5组数据）===
        # 基准位置：屏幕高度51.5%处
        # 垂直偏移：基准位置 + 90px（向下移动）
        # 水平位置：屏幕宽度63%处（右侧对齐数值区域）
        # 行间距计算：屏幕高度5.5% × 0.891（总高度系数）
        #   - 原始系数：0.055（基准行距）
        #   - 调整系数：0.891 = 0.85（减少15%）× 1.08（增加8%）× 0.97（减少3%）
        stats_start_y = int(self.height * 0.58) + 10  # 第一行Y坐标
        stats_value_x = int(self.width * 0.63)  # 数字X坐标（右侧）
        stats_spacing = int(self.height * 0.0491)  # 行间距（总高度减少3%）
        
        # 定义统计数字（按顺序：良、可、不可、连打数、最大连段数）
        stats_values = [
            perfect_count,  # 良（完美击打）
            good_count,     # 可（良好击打）
            miss_count,     # 不可（失误）
            drumroll_count, # 连打数（drumroll计数）
            max_combo       # 最大连段数（最大combo）
        ]
        
        # 绘制统计数字
        # - 使用图片渲染数字（n 2 00.png ~ n 2 09.png）
        # - scale=0.7：缩小到70%
        # - spacing=2：数字间距2px
        # - center=False：左对齐
        for i, value in enumerate(stats_values):
            y = stats_start_y + i * stats_spacing  # 计算每行Y坐标
            self._draw_number_images(value, stats_value_x, y, center=False, spacing=2, scale=0.7)
        
        pygame.display.flip()
    
    def wait_for_input(self, clock):
        """
        等待用户输入以关闭结算画面
        
        Args:
            clock: pygame时钟对象
        
        Returns:
            bool: 是否正常退出（True=按键退出, False=点击关闭按钮）
        """
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                # 只有回车键或鼠标点击才返回
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    return True
                if event.type == pygame.MOUSEBUTTONDOWN:
                    return True
            clock.tick(30)
        return True

