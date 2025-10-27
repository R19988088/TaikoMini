"""
TaikoMini Game Logic
Simplified Taiko game with basic gameplay

重构版本 - 使用模块化架构
"""

import pygame
import gc
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass

# Import from original tja.py
from lib.tja import Note, Drumroll, Balloon
from lib.audio import AudioEngine

# Import new modular components
from lib.combo_display import ComboDisplay
from lib.game_input import InputHandler
from lib.note_judgment import NoteJudgment
from lib.sound_manager import SoundManager
from lib.game_renderer import GameRenderer
from lib.game_controls import GameControls
from lib.practice_controls import PracticeControls
from lib.timing_manager import TimingManager
from lib.song_info_display import SongInfoDisplay

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (230, 74, 25)
BLUE = (0, 162, 232)
ORANGE = (247, 152, 36)
YELLOW = (255, 242, 0)
GREEN = (0, 200, 100)
GRAY = (127, 127, 127)
DARK_GRAY = (50, 50, 50)
LIGHT_BLUE = (100, 150, 255)

# Judgment windows (milliseconds)
PERFECT_WINDOW = 25   # ±25ms = Perfect
GOOD_WINDOW = 75      # ±75ms = Good
OK_WINDOW = 108       # ±108ms = OK

# Layout ratios (based on window size percentage)
GAME_AREA_RATIO = 0.20   # Game area occupies 20% of screen height (orange strip)
JUDGE_X_RATIO = 0.15     # Judge line position (15% from left)

# === 可调整的大鼓布局 ===
# 鼓的大小 (相对于窗口宽度). 默认: 0.40, 增加了20% -> 0.48
DRUM_RATIO = 0.48
# 鼓的垂直偏移量 (相对于鼓自身的高度). 0.0 为贴紧底部, 0.2 为向下移动20%, 使其部分在屏幕外.
DRUM_Y_OFFSET_RATIO = 0.20
# =======================

# Game timing constants
NOTE_LEAD_TIME = 1500    # Note lead time (milliseconds) - time from screen right to judge line

class TaikoGame:
    def __init__(self, screen, chart_data: Dict, audio_path: Path, song_category: str = ""):
        self.screen = screen
        self.chart_data = chart_data
        self.audio_path = audio_path
        self.song_category = song_category  # 歌曲分类

        # === 音频引擎 ===
        self.audio_engine = AudioEngine()
        
        # === 时间管理器 ===
        offset_seconds = chart_data.get('offset', 0)
        self.timing_manager = TimingManager(self.audio_engine, offset_seconds * 1000)
        
        # 配置管理器（用于读取配置）
        from lib.config_manager import ConfigManager
        from lib.game_settings import GameSettings
        self.config = ConfigManager()
        self.game_settings = GameSettings()
        
        # 设置目标帧率
        self.target_fps = self.game_settings.get_target_fps()
        
        # 初始化歌曲信息显示（传递配置管理器）
        self.song_info_display = SongInfoDisplay(screen, self.config)
        
        # 设置歌曲信息显示位置（直接控制整个区域的位置）
        self.song_info_display.set_position(
            right_margin=30,
            top_margin=100,  # 直接设置Y位置（如需调整，直接修改此值）
            vertical_spacing=15
        )
        
        # 从配置文件读取字体大小和描边设置
        try:
            # 读取配置值并去除行内注释（支持 # 注释）
            title_size_str = self.config.get_display_setting('title_font_size', '84').split('#')[0].strip()
            category_size_str = self.config.get_display_setting('category_font_size', '26').split('#')[0].strip()
            title_outline_str = self.config.get_display_setting('title_outline', '3').split('#')[0].strip()
            category_outline_str = self.config.get_display_setting('category_outline', '2').split('#')[0].strip()
            
            title_size = int(title_size_str)
            category_size = int(category_size_str)
            title_outline = int(title_outline_str)
            category_outline = int(category_outline_str)
        except Exception as e:
            # 如果配置读取失败，使用默认值
            print(f"Warning: Failed to read display settings ({e}), using defaults")
            title_size = 84
            category_size = 26
            title_outline = 3
            category_outline = 2
        
        self.song_info_display.set_font_sizes(
            title_size=title_size,
            category_size=category_size
        )
        self.song_info_display.set_outline(
            title_outline=title_outline,
            category_outline=category_outline
        )
        
        # 歌名和分类
        self.song_title = chart_data.get('title', '')
        self.category_color = self._load_category_color()
        # ====================
        
        # 鼓动画时间变量
        self.drum_don_left_time = -10000
        self.drum_don_right_time = -10000
        self.drum_kat_left_time = -10000
        self.drum_kat_right_time = -10000
        self.drum_press_time = -10000
        
        # Note list (with branching support)
        master_notes = chart_data['notes']
        self.notes: List[Note] = master_notes.play_notes
        self.bars: List[Note] = master_notes.bars
        self.branch_m = chart_data.get('branch_m', [])
        self.branch_n = chart_data.get('branch_n', [])
        self.branch_e = chart_data.get('branch_e', [])
        
        # 应用谱面偏移（正数提前 负数延后）
        chart_offset = self.game_settings.get_chart_offset()
        if chart_offset != 0:
            for note in self.notes:
                note.hit_ms -= chart_offset  # 正数减 = 提前
                note.load_ms -= chart_offset
            for bar in self.bars:
                bar.hit_ms -= chart_offset
                bar.load_ms -= chart_offset
            # 同样应用到分支谱面
            for branch_notes in [self.branch_m, self.branch_n, self.branch_e]:
                if branch_notes and hasattr(branch_notes, 'play_notes'):
                    for note in branch_notes.play_notes:
                        note.hit_ms -= chart_offset
                        note.load_ms -= chart_offset
                if branch_notes and hasattr(branch_notes, 'bars'):
                    for bar in branch_notes.bars:
                        bar.hit_ms -= chart_offset
                        bar.load_ms -= chart_offset
            print(f"Applied chart offset: {chart_offset:+.0f}ms")
        
        # === 计算真打分数系统（需要在notes被赋值后） ===
        self.base_note_score = self._calculate_shinuchi_score()
        
        # === 模块初始化（需要在真打分数计算后） ===
        self.renderer = GameRenderer(screen)
        self.input_handler = InputHandler()
        self.note_judgment = NoteJudgment(base_note_score=self.base_note_score)
        self.combo_display = ComboDisplay()
        self.game_controls = GameControls(screen)
        self.practice_controls = PracticeControls(screen)
        self.sound_manager = SoundManager()
        
        # Save original note types and lists for restart
        self.original_note_types = {id(note): note.type for note in self.notes}
        self.original_notes = list(self.notes)  # 保存初始音符列表（分支前）
        self.original_bars = list(self.bars)    # 保存初始小节线列表（分支前）
        self.branch_index = 0
        
        # Find all bars that trigger a branch choice
        self.branch_bars = sorted(
            [b for b in self.bars if hasattr(b, 'branch_params') and b.branch_params],
            key=lambda b: b.hit_ms
        )
        self.next_branch_idx = 0
        self.current_note_index = 0
        
        # Timing
        self.clock = pygame.time.Clock()
        
        # Performance monitoring
        # 移除性能监控以提升性能
        self.frames_elapsed = -1
        
        # Statistics
        self.score = 0
        self.combo = 0
        self.perfect_count = 0
        self.good_count = 0
        self.ok_count = 0
        self.miss_count = 0
        
        # Control state
        self.is_paused = False
        self.playback_speed = 1.0
        self.is_dragging_slider = False
        self._speed_changed = False
        
        # 从配置文件读取自动演奏设置
        try:
            auto_play_config = self.config.get_game_setting('auto_play', 'false').lower()
            self.auto_play = auto_play_config == 'true'
            self.practice_controls.set_auto_play_state(self.auto_play)
            if self.auto_play:
                print("Auto Play: ON (from config)")
        except:
            self.auto_play = False
        
        # Practice mode
        self.is_practice_mode = False
        self.practice_audio_paths = {}
        self.current_practice_speed = 1.0
        self.practice_music_streams = {}
        
        # Drumroll/Balloon state
        self.active_drumroll = None
        self.last_drumroll_hit_time = 0
        
        # Metronome (节拍器) state
        self.metronome_events = []  # 节拍器事件列表 [(time_ms, sound_type), ...]
        self.metronome_event_index = 0  # 当前待播放的节拍器事件索引

        # Load sound effects
        self._load_sounds()
        
        # Generate metronome events for slow speed mode
        self._generate_metronome_events()
        
        # Update layout and UI elements
        self._update_ui_layout()
    
    def _load_category_color(self):
        """从配置文件加载分类颜色"""
        try:
            return self.config.get_category_color(self.song_category)
        except Exception as e:
            print(f"Error loading category color: {e}")
            return None
    
    def _calculate_shinuchi_score(self):
        """
        计算真打分数系统的每音符基础分数
        完全按照parse_tja.py中的规则计算
        目标总分: 1,000,000分
        """
        import math
        
        # 统计音符数量（只计算1,2,3,4类型的音符）
        note_count = 0
        balloon_count = 0  # 气球数量
        
        for note in self.notes:
            if note.type in [1, 2, 3, 4]:  # don, ka, big don, big ka
                note_count += 1
            elif note.type in [7, 9]:  # balloon, 草
                balloon_count += 1
        
        # 固定的连打速度（每秒次数）假设为5次/秒
        # 这里暂时假设没有连打，或者连打分数很少
        # 如果需要精确计算，需要遍历所有连打音符并计算总时长
        drumroll_score = 0
        
        # 气球分数：每个气球100分
        balloon_score = balloon_count * 100
        
        # 音符分数计算
        remaining_score = 1000000 - balloon_score - drumroll_score
        
        if note_count > 0:
            # 计算每个音符的基础分数
            per_note_score = remaining_score / note_count
            # 除以10后向上取整，再乘以10
            per_note_score = math.ceil(per_note_score / 10) * 10
        else:
            per_note_score = 100  # 默认值
        
        print(f"[Shinuchi Score] Notes: {note_count}, Balloons: {balloon_count}")
        print(f"[Shinuchi Score] Per Note: {per_note_score}, Total Target: ~1,000,000")
        
        return per_note_score
    
    def restart(self):
        """Resets the game to its initial state for a restart."""
        # 保存自动演奏状态（重启时保持）
        current_auto_play = self.auto_play
        
        # Reset timing
        self.timing_manager.reset()
        
        # Reset statistics
        self.score = 0
        self.combo = 0
        self.perfect_count = 0
        self.good_count = 0
        self.ok_count = 0
        self.miss_count = 0
        
        # Reset note state
        self.current_note_index = 0
        
        # 恢复初始的音符和小节线列表（分歧谱面会动态添加音符）
        self.notes = list(self.original_notes)
        self.bars = list(self.original_bars)
        
        # 恢复音符类型
        for note in self.notes:
            if id(note) in self.original_note_types:
                note.type = self.original_note_types[id(note)]
        
        # 重新计算分支小节线列表
        self.branch_bars = sorted(
            [b for b in self.bars if hasattr(b, 'branch_params') and b.branch_params],
            key=lambda b: b.hit_ms
        )
        
        # Reset branch logic
        self.branch_index = 0
        self.next_branch_idx = 0
        
        # Reset drumroll state
        self.active_drumroll = None
        self.note_judgment.active_drumroll = None
        self.note_judgment.last_drumroll_hit_time = 0  # 重置连打时间
        
        # Reset judgment display state
        self.note_judgment.current_judgment = ""
        self.note_judgment.judgment_time = 0
        self.note_judgment.is_super_large_note = False
        
        # 清除输入处理器状态，避免积累音符
        self.input_handler.last_auto_hit_index = -1
        self.input_handler.last_drumroll_hit_time = 0
        self.input_handler._last_auto_drumroll_time = 0
        
        # 重置鼓动画时间
        self.drum_don_left_time = -10000
        self.drum_don_right_time = -10000
        self.drum_kat_left_time = -10000
        self.drum_kat_right_time = -10000
        self.drum_press_time = -10000

        # Stop current audio and reload it with the new speed
        self.audio_engine.stop()
        if not self.audio_engine.load_sound(str(self.audio_path)):
             print("Failed to reload audio on restart.")
             return # Or handle error appropriately
        
        self.timing_manager.playback_speed = self.playback_speed
        
        # 变速模式下静音播放音乐，使用节拍器
        self.audio_engine.play()
        
        if self.playback_speed != 1.0:
            # 变速模式（慢速/快速）：静音背景音乐，使用节拍器
            pygame.mixer.music.set_volume(0.0)
            self.metronome_event_index = 0
            print(f"[Metronome] Variable speed mode ({self.playback_speed}x): Music muted, metronome ready with {len(self.metronome_events)} events")
        else:
            # 正常速度：恢复音乐音量
            pygame.mixer.music.set_volume(1.0)
        
        self.timing_manager.start()

        # Reset controls state if needed
        self.is_paused = False

        # Reset renderer state
        self.renderer.reset()
        self.frames_elapsed = -1
        
        # 恢复自动演奏状态（确保 practice_controls 与 self.auto_play 同步）
        self.auto_play = current_auto_play
        self.practice_controls.set_auto_play_state(self.auto_play)

    def _load_sounds(self):
        """Load sound effects from the 'wav' resource folder."""
        try:
            sound_dir = Path("lib/res/wav")
            if not sound_dir.exists():
                print("Warning: Sound directory not found")
                self.sound_don = None
                self.sound_kat = None
                self.metronome_se01 = None
                self.metronome_se02 = None
                return
                
            don_file = sound_dir / "taiko_don.wav"
            kat_file = sound_dir / "taiko_ka.wav"
            se01_file = sound_dir / "se_01.wav"
            se02_file = sound_dir / "se_02.wav"
            
            if don_file.exists():
                self.sound_don = pygame.mixer.Sound(str(don_file))
                print(f"Loaded: {don_file.name}")
            else:
                self.sound_don = None
                print(f"Warning: {don_file.name} not found")
                
            if kat_file.exists():
                self.sound_kat = pygame.mixer.Sound(str(kat_file))
                print(f"Loaded: {kat_file.name}")
            else:
                self.sound_kat = None
                print(f"Warning: {kat_file.name} not found")
                
            # 加载节拍器音效
            if se01_file.exists():
                self.metronome_se01 = pygame.mixer.Sound(str(se01_file))
                print(f"Loaded metronome: {se01_file.name}")
            else:
                self.metronome_se01 = None
                print(f"Warning: {se01_file.name} not found")
                
            if se02_file.exists():
                self.metronome_se02 = pygame.mixer.Sound(str(se02_file))
                print(f"Loaded metronome: {se02_file.name}")
            else:
                self.metronome_se02 = None
                print(f"Warning: {se02_file.name} not found")
                
        except Exception as e:
            print(f"Error loading sounds: {e}")
            self.sound_don = None
            self.sound_kat = None
            self.metronome_se01 = None
            self.metronome_se02 = None

    def _generate_metronome_events(self):
        """
        生成节拍器事件列表
        根据小节线的拍号，在慢速模式下播放节拍器音效
        
        注意：如果在游戏中途调用（如分歧后），会保持当前播放位置
        """
        # 保存当前游戏时间（如果已经开始播放）
        current_time = self.timing_manager.get_game_time() if hasattr(self, 'timing_manager') else 0
        
        self.metronome_events = []
        
        try:
            for bar in self.bars:
                # 获取拍号（如4/4拍=1.0, 3/4拍=0.75, 8/4拍=2.0）
                time_sig = getattr(bar, 'time_signature', 1.0)
                
                # 计算拍数（例如：1.0 -> 4拍, 0.75 -> 3拍, 2.0 -> 8拍）
                beat_count = int(time_sig * 4)
                
                if beat_count < 1:
                    beat_count = 1
                
                # 计算这个小节的持续时间
                bpm = getattr(bar, 'bpm', 120.0)
                if bpm <= 0:
                    bpm = 120.0
                
                ms_per_measure = 60000 * (time_sig * 4) / bpm
                ms_per_beat = ms_per_measure / beat_count
                
                # 第一拍使用 se_01
                self.metronome_events.append((bar.hit_ms, 'se01'))
                
                # 剩余拍使用 se_02
                for beat_num in range(1, beat_count):
                    beat_time = bar.hit_ms + (beat_num * ms_per_beat)
                    self.metronome_events.append((beat_time, 'se02'))
            
            # 按时间排序
            self.metronome_events.sort(key=lambda x: x[0])
            
            # 如果在游戏中途重新生成（如分歧后），更新播放索引到当前时间
            self.metronome_event_index = 0
            for i, (event_time, _) in enumerate(self.metronome_events):
                if event_time > current_time:
                    self.metronome_event_index = i
                    break
            else:
                # 所有事件都已过期
                self.metronome_event_index = len(self.metronome_events)
            
            print(f"[Metronome] Generated {len(self.metronome_events)} metronome events (index: {self.metronome_event_index})")
        except Exception as e:
            print(f"[Metronome] Error generating metronome events: {e}")
            self.metronome_events = []
    
    def _play_metronome(self, game_time):
        """
        播放节拍器音效（仅在慢速模式下）
        
        Args:
            game_time: 当前游戏时间（毫秒）
        """
        # 检查是否有待播放的节拍器事件
        played_count = 0
        while (self.metronome_event_index < len(self.metronome_events) and 
               self.metronome_events[self.metronome_event_index][0] <= game_time):
            
            event_time, sound_type = self.metronome_events[self.metronome_event_index]
            
            # 播放对应的音效
            if sound_type == 'se01' and self.metronome_se01:
                self.metronome_se01.play()
                played_count += 1
            elif sound_type == 'se02' and self.metronome_se02:
                self.metronome_se02.play()
                played_count += 1
            
            self.metronome_event_index += 1
        
        # 节拍器播放完成（不打印避免影响性能）
    
    def _update_ui_layout(self):
        """
        Dynamically updates UI element positions based on the current window size.
        """
        self.screen_width = self.screen.get_width()
        self.screen_height = self.screen.get_height()
        
        # Calculate layout areas
        self.game_area_height = int(self.screen_height * GAME_AREA_RATIO)
        self.game_area_top = int((self.screen_height - self.game_area_height) * 0.35)  # Mid-upper position
        self.game_area_bottom = self.game_area_top + self.game_area_height
        
        # Judge position
        self.judge_x = int(self.screen_width * JUDGE_X_RATIO)
        self.judge_y = self.game_area_top + self.game_area_height // 2
        self.judge_radius = int(min(self.screen_width, self.screen_height) * 0.05)
        
        # Update controls layout
        self.game_controls.update_layout()
        self.practice_controls.update_layout()
        
        # Drum position (lower part)
        self.drum_center_x = self.screen_width // 2
        self.drum_radius = int(self.screen_width * DRUM_RATIO)
        
        # Scale drum image to fit screen width
        if self.renderer.drum_img:
            drum_width = self.drum_radius * 2
            drum_height = int(self.renderer.drum_img.get_height() * drum_width / self.renderer.drum_img.get_width())
            drum_size = (drum_width, drum_height) # This size is used for the entire group

            # Scale all three images to the exact same size to act as a container group
            self.renderer.scaled_drum_img = pygame.transform.smoothscale(self.renderer.drum_img, drum_size)
            if self.renderer.drum_don_hit_img:
                self.renderer.scaled_don_hit_img = pygame.transform.smoothscale(self.renderer.drum_don_hit_img, drum_size)
            if self.renderer.drum_kat_hit_img:
                self.renderer.scaled_kat_hit_img = pygame.transform.smoothscale(self.renderer.drum_kat_hit_img, drum_size)
            
            # Align drum to the bottom of the screen, with a vertical offset
            y_offset = int(self.renderer.scaled_drum_img.get_height() * DRUM_Y_OFFSET_RATIO)
            self.drum_center_y = self.screen_height - self.renderer.scaled_drum_img.get_height() // 2 + y_offset
        else:
            # Fallback if image isn't loaded
            self.drum_center_y = int(self.screen_height * 0.75)
        
        # Fonts
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 36)

    def run(self):
        """Main game loop."""
        # Load audio using the new engine
        if not self.audio_engine.load_sound(str(self.audio_path)):
            return False  # Return False if audio loading fails
        
        # Apply initial speed setting
        self.timing_manager.playback_speed = self.playback_speed
        
        # Start playback (变速模式下静音播放音乐，使用节拍器)
        self.audio_engine.play()
        
        if self.playback_speed != 1.0:
            # 变速模式（慢速/快速）：静音背景音乐，使用节拍器
            pygame.mixer.music.set_volume(0.0)
            self.metronome_event_index = 0
            print(f"Variable speed mode ({self.playback_speed}x): Music muted, using metronome")
        else:
            # 正常速度：恢复音乐音量
            pygame.mixer.music.set_volume(1.0)
            print(f"Normal speed mode ({self.playback_speed}x): Playing music")
        
        self.timing_manager.start()
        
        running = True
        while running:
            # --- Event Handling (delegated to InputHandler) ---
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    # 播放返回音效
                    self.sound_manager.play_cancel_sound()
                    running = False
                
                elif event.type == pygame.VIDEORESIZE:
                    self._update_ui_layout()
                
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    # ESC键返回选曲界面
                    self.sound_manager.play_cancel_sound()
                    running = False
                
                else:
                    # Handle game controls (always use practice controls)
                    action = self.practice_controls.handle_event(event, self.playback_speed, self.is_paused)
                    
                    if action:
                        if action['action'] == 'toggle_pause':
                            self.is_paused = not self.is_paused
                            # 播放暂停音效
                            self.sound_manager.play_pause_sound()
                            if self.is_paused:
                                self.timing_manager.pause()
                            else:
                                self.timing_manager.unpause()
                        elif action['action'] == 'restart':
                            # 播放返回音效
                            self.sound_manager.play_cancel_sound()
                            # 直接重启游戏，不退出循环
                            self.restart()
                        elif action['action'] == 'toggle_auto':
                            self.auto_play = not self.auto_play
                            self.practice_controls.set_auto_play_state(self.auto_play)
                            print(f"Auto Play: {'ON' if self.auto_play else 'OFF'}")
                        elif action['action'] == 'change_speed':
                            new_speed = action['value']
                            # 切换速度会重新开始（因为技术限制无法完美保持位置）
                            self.playback_speed = new_speed
                            print(f"Changing speed to {new_speed}x, game will restart")
                            
                            # 变速模式切换
                            if new_speed != 1.0:
                                print(f"Switching to variable speed mode: Metronome enabled")
                            else:
                                print(f"Switching to normal speed mode: Music enabled")
                            
                            self.restart()

                    # Handle gameplay input
                    self.input_handler.handle_event(
                        event,
                        self.timing_manager.get_game_time(),
                        self._try_hit_manual,
                        self.screen.get_width()
                    )

            # --- Game Logic ---
            if not self.is_paused:
                game_time = self.timing_manager.get_game_time()
                
                # 节拍器播放（变速模式下）
                if self.playback_speed != 1.0:
                    self._play_metronome(game_time)
                
                # 同步自动演奏状态（从控制按钮）
                self.auto_play = self.practice_controls.get_auto_play_state()
                
                # 检查连打结束
                self._check_drumroll_end(game_time)
                
                if self.frames_elapsed >= 0:
                    self.input_handler.auto_play_notes(
                        self.auto_play,
                        self.current_note_index,
                        self.notes,
                        game_time,
                        self._try_hit,
                        self.active_drumroll,  # 传递连打状态
                        self,  # 传递game对象用于更新鼓动画时间
                        self.sound_don,  # 传递音效
                        self.sound_kat   # 传递音效
                    )
                
                self._check_miss()
                self._execute_branch()
                
                # Check for game end
                if not self.audio_engine.is_busy():
                    running = False

            # --- Drawing ---
            self._draw()
            
            if self.frames_elapsed < 0:
                self.frames_elapsed = 0
            else:
                self.frames_elapsed += 1
            # 使用配置的目标帧率，无论播放速度如何都保持固定帧率
            self.clock.tick(self.target_fps)
            
        self.audio_engine.stop()
        
        # 游戏结束后手动触发垃圾回收
        print("[GC] Manual garbage collection started")
        gc.collect()
        print("[GC] Manual garbage collection completed")
        
        return False
    
    def _handle_keydown(self, key):
        """Handle key press"""
        # Set drum press time for animation
        if key in [pygame.K_f, pygame.K_j, pygame.K_d, pygame.K_k]:
            self.drum_press_time = self.game_time
            
        # Don keys (F/J)
        if key == pygame.K_f:
            self.key_don_left = True
            self.drum_don_left_time = self.game_time
            self._try_hit(is_don=True)
        elif key == pygame.K_j:
            self.key_don_right = True
            self.drum_don_right_time = self.game_time
            self._try_hit(is_don=True)
        # Kat keys (D/K)
        elif key == pygame.K_d:
            self.key_kat_left = True
            self.drum_kat_left_time = self.game_time
            self._try_hit(is_don=False)
        elif key == pygame.K_k:
            self.key_kat_right = True
            self.drum_kat_right_time = self.game_time
            self._try_hit(is_don=False)
    
    def _handle_keyup(self, key):
        """Handle key release"""
        if key == pygame.K_f:
            self.key_don_left = False
        elif key == pygame.K_j:
            self.key_don_right = False
        elif key == pygame.K_d:
            self.key_kat_left = False
        elif key == pygame.K_k:
            self.key_kat_right = False
    
    def _try_hit_manual(self, is_don: bool):
        """手动输入的击打尝试（会检查自动演奏状态）"""
        # 如果开启自动演奏，不进行音符判定
        if self.practice_controls.get_auto_play_state():
            return
        
        # 获取实时时间用于鼓动画
        real_time = self.timing_manager.get_real_time()
        
        # 更新鼓按下时间（用于下沉动画）
        self.drum_press_time = real_time
        
        # 更新鼓击打时间（用于闪光效果）
        if is_don:
            # 咚 - 交替左右
            if real_time - self.drum_don_right_time > 100:
                self.drum_don_left_time = real_time
            else:
                self.drum_don_right_time = real_time
        else:
            # 咔 - 交替左右
            if real_time - self.drum_kat_right_time > 100:
                self.drum_kat_left_time = real_time
            else:
                self.drum_kat_right_time = real_time
        
        # 立即播放音效（手动敲击总是有音效）
        if is_don:
            self.sound_don.play()
        else:
            self.sound_kat.play()
        
        # 只有在有音符时才进行判定
        if self.current_note_index < len(self.notes):
            self._try_hit(is_don)
    
    def _try_hit(self, is_don: bool):
        """Attempts a hit and updates game state based on the judgment."""
        # 不检查索引，让判定模块自己处理
        if self.current_note_index >= len(self.notes):
            return
        
        # 获取两种时间
        game_time = self.timing_manager.get_game_time()  # 用于判定
        real_time = self.timing_manager.get_real_time()  # 用于动画
        
        # 在判定之前先检查连打是否该结束了
        self._check_drumroll_end(game_time)
        
        # 如果索引超出范围，直接返回
        if self.current_note_index >= len(self.notes):
            return

        note = self.notes[self.current_note_index]
        # print(f"[DEBUG] _try_hit: idx={self.current_note_index}, note_type={note.type}, in_drumroll={self.active_drumroll is not None}")
        
        # Delegate judgment to the NoteJudgment module
        result = self.note_judgment.try_hit(
            is_don,
            note,
            game_time,
            self.sound_don,
            self.sound_kat,
            self.renderer.trigger_hit_animation,
            self.current_note_index,
            real_time,  # 传递实时时间给动画
            self.notes  # 传递音符列表用于获取气球最大敲打数
        )
        
        # 处理连打开始
        if result.get('drumroll_start'):
            # 激活连打状态
            self.active_drumroll = (self.current_note_index, -1, note.type, 0)
            self.note_judgment.active_drumroll = self.active_drumroll
            print(f"Drumroll started: type={note.type}")
        
        # 处理连打更新
        if result.get('drumroll_update') is not None:
            self.active_drumroll = result['drumroll_update']
            self.note_judgment.active_drumroll = self.active_drumroll
        
        # 真打系统：连打/气球每次击打实时加100分
        if result['score'] > 0:
            self.score += result['score']
        
        if result['note_hit']:
            note.type = -1  # Mark note as hit
            self.combo += result['combo_add']
            
            if result['judgment'] == "Perfect":
                self.perfect_count += 1
            elif result['judgment'] == "Good":
                self.good_count += 1
            elif result['judgment'] == "OK":
                self.ok_count += 1
        
        if result['advance_index']:
            self.current_note_index += 1
            # print(f"[DEBUG] advance_index: {old_idx} -> {self.current_note_index}")

    def _check_drumroll_end(self, game_time):
        """检查连打/气球是否结束"""
        if not self.active_drumroll:
            return
        
        start_idx, end_idx, dr_type, hits = self.active_drumroll
        
        # 找到结束音符（type=8）
        if end_idx == -1:
            # 还没找到结束音符，搜索它
            for i in range(start_idx + 1, len(self.notes)):
                if self.notes[i].type == 8:
                    end_idx = i
                    self.active_drumroll = (start_idx, end_idx, dr_type, hits)
                    self.note_judgment.active_drumroll = self.active_drumroll
                    break
        
        if end_idx == -1:
            # 没找到结束音符，这是个错误
            return
        
        # 检查是否到达结束时间
        end_note = self.notes[end_idx]
        end_time = end_note.hit_ms if hasattr(end_note, 'hit_ms') else end_note.time_ms
        
        if game_time >= end_time:
            # 连打结束 - 不额外加分（每次击打已经加了100分）
            score = 0
            self.score += score
            
            # 标记结束音符为已处理
            end_note.type = -1
            
            # 清除连打状态
            self.active_drumroll = None
            self.note_judgment.active_drumroll = None
            self.note_judgment.last_drumroll_hit_time = 0  # 清除连打计时
            
            print(f"Drumroll ended: hits={hits}, score={score}")
            
            # 正确更新索引：移动到结束音符之后
            # 注意：连打开始时 current_note_index 已经 +1，所以现在应该在 start_idx+1
            # 我们需要跳过结束音符，移动到 end_idx+1
            self.current_note_index = end_idx + 1
            # print(f"[DEBUG] drumroll_end: idx {old_idx} -> {self.current_note_index}, start={start_idx}, end={end_idx}")

    def _check_miss(self):
        """Checks for missed notes."""
        if self.current_note_index >= len(self.notes):
            return
        
        game_time = self.timing_manager.get_game_time()
        note = self.notes[self.current_note_index]
        
        # 跳过连打结束标记
        if note.type == 8:
            return
        
        if self.note_judgment.check_miss(note, game_time):
            self.miss_count += 1
            self.combo = 0
            self.current_note_index += 1

    def _execute_branch(self):
        """
        Execute a branch choice. For now, it defaults to Normal -> Expert -> Master.
        In a real implementation, this would check player accuracy.
        """
        game_time = self.timing_manager.get_game_time()
        branch_notelist = None
        
        # Default to Normal, then Expert, then Master
        if self.branch_n and len(self.branch_n) > self.branch_index:
            branch_notelist = self.branch_n[self.branch_index]
            print(f"[{game_time / 1000:.2f}s] Branching to: Normal")
        elif self.branch_e and len(self.branch_e) > self.branch_index:
            branch_notelist = self.branch_e[self.branch_index]
            print(f"[{game_time / 1000:.2f}s] Branching to: Expert")
        elif self.branch_m and len(self.branch_m) > self.branch_index:
            branch_notelist = self.branch_m[self.branch_index]
            print(f"[{game_time / 1000:.2f}s] Branching to: Master")
            
        if branch_notelist:
            # Add notes and bars from the selected branch
            self.notes.extend(branch_notelist.play_notes)
            self.bars.extend(branch_notelist.bars)
            
            # Re-sort to maintain chronological order
            self.notes.sort(key=lambda n: n.hit_ms)
            self.bars.sort(key=lambda b: b.hit_ms)

            # Update the list of branch bars since new ones might have been added
            self.branch_bars = sorted(
                [b for b in self.bars if hasattr(b, 'branch_params') and b.branch_params],
                key=lambda b: b.hit_ms
            )
            
            # Regenerate metronome events with the new bars (for variable speed mode)
            self._generate_metronome_events()
            
            # 重新定位 current_note_index 到当前时间之后的第一个音符
            # 因为 notes 列表被重新排序，旧的索引已经无效
            for i, note in enumerate(self.notes):
                if note.hit_ms > game_time:
                    self.current_note_index = i
                    break
            else:
                # 所有音符都已经过去
                self.current_note_index = len(self.notes)

            # Move to the next set of branches for the next branch point
            self.branch_index += 1

    def _check_branching(self):
        """Check if it's time to make a branch choice."""
        if self.next_branch_idx >= len(self.branch_bars):
            return

        game_time = self.timing_manager.get_game_time()
        bar = self.branch_bars[self.next_branch_idx]
        
        # If game time has passed the branch bar, execute branch
        if game_time >= bar.hit_ms:
            self._execute_branch()
            self.next_branch_idx += 1
            
    def _draw(self):
        """Draws all game elements to the screen."""
        self.screen.fill(BLACK)

        # 获取两种时间
        game_time = self.timing_manager.get_game_time()  # 用于游戏逻辑（音符移动）
        real_time = self.timing_manager.get_real_time()  # 用于动画和特效

        # === 渲染器模块 ===
        self.renderer.draw_game_area()
        self.renderer.draw_bars(self.bars, game_time)
        self.renderer.draw_drumrolls(self.notes, game_time, self.combo)
        self.renderer.draw_notes(self.notes, self.current_note_index, game_time, self.combo)
        self.renderer.draw_stats(self.score)
        
        # 歌名和分类显示（独立模块）
        self.song_info_display.draw(self.song_title, self.song_category, self.category_color)
        
        # 判定文字 - 使用游戏时间
        judgment_text, judgment_time, is_super_large = self.note_judgment.get_judgment_display(game_time)
        if judgment_text:
            self.renderer.draw_judgment(judgment_text, game_time, judgment_time, is_super_large)
            
        # 击打动画 - 使用实时时间（不受变速影响）
        self.renderer.draw_hit_animations(real_time)
        
        # Draw controls (always use practice controls)
        self.practice_controls.draw(self.playback_speed, self.is_paused)

        # 准备鼓动画时间数据
        drum_times = {
            'don_left': self.drum_don_left_time,
            'don_right': self.drum_don_right_time,
            'kat_left': self.drum_kat_left_time,
            'kat_right': self.drum_kat_right_time,
            'press': self.drum_press_time
        }
        # 鼓动画也使用实时时间
        self.renderer.draw_drum(drum_times, real_time)
        
        # === 连段显示模块 ===
        if self.renderer.scaled_drum_img:
            self.combo_display.draw(
                self.screen,
                self.combo,
                self.renderer.screen_width,
                self.renderer.screen_height,
                self.renderer.drum_center_x,
                self.renderer.drum_center_y,
                self.renderer.scaled_drum_img.get_height()
            )

        pygame.display.flip()

    def _show_result(self):
        """Show result screen"""
        self.screen.fill(BLACK)
        
        # Responsive positioning for vertical layout
        center_x = self.screen_width // 2
        start_y = self.screen_height // 6
        
        title = self.font_large.render("Results", True, WHITE)
        self.screen.blit(title, (center_x - title.get_width()//2, start_y))
        
        y = start_y + 100
        spacing = min(80, self.screen_height // 12)
        
        results = [
            f"Score: {self.score}",
            f"Perfect: {self.perfect_count}",
            f"Good: {self.good_count}",
            f"OK: {self.ok_count}",
            f"Miss: {self.miss_count}",
            f"Max Combo: {self.combo}"
        ]
        
        for line in results:
            text = self.font_medium.render(line, True, WHITE)
            self.screen.blit(text, (center_x - text.get_width()//2, y))
            y += spacing
        
        # Draw hint at bottom
        hint = self.font_small.render("Press any key to continue", True, GRAY)
        self.screen.blit(hint, (center_x - hint.get_width()//2, self.screen_height - 80))
        
        pygame.display.flip()
        
        # Wait for user to close
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                    # 播放返回音效
                    self.sound_manager.play_cancel_sound()
                    waiting = False
            self.clock.tick(30)

