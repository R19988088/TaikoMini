# 临时测试文件 - 检查缩进
class SongButton:
    def __init__(self):
        self.expanded = False
        # 默认选择鬼难度（Oni），如果没有则选第一个
        if 'Oni' in self.difficulties:
            self.selected_diff_index = self.difficulties.index('Oni')
        else:
            self.selected_diff_index = 0
        self.y_offset = 0  # For animation

