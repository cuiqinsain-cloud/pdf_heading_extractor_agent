#!/bin/bash

# PDF标题提取Agent - 快速设置脚本

echo "======================================"
echo "PDF标题提取Agent - 环境设置"
echo "======================================"

# 检查Python版本
echo -e "\n1. 检查Python版本..."
python3 --version

# 激活虚拟环境
echo -e "\n2. 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo -e "\n3. 安装依赖包..."
pip install --upgrade pip
pip install -r requirements.txt

# 创建必要的目录
echo -e "\n4. 创建必要的目录..."
mkdir -p output logs examples prompts cache

# 检查.env文件
echo -e "\n5. 检查环境变量配置..."
if [ ! -f .env ]; then
    echo "  ⚠ .env文件不存在，正在创建..."
    cp .env.example .env
    echo "  → 请编辑 .env 文件，填入你的API密钥"
else
    echo "  ✓ .env文件已存在"
fi

echo -e "\n======================================"
echo "✓ 环境设置完成!"
echo "======================================"

echo -e "\n下一步:"
echo "  1. 编辑 .env 文件，填入API密钥:"
echo "     nano .env"
echo ""
echo "  2. 运行Agent:"
echo "     python main.py your_document.pdf"
echo ""
echo "  3. 查看配置选项:"
echo "     cat config.yaml"
echo ""
echo "详细文档请查看 README.md 和 架构说明.md"
