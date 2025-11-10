"""
重构后的 TaikoGame 示例
展示如何使用新的模块化架构
"""

import pygame
from pathlib import Path
from typing import Dict, List

# 导入新模块
from lib.combo_display import ComboDisplay
from lib.game_input import InputHandler
from lib.note_judgment import NoteJudgment, PERFECT_WINDOW, GOOD_WINDOW, OK_WINDOW
from lib.game_renderer import GameRenderer

# 导入原有模块
from lib.tja import Note
from lib.audio import AudioEngine


class TaikoGameRefactored:
    """
    重构后的太鼓游戏主类
    
    使用模块化架构，代码更清晰、易维护
    """
    
    def __init__(self, screen, chart_data: Dict, audio_path: Path):
        """初始化游戏"""
        self.screen = screen
        self.chart_data = chart_data
        self.audio_path = audio_path
        
        # === 初始化新模块 ===
        self.renderer = GameRenderer(screen)
        self.input_handler = InputHandler()
        self.note_judgment = NoteJudgment()
        self.combo_display = ComboDisplay()
        
        # === 音频引擎 ===
        self.audio_engine = AudioEngine()
        
        # === 谱面数据 ===
        master_notes = chart_data['notes']
        self.notes: List[Note] = master_notes.play_notes
        self.bars: List[Note] = master_notes.bars
        self.current_note_index = 0
        
        # === 游戏状态 ===
        self.game_time = 0
        self.offset_ms = chart_data.get('offset', 0) * 1000
        self.clock = pygame.time.Clock()
        
        # === 统计数据 ===
        self.score = 0
        self.combo = 0
        self.perfect_count = 0
        self.good_count = 0
        self.ok_count = 0
        self.miss_count = 0
        
        # === 控制状态 ===
        self.is_paused = False
        self.playback_speed = 1.0
        
        # === UI元素 ===
        self.play_pause_rect = pygame.Rect(0, 0, 60, 60)
        self.restart_rect = pygame.Rect(0, 0, 60, 60)
        self._update_ui_layout()
        
        # === 音效 ===
        self._load_sounds()
    
    def _load_sounds(self):
        """加载音效"""
        try:
            sound_dir = Path("lib/res/wav")
            self.sound_don = pygame.mixer.Sound(str(sound_dir / "taiko_don.wav"))
            self.sound_kat = pygame.mixer.Sound(str(sound_dir / "taiko_ka.wav"))
        except Exception as e:
            print(f"⚠ Could not load sounds: {e}")
            self.sound_don = None
            self.sound_kat = None
    
    def _update_ui_layout(self):
        """更新UI布局"""
        screen_width = self.screen.get_width()
        
        # 更新渲染器布局
        self.renderer.update_layout()
        
        # 更新按钮位置
        slider_x = int(screen_width * 0.1)
        slider_y = self.renderer.game_area_bottom + 60
        
        self.play_pause_rect.centery = slider_y
        self.play_pause_rect.right = screen_width - slider_x - 80
        
        self.restart_rect.centery = slider_y
        self.restart_rect.right = screen_width - slider_x
    
    def run(self):
        """主游戏循环"""
        # 加载音频
        if not self.audio_engine.load_sound(str(self.audio_path)):
            print("✗ Could not load audio")
            return False
        
        self.audio_engine.playback_speed = self.playback_speed
        self.audio_engine.play()
        
        start_time = pygame.time.get_ticks()
        running = True
        
        while running:
            # === 时间管理 ===
            self.game_time = self.audio_engine.get_time_ms() + self.offset_ms - 580
            
            # === 事件处理 ===
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.VIDEORESIZE:
                    self._update_ui_layout()
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif not self.is_paused:
                        self.input_handler.handle_keydown(
                            event.key,
                            self.game_time,
                            self._try_hit
                        )
                
                elif event.type == pygame.KEYUP:
                    self.input_handler.handle_keyup(event.key)
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # 触摸/鼠标支持
                    if not self.is_paused:
                        self.input_handler.handle_touch(
                            event,
                            self.screen.get_width(),
                            self.game_time,
                            self._try_hit
                        )
                    
                    # UI按钮点击
                    if self.play_pause_rect.collidepoint(event.pos):
                        self.is_paused = not self.is_paused
                        if self.is_paused:
                            self.audio_engine.pause()
                        else:
                            self.audio_engine.unpause()
            
            # === 游戏逻辑 ===
            if not self.is_paused:
                # 自动演奏
                self.input_handler.auto_play_notes(
                    self.current_note_index,
                    self.notes,
                    self.game_time,
                    self._try_hit
                )
                
                # 检查Miss
                self._check_miss()
                
                # 检查游戏结束
                if not self.audio_engine.is_busy():
                    running = False
            
            # === 渲染 ===
            self._draw()
            
            self.clock.tick(60)
        
        self.audio_engine.stop()
        return True
    
    def _try_hit(self, is_don: bool):
        """
        尝试击打音符
        
        参数:
            is_don: 是否击打咚（False=咔）
        """
        if self.current_note_index >= len(self.notes):
            return
        
        note = self.notes[self.current_note_index]
        
        # 调用判定系统
        result = self.note_judgment.try_hit(
            is_don,
            note,
            self.game_time,
            self.sound_don,
            self.sound_kat,
            self._trigger_animation,
            self.current_note_index
        )
        
        # 更新统计
        if result['note_hit']:
            note.type = -1  # 标记为已击打
            self.score += result['score']
            self.combo += result['combo_add']
            
            # 更新判定计数
            if result['judgment'] == "Perfect":
                self.perfect_count += 1
            elif result['judgment'] == "Good":
                self.good_count += 1
            elif result['judgment'] == "OK":
                self.ok_count += 1
        
        if result['advance_index']:
            self.current_note_index += 1
    
    def _trigger_animation(self, is_big, is_don):
        """触发击打动画"""
        self.renderer.trigger_hit_animation(is_big, is_don, self.game_time)
    
    def _check_miss(self):
        """检查Miss"""
        if self.current_note_index >= len(self.notes):
            return
        
        note = self.notes[self.current_note_index]
        
        if self.note_judgment.check_miss(note, self.game_time):
            self.miss_count += 1
            self.combo = 0
            self.current_note_index += 1
    
    def _draw(self):
        """绘制所有元素"""
        # 清屏
        self.screen.fill((0, 0, 0))
        
        # 游戏区域
        self.renderer.draw_game_area()
        
        # 小节线
        self.renderer.draw_bars(self.bars, self.game_time)
        
        # 连打条
        self.renderer.draw_drumrolls(self.notes, self.game_time)
        
        # 音符
        self.renderer.draw_notes(self.notes, self.current_note_index, self.game_time)
        
        # 统计信息
        self.renderer.draw_stats(self.score)
        
        # 判定文字
        judgment_text = self.note_judgment.get_judgment_display(self.game_time)
        if judgment_text:
            self.renderer.draw_judgment(
                judgment_text,
                self.game_time,
                self.note_judgment.judgment_time
            )
        
        # 击打动画
        self.renderer.draw_hit_animations(self.game_time)
        
        # 速度按钮
        self.renderer.draw_speed_buttons(self.playback_speed)
        
        # 控制按钮
        self.renderer.draw_control_buttons(
            self.is_paused,
            self.play_pause_rect,
            self.restart_rect
        )
        
        # 鼓
        drum_times = self.input_handler.get_drum_animation_times()
        self.renderer.draw_drum(drum_times, self.game_time)
        
        # 连段显示
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


# 使用示例
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((720, 1280), pygame.RESIZABLE)
    
    # 这里需要实际的chart_data和audio_path
    # game = TaikoGameRefactored(screen, chart_data, audio_path)
    # game.run()
    
    print("✓ 重构后的游戏架构已就绪")
    print("  - 代码行数从 1436 行减少到 ~250 行")
    print("  - 4个独立模块，职责清晰")
    print("  - 支持触摸输入，便于安卓移植")

