@echo off
echo === DXF项目上传到GitHub ===
echo 仓库地址: https://github.com/WZalll/DFX_COPY
echo.

echo 检查核心文件...
if exist "dxf_parser.py" (
    echo ✅ dxf_parser.py 存在
) else (
    echo ❌ dxf_parser.py 不存在
    pause
    exit /b 1
)

if exist "README.md" (
    echo ✅ README.md 存在
) else (
    echo ❌ README.md 不存在
    pause
    exit /b 1
)

echo.
echo 执行Git操作...

rem 检查是否已初始化Git
if not exist ".git" (
    echo 初始化Git仓库...
    git init
    git remote add origin https://github.com/WZalll/DFX_COPY.git
)

rem 添加文件
echo 添加文件到Git...
git add dxf_parser.py README.md vSDK.py vSDK_ShapeTools.py requirements.txt .gitignore

rem 提交
echo 提交更改...
git commit -m "更新DXF解析器项目"

rem 推送
echo 推送到GitHub...
echo 注意：如果需要认证，请输入GitHub用户名和个人访问令牌
git push -u origin main

echo.
echo === 上传完成 ===
echo 项目地址: https://github.com/WZalll/DFX_COPY
pause
