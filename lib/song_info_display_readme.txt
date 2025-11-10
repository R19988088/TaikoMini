============================
歌曲信息显示模块使用说明
Song Info Display Module Manual
============================

这是一个独立的模块，用于在游戏界面右上角显示歌名和分类。

## 位置
文件: lib/song_info_display.py

## 功能
- 在屏幕右上角显示歌名和分类
- 分类带有彩色圆角背景
- 支持中文字体
- 可以自定义各种参数

## 使用方法

### 1. 基本使用（已集成在game.py中）
```python
from lib.song_info_display import SongInfoDisplay

# 创建显示器
song_display = SongInfoDisplay(screen)

# 在游戏循环中绘制
song_display.draw(song_title="歌曲名称", category="分类", category_color=(255, 128, 0))
```

### 2. 自定义位置
```python
# 设置显示位置
song_display.set_position(
    right_margin=30,      # 右边距（像素）
    top_margin=30,        # 上边距（像素）
    vertical_spacing=15   # 歌名和分类之间的间距（像素）
)
```

### 3. 自定义字体大小
```python
# 设置字体大小
song_display.set_font_sizes(
    title_size=40,        # 歌名字体大小
    category_size=30      # 分类字体大小
)
```

### 4. 自定义颜色
```python
# 设置颜色
song_display.set_colors(
    title_color=(255, 255, 255),           # 歌名颜色（白色）
    category_text_color=(255, 255, 255),   # 分类文字颜色（白色）
    default_category_bg=(247, 152, 36)     # 默认分类背景颜色（橙色）
)
```

### 5. 自定义分类背景
```python
# 设置背景内边距
song_display.set_category_padding(
    padding_x=20,         # 横向内边距（像素）
    padding_y=10          # 纵向内边距（像素）
)

# 设置圆角半径比例（0.0-1.0）
song_display.set_border_radius_ratio(0.5)  # 0.5=完全圆角，0.0=无圆角
```

## 配置文件

分类颜色从 songs/category_colors.ini 读取：

```ini
# 分类颜色配置
南梦宫原创音乐 = #FF7027
综合音乐 = #1DC83B
动漫音乐 = #FF90D3
```

支持的格式：
- RGB: 255,128,0
- 十六进制: #FF8000

## 默认配置

- 右边距: 20像素
- 上边距: 20像素
- 歌名和分类间距: 10像素
- 歌名字体大小: 36
- 分类字体大小: 28
- 歌名颜色: 白色
- 分类文字颜色: 白色
- 默认分类背景: 橙色 (247, 152, 36)
- 背景横向内边距: 15像素
- 背景纵向内边距: 8像素
- 圆角半径比例: 0.5 (完全圆角)

## 注意事项

1. 字体文件使用 lib/res/FZPangWaUltra-Regular.ttf
2. 如果字体文件不存在，会自动使用系统中文字体
3. 修改字体大小后会自动重新加载字体
4. 窗口大小改变时，调用 update_screen_size(width, height) 更新

## 示例：在game.py中修改配置

在 __init__ 方法中，创建 SongInfoDisplay 后添加：

```python
self.song_info_display = SongInfoDisplay(screen)

# 自定义配置
self.song_info_display.set_position(right_margin=25, top_margin=25)
self.song_info_display.set_font_sizes(title_size=42, category_size=30)
self.song_info_display.set_border_radius_ratio(0.4)
```

## 完整的可配置参数列表

| 参数 | 默认值 | 说明 |
|------|--------|------|
| right_margin | 20 | 右边距（像素）|
| top_margin | 20 | 上边距（像素）|
| vertical_spacing | 10 | 歌名和分类间距（像素）|
| title_font_size | 36 | 歌名字体大小 |
| category_font_size | 28 | 分类字体大小 |
| title_color | (255,255,255) | 歌名颜色 |
| category_text_color | (255,255,255) | 分类文字颜色 |
| default_category_bg_color | (247,152,36) | 默认分类背景 |
| category_padding_x | 15 | 背景横向内边距 |
| category_padding_y | 8 | 背景纵向内边距 |
| category_border_radius_ratio | 0.5 | 圆角比例(0-1) |

