"""
音符图案管理器
Note Pattern Manager

管理各种音符的图案和视觉效果
Manages note patterns and visual effects
"""

import pygame
from pathlib import Path
from typing import Dict, Optional, Tuple
import math


class NotePatternManager:
    """音符图案管理器"""
    
    def __init__(self, res_dir: Path = None):
        """
        初始化音符图案管理器
        
        Args:
            res_dir: 资源目录路径
        """
        if res_dir is None:
            res_dir = Path("lib/res/Texture/note")
        self.res_dir = Path(res_dir)
        
        # 音符图案字典
        self.patterns: Dict[str, pygame.Surface] = {}
        
        # 音符类型定义
        self.note_types = {
            'don': 'don1.png',            # 1 咚音符（连击<=20）
            'don2': 'don2.png',           # 1 咚音符（连击>20，动画帧1）
            'don3': 'don3.png',           # 1 咚音符（连击>20，动画帧2）
            'a': 'a1.png',                # 2 咔音符（连击<=20）
            'ka2': 'ka2.png',             # 2 咔音符（连击>20，动画帧1）
            'ka3': 'ka3.png',             # 2 咔音符（连击>20，动画帧2）
            'big_don': 'big_don3.png',    # 3 大咚音符（默认）
            'big_don1': 'big_don1.png',   # 3 大咚音符（连击<=20）
            'big_don2': 'big_don2.png',   # 3 大咚音符（连击>20，动画帧1）
            'big_don3': 'big_don3.png',   # 3 大咚音符（连击>20，动画帧2）
            'big_ka': 'big_ka3.png',      # 4 大咔音符（默认）
            'big_ka1': 'big_ka1.png',     # 4 大咔音符（连击<=20）
            'big_ka2': 'big_ka2.png',     # 4 大咔音符（连击>20，动画帧1）
            'big_ka3': 'big_ka3.png',     # 4 大咔音符（连击>20，动画帧2）
            # 连打音符图案
            'rapid_tail': 'rapid_tail.png',      # 5 连打尾部
            'rapid_front': 'front.png',          # 5 连打头部（连击<=20）
            'front2': 'front2.png',              # 5 连打头部（连击>20，动画帧1）
            'front3': 'front3.png',              # 5 连打头部（连击>20，动画帧2）
            'rapid_body': 'rapid.png',           # 5 连打主体
            'big_rapid_tail': 'big_rapid_tail.png',  # 6 大连打尾部
            'big_rapid_front': 'big_front2.png',     # 6 大连打头部
            'big_rapid_body': 'big_rapid.png',       # 6 大连打主体
            'balloon_tail': 'ballon_tail2.png',      # 7 气球尾部
            'balloon_front': 'ballon_front.png',     # 7 气球头部（连击<=20）
            'ballon_front2': 'ballon_front2.png',    # 7 气球头部（连击>20，动画帧1）
            'ballon_front3': 'ballon_front3.png',    # 7 气球头部（连击>20，动画帧2）
            'balloon_body': 'ballon_tail.png'        # 7 气球主体
        }
        
        # 加载所有音符图案
        self._load_patterns()
    
    def _load_patterns(self):
        """加载所有音符图案"""
        print("Loading note patterns...")
        
        for pattern_name, filename in self.note_types.items():
            pattern_path = self.res_dir / filename
            
            if pattern_path.exists():
                try:
                    pattern = pygame.image.load(str(pattern_path)).convert_alpha()
                    self.patterns[pattern_name] = pattern
                    print(f"Loaded pattern: {pattern_name} from {filename}")
                except Exception as e:
                    print(f"Failed to load pattern {pattern_name}: {e}")
            else:
                print(f"Pattern file not found: {pattern_path}")
        
        # 如果没有找到a1.png，尝试使用其他替代
        if 'a' not in self.patterns:
            # 尝试使用ka1.png作为替代
            alt_path = self.res_dir / "ka1.png"
            if alt_path.exists():
                try:
                    pattern = pygame.image.load(str(alt_path)).convert_alpha()
                    self.patterns['a'] = pattern
                    print(f"Using ka1.png as substitute for a1.png")
                except Exception as e:
                    print(f"Failed to load substitute pattern: {e}")
            else:
                print(f"Warning: a1.png not found and no substitute available")
        
        # 为类型9的气球使用与类型7相同的图案
        if 'balloon_tail' in self.patterns:
            self.patterns['balloon9_tail'] = self.patterns['balloon_tail']
        if 'balloon_front' in self.patterns:
            self.patterns['balloon9_front'] = self.patterns['balloon_front']
        if 'balloon_body' in self.patterns:
            self.patterns['balloon9_body'] = self.patterns['balloon_body']
    
    def get_pattern(self, pattern_name: str) -> Optional[pygame.Surface]:
        """
        获取音符图案
        
        Args:
            pattern_name: 图案名称
            
        Returns:
            pygame.Surface: 音符图案，如果不存在则返回None
        """
        return self.patterns.get(pattern_name)
    
    def get_pattern_size(self, pattern_name: str) -> Tuple[int, int]:
        """
        获取音符图案尺寸
        
        Args:
            pattern_name: 图案名称
            
        Returns:
            Tuple[int, int]: (宽度, 高度)
        """
        pattern = self.get_pattern(pattern_name)
        if pattern:
            return pattern.get_size()
        return (0, 0)
    
    def draw_pattern(self, surface: pygame.Surface, pattern_name: str, 
                    x: int, y: int, scale: float = 1.0, 
                    rotation: float = 0.0, alpha: int = 255) -> bool:
        """
        绘制音符图案
        
        Args:
            surface: 目标表面
            pattern_name: 图案名称
            x: X坐标
            y: Y坐标
            scale: 缩放比例
            rotation: 旋转角度（度）
            alpha: 透明度 (0-255)
            
        Returns:
            bool: 是否成功绘制
        """
        pattern = self.get_pattern(pattern_name)
        if not pattern:
            return False
        
        # 创建图案副本
        draw_pattern = pattern.copy()
        
        # 应用缩放
        if scale != 1.0:
            orig_size = draw_pattern.get_size()
            new_size = (int(orig_size[0] * scale), int(orig_size[1] * scale))
            draw_pattern = pygame.transform.scale(draw_pattern, new_size)
        
        # 应用旋转
        if rotation != 0.0:
            draw_pattern = pygame.transform.rotate(draw_pattern, rotation)
        
        # 应用透明度
        if alpha < 255:
            draw_pattern.set_alpha(alpha)
        
        # 绘制图案
        surface.blit(draw_pattern, (x, y))
        return True
    
    def draw_pattern_centered(self, surface: pygame.Surface, pattern_name: str,
                             center_x: int, center_y: int, scale: float = 1.0,
                             rotation: float = 0.0, alpha: int = 255) -> bool:
        """
        居中绘制音符图案
        
        Args:
            surface: 目标表面
            pattern_name: 图案名称
            center_x: 中心X坐标
            center_y: 中心Y坐标
            scale: 缩放比例
            rotation: 旋转角度（度）
            alpha: 透明度 (0-255)
            
        Returns:
            bool: 是否成功绘制
        """
        pattern = self.get_pattern(pattern_name)
        if not pattern:
            return False
        
        # 计算图案尺寸
        orig_width, orig_height = pattern.get_size()
        scaled_width = int(orig_width * scale)
        scaled_height = int(orig_height * scale)
        
        # 计算绘制位置（居中）
        x = center_x - scaled_width // 2
        y = center_y - scaled_height // 2
        
        return self.draw_pattern(surface, pattern_name, x, y, scale, rotation, alpha)
    
    def get_available_patterns(self) -> list:
        """
        获取所有可用的图案名称
        
        Returns:
            list: 图案名称列表
        """
        return list(self.patterns.keys())
    
    def get_pattern_info(self) -> Dict[str, Dict]:
        """
        获取所有图案的详细信息
        
        Returns:
            Dict[str, Dict]: 图案信息字典
        """
        info = {}
        for pattern_name, pattern in self.patterns.items():
            width, height = pattern.get_size()
            info[pattern_name] = {
                'size': (width, height),
                'loaded': True
            }
        return info
    
    def create_pattern_variant(self, pattern_name: str, variant_name: str,
                             scale: float = 1.0, rotation: float = 0.0,
                             color_mod: Tuple[int, int, int] = None) -> bool:
        """
        创建图案变体
        
        Args:
            pattern_name: 原始图案名称
            variant_name: 变体名称
            scale: 缩放比例
            rotation: 旋转角度
            color_mod: 颜色修改 (R, G, B)
            
        Returns:
            bool: 是否成功创建
        """
        pattern = self.get_pattern(pattern_name)
        if not pattern:
            return False
        
        # 创建变体
        variant = pattern.copy()
        
        # 应用缩放
        if scale != 1.0:
            orig_size = variant.get_size()
            new_size = (int(orig_size[0] * scale), int(orig_size[1] * scale))
            variant = pygame.transform.scale(variant, new_size)
        
        # 应用旋转
        if rotation != 0.0:
            variant = pygame.transform.rotate(variant, rotation)
        
        # 应用颜色修改
        if color_mod:
            variant.fill(color_mod, special_flags=pygame.BLEND_MULT)
        
        # 保存变体
        self.patterns[variant_name] = variant
        return True
    
    def clear_patterns(self):
        """清空所有图案"""
        self.patterns.clear()
    
    def reload_patterns(self):
        """重新加载所有图案"""
        self.clear_patterns()
        self._load_patterns()
    
    def get_stats(self) -> Dict:
        """
        获取管理器统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            'total_patterns': len(self.patterns),
            'available_patterns': list(self.patterns.keys()),
            'resource_dir': str(self.res_dir),
            'note_types': self.note_types
        }
