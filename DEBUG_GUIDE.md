# Android APK 调试指南

## 问题：APK 安装后闪退

### 🔍 原因分析

Android APK 闪退的原因可能是：

1. **资源文件路径错误** - 图片、字体等文件找不到
2. **Python 模块导入失败** - 某些库在 Android 上不可用
3. **权限问题** - 没有正确请求存储权限
4. **字符编码问题** - 中文路径或文件名
5. **pygame 初始化失败** - 在某些设备上可能有问题

---

## 📱 如何获取崩溃日志

### 方法1：使用 ADB（推荐）

1. **安装 ADB**
   - 下载 Android SDK Platform Tools: https://developer.android.com/studio/releases/platform-tools
   - 或使用 Android Studio 附带的 ADB

2. **连接手机**
   ```bash
   # 检查设备是否连接
   adb devices
   
   # 查看实时日志
   adb logcat | grep -i taikomini
   
   # 或查看 Python 相关日志
   adb logcat | grep -i python
   ```

3. **安装 APK 并查看日志**
   ```bash
   # 安装 APK
   adb install -r TaikoMini-*.apk
   
   # 清除旧日志
   adb logcat -c
   
   # 启动应用并实时查看日志
   adb logcat -s python:* EARLY_LOG:*
   ```

### 方法2：使用 Logcat 应用

在手机上安装 Logcat Reader 应用，可以直接查看日志，无需电脑。

---

## 🛠️ 修复步骤

### 1. 确保资源文件被包含

检查 `buildozer.spec` 中的 `source.include_patterns`：

```ini
source.include_patterns = lib/*,lib/res/*,lib/res/Texture/*,lib/res/wav/*
```

### 2. 使用简化版本测试

我在 `main.py` 中添加了简化版本作为回退。如果主游戏无法加载，会自动切换到简化版本显示错误信息。

### 3. 检查字体加载

pygame 字体加载在某些 Android 设备上可能失败。代码中已经添加了多个字体回退选项。

### 4. 添加更多日志

如果问题仍然存在，在代码中添加更多日志：

```python
import sys

def log(message):
    print(message)
    if hasattr(sys, 'getandroidapp'):
        try:
            sys.getandroidapp().log(message)
        except:
            pass
```

---

## 🧪 测试 APK

### 步骤 1：构建调试版本

```bash
buildozer android debug
```

### 步骤 2：安装并查看日志

```bash
# 安装
adb install -r .buildozer/android/platform/build/dists/taikomini/bin/taikomini-*.apk

# 启动并查看日志
adb logcat -c  # 清除旧日志
adb shell am start -n org.taikomini/org.kivy.android.PythonActivity
adb logcat | grep -E "(python|TaikoMini|ERROR)"
```

### 步骤 3：分析日志

查找以下关键词：
- `FATAL EXCEPTION` - 致命错误
- `Traceback` - Python 异常
- `ImportError` - 模块导入失败
- `FileNotFoundError` - 文件未找到
- `pygame.error` - pygame 相关错误

---

## 🔧 常见问题修复

### 问题1：字体加载失败

**症状**：屏幕显示但文字不显示

**修复**：已经在 `resource_loader.py` 中添加了多个字体回退选项

### 问题2：图片加载失败

**症状**：界面空白或缺少图片

**修复**：确保 `lib/res/Texture/selectsongs/` 目录中的所有图片都被包含

### 问题3：音频播放失败

**症状**：游戏运行但无声音

**修复**：在 `buildozer.spec` 中已配置音频权限

### 问题4：权限被拒绝

**症状**：无法访问文件

**修复**：在 Android 设置中手动授予存储权限

---

## 📝 日志示例

### 正常启动日志

```
=== TaikoMini Starting ===
[ANDROID] Environment configured
[PATH] Added lib path: /data/user/0/org.taikomini/files/app/lib
[INIT] Initializing pygame...
[AUDIO] Mixer initialized
[STORAGE] Songs path: /storage/emulated/0/Android/data/org.taikomini/files/songs
[IMPORT] Importing game modules...
[SONGS] Looking for songs in: /data/user/0/org.taikomini/files/app/songs
[SONGS] Found 5 songs
[GAME] Starting game loop...
```

### 错误日志

```
=== TaikoMini Starting ===
[ANDROID] Environment configured
[PATH] Added lib path: /data/user/0/org.taikomini/files/app/lib
[INIT] Initializing pygame...
[ERROR] Import failed: No module named 'lib.game'
[FALLBACK] Using simplified version...
```

---

## 🚀 快速修复流程

1. **查看日志**
   ```bash
   adb logcat | grep TaikoMini
   ```

2. **如果是导入错误**
   - 检查是否所有 `lib/` 文件都被包含
   - 运行 `buildozer android clean` 后重新构建

3. **如果是资源错误**
   - 检查 `lib/res/` 目录结构
   - 确认所有资源文件都在 APK 中

4. **如果是权限错误**
   - 手动授予存储权限
   - 在 `android_manifest.xml` 中检查权限配置

---

## 📞 需要帮助？

如果问题仍然存在，请提供以下信息：

1. 完整的 logcat 日志
2. Android 版本和型号
3. buildozer.spec 配置
4. 错误截图（如果有）

---

## 💡 调试技巧

1. **使用简化版本**
   - 代码会自动回退到简化版本
   - 可以显示基本信息，证明应用已经启动

2. **逐步添加功能**
   - 先确保基础功能（显示界面）正常
   - 再添加游戏逻辑

3. **远程调试**
   - 使用 ADB 连接
   - 可以实时查看日志和调试

4. **测试不同设备**
   - 在不同 Android 版本和设备上测试
   - 某些问题可能只在特定设备上出现

