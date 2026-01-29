import pytest
from api_keys.api_keys import ApiKeys
from conf.set_conf import write_conf, read_yaml, write_yaml
import os


class TestLogin:
    @pytest.mark.parametrize('data', read_yaml('./test_data/login.yaml'))
    @pytest.mark.login
    @pytest.mark.priority_P0
    def test_01_login(self, api, data):
        # 发送登录请求
        res = api.request(save_cookie=True, **data['login'])
        
        # 提取token
        access_token = api.get_values(res.json(), 'access_token')
        if access_token:
            # 保存token到extract.yaml文件
            token_data = {'token': str(access_token)}
            write_yaml('./test_data/extract.yaml', token_data)

        

    



if __name__ == '__main__':
    pytest.main(['-sv'])