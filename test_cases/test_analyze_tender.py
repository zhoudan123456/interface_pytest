import os

import pytest
import yaml

from conf.set_conf import read_yaml, read_conf


class TestAnalyzeTender:
    @pytest.mark.parametrize('data', read_yaml('../test_data/login.yaml'))
    def test_analyze_tender_sync(self, api, data):
        """测试解析招标文件接口"""
        # 获取分析招标文件的配置数据
        analyze_tender_data = data['analyze_tender']
        type_param = data['upload']['data']['type']
        print(f"Using type: {type_param}")

        # 从extract.yaml中读取上传后保存的文档ID
        extract_file_path = '../test_data/extract.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                document_id = extract_data.get('document_id') if extract_data else None
        else:
            document_id = None

        # 确保文档ID存在
        assert document_id, "Document ID not found in extract.yaml. Please run upload test first."

        print(f"Using document ID: {document_id}")



        form_data = {
            "tenderId": (None, str(document_id)),
            "type": (None, str(type_param) )
        }
        
        # 发送POST请求，使用form data格式
        res = api.request(
            method=analyze_tender_data['method'],
            path=analyze_tender_data['path'],
            data=form_data
        )
        
        # 打印响应结果
        print("Analyze Tender Response:", res.json())
        
        # 验证响应状态码
        assert res.status_code == 200, f"Analyze tender failed with status code: {res.status_code}, response: {res.json()}"
        



if __name__ == '__main__':
    pytest.main(['-sv'])