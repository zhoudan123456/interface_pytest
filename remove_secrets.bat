@echo off
echo 🔧 正在清除敏感信息...

REM 步骤1：备份当前文件（可选）
copy test_data\extract.yaml test_data\extract.yaml.backup
copy test_data\bid_generate.yaml test_data\bid_generate.yaml.backup

REM 步骤2：清空 extract.yaml 中的敏感数据
echo token: > test_data\extract.yaml
echo user_id: >> test_data\extract.yaml
echo document_id: >> test_data\extract.yaml
echo company_id: >> test_data\extract.yaml
echo cookie: >> test_data\extract.yaml

REM 步骤3：清空 bid_generate.yaml 中的敏感数据
echo. > test_data\bid_generate.yaml

REM 步骤4：添加到 .gitignore
echo test_data/extract.yaml >> .gitignore
echo test_data/bid_generate.yaml >> .gitignore
echo test_data/*.yaml >> .gitignore

echo ✅ 已完成敏感信息清除
echo 📝 请运行以下命令提交更改：
echo    git add test_data/extract.yaml test_data/bid_generate.yaml .gitignore
echo    git commit -m "chore: 移除敏感信息"
echo    git push origin main
