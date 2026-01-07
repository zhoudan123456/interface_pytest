import pytest
from conf.set_conf import read_yaml, read_conf


class TestCheckBidFile:
    @pytest.mark.parametrize('data', read_yaml('../test_data/login.yaml'))
    def test_check_bid_file(self, api, data):
        """检查投标文件"""
        # 从配置中读取上传后保存的文档ID
        document_id = read_conf('data', 'document_id')

        # 确保文档ID存在
        assert document_id, "Document ID not found. Please run upload test first."

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