"""
歌曲选择界面模块
Song Selection Screen Module

这个模块负责处理歌曲选择界面的所有功能，包括：
- 歌曲分类管理（按文件夹自动分类）
- 倾斜圆角矩形UI设计
- 平滑滚动和循环显示
- 难度选择（Easy, Normal, Hard, Oni, Edit/Ura）
- 练习模式支持
- 收藏功能
- 鼠标和键盘交互

主要类：
- SongSelectScreen: 歌曲选择界面的主控制器

设计特点：
- 使用倾斜的圆角矩形按钮设计
- 支持无限循环滚动
- 选中歌曲会有发光呼吸效果
- 支持长按鬼难度切换到里模式
- 自动保存用户选择状态
"""

import pygame
import math
from pathlib import Path
from typing import List, Tuple, Dict
from lib.song_button import SongButton  # 导入歌曲按钮类
from lib.resource_loader import ResourceLoader  # 导入资源加载器
from lib.data_organizer import DataOrganizer  # 导入数据组织器
from lib.event_handler import EventHandler  # 导入事件处理器
from lib.ui_renderer import UIRenderer  # 导入UI渲染器
from lib.scroll_manager import ScrollManager  # 导入滚动管理器
from lib.selection_manager import SelectionManager  # 导入选择管理器
from lib.sound_manager import SoundManager  # 导入音效管理器
# from lib.memory_monitor import get_monitor  # 已禁用 - 影响性能

# ==================== 颜色常量 ====================
# Color constants for UI elements
BLACK = (0, 0, 0)           # 黑色 - 文字描边、背景
WHITE = (255, 255, 255)     # 白色 - 文字、边框
ORANGE = (247, 152, 36)     # 橙色 - 背景色
RED = (230, 74, 25)         # 红色 - 警告、错误
GREEN = (0, 200, 100)       # 绿色 - 成功、激活状态
BLUE = (0, 162, 232)        # 蓝色 - 普通按钮
YELLOW = (255, 242, 0)      # 黄色 - 选中、高亮
GRAY = (100, 100, 100)      # 灰色 - 禁用状态

# ==================== 难度映射 ====================
# Difficulty mapping to image level (1-5)
# 难度等级到图片编号的映射关系
DIFF_MAPPING = {
    'Easy': 1,      # 简单难度 - 对应 lv_1.png
    'Normal': 2,    # 普通难度 - 对应 lv_2.png
    'Hard': 3,      # 困难难度 - 对应 lv_3.png
    'Oni': 4,       # 鬼难度 - 对应 lv_4.png
    'Edit': 5       # 里/编辑难度 - 对应 lv_5.png
}

# ==================== 说明 ====================
# SongButton 类已移至 lib/song_button.py（见上方 import）
# 该类负责单个歌曲按钮的显示和状态管理

class SongSelectScreen:
    """
    歌曲选择界面主控制器
    Song Selection Screen Controller
    
    负责管理整个歌曲选择界面的状态和交互逻辑
    """
    
    def __init__(self, screen, songs: List[Tuple[str, Path]]):
        """
        初始化歌曲选择界面
        
        Args:
            screen: pygame显示表面
            songs: 歌曲列表，格式为[(标题, 路径), ...]
        """
        # ==================== 基础属性 ====================
        self.screen = screen                    # pygame显示表面
        self.width = screen.get_width()         # 屏幕宽度
        self.height = screen.get_height()       # 屏幕高度
        
        # ==================== 歌曲数据管理 ====================
        self.data_organizer = DataOrganizer()   # 数据组织器
        self.categories, self.folder_songs = self.data_organizer.organize_songs(songs)  # 组织歌曲数据
        
        # ==================== 分类选择状态 ====================
        self.selected_category_index = 0        # 当前选中的分类索引
        self.current_category = self.categories[0] if self.categories else "All"  # 当前分类名称
        
        # ==================== 按钮管理 ====================
        self._update_buttons()                  # 创建当前分类的歌曲按钮
        
        
        # ==================== UI视觉设置 ====================
        self.button_height = 140                # 按钮高度（像素）
        self.button_spacing = 2                 # 按钮间距（像素）
        self.slant_angle = 5                    # 按钮倾斜角度（度）
        
        # ==================== 资源加载 ====================
        self.resource_loader = ResourceLoader()        # 资源加载器
        self.diff_images = self.resource_loader.load_difficulty_images()    # 难度图标图片
        self.bg_images = self.resource_loader.load_background_images()      # 按钮背景图片
        
        # ==================== 结算画面 ====================
        from lib.result_screen import ResultScreen
        from lib.score_manager import ScoreManager
        self.result_screen = ResultScreen(screen, self.resource_loader)  # 结算画面渲染器
        self.score_manager = ScoreManager()  # 成绩管理器
        
        # ==================== 动画状态 ====================
        self.blink_time = 0                     # 闪烁动画时间计数器
        
        # ==================== 练习模式设置 ====================
        self.practice_mode = False               # 练习模式开关
        self.practice_audio_paths = {}          # 练习音频文件路径字典
        self.practice_generating = False        # 是否正在生成练习音频
        self.practice_speeds = [0.5, 0.8, 1.0, 1.3]  # 练习速度选项
        
        # ==================== 配置管理 ====================
        # 加载配置管理器
        from lib.config_manager import ConfigManager
        self.config = ConfigManager()
        
        # ==================== UI渲染 ====================
        self.ui_renderer = UIRenderer(screen, self.resource_loader)  # UI渲染器
        
        # ==================== 滚动管理 ====================
        self.scroll_manager = ScrollManager(screen.get_height(), self.button_height, self.button_spacing, self.ui_renderer)  # 滚动管理器
        
        # ==================== 选择管理 ====================
        self.selection_manager = SelectionManager(self.config, self.scroll_manager)  # 选择管理器
        
        # ==================== 音效管理 ====================
        self.sound_manager = SoundManager()     # 音效管理器
        
        # ==================== 事件处理 ====================
        self.event_handler = EventHandler()     # 事件处理器
        self._setup_event_callbacks()           # 设置事件回调
        
        # ==================== 字体加载 ====================
        # 使用资源加载器加载所有字体
        ui_fonts = self.resource_loader.load_ui_fonts()
        self.font_title = ui_fonts['title']          # 主标题字体
        self.font_title_cn = ui_fonts['title_cn']    # 中文标题字体
        self.font_subtitle = ui_fonts['subtitle']    # 副标题字体
        self.font_small = ui_fonts['small']          # 小字体
        self.font_category = ui_fonts['category']    # 分类字体
        self.font_star = ui_fonts['star']            # 星级显示字体
        self.font_header = ui_fonts['header']        # 页面标题字体
        
        # ==================== 时钟 ====================
        self.clock = pygame.time.Clock()                                # 游戏时钟
        
        # ==================== 音乐预览 ====================
        self.preview_delay = 250  # 预览延迟时间（毫秒），选中歌曲后0.25秒开始播放
        self.last_selected_song = None  # 上次选中的歌曲
        self.selection_time = 0  # 选中歌曲的时间
        self.is_previewing = False  # 是否正在预览
        
        # ==================== 状态恢复 ====================
        # 设置按钮列表到选择管理器
        self.selection_manager.set_buttons(self.buttons)
        # 恢复上次选择的歌曲
        self.selection_manager.set_selected_index(self.selection_manager.restore_last_selection())
    
    def _setup_event_callbacks(self):
        """
        设置事件回调函数
        Setup event callback functions
        """
        # 设置移动选择回调（带音效）
        self.event_handler.set_callback('move_selection', self._move_selection_with_sound)
        
        # 设置分类切换回调（带音效）
        self.event_handler.set_callback('change_category', self._change_category_with_sound)
        
        # 设置返回回调（带音效）
        self.event_handler.set_callback('cancel', self._cancel_with_sound)
        
        # 设置选中索引回调
        self.event_handler.set_callback('set_selected_index', self.selection_manager.set_selected_index)
        
        # 设置收藏切换回调
        self.event_handler.set_callback('toggle_favorite', self._toggle_favorite_callback)
        
        # 设置练习模式切换回调
        self.event_handler.set_callback('toggle_practice', self._toggle_practice_callback)
        
        # 设置退出回调
        self.event_handler.set_callback('quit', self._quit_callback)
        
        # 设置确认回调（带音效）
        self.event_handler.set_callback('confirm', self._confirm_with_sound)
        
        # 设置滚动更新回调（展开/收起时重新计算位置）
        self.event_handler.set_callback('update_scroll', self._update_scroll_position)
        
        # 设置显示结算画面回调
        self.event_handler.set_callback('show_result_screen', self._show_result_screen_callback)
    
    def _update_scroll_position(self):
        """
        更新滚动位置（展开/收起时调用）
        Update scroll position (called when expanding/collapsing)
        """
        # 使用 self.buttons 获取当前分类的按钮列表
        selected_index = self.selection_manager.selected_index
        self.scroll_manager.scroll_to_selection(self.buttons, selected_index)
    
    def _move_selection_with_sound(self, delta: int):
        """
        移动选择（带音效）
        Move selection with sound
        
        Args:
            delta: 移动步数
        """
        # 播放选择音效
        self.sound_manager.play_select_sound()
        # 执行选择移动
        self.selection_manager.move_selection(delta)
        # 重置预览计时
        self._reset_preview_timer()
        # 重置发光动画（从第一帧开始）
        self.blink_time = 0
    
    def _reset_preview_timer(self):
        """
        重置预览计时器
        Reset preview timer
        """
        self.selection_time = pygame.time.get_ticks()
        self.is_previewing = False
        # 停止当前音乐
        pygame.mixer.music.stop()
    
    def _update_preview(self):
        """
        更新音乐预览
        Update music preview
        """
        # 获取当前选中的歌曲
        selected_index = self.selection_manager.get_selected_index()
        if selected_index < 0 or selected_index >= len(self.buttons):
            return
        
        current_song = self.buttons[selected_index]
        
        # 检查是否切换了歌曲
        if current_song != self.last_selected_song:
            self.last_selected_song = current_song
            self._reset_preview_timer()
        
        # 检查是否需要开始预览
        if not self.is_previewing:
            current_time = pygame.time.get_ticks()
            if current_time - self.selection_time >= self.preview_delay:
                self._start_preview(current_song)
    
    def _start_preview(self, song_button: SongButton):
        """
        开始播放歌曲预览
        Start playing song preview
        
        Args:
            song_button: 歌曲按钮对象
        """
        # 检查音频文件是否存在
        if not song_button.audio_path or not song_button.audio_path.exists():
            try:
                print(f"Audio file not found: {song_button.audio_path}")
            except UnicodeEncodeError:
                print(f"Audio file not found: [path encoding error]")
            return
        
        try:
            # 停止当前播放
            pygame.mixer.music.stop()
            
            # 加载音乐文件
            pygame.mixer.music.load(str(song_button.audio_path))
            
            # 设置音量（可以根据需要调整）
            pygame.mixer.music.set_volume(0.6)
            
            # 开始播放
            pygame.mixer.music.play()
            
            # 设置播放位置到DEMOSTART（使用set_pos，单位是秒）
            # 注意：set_pos对于某些格式（如MP3）可能不精确，OGG格式支持较好
            if song_button.demo_start > 0:
                pygame.mixer.music.set_pos(song_button.demo_start)
            
            self.is_previewing = True
            try:
                print(f"Started preview: {song_button.title} at {song_button.demo_start}s")
            except UnicodeEncodeError:
                print(f"Started preview: [title encoding error] at {song_button.demo_start}s")
        except Exception as e:
            try:
                print(f"Error playing preview: {e}")
            except UnicodeEncodeError:
                print(f"Error playing preview: [encoding error]")
    
    def _stop_preview(self):
        """
        停止音乐预览
        Stop music preview
        """
        pygame.mixer.music.stop()
        self.is_previewing = False
    
    def _change_category_with_sound(self, delta: int):
        """
        切换分类（带音效）
        Change category with sound
        
        Args:
            delta: 切换步数
        """
        # 播放切换分类音效
        self.sound_manager.play_fast_sound()
        # 执行分类切换
        self.change_category(delta)
        # 重置预览计时
        self._reset_preview_timer()
        # 重置发光动画（从第一帧开始）
        self.blink_time = 0
    
    def _cancel_with_sound(self):
        """
        返回操作（带音效）
        Cancel operation with sound
        """
        # 播放返回音效
        self.sound_manager.play_cancel_sound()
    
    def _confirm_with_sound(self):
        """
        确认选择（带音效）
        Confirm selection with sound
        """
        # 播放确认音效
        self.sound_manager.play_confirm_sound()
        # 停止预览
        self._stop_preview()
    
    def _toggle_favorite_callback(self):
        """
        收藏切换回调
        Toggle favorite callback
        """
        if self.buttons and self.selected_index < len(self.buttons):
            self._toggle_favorite(self.buttons[self.selected_index])
    
    def _toggle_practice_callback(self):
        """
        练习模式切换回调
        Toggle practice mode callback
        """
        if self.buttons and self.selected_index < len(self.buttons):
            self._toggle_practice_mode(self.buttons[self.selected_index])
    
    def _quit_callback(self):
        """
        退出回调
        Quit callback
        """
        # 停止预览
        self._stop_preview()
        pygame.quit()
        exit()
    
    def _show_result_screen_callback(self, button: SongButton):
        """
        显示结算画面回调
        Show result screen callback
        
        Args:
            button: 选中的歌曲按钮
        """
        print(f"[DEBUG] Tab pressed - showing result screen for: {button.title}")
        
        # 获取歌曲ID（TJA文件名，不含扩展名）
        song_id = button.tja_path.stem
        print(f"[DEBUG] Song ID: {song_id}")
        
        # 尝试获取所有难度的成绩，优先显示有成绩的难度
        score_data = None
        selected_difficulty = None
        
        # 难度优先级：Oni > Hard > Normal > Easy > Edit
        difficulty_priority = ['Oni', 'Hard', 'Normal', 'Easy', 'Edit']
        
        # 首先检查当前选中的难度是否有成绩
        if button.difficulties:
            current_diff = button.difficulties[button.selected_diff_index]
            print(f"[DEBUG] Checking current difficulty: {current_diff}")
            score_data = self.score_manager.get_score(song_id, current_diff)
            if score_data:
                selected_difficulty = current_diff
                print(f"[DEBUG] Found score for {current_diff}: {score_data.get('score')}")
        
        # 如果当前难度没有成绩，按优先级查找其他难度
        if not score_data:
            print(f"[DEBUG] Searching other difficulties...")
            for diff in difficulty_priority:
                if diff in button.difficulties:
                    score_data = self.score_manager.get_score(song_id, diff)
                    if score_data:
                        selected_difficulty = diff
                        print(f"[DEBUG] Found score for {diff}: {score_data.get('score')}")
                        break
        
        # 如果没有任何成绩记录，显示提示
        if not score_data:
            print(f"[DEBUG] No score record found for: {button.title} (song_id: {song_id})")
            print(f"[DEBUG] Available sections in scores.ini: {list(self.score_manager.config.sections())}")
            # 播放取消音效
            self.sound_manager.play_cancel_sound()
            return
        
        print(f"[DEBUG] Displaying result screen...")
        
        # 播放确认音效
        self.sound_manager.play_confirm_sound()
        
        # 计算总音符数（从成绩数据中获取，如果没有则计算）
        total_notes = score_data.get('total_notes', 0)
        if total_notes == 0:
            # 如果没有保存total_notes，尝试从判定数计算
            total_notes = score_data.get('perfect_count', 0) + score_data.get('good_count', 0) + score_data.get('ok_count', 0) + score_data.get('miss_count', 0)
        
        # 获取歌曲标题和副标题（优先使用中文版本）
        subtitle = getattr(button, 'subtitle', '')
        titlecn = getattr(button, 'title_cn', '')  # 注意是title_cn不是titlecn
        subtitlecn = getattr(button, 'subtitle_cn', '')  # 注意是subtitle_cn不是subtitlecn
        
        # 获取歌曲分类颜色作为背景色
        category_color = None
        try:
            category_color = self.config.get_category_color(button.category)
        except Exception as e:
            print(f"[DEBUG] Error getting category color: {e}")
        
        # 显示结算画面
        self.result_screen.draw(
            song_title=button.title,
            difficulty=selected_difficulty,
            score=score_data.get('score', 0),
            perfect_count=score_data.get('perfect_count', 0),
            good_count=score_data.get('good_count', 0),
            ok_count=score_data.get('ok_count', 0),
            miss_count=score_data.get('miss_count', 0),
            drumroll_count=score_data.get('drumroll_hits', 0),
            max_combo=score_data.get('max_combo', 0),
            total_notes=total_notes,
            subtitle=subtitle,
            titlecn=titlecn,
            subtitlecn=subtitlecn,
            bg_color=category_color  # 使用歌曲分类颜色作为背景
        )
        
        # 等待用户输入
        self.result_screen.wait_for_input(self.clock)
    
    
    def _update_buttons(self):
        """
        根据选中的分类更新按钮列表
        Update buttons based on selected category
        
        处理逻辑：
        1. 根据当前分类获取歌曲列表
        2. 对歌曲进行排序（支持数字前缀）
        3. 为每首歌曲创建SongButton对象
        4. 传递分类信息给按钮
        """
        # ==================== 获取歌曲列表 ====================
        songs = self.data_organizer.get_songs_for_category(self.current_category)
        
        # ==================== 排序歌曲 ====================
        # 使用数据组织器的排序功能
        sorted_songs = self.data_organizer.sort_songs(songs)
        
        # ==================== 创建按钮 ====================
        self.buttons = []
        for i, (title, path) in enumerate(sorted_songs):
            # 确定分类：如果是All分类，则从路径中提取实际分类
            if self.current_category == "All":
                category = self.data_organizer.get_category_for_song(path)
            else:
                category = self.current_category
            
            # 创建歌曲按钮对象
            self.buttons.append(SongButton(title, path, i, category))
    
    
    
        
    def run(self) -> Tuple[Path, str]:
        """
        运行歌曲选择界面
        Run song selection interface
        
        主循环处理：
        1. 事件处理（键盘、鼠标）
        2. 平滑滚动更新
        3. 动画状态更新
        4. 界面绘制
        
        返回:
            Tuple[Path, str]: (歌曲路径, 难度, 分类) 或 None（退出）
        """
        # 内存监控已禁用
        # memory_monitor = get_monitor()
        # memory_monitor.full_report("Song Select Start")
        
        running = True
        
        # 重置发光动画（从第一帧开始）
        self.blink_time = 0
        
        # ==================== 主循环 ====================
        while running:
            # 获取所有事件
            events = pygame.event.get()
            
            # 使用事件处理器处理事件
            result = self.event_handler.process_events(
                events, self.buttons, self.selection_manager.get_selected_index(),
                self.current_category, self.categories, self.selected_category_index,
                self.scroll_manager.get_scroll_offset(), self.width, self.height
            )
            
            # 如果事件处理器返回了结果，处理它
            if result is not None:
                if result == "quit":
                    # 内存监控已禁用
                    # memory_monitor.full_report("Song Select - Quit")
                    return None
                elif isinstance(result, tuple) and len(result) == 3:
                    # 保存上次选择
                    song_path, difficulty, category = result
                    self.config.set_last_selected(str(song_path), difficulty, category)
                    # 内存监控已禁用
                    # memory_monitor.full_report("Song Select - Song Selected")
                    return result
            
            # ==================== 更新滚动 ====================
            self.scroll_manager.update_scroll(self.buttons, self.selection_manager.get_selected_index())
            
            # ==================== 更新音乐预览 ====================
            self._update_preview()
            
            # 更新闪烁动画
            self.blink_time += self.clock.get_time()
            
            self._draw()
            self.clock.tick(60)
    
    
    
    
    def change_category(self, delta: int):
        """Change category left/right"""
        self.selected_category_index = (self.selected_category_index + delta) % len(self.categories)
        self.current_category = self.categories[self.selected_category_index]
        self._update_buttons()
        self.selection_manager.set_buttons(self.buttons)  # 更新按钮列表
        self.selection_manager.reset_selection()  # 重置选择到第一个
    
    
    def _toggle_favorite(self, button: SongButton):
        """Toggle favorite status for a song"""
        # TODO: Implement favorite functionality
        print(f"Toggled favorite for: {button.title}")
    
    def _toggle_practice_mode(self, button: SongButton):
        """Toggle practice mode for a song"""
        if self.practice_generating:
            return  # Don't allow multiple generations
            
        self.practice_mode = not self.practice_mode
        if self.practice_mode:
            print(f"Starting practice mode for: {button.title}")
            self._generate_practice_audio(button)
        else:
            print(f"Stopped practice mode for: {button.title}")
            self.practice_audio_paths = {}
    
    def _generate_practice_audio(self, button: SongButton):
        """Generate practice audio files for different speeds"""
        import threading
        import subprocess
        import tempfile
        
        self.practice_generating = True
        
        def generate_audio():
            # Find audio file
            audio_file = None
            for ext in ['.ogg', '.wav', '.mp3']:
                test_path = button.tja_path.with_suffix(ext)
                if test_path.exists():
                    audio_file = test_path
                    break
            
            if not audio_file:
                print(f"No audio file found for {button.title}")
                self.practice_generating = False
                return
            
            # Create cache directory
            cache_dir = Path("cache") / "practice_audio"
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            for speed in self.practice_speeds:
                if speed == 1.0:
                    self.practice_audio_paths[speed] = audio_file
                    continue
                
                output_path = cache_dir / f"{audio_file.stem}_{speed}x.ogg"
                self.practice_audio_paths[speed] = output_path
                
                if output_path.exists():
                    print(f"Using cached practice audio for {speed}x: {output_path}")
                    continue
                
                print(f"Generating practice audio for {speed}x...")
                try:
                    result = subprocess.run([
                        "ffmpeg",
                        "-i", str(audio_file),
                        "-filter:a", f"atempo={speed}",
                        "-vn",
                        "-acodec", "libvorbis",
                        "-q:a", "5",
                        str(output_path),
                        "-y"
                    ], check=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                    print(f"Finished generating {speed}x audio.")
                except (subprocess.CalledProcessError, FileNotFoundError) as e:
                    print(f"Error generating practice audio for {speed}x: {e}")
                    if isinstance(e, subprocess.CalledProcessError):
                        print("FFmpeg stderr:", e.stderr)
                    self.practice_audio_paths[speed] = None
            
            self.practice_generating = False
            print("All practice audio generated.")
        
        threading.Thread(target=generate_audio).start()
    
    def _draw(self):
        """
        绘制选择界面
        Draw selection screen
        """
        # ==================== 确定显示的分类（用于背景色和顶部遮挡层） ====================
        # 如果是All分类，使用当前选中歌曲的实际分类颜色
        display_category = self.current_category
        if self.current_category == "All" and self.buttons:
            selected_index = self.selection_manager.get_selected_index()
            if 0 <= selected_index < len(self.buttons):
                selected_button = self.buttons[selected_index]
                display_category = selected_button.category  # 使用歌曲的实际分类
        
        # ==================== 绘制主界面 ====================
        # 去掉下面的文字提示，传递分类用于背景色
        self.ui_renderer.draw_main_screen("SELECT SONG", None, display_category)
        
        # ==================== 绘制歌曲按钮 ====================
        if self.buttons:
            self.ui_renderer.draw_song_buttons(
                self.buttons, self.selection_manager.get_selected_index(), 
                self.scroll_manager.get_scroll_offset(), self.blink_time
            )
        
        # ==================== 绘制顶部遮挡层（在歌曲按钮之上） ====================
        self.ui_renderer.draw_top_mask(display_category)
        
        # ==================== 绘制分类选择器（最上层） ====================
        self.ui_renderer.draw_categories(self.categories, self.selected_category_index)
        
        # ==================== 绘制成绩面板（真正的最上层，在所有UI元素之上） ====================
        self.ui_renderer.draw_score_panel_if_needed()
        
        # ==================== 刷新显示 ====================
        self.ui_renderer.flip_display()
    
    
    

