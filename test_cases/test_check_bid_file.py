import pytest
from conf.set_conf import read_yaml, read_conf, write_conf, read_yaml as read_yaml_util
import yaml
import os


class TestCheckBidFile:
    @pytest.mark.parametrize('data', read_yaml('./test_data/login.yaml'))
    def test_check_bid_file(self, api, data):
        """检查招标文件"""
        # 从extract.yaml中读取上传后保存的文档ID
        extract_file_path = './test_data/extract.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                document_id = extract_data.get('document_id') if extract_data else None
        else:
            document_id = None

        # 确保文档ID存在
        assert document_id, "Document ID not found in extract.yaml. Please run upload test first."

        print(f"Using document ID: {document_id}")

        query_params = {
            "tenderId": f"{document_id}"
        }

        # 获取检查投标文件的配置数据
        check_bid_data = data['check_bid_file']
        
        # 发送GET请求
        res = api.request(
            method=check_bid_data['method'],
            path=check_bid_data['path'],
            params=query_params
        )
        
        # 打印响应结果
        print("Check Bid File Response:", res.json())
        
        # 验证响应状态码
        assert res.status_code == 200, f"Check bid file failed with status code: {res.status_code}"
        


if __name__ == '__main__':
    pytest.main(['-sv'])