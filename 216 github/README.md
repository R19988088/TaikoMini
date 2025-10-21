# TaikoMini - Android 太鼓达人小游戏

一个专为 Android 13-16 设计的太鼓达人风格音乐游戏。

## 特性

- 🎮 支持 Android 13-16
- 🎵 支持 TJA 格式歌曲文件
- 📱 竖屏优化界面
- 🔊 音频播放支持
- 💾 外部存储访问

## 系统要求

- Android 13+ (API 33+)
- 至少 100MB 可用存储空间
- 支持音频输出

## 安装

### 方法1：下载 APK
1. 从 Releases 页面下载最新 APK
2. 允许安装未知来源应用
3. 安装 APK

### 方法2：源码构建
```bash
# 安装 buildozer
pip install buildozer

# 构建 APK
buildozer android debug
```

## 使用说明

### 添加歌曲
1. 在手机存储中创建文件夹：`/sdcard/TaikoMini/songs/`
2. 将歌曲文件夹放入该目录
3. 每个歌曲文件夹应包含：
   - `歌曲名.tja` - 谱面文件
   - `歌曲名.ogg` - 音频文件

### 游戏操作
- 点击屏幕开始游戏
- 按 ESC 键暂停/继续
- 按 ESC 键退出游戏

## 权限说明

应用需要以下权限：
- `READ_EXTERNAL_STORAGE` - 读取歌曲文件
- `WRITE_EXTERNAL_STORAGE` - 保存游戏数据
- `READ_MEDIA_AUDIO` - 播放音频文件
- `WAKE_LOCK` - 防止屏幕休眠

## 开发

### 环境要求
- Python 3.8+
- pygame 2.6.1
- buildozer

### 本地运行
```bash
python main.py
```

### 构建 APK
```bash
buildozer android debug
```

## 文件结构

```
TaikoMini/
├── main.py              # 主程序入口
├── buildozer.spec       # 构建配置
├── android_manifest.xml # Android 清单文件
├── requirements.txt     # Python 依赖
├── lib/                 # 游戏库
│   ├── __init__.py
│   ├── android_adapter.py
│   └── game.py
└── res/                 # 资源文件
    └── xml/             # Android XML 配置
```

## 故障排除

### 常见问题

1. **应用闪退**
   - 检查是否授予了存储权限
   - 确认歌曲文件格式正确

2. **找不到歌曲**
   - 确认歌曲文件放在正确位置
   - 检查文件权限

3. **音频播放问题**
   - 确认设备支持音频输出
   - 检查音频文件格式

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v1.0.0
- 初始版本
- 支持 Android 13-16
- 基本的游戏功能
