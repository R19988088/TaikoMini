"""
分数记录管理器
Score Record Manager

负责记录和管理游戏成绩
"""

import configparser
from pathlib import Path
from typing import Optional, Dict, Tuple, List
from datetime import datetime


class ScoreManager:
    """
    分数记录管理器
    Score Record Manager
    
    管理游戏成绩的保存和读取
    """
    
    def __init__(self, config_dir: Path = None):
        """
        初始化分数管理器
        
        Args:
            config_dir: 配置文件目录，默认为songs目录
        """
        if config_dir is None:
            config_dir = Path("songs")
        
        self.score_file = config_dir / "scores.ini"
        self.config = configparser.ConfigParser()
        
        # 加载现有分数
        self._load_scores()
    
    def _load_scores(self):
        """加载现有分数记录"""
        if self.score_file.exists():
            try:
                self.config.read(self.score_file, encoding='utf-8')
                print(f"Loaded scores from {self.score_file}")
            except Exception as e:
                print(f"Error loading scores: {e}")
                self.config = configparser.ConfigParser()
        else:
            print(f"No existing scores file, will create new one")
    
    def _save_scores(self):
        """保存分数记录到文件"""
        try:
            # 确保目录存在
            self.score_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存配置
            with open(self.score_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
            print(f"Scores saved to {self.score_file}")
        except Exception as e:
            print(f"Error saving scores: {e}")
    
    def save_score(self, song_id: str, difficulty: str, score: int, 
                   perfect_count: int, good_count: int, ok_count: int, 
                   miss_count: int, drumroll_hits: int, max_combo: int, total_notes: int = 0):
        """
        保存游戏成绩
        
        Args:
            song_id: 歌曲ID（tja文件名，不含扩展名）
            difficulty: 难度（Easy, Normal, Hard, Oni, Edit）
            score: 总分
            perfect_count: 精准判定数
            good_count: 良判定数
            ok_count: 可判定数
            miss_count: 不可判定数
            drumroll_hits: 连打数
            max_combo: 最大连段数
            total_notes: 总音符数
        """
        # 创建section名称：歌曲ID_难度
        section_name = f"{song_id}_{difficulty}"
        
        # 如果section不存在，创建它
        if section_name not in self.config:
            self.config.add_section(section_name)
        
        # 获取现有最高分
        try:
            existing_score = self.config.getint(section_name, 'score', fallback=0)
        except:
            existing_score = 0
        
        # 只有新分数更高时才更新
        if score >= existing_score:
            self.config.set(section_name, 'score', str(score))
            self.config.set(section_name, 'perfect_count', str(perfect_count))
            self.config.set(section_name, 'good_count', str(good_count))
            self.config.set(section_name, 'ok_count', str(ok_count))
            self.config.set(section_name, 'miss_count', str(miss_count))
            self.config.set(section_name, 'drumroll_hits', str(drumroll_hits))
            self.config.set(section_name, 'max_combo', str(max_combo))
            self.config.set(section_name, 'total_notes', str(total_notes))
            self.config.set(section_name, 'last_played', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            # 保存到文件
            self._save_scores()
            
            print(f"New high score saved for {song_id} [{difficulty}]: {score}")
            return True
        else:
            print(f"Score not saved (not higher than existing: {existing_score})")
            return False
    
    def get_score(self, song_id: str, difficulty: str) -> Optional[Dict[str, int]]:
        """
        获取指定歌曲和难度的成绩
        
        Args:
            song_id: 歌曲ID
            difficulty: 难度
            
        Returns:
            包含成绩数据的字典，如果没有记录则返回None
        """
        section_name = f"{song_id}_{difficulty}"
        
        if section_name not in self.config:
            return None
        
        try:
            return {
                'score': self.config.getint(section_name, 'score', fallback=0),
                'perfect_count': self.config.getint(section_name, 'perfect_count', fallback=0),
                'good_count': self.config.getint(section_name, 'good_count', fallback=0),
                'ok_count': self.config.getint(section_name, 'ok_count', fallback=0),
                'miss_count': self.config.getint(section_name, 'miss_count', fallback=0),
                'drumroll_hits': self.config.getint(section_name, 'drumroll_hits', fallback=0),
                'max_combo': self.config.getint(section_name, 'max_combo', fallback=0),
                'total_notes': self.config.getint(section_name, 'total_notes', fallback=0),
                'last_played': self.config.get(section_name, 'last_played', fallback='')
            }
        except Exception as e:
            print(f"Error getting score: {e}")
            return None
    
    def get_all_scores(self, song_id: str) -> Dict[str, Dict[str, int]]:
        """
        获取指定歌曲所有难度的成绩
        
        Args:
            song_id: 歌曲ID
            
        Returns:
            以难度为key的成绩字典
        """
        scores = {}
        difficulties = ['Easy', 'Normal', 'Hard', 'Oni', 'Edit']
        
        for difficulty in difficulties:
            score_data = self.get_score(song_id, difficulty)
            if score_data:
                scores[difficulty] = score_data
        
        return scores
    
    def get_crown_type(self, song_id: str, difficulty: str) -> Optional[int]:
        """
        获取指定歌曲和难度的皇冠类型
        
        Args:
            song_id: 歌曲ID
            difficulty: 难度
            
        Returns:
            皇冠类型: 0=过关(分数>=6000), 1=全连(Full Combo), 2=全P的全连(All Perfect)
            如果没有达成任何条件则返回None
        """
        score_data = self.get_score(song_id, difficulty)
        if not score_data:
            return None
        
        score = score_data.get('score', 0)
        perfect_count = score_data.get('perfect_count', 0)
        good_count = score_data.get('good_count', 0)
        ok_count = score_data.get('ok_count', 0)
        miss_count = score_data.get('miss_count', 0)
        
        # 检查是否全P的全连（最高级别）
        if miss_count == 0 and ok_count == 0 and good_count == 0 and perfect_count > 0:
            return 2  # All Perfect
        
        # 检查是否全连
        if miss_count == 0 and (perfect_count > 0 or good_count > 0 or ok_count > 0):
            return 1  # Full Combo
        
        # 检查是否过关
        if score >= 6000:
            return 0  # Clear
        
        return None
    
    def get_crown_info(self, song_id: str, difficulties: List[str]) -> Tuple[Optional[int], int]:
        """
        获取歌曲的皇冠显示信息
        
        Args:
            song_id: 歌曲ID
            difficulties: 该歌曲存在的难度列表
            
        Returns:
            (最高皇冠类型, 拥有皇冠的难度数量)
            如果没有任何皇冠则返回(None, 0)
        """
        crown_types = []
        for difficulty in difficulties:
            crown_type = self.get_crown_type(song_id, difficulty)
            if crown_type is not None:
                crown_types.append(crown_type)
        
        if not crown_types:
            return (None, 0)
        
        # 返回最高级别的皇冠和拥有皇冠的难度数量
        return (max(crown_types), len(crown_types))

