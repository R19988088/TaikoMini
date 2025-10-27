# GitHub 仓库重构计划

## 🔍 当前问题

GitHub 仓库的文件结构混乱：
- **根目录**：`lib/`、`TaikoMini.py`、`songs/` 等
- **216 github/** 目录：Android 构建文件（`main.py`、`buildozer.spec` 等）
- **GitHub Actions**：在根目录的 `.github/`，但引用 `216 github/` 目录

这导致：
- ❌ 文件路径混乱
- ❌ Buildozer 找不到正确的文件
- ❌ 不清楚哪些文件是 Android 用的

---

## ✅ 推荐方案：将 Android 项目移到根目录

### 目标结构

```
TaikoMini/                          # GitHub 仓库根目录
├── .github/
│   └── workflows/
│       └── build-android.yml      # GitHub Actions
├── lib/                            # 游戏库（共享）
│   ├── __init__.py
│   ├── game.py
│   ├── audio.py
│   ├── res/                        # 资源文件
│   └── ...
├── songs/                          # 歌曲文件（共享）
│   ├── 1 流行音乐/
│   └── ...
├── main.py                         # Android 入口
├── buildozer.spec                  # Android 构建配置
├── android_manifest.xml             # Android 清单
├── requirements.txt                 # Python 依赖
├── README.md                        # 主文档
├── QUICK_START.md                   # 快速开始
├── BUILD_GUIDE.md                   # 构建指南
├── DEBUG_GUIDE.md                  # 调试指南
├── .gitignore                      # Git 忽略文件
└── TaikoMini.py                    # 桌面版入口（可选）
```

### 优势

✅ 结构清晰，一目了然  
✅ Buildozer 配置简单（不需要指定子目录）  
✅ 符合标准 Python 项目结构  
✅ GitHub Actions 配置简化  

---

## 🛠️ 执行步骤

### 方案A：自动化脚本（推荐）

```bash
# 1. 备份当前项目
git add .
git commit -m "Backup before restructure"

# 2. 删除重复的根目录文件（保留代码）
# 3. 移动 216 github 的内容到根目录
# 4. 删除 216 github 目录
# 5. 更新 GitHub Actions 配置
# 6. 提交更改
```

### 方案B：手动重构

1. **备份仓库**
2. **将 216 github/ 的所有内容移到根目录**
3. **删除根目录的重复文件**
4. **更新 buildozer.spec**（删除 `source.dir = .` 中的工作目录引用）
5. **更新 GitHub Actions**（删除 `working-directory: 216 github`）
6. **提交更改**

---

## ⚠️ 注意事项

### 1. Git 历史

移动大量文件可能会影响 Git 历史记录。

**选项A：保留历史**
```bash
git mv 216\ github/lib lib
git mv 216\ github/*.* .
```

**选项B：重新开始**
```bash
# 删除 .git，重新初始化
rm -rf .git
git init
git add .
git commit -m "Initial commit after restructure"
```

### 2. 备份

**强烈建议**：先创建一个备份分支
```bash
git checkout -b backup-before-restructure
git push origin backup-before-restructure
```

### 3. 测试

重构后必须测试：
- ✅ GitHub Actions 构建
- ✅ 本地 Python 运行
- ✅ Buildozer 构建

---

## 📋 执行清单

- [ ] 备份当前仓库到新分支
- [ ] 将 `216 github/lib/` 移到根目录
- [ ] 将 `216 github/main.py` 移到根目录
- [ ] 将 `216 github/buildozer.spec` 移到根目录
- [ ] 将其他 Android 文件移到根目录
- [ ] 删除根目录的 `lib/`（避免冲突）
- [ ] 删除 `216 github/` 目录
- [ ] 更新 `buildozer.spec` 配置
- [ ] 更新 `.github/workflows/build-android.yml`
- [ ] 更新文档中的路径引用
- [ ] 测试本地运行
- [ ] 测试 GitHub Actions 构建
- [ ] 提交更改

---

## 🚀 快速执行（自动化）

运行以下 PowerShell 脚本：

```powershell
# 进入仓库根目录
cd D:\temp\py太鼓\TaikoMini

# 备份
git add .
git commit -m "Backup before restructure"

# 创建备份分支
git checkout -b backup-before-restructure
git push origin backup-before-restructure
git checkout main

# 移动文件
Move-Item -Path "216 github\lib" -Destination "lib_new" -Force
Move-Item -Path "216 github\main.py" -Destination "main.py" -Force
Move-Item -Path "216 github\buildozer.spec" -Destination "buildozer.spec" -Force
Move-Item -Item "216 github\*" -Destination "." -Exclude "lib" -Force

# 删除旧目录
Remove-Item -Path "lib" -Recurse -Force
Rename-Item -Path "lib_new" -NewName "lib"

# 删除 216 github 目录
Remove-Item -Path "216 github" -Recurse -Force

# 提交
git add .
git commit -m "Restructure: Move Android project to root directory"
git push origin main
```

---

## 📞 需要帮助？

如果执行过程中遇到问题，可以：
1. 恢复备份分支
2. 查看 Git 历史记录
3. 重新克隆仓库

