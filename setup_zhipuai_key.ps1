# 设置智谱AI API密钥的环境变量
# Windows PowerShell

# 临时设置（仅当前会话有效）
$env:ZHIPUAI_API_KEY = "your-api-key-here"

# 永久设置（需要管理员权限）
[System.Environment]::SetEnvironmentVariable('ZHIPUAI_API_KEY', 'your-api-key-here', 'User')

# 验证设置
echo $env:ZHIPUAI_API_KEY
