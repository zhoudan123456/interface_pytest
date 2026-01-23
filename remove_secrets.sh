# 清除敏感信息的脚本

echo "🔧 步骤1：备份当前 extract.yaml（如果需要保留数据）"
cp test_data/extract.yaml test_data/extract.yaml.backup

echo "🗑️  步骤2：清空 extract.yaml 中的敏感数据"
# 创建一个空的 extract.yaml，只保留基本结构
cat > test_data/extract.yaml << 'EOF'
# 这是一个临时数据存储文件，会被 git 忽略
# 实际数据从测试接口中动态获取
token: ""
user_id: ""
document_id: ""
company_id: ""
cookie: ""
EOF

echo "📝 步骤3：将 extract.yaml 添加到 .gitignore"
if ! grep -q "extract.yaml" .gitignore; then
    echo "test_data/extract.yaml" >> .gitignore
    echo "test_data/bid_generate.yaml" >> .gitignore
    echo "test_data/*.yaml" >> .gitignore
fi

echo "✅ 步骤4：提交更改"
git add test_data/extract.yaml
git add .gitignore
git commit -m "chore: 移除敏感信息，清空 extract.yaml"

echo "🧹 步骤5：使用 git filter-branch 从历史记录中删除敏感文件"
# 从所有历史记录中删除 extract.yaml 的敏感内容
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch test_data/extract.yaml' \
  --prune-empty HEAD

echo "🚀 步骤6：强制推送（清理历史后需要强制推送）"
git push origin main --force

echo "✨ 完成！敏感信息已清除"
