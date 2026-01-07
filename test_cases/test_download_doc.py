import os
import time

import pytest
import requests

from conf.set_conf import read_yaml
from test_data.config import API_URL

completed_count = 0
failed_count = 0

@pytest.mark.parametrize(
    "test_case",
    read_yaml("../test_data/task_ids.yaml"),  # 数据源：YAML文件中的测试用例
    ids=[case["case_name"] for case in read_yaml("../test_data/task_ids.yaml")]  # 用例名称（测试报告中显示）

)
def test_download_doc(test_case):
    task_id = test_case["task_id"]
    # 循环检查状态
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

    # completed_count = 0
    # failed_count = 0

    while True:
        check_state_url = API_URL + f"/status/{task_id}"
        check_state_response = requests.get(check_state_url)
        try:
            check_state_response.raise_for_status()  # 检查HTTP请求是否成功（状态码200）
            check_state_data = check_state_response.json()
            check_state = check_state_data.get("status")

            if check_state == "completed":
                global completed_count
                completed_count += 1
                break
            elif check_state == "failed":
                global failed_count
                failed_count += 1
                print(f"任务 {task_id} 处理失败")
                break
            else:
                print(f"任务 {task_id} 正在处理中")
                time.sleep(60)
        except requests.exceptions.HTTPError as err:
            print(f"HTTP请求错误: {err}")
            failed_count += 1
            break

    if completed_count > 0:
        print(f"共有 {completed_count} 个任务完成")
    if failed_count > 0:
        print(f"共有 {failed_count} 个任务失败")

    doc_download_url = API_URL+ f"/download/{task_id}"
    download_response = requests.get(doc_download_url, stream=True)  # 使用stream模式处理大文件
    download_response.raise_for_status()

    save_path = './download/'
    os.makedirs(save_path, exist_ok=True)  # 自动创建目录（若不存在）
    file_name = f"{task_id}.docx"  # 可根据需求修改文件名规则
    save_file_path = os.path.join(save_path, file_name)

    with open(save_file_path, "wb") as f:
        for chunk in download_response.iter_content(chunk_size=8192):  # 分块写入（适合大文件）
            if chunk:  # 过滤空块
                f.write(chunk)

    print(f"文件保存成功，路径: {save_file_path}")
    # return save_file_path

if __name__ == '__main__':
    pytest.main(['-sv'])