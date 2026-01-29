"""
招标文件检查工作流测试
流程：上传文件 -> 启动检查任务 -> 检查检查点 -> 查询状态 -> 获取投标信息
"""
import json
import os
import time
import uuid
import pytest
import yaml
from datetime import datetime

from conf.set_conf import read_yaml, write_yaml


class TestBidCheckWorkflow:
    """招标文件检查工作流测试"""

    def _save_response_for_evaluation(self, response_type: str, response_data: dict):
        """
        保存API响应数据用于后续评估

        Args:
            response_type: 响应类型 ('check_point' 或 'bid_info')
            response_data: 响应数据字典
        """
        output_dir = './test_data/evaluation/responses'
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{response_type}_response_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(response_data, f, ensure_ascii=False, indent=2)

        print(f"✓ 响应已保存到: {filepath}")
        return filepath

    def test_01_upload_documents(self, api):
        """
        步骤1: 上传招标文件和投标文件
        接口: POST /prod-api/backend/bidCheck/upload
        """
        print("\n" + "=" * 60)
        print("步骤1: 上传文件（招标文件 + 投标文件）")
        print("=" * 60)

        # 加载测试配置
        with open('./test_data/bid_check_workflow.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 上传招标文件
        print("\n--- 上传招标文件 ---")
        zb_file_path = config['zb_upload']['files']['file']
        zb_type = config['zb_upload']['data']['type']

        if not os.path.exists(zb_file_path):
            pytest.fail(f"招标文件不存在: {zb_file_path}")

        print(f"招标文件路径: {zb_file_path}")
        print(f"文件类型: {zb_type}")

        zb_upload_data = {'type': zb_type}
        zb_files = {'file': open(zb_file_path, 'rb')}

        try:
            zb_res = api.request(
                method=config['zb_upload']['method'],
                path=config['zb_upload']['path'],
                # data=zb_upload_data,
                files=zb_files
            )

            print(f"状态码: {zb_res.status_code}")
            zb_response_data = zb_res.json()
            print(f"响应内容: {zb_response_data}")

            assert zb_res.status_code == 200, f"招标文件上传失败: {zb_res.status_code}"

            if zb_response_data.get('code') == 200 and zb_response_data.get('data'):
                zb_data = zb_response_data['data']
                zb_file_name = zb_data.get('fileName', '')
                zb_upload_url = zb_data.get('uploadUrl', '')

                print(f"✓ 招标文件名: {zb_file_name}")
                print(f"✓ 招标文件URL: {zb_upload_url}")

                # 保存招标文件信息
                config['zb_file_name'] = zb_file_name
                config['zb_upload_url'] = zb_upload_url
            else:
                pytest.fail(f"招标文件上传失败: {zb_response_data}")
        finally:
            zb_files['file'].close()

        # 上传投标文件
        print("\n--- 上传投标文件 ---")
        tb_file_path = config['tb_upload']['files']['file']
        tb_type = config['tb_upload']['data']['type']

        if not os.path.exists(tb_file_path):
            pytest.fail(f"投标文件不存在: {tb_file_path}")

        print(f"投标文件路径: {tb_file_path}")
        print(f"文件类型: {tb_type}")

        tb_upload_data = {'type': tb_type}
        tb_files = {'file': open(tb_file_path, 'rb')}

        try:
            tb_res = api.request(
                method=config['tb_upload']['method'],
                path=config['tb_upload']['path'],
                # data=tb_upload_data,
                files=tb_files
            )

            print(f"状态码: {tb_res.status_code}")
            tb_response_data = tb_res.json()
            print(f"响应内容: {tb_response_data}")

            assert tb_res.status_code == 200, f"投标文件上传失败: {tb_res.status_code}"

            if tb_response_data.get('code') == 200 and tb_response_data.get('data'):
                tb_data = tb_response_data['data']
                tb_file_name = tb_data.get('fileName', '')
                tb_upload_url = tb_data.get('uploadUrl', '')

                print(f"✓ 投标文件名: {tb_file_name}")
                print(f"✓ 投标文件URL: {tb_upload_url}")

                # 保存投标文件信息
                config['tb_file_name'] = tb_file_name
                config['tb_upload_url'] = tb_upload_url

                # 保存所有上传信息到配置文件
                write_yaml('./test_data/bid_check_workflow.yaml', config)
                print(f"\n✓ 所有文件上传信息已保存")
            else:
                pytest.fail(f"投标文件上传失败: {tb_response_data}")
        finally:
            tb_files['file'].close()

    

    def test_02_refresh_token(self, api):
        """
        步骤2: 刷新Token
        接口: POST /prod-api/auth/refresh
        """
        print("\n" + "=" * 60)
        print("步骤2: 刷新Token")
        print("=" * 60)

        # 发送刷新token请求
        res = api.request(
            method='POST',
            path='/prod-api/auth/refresh',
            json={}
        )

        # 打印响应结果
        print(f"状态码: {res.status_code}")
        print(f"响应内容: {res.json()}")

        # 验证响应状态码
        assert res.status_code == 200, f"Refresh token failed with status code: {res.status_code}"

        # 验证响应数据
        response_data = res.json()
        if response_data.get('code') == 200:
            print("✓ Token刷新成功")
        else:
            print(f"⚠ Token刷新响应: {response_data}")

    def test_03_start_check_task(self, api):
        """
        步骤3: 启动检查任务
        接口: POST /prod-api/check/check/task/start
        """
        print("\n" + "=" * 60)
        print("步骤3: 启动检查任务")
        print("=" * 60)

        # 加载测试配置
        with open('./test_data/bid_check_workflow.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 从配置文件中读取上传信息
        zb_file_name = config.get('zb_file_name', '')
        zb_upload_url = config.get('zb_upload_url', '')
        tb_file_name = config.get('tb_file_name', '')
        tb_upload_url = config.get('tb_upload_url', '')

        if not zb_upload_url or not tb_upload_url:
            pytest.skip("Upload URLs not found. Please run test_01_upload_documents first.")

        print(f"招标文件名: {zb_file_name}")
        print(f"招标文件URL: {zb_upload_url}")
        print(f"投标文件名: {tb_file_name}")
        print(f"投标文件URL: {tb_upload_url}")

        # 准备zbFiles（招标文件）
        zb_files = {
            "zb_dir": {
                "fileName": zb_file_name,
                "fileUrl": zb_upload_url,
                "fileId": str(uuid.uuid4())
            },
            "gc_dir": {},
            "other_dir": []
        }

        # 准备tbFiles（投标文件）
        tb_files = [
            {
                "company_name": "投标单位一",
                "tb_dir": {
                    "fileName": tb_file_name,
                    "fileUrl": tb_upload_url,
                    "fileId": str(uuid.uuid4())
                },
                "sw_dir": {},
                "bj_dir": {},
                "other_file_dir": []
            }
        ]

        # 准备rules（规则配置）
        rules = {
            "file_sim_value": 0.01,
            "conmmon_text_length": 20,
            "has_err_or_has_special_chars": 1,
            "exclude_zb_file": 1,
            "image_check": 1
        }

        # 准备请求数据
        start_task_data = {
            "taskName": "1",
            "zbFiles": json.dumps(zb_files, ensure_ascii=False),
            "tbFiles": json.dumps(tb_files, ensure_ascii=False),
            "rules": json.dumps(rules, ensure_ascii=False),
            "parseStatus": 0,
            "checkStatus": 0,
            "repeatStatus": -1
        }

        print(f"任务名称: {start_task_data['taskName']}")
        print(f"招标文件: {zb_files['zb_dir']['fileName']}")
        print(f"投标文件数量: {len(tb_files)}")

        # 发送启动任务请求
        res = api.request(
            method=config['start_task']['method'],
            path=config['start_task']['path'],
            json=start_task_data
        )

        # 打印响应结果
        print(f"状态码: {res.status_code}")
        print(f"响应内容: {res.json()}")

        # 验证响应状态码
        assert res.status_code == 200, f"Start task failed with status code: {res.status_code}"

        # 提取并保存taskId用于后续接口
        response_data = res.json()
        if response_data.get('code') == 200:
            data_content = response_data.get('data', {})
            if isinstance(data_content, dict):
                task_id = data_content.get('taskId') or data_content.get('id') or data_content.get('task_id')
            else:
                task_id = data_content

            if task_id:
                # 保存taskId到测试数据文件
                config['task_id'] = str(task_id)
                write_yaml('./test_data/bid_check_workflow.yaml', config)
                print(f"✓ Task ID saved: {task_id}")
            else:
                print("⚠ Task ID not found in response")
        else:
            print(f"⚠ Start task response: {response_data}")

    def test_04_query_analysis_status(self, api):
        """
        步骤6: 查询分析状态（带轮询）
        接口: POST /prod-api/check/check/task/analysis/status
        """
        print("\n" + "=" * 60)
        print("步骤6: 查询分析状态（轮询直到完成）")
        print("=" * 60)

        # 加载测试配置
        with open('./test_data/bid_check_workflow.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 从配置文件中读取taskId
        task_id = config.get('task_id')
        if not task_id:
            pytest.skip("Task ID not found. Please run test_03_start_check_task first.")

        print(f"Task ID: {task_id}")

        # 轮询参数
        max_polls = 30  # 最多轮询30次
        poll_interval = 60  # 每次间隔60秒
        completed = False

        print(f"开始轮询分析状态（最多{max_polls}次，每次间隔{poll_interval}秒）")

        for poll_count in range(max_polls):
            print(f"\n第{poll_count + 1}次轮询...")

            # 准备请求数据
            status_data = {
                "taskId": task_id
            }

            # 发送查询状态请求
            res = api.request(
                method=config['analysis_status']['method'],
                path=config['analysis_status']['path'],
                json=status_data
            )

            # 打印响应结果
            print(f"状态码: {res.status_code}")
            response_json = res.json()

            # 验证响应状态码
            assert res.status_code == 200, f"Query status failed with status code: {res.status_code}"

            # 检查响应数据
            if response_json.get('code') == 200:
                data = response_json.get('data', {})
                if isinstance(data, dict):
                    parse_progress = data.get('parseProgress', 0)
                    check_status = data.get('checkStatus')
                    repeat_status = data.get('repeatStatus')
                    parse_status = data.get('parseStatus')

                    print(f"  解析进度: {parse_progress}%")
                    print(f"  检查状态: {check_status}")
                    print(f"  重复状态: {repeat_status}")
                    print(f"  解析状态: {parse_status}")

                    # 检查是否完成（parseProgress 为 100.0）
                    if parse_progress == 100.0:
                        print(f"\n✓ 解析完成! (进度: {parse_progress}%)")
                        completed = True
                        break

            # 如果不是最后一次轮询，则等待
            if poll_count < max_polls - 1:
                print(f"等待{poll_interval}秒后继续...")
                time.sleep(poll_interval)

        if not completed:
            print(f"\n⚠ 轮询超时（{max_polls * poll_interval}秒），解析未完成")

        print("\n" + "=" * 60)
    def test_05_check_check_point(self, api):
        """
        步骤5: 检查检查点
        接口: POST /prod-api/check/check/task/check/point
        """
        print("\n" + "=" * 60)
        print("步骤5: 检查检查点")
        print("=" * 60)

        # 加载测试配置
        with open('./test_data/bid_check_workflow.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 从配置文件中读取taskId
        task_id = config.get('task_id')
        if not task_id:
            pytest.skip("Task ID not found. Please run test_03_start_check_task first.")

        print(f"Task ID: {task_id}")

        # 准备请求数据
        check_point_data = {
            "taskId": task_id
        }

        # 发送检查检查点请求
        res = api.request(
            method=config['check_point']['method'],
            path=config['check_point']['path'],
            json=check_point_data
        )

        # 打印响应结果
        print(f"状态码: {res.status_code}")
        response_json = res.json()
        print(f"响应内容: {response_json}")

        # 验证响应状态码
        assert res.status_code == 200, f"Check point failed with status code: {res.status_code}"

        # 保存响应用于评估
        self._save_response_for_evaluation('check_point', response_json)

    

    
    def test_06_get_bid_info(self, api):
        """
        步骤7: 获取投标信息
        接口: POST /prod-api/check/check/task/bid/info
        """
        print("\n" + "=" * 60)
        print("步骤7: 获取投标信息")
        print("=" * 60)

        # 加载测试配置
        with open('./test_data/bid_check_workflow.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 从配置文件中读取taskId
        task_id = config.get('task_id')
        if not task_id:
            pytest.skip("Task ID not found. Please run test_03_start_check_task first.")

        print(f"Task ID: {task_id}")

        # 准备请求数据
        bid_info_data = {
            "taskId": task_id
        }

        # 发送获取投标信息请求
        res = api.request(
            method=config['bid_info']['method'],
            path=config['bid_info']['path'],
            json=bid_info_data
        )

        # 打印响应结果
        print(f"状态码: {res.status_code}")
        response_json = res.json()
        print(f"响应内容: {response_json}")

        # 验证响应状态码
        assert res.status_code == 200, f"Get bid info failed with status code: {res.status_code}"

        # 保存响应用于评估
        self._save_response_for_evaluation('bid_info', response_json)

    
