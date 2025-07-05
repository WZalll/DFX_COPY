#!/bin/bash
# GitHub上传脚本

echo "=== DXF项目上传到GitHub ==="
echo "仓库地址: https://github.com/WZalll/DFX_COPY"
echo ""

# 检查文件是否存在
echo "检查核心文件..."
if [ -f "dxf_parser.py" ]; then
    echo "✅ dxf_parser.py 存在"
else
    echo "❌ dxf_parser.py 不存在"
    exit 1
fi

if [ -f "README.md" ]; then
    echo "✅ README.md 存在"
else
    echo "❌ README.md 不存在"
    exit 1
fi

# Git操作
echo ""
echo "执行Git操作..."

# 初始化仓库（如果需要）
if [ ! -d ".git" ]; then
    echo "初始化Git仓库..."
    git init
    git remote add origin https://github.com/WZalll/DFX_COPY.git
fi

# 添加文件
echo "添加文件到Git..."
git add dxf_parser.py README.md vSDK.py vSDK_ShapeTools.py requirements.txt .gitignore

# 提交
echo "提交更改..."
git commit -m "更新DXF解析器项目"

# 推送
echo "推送到GitHub..."
echo "注意：如果需要认证，请输入GitHub用户名和个人访问令牌"
git push -u origin main

echo ""
echo "=== 上传完成 ==="
echo "项目地址: https://github.com/WZalll/DFX_COPY"
