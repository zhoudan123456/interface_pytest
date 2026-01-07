import pytest
import os
import requests
from conf.set_conf import read_yaml, read_conf, write_conf


class TestUploadDocument:
    @pytest.mark.parametrize('data', read_yaml('../test_data/login.yaml'))
    def test_01_upload_document(self, api, data):
        # 获取文件路径和类型参数
        file_path = data['upload']['files']['file']
        type_param = data['upload']['data']['type']
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            pytest.fail(f"File not found: {file_path}")
        
        # 准备上传文件的数据
        upload_data = {
            'type': type_param
        }
        
        # 准备文件参数
        files = {
            'file': open(file_path, 'rb')
        }
        
        try:
            # 发送上传请求
            res = api.request(
                method=data['upload']['method'],
                path=data['upload']['path'],
                data=upload_data,
                files=files
            )
            
            # 打印响应结果
            print(res.json())
            
            # 验证响应状态码
            assert res.status_code == 200, f"Upload failed with status code: {res.status_code}"
            
            # 提取并保存文档ID用于后续接口
            response_data = res.json()
            if response_data.get('code') == 200 and response_data.get('data'):
                document_id = response_data['data']
                # 保存文档ID到配置文件，供后续接口使用
                write_conf('data', 'document_id', str(document_id))
                print(f"Document ID saved: {document_id}")
            else:
                pytest.fail(f"Upload failed with response: {response_data}")
            
        finally:
            # 确保文件被关闭
            files['file'].close()