# 清理 GitHub 仓库结构 - 执行说明

## 🎯 目标

清理混乱的文件结构，将所有 Android 项目文件移到仓库根目录。

---

## 📋 已完成的准备工作

✅ 创建了重构计划文档：`216 github/RESTRUCTURE_PLAN.md`  
✅ 创建了自动化清理脚本：`cleanup_repo.ps1`  
✅ 更新了 GitHub Actions 配置  

---

## 🚀 执行清理（推荐方案）

### 方法1：使用自动化脚本（最简单）

```powershell
# 在仓库根目录运行
.\cleanup_repo.ps1
```

脚本会自动执行：
1. 备份当前状态
2. 创建备份分支
3. 移动文件
4. 更新配置
5. 清理临时文件

### 方法2：手动执行

```powershell
# 1. 进入仓库根目录
cd D:\temp\py太鼓\TaikoMini

# 2. 备份
git add .
git commit -m "Backup before cleanup"
git checkout -b backup-before-cleanup
git push origin backup-before-cleanup
git checkout main

# 3. 移动 lib 目录
if (Test-Path "lib") { Remove-Item -Path "lib" -Recurse -Force }
Move-Item -Path "216 github\lib" -Destination "lib" -Force

# 4. 移动主要文件
Move-Item -Path "216 github\main.py" -Destination "main.py" -Force
Move-Item -Path "216 github\buildozer.spec" -Destination "buildozer.spec" -Force
Move-Item -Path "216 github\android_manifest.xml" -Destination "android_manifest.xml" -Force
Move-Item -Path "216 github\requirements.txt" -Destination "requirements.txt" -Force
Move-Item -Path "216 github\README.md" -Destination "README.md" -Force

# 5. 移动文档
Move-Item -Path "216 github\*.md" -Destination "." -Force

# 6. 移动其他目录
if (Test-Path "res") { Remove-Item -Path "res" -Recurse -Force }
Move-Item -Path "216 github\res" -Destination "res" -Force

if (Test-Path "taikomini") { Remove-Item -Path "taikomini" -Recurse -Force }
Move-Item -Path "216 github\taikomini" -Destination "taikomini" -Force

# 7. 删除 216 github 目录
Remove-Item -Path "216 github" -Recurse -Force

# 8. 提交更改
git add .
git commit -m "Clean up repository structure"
git push origin main
```

---

## ✅ 清理后的结构

```
TaikoMini/                    # GitHub 仓库根目录
├── .github/
│   └── workflows/
│       └── build-android.yml
├── lib/                      # 游戏库
│   ├── __init__.py
│   ├── game.py
│   ├── audio.py
│   ├── res/                  # 资源文件
│   └── ...
├── songs/                    # 歌曲文件
├── taikomini/               # Android 特定资源
├── main.py                  # Android 入口
├── buildozer.spec           # Android 构建配置
├── android_manifest.xml      # Android 清单
├── requirements.txt          # Python 依赖
├── README.md                 # 主文档
├── QUICK_START.md
├── BUILD_GUIDE.md
├── DEBUG_GUIDE.md
└── .gitignore
```

---

## 🔍 验证清理结果

```powershell
# 1. 检查文件结构
ls

# 2. 检查 Git 状态
git status

# 3. 确认没有 216 github 目录
Test-Path "216 github"  # 应该返回 False

# 4. 确认主要文件在根目录
Test-Path "main.py"      # 应该返回 True
Test-Path "buildozer.spec" # 应该返回 True
Test-Path "lib"          # 应该返回 True
```

---

## 🧪 测试

### 1. 测试本地运行

```bash
python main.py
```

### 2. 测试 GitHub Actions

```bash
# 推送代码
git push origin main

# 在 GitHub 上触发构建
# 访问 Actions 标签页
```

---

## ⚠️ 如果需要恢复

```powershell
# 恢复备份分支
git checkout backup-before-cleanup

# 或恢复最后一个提交
git reset --hard HEAD~1
```

---

## 📝 注意事项

1. **备份很重要**：脚本会自动创建备份分支
2. **一次执行**：清理操作是一次性的
3. **测试构建**：清理后测试 GitHub Actions 构建
4. **文档更新**：如果有硬编码路径的文档，需要更新

---

## 🎉 清理完成后的好处

✅ 清晰的文件结构  
✅ 简单的构建配置  
✅ 标准 Python 项目布局  
✅ 更容易维护  
✅ 更快的构建速度  

---

## 📞 需要帮助？

如果遇到问题：
1. 查看备份分支：`git checkout backup-before-cleanup`
2. 查看重构计划：`216 github/RESTRUCTURE_PLAN.md`
3. 重新克隆仓库

