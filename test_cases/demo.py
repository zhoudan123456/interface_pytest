import unittest

import pytest


from api_keys.api_keys import ApiKeys
from conf.set_conf import write_conf, read_conf, read_yaml


# @ddt
# class TestBlackCore(unittest.TestCase):
#     @classmethod
#     def setUpClass(cls):
#         cls.api = ApiKeys('Test_Env')
#
#     @file_data('../test_data/login.yaml')
#     def test_01_login(self, **kwargs):
#         res = self.api.request(**kwargs['login'])
#         print(res.json())
#
#         write_conf('data', 'token', self.api.get_values(res.json(), 'token'))
#
#     @file_data('../test_data/login.yaml')
#     def test_02_userInfo(self,**kwargs):
#         res = self.api.request(**kwargs['user_info'])
#         print(res.json())
#         write_conf('data','user_id',str(self.api.get_values(res.json(),'user_id')))
#
#     @file_data('../test_data/login.yaml')
#     def test_03_add_balance(self,**kwargs):
#         kwargs['add_balance']['json']['user_id'] = read_conf('data','user_id')
#         res = self.api.request(**kwargs['add_balance'])

class TestBlackCore:
    @pytest.mark.parametrize('data',read_yaml('../test_data/login.yaml'))
    def test_01_login(self, api,data):
        res = api.request(**data['login'])
        print(res.json())
        write_conf('data', 'token', str(api.get_values(res.json(), 'token')))

    @pytest.mark.parametrize('data', read_yaml('../test_data/login.yaml'))
    def test_02_userInfo(self, data, api,api_teardown):
        res = api.request(**data['user_info'])
        print(res.json())
        write_conf('data','user_id',str(api.get_values(res.json(),'user_id')))






if __name__ == '__main__':
    pytest.main(['-sv'])

