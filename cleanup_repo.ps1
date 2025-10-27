# GitHub 仓库清理脚本
# PowerShell 脚本

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "GitHub 仓库清理脚本" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查当前目录
$currentDir = Get-Location
Write-Host "当前目录: $currentDir" -ForegroundColor Yellow

# 2. 确认执行
Write-Host ""
Write-Host "此脚本将执行以下操作:" -ForegroundColor Yellow
Write-Host "  1. 备份当前 Git 状态" -ForegroundColor White
Write-Host "  2. 将 216 github/ 目录内容移到根目录" -ForegroundColor White
Write-Host "  3. 删除重复文件" -ForegroundColor White
Write-Host "  4. 清理 216 github/ 目录" -ForegroundColor White
Write-Host "  5. 更新 GitHub Actions 配置" -ForegroundColor White
Write-Host ""
$confirm = Read-Host "是否继续? (Y/N)"

if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "操作已取消" -ForegroundColor Red
    exit
}

# 3. 备份
Write-Host ""
Write-Host "正在备份..." -ForegroundColor Green
git add .
git commit -m "Backup before cleanup" 2>&1 | Out-Null
Write-Host "✓ 备份完成" -ForegroundColor Green

# 4. 创建备份分支
Write-Host ""
Write-Host "正在创建备份分支..." -ForegroundColor Green
git checkout -b backup-before-cleanup 2>&1 | Out-Null
git push origin backup-before-cleanup 2>&1 | Out-Null
git checkout main 2>&1 | Out-Null
Write-Host "✓ 备份分支已创建: backup-before-cleanup" -ForegroundColor Green

# 5. 检查是否需要移动文件
Write-Host ""
Write-Host "正在分析文件结构..." -ForegroundColor Green

$has216Dir = Test-Path "216 github"
$hasLibInRoot = Test-Path "lib"
$hasMainIn216 = Test-Path "216 github\main.py"

if ($has216Dir -and $hasMainIn216) {
    Write-Host "✓ 需要清理" -ForegroundColor Yellow
    
    # 移动 lib 目录
    if (Test-Path "216 github\lib") {
        Write-Host "  移动 lib/ 目录..." -ForegroundColor White
        if (Test-Path "lib") {
            Remove-Item -Path "lib" -Recurse -Force
        }
        Move-Item -Path "216 github\lib" -Destination "lib" -Force
        Write-Host "  ✓ lib/ 已移动" -ForegroundColor Green
    }
    
    # 移动其他文件
    Write-Host "  移动其他文件..." -ForegroundColor White
    $filesToMove = @(
        "main.py",
        "buildozer.spec",
        "android_manifest.xml",
        "requirements.txt",
        "README.md",
        "QUICK_START.md",
        "BUILD_GUIDE.md",
        "DEBUG_GUIDE.md",
        "FIX_SUMMARY.md",
        "test_android_compatibility.py",
        "parse_tja.py",
        "TaikoMini.py",
        "run.bat"
    )
    
    foreach ($file in $filesToMove) {
        $sourcePath = "216 github\$file"
        if (Test-Path $sourcePath) {
            # 如果根目录已有此文件，备份旧文件
            if (Test-Path $file) {
                Copy-Item -Path $file -Destination "$file.backup" -Force
            }
            Move-Item -Path $sourcePath -Destination $file -Force
            Write-Host "  ✓ $file" -ForegroundColor Green
        }
    }
    
    # 移动 res 目录
    if (Test-Path "216 github\res") {
        if (Test-Path "res") {
            Remove-Item -Path "res" -Recurse -Force
        }
        Move-Item -Path "216 github\res" -Destination "res" -Force
        Write-Host "  ✓ res/ 已移动" -ForegroundColor Green
    }
    
    # 移动 taikomini 目录
    if (Test-Path "216 github\taikomini") {
        if (Test-Path "taikomini") {
            Remove-Item -Path "taikomini" -Recurse -Force
        }
        Move-Item -Path "216 github\taikomini" -Destination "taikomini" -Force
        Write-Host "  ✓ taikomini/ 已移动" -ForegroundColor Green
    }
    
    # 删除 216 github 目录
    Write-Host ""
    Write-Host "删除 216 github/ 目录..." -ForegroundColor Yellow
    Remove-Item -Path "216 github" -Recurse -Force
    Write-Host "✓ 已删除" -ForegroundColor Green
    
} else {
    Write-Host "✓ 文件结构看起来已经是正确的" -ForegroundColor Green
}

# 6. 更新 GitHub Actions
Write-Host ""
Write-Host "更新 GitHub Actions 配置..." -ForegroundColor Green

$workflowFile = ".github\workflows\build-android.yml"
if (Test-Path $workflowFile) {
    $content = Get-Content $workflowFile -Raw
    
    # 删除 working-directory: 216 github
    $content = $content -replace "working-directory: 216 github", "working-directory: ."
    $content = $content -replace 'path: 216 github/build\.log', 'path: build.log'
    $content = $content -replace 'path: 216 github/\.buildozer', 'path: .buildozer'
    
    Set-Content -Path $workflowFile -Value $content -NoNewline
    Write-Host "✓ GitHub Actions 已更新" -ForegroundColor Green
}

# 7. 清理备份文件
Write-Host ""
Write-Host "清理备份文件..." -ForegroundColor Green
Get-ChildItem -Filter "*.backup" | Remove-Item -Force
Write-Host "✓ 已清理" -ForegroundColor Green

# 8. 显示状态
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "清理完成！" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步操作:" -ForegroundColor Yellow
Write-Host "  1. 检查文件: git status" -ForegroundColor White
Write-Host "  2. 提交更改: git add . && git commit -m 'Clean up repository structure'" -ForegroundColor White
Write-Host "  3. 推送到 GitHub: git push origin main" -ForegroundColor White
Write-Host ""
Write-Host "如有问题，可恢复到备份分支:" -ForegroundColor Yellow
Write-Host "  git checkout backup-before-cleanup" -ForegroundColor White
Write-Host ""

