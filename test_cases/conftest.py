# conftest.py是文件固定名称，不允许修改。否则不生效。所有的hook函数都是写在conftest之中的。
# ids解析中文，正常显示中文内容的设置定义，通过hook函数来实现。所有代码内容都是固定的，不需要做任何修改
import os
import pathlib

import pytest


from api_keys.api_keys import ApiKeys
from conf.set_conf import write_conf


def pytest_collection_modifyitems(items):
    for item in items:
        item.name = item.name.encode('utf-8').decode('unicode_escape')
        item._nodeid = item._nodeid.encode('utf-8').decode('unicode_escape')




@pytest.fixture(scope="session")
def api(request):
    api = ApiKeys('Test_Env')
    yield api


@pytest.fixture()
def clean_test_data(request):
    """Fixture to clean up test data after test execution"""
    def cleanup():
        # 清理测试数据
        write_conf('data', 'document_id', '')
        print("Test data cleaned up")
    
    request.addfinalizer(cleanup)
    return cleanup


@pytest.fixture()
def api_teardown(request):
    def api_teardown_finalizer():
        write_conf('data','token','')
        write_conf('data','user_id','')
        write_conf('data', 'cookie', '')



    request.addfinalizer(api_teardown_finalizer)

@pytest.fixture(autouse=True)  # autouse=True 表示自动使用，无需在测试函数中声明
def clear_extract_data():
    """在每个测试开始前，自动清空存储临时参数的extract.yaml文件。"""
    file_path = pathlib.Path(__file__).parents[1].resolve() / 'test_data/extract.yaml'
    # 测试开始前 (setup)
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"已清理旧数据文件: {file_path}")
    yield  # 在这里暂停，执行测试函数
    # 测试结束后 (teardown) 如果需要也可以做清理
    # print("测试完毕")