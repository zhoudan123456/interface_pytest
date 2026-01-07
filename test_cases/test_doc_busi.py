import json
import os
import time

import pytest
import requests
import yaml
from deepmerge import Merger

from conf.set_conf import read_yaml
from test_data.config import base_payload, API_URL

# 初始化合并器（配置合并规则）

merger = Merger(
   [(dict, "override")],  # 字典类型：合并
   ["override"],       # 列表类型：覆盖（如需合并列表，可改为"append"）
   ["override"]        # 其他类型：覆盖
)

def merge_payload(base: dict, update: dict) -> dict:
   """合并基础payload和测试用例payload"""
   return merger.merge(base.copy(), update)  # 复制base，避免修改原基础payload

def merge(base, update):
    base_copy = base.copy()
    base_copy.update(update)
    return base_copy







@pytest.mark.parametrize(
    "test_case",
    read_yaml("../test_data/doc_busi_1.yaml"),  # 数据源：YAML文件中的测试用例
    ids=[case["case_name"] for case in read_yaml("../test_data/doc_busi_1.yaml")]  # 用例名称（测试报告中显示）
)
def test_generate_document(test_case: dict):
    """测试文档生成接口，验证task_id返回逻辑"""
    # 1. 解析测试用例数据
    case_name = test_case["case_name"]
    payload_update = {
        "文档": test_case["payload"]
    }
    # payload_update = test_case["payload"]
    # expected_status = test_case["expected_status"]
    # expect_task_id = test_case.get("expect_task_id", False)
    # expected_msg = test_case.get("expected_msg", "")

    # 2. 合并基础payload与场景payload（保留固定部分，更新变化部分）
    merged_payload = merge(base_payload, payload_update)
    # merged_payload = merger.merge(base_payload.copy(), payload_update)

    # 3. 发送POST请求（模拟Postman，自动设置Content-Type: application/json）
    try:
        response = requests.post(
            url=API_URL + "/generate_document?type=busi_gen" ,
            json=merged_payload,
            timeout=10  # 超时时间（防止无限等待）
        )
    except requests.exceptions.Timeout:
        pytest.fail(f"用例[{case_name}]失败：请求超时（超过10秒）")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"用例[{case_name}]失败：请求异常 - {str(e)}")

    # 4. 打印调试信息（可选，方便排查问题）
    print(f"\n=== 用例名称: {case_name} ===")
    print(f"请求URL: {API_URL}")
    print(f"请求payload: {merged_payload}")
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.text}")

    # 5. 断言响应状态码（必选）
    # assert response.status_code == expected_status, \
    #     f"用例[{case_name}]失败：状态码不符，期望{expected_status}，实际{response.status_code}"

    # 6. 断言响应内容类型为JSON（必选，确保接口返回JSON格式）
    assert "application/json" in response.headers.get("Content-Type", ""), \
        f"用例[{case_name}]失败：响应内容类型不是JSON（当前为{response.headers.get('Content-Type')}）"

    # 7. 解析响应JSON（处理可能的JSON解析错误）
    try:
        response_json = response.json()
    except ValueError:
        pytest.fail(f"用例[{case_name}]失败：响应内容不是有效的JSON - {response.text}")

    # 8. 断言task_id存在性（核心逻辑）
    try:

        task_id = response_json["task_id"]
    except (json.JSONDecodeError, KeyError) as e:
        print(f"解析任务ID失败: {str(e)}")
        return None

    # 正常场景：断言存在task_id且不为空
    assert "task_id" in response_json, \
        f"用例[{case_name}]失败：成功场景未返回task_id"
    assert isinstance(response_json["task_id"], str), \
        f"用例[{case_name}]失败：task_id不是字符串类型（当前为{type(response_json['task_id'])}）"
    assert len(response_json["task_id"]) > 0, \
        f"用例[{case_name}]失败：task_id为空字符串"

    # 遍历场景，获取task_id并关联case_name



    # 8. 尝试解析task_id并保存到yaml文件中，供后续接口测试使用
    test_cases = []
    test_cases.append({"case_name": case_name, "task_id": task_id})
    """将测试用例（case_name+task_id）写入YAML文件"""
    with open("../test_data/task_ids.yaml", "a", encoding="utf-8") as f:
        yaml.dump(
            test_cases,
            f,
            default_flow_style=False,  # 禁用流式格式（保持块格式，更易读）
            allow_unicode=True,  # 允许 Unicode 字符（如中文case_name）
            indent=2 ) # 缩进2个空格（YAML标准风格）

        # try:
    #     task_id = response_json["task_id"]
    #     with open("../test_data/task_ids.yaml", "a") as file:
    #         yaml.dump([task_id], file)
    # except (json.JSONDecodeError, KeyError) as e:
    #     print(f"解析任务ID失败: {str(e)}")
    #     return None


    # assert "task_id" not in response_json, \
    #     f"用例[{case_name}]失败：异常场景返回了task_id（当前task_id为{response_json.get('task_id')}）"

    # # 9. 断言响应错误信息（可选，针对异常场景）
    # if expected_msg:
    #     assert "msg" in response_json, \
    #         f"用例[{case_name}]失败：响应中没有msg字段"
    #     assert expected_msg in response_json["msg"], \
    #         f"用例[{case_name}]失败：响应信息不符，期望包含'{expected_msg}'，实际为'{response_json['msg']}'"

    # # 循环检查状态
    # while True:
    #     check_state_url = API_URL + f"/status/{task_id}"
    #     check_state_response = requests.get(check_state_url)
    #     check_state_response.raise_for_status()  # 检查HTTP请求是否成功（状态码200）
    #     check_state_data = check_state_response.json()
    #     check_state = check_state_data.get("status")
    #     if check_state == "completed":
    #         break
    #     # 等待一分钟
    #     print(f"任务 {task_id} 正在处理中")
    #     time.sleep(60)
    #
    # doc_download_url = API_URL+ f"/download/{task_id}"
    # download_response = requests.get(doc_download_url, stream=True)  # 使用stream模式处理大文件
    # download_response.raise_for_status()
    #
    # save_path = './download/'
    # os.makedirs(save_path, exist_ok=True)  # 自动创建目录（若不存在）
    # file_name = f"{task_id}.docx"  # 可根据需求修改文件名规则
    # save_file_path = os.path.join(save_path, file_name)
    #
    # with open(save_file_path, "wb") as f:
    #     for chunk in download_response.iter_content(chunk_size=8192):  # 分块写入（适合大文件）
    #         if chunk:  # 过滤空块
    #             f.write(chunk)
    #
    # print(f"文件保存成功，路径: {save_file_path}")
    # return save_file_path




if __name__ == '__main__':
    pytest.main(['-sv'])

