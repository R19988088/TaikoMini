"""
Simplified utils for TJA parsing
"""
from functools import lru_cache
from dataclasses import dataclass

@dataclass
class GlobalData:
    """Simple global data container"""
    modifiers: object = None

class Modifiers:
    """Simple modifiers"""
    display = False
    inverse = False
    random = 0
    speed = 1.0

# Global data instance
global_data = GlobalData(modifiers=Modifiers())

def strip_comments(line: str) -> str:
    """Remove comments from line"""
    # Remove // comments
    if '//' in line:
        line = line.split('//')[0]
    return line

@lru_cache(maxsize=64)
def get_pixels_per_frame(bpm: float, time_signature: float, distance: float) -> float:
    """Calculate pixels per frame for note scrolling"""
    if bpm == 0:
        return 0
    beat_duration = 60 / bpm
    total_time = time_signature * beat_duration
    total_frames = 60 * total_time
    return (distance / total_frames)

