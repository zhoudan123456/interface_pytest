import pytest
from conf.set_conf import read_yaml, read_conf


class TestAnalyzeTender:
    @pytest.mark.parametrize('data', read_yaml('../test_data/login.yaml'))
    def test_analyze_tender_sync(self, api, data):
        """测试解析招标文件接口"""
        # 获取分析招标文件的配置数据
        analyze_tender_data = data['analyze_tender']
        type_param = data['upload']['data']['type']

        # 从配置中读取上传后保存的文档ID
        document_id = read_conf('data', 'document_id')

        # 确保文档ID存在
        assert document_id, "Document ID not found. Please run upload test first."

        print(f"Using document ID: {document_id}")


        # 准备上传文件的数据
        form_data  = {
            'type': type_param,
            'tenderId': f"{document_id}"
        }
        
        # 发送POST请求
        res = api.request(
            method=analyze_tender_data['method'],
            path=analyze_tender_data['path'],
            data=form_data
        )
        
        # 打印响应结果
        print("Analyze Tender Response:", res.json())
        
        # 验证响应状态码
        assert res.status_code == 200, f"Analyze tender failed with status code: {res.status_code}"
        



if __name__ == '__main__':
    pytest.main(['-sv'])