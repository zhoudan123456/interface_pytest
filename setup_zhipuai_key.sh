# 设置智谱AI API密钥的环境变量
# Linux/Mac

# 临时设置（仅当前会话有效）
export ZHIPUAI_API_KEY="your-api-key-here"

# 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export ZHIPUAI_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc

# 验证设置
echo $ZHIPUAI_API_KEY
