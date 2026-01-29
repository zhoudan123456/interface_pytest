import json
import os
import time
from datetime import datetime
import pytest
import yaml
import re
from urllib.parse import unquote

from conf.set_conf import read_yaml, write_yaml


class TestBidGenerateWorkflow:
    @pytest.mark.parametrize('data', read_yaml('./test_data/bid_generate_workflow.yaml'))
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
                # 保存文档ID到bid_generate.yaml文件，供后续接口使用
                document_data = {'document_id': str(document_id)}
                write_yaml('./test_data/bid_generate.yaml', document_data)
                print(f"Document ID saved: {document_id}")
            else:
                pytest.fail(f"Upload failed with response: {response_data}")

        finally:
            # 确保文件句柄被关闭
            files['file'].close()

    @pytest.mark.parametrize('data', read_yaml('./test_data/bid_generate_workflow.yaml'))
    def test_02_check_bid_file(self, api, data):
        """检查招标文件"""
        # 从bid_generate.yaml中读取上传后保存的文档ID
        extract_file_path = './test_data/bid_generate.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                document_id = extract_data.get('document_id') if extract_data else None
        else:
            document_id = None

        # 确保文档ID存在
        assert document_id, "Document ID not found in bid_generate.yaml. Please run upload test first."

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

    @pytest.mark.parametrize('data', read_yaml('./test_data/bid_generate_workflow.yaml'))
    def test_03_analyze_tender_sync(self, api, data):
        """测试解析招标文件接口"""
        # 获取分析招标文件的配置数据
        analyze_tender_data = data['analyze_tender']
        type_param = data['upload']['data']['type']

        print(f"Using type: {type_param}")

        # 从bid_generate.yaml中读取上传后保存的文档ID
        extract_file_path = './test_data/bid_generate.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                document_id = extract_data.get('document_id') if extract_data else None
        else:
            document_id = None

        # 确保文档ID存在
        assert document_id, "Document ID not found in bid_generate.yaml. Please run upload test first."

        print(f"Using document ID: {document_id}")

        form_data = {
            "tenderId": (None, str(document_id)),
            "type": (None, str(type_param))
        }

        res = api.request(
            save_cookie=True,
            files=form_data,
            **analyze_tender_data
        )

        # 打印响应结果
        print("Analyze Tender Response:", res.json())

        # 验证响应状态码
        assert res.status_code == 200, f"Analyze tender failed with status code: {res.status_code}, response: {res.json()}"

    @pytest.mark.parametrize('data', read_yaml('./test_data/bid_generate_workflow.yaml'))
    def test_04_poll_parse_progress(self, api, data):
        """
        步骤4: 轮询解析进度
        接口: /prod-api/bid/ua/query/oneTenderProgressUser
        """
        print("\n" + "=" * 50)
        print("步骤3: 轮询解析进度")
        print("=" * 50)

        # 从bid_generate.yaml中读取上传后保存的文档ID
        extract_file_path = './test_data/bid_generate.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                document_id = extract_data.get('document_id') if extract_data else None
        else:
            document_id = None

        # 确保文档ID存在
        assert document_id, "Document ID not found in bid_generate.yaml. Please run upload test first."

        print(f"Using document ID: {document_id}")

        form_data = {
            "tenderId": (None, str(document_id))
        }

        # 轮询配置
        max_attempts = 30  # 最多尝试30次 (30分钟)
        poll_interval = 60  # 每次间隔60秒 (1分钟)
        max_wait_time = 1800  # 最多等待1800秒 (30分钟)

        start_time = time.time()

        # 初始化解析状态
        parse_completed = False

        for attempt in range(1, max_attempts + 1):
            print(f"\n轮询尝试 #{attempt}/{max_attempts}")

            try:
                response = api.request(save_cookie=True, data=form_data, **data['query_tender_progress'])

                if response.status_code != 200:
                    print(f"⚠️  状态码异常: {response.status_code}")
                    # 如果发生错误，等待下次轮询
                    if attempt < max_attempts:
                        print(f"等待{poll_interval}秒后继续轮询...")
                        time.sleep(poll_interval)
                    continue

                result = response.json()
                print(f"进度响应: {json.dumps(result, indent=2, ensure_ascii=False)}")

            except Exception as e:
                print(f"⚠️  请求异常: {str(e)}")
                # 如果发生异常，等待下次轮询
                if attempt < max_attempts:
                    print(f"等待{poll_interval}秒后继续轮询...")
                    time.sleep(poll_interval)
                continue

            def check_all_parse_finished(resp_data):
                # 1. 提取"招标解析分块进度"数组
                parse_blocks = resp_data.get("data", {}).get("招标解析分块进度", [])
                if not parse_blocks:
                    return False, "没有解析分块数据"

                # 2. 遍历每个结点，检查"解析状态"
                for block in parse_blocks:
                    parse_status = block.get("解析状态")
                    # 只要有一个结点不是"已完成"，就判定未完成
                    if parse_status != "已完成":
                        return False, f"结点{block.get('0')}解析状态为：{parse_status}"

                # 所有结点都满足
                return True, "所有解析分块均已完成"

            # 执行检查并打印结果
            is_finished, msg = check_all_parse_finished(result)
            print("整体解析是否完成：", is_finished)
            print("检查说明：", msg)

            if is_finished:
                print("✅ 解析进度已完成！")
                parse_completed = True
                # 保存解析结果到 bid_generate.yaml
                extract_data = {}
                if os.path.exists(extract_file_path):
                    with open(extract_file_path, 'r', encoding='utf-8') as f:
                        extract_data = yaml.safe_load(f) or {}
                extract_data['parse_result'] = str(parse_completed)
                with open(extract_file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(extract_data, f, allow_unicode=True)
                break

            # 检查超时
            elapsed_time = time.time() - start_time
            if elapsed_time > max_wait_time:
                print(f"⏰ 达到最大等待时间 {max_wait_time} 秒，停止轮询")
                break

            # 等待下一次轮询
            if attempt < max_attempts and not is_finished:
                print(f"等待{poll_interval}秒后继续轮询...")
                time.sleep(poll_interval)

        # 如果解析未完成，抛出异常让后续测试依赖此条件的无法执行
        if not parse_completed:
            pytest.fail("解析进度轮询超时或未能完成，无法执行后续的目录生成步骤")

    @pytest.mark.parametrize('data', read_yaml('./test_data/bid_generate_workflow.yaml'))
    def test_05_init_business(self, api, data):
        """
        步骤14: 初始化业务
        接口: /prod-api/bid/init/busi
        """
        print("\n" + "=" * 50)
        print("步骤14: 初始化业务")
        print("=" * 50)

        # 从bid_generate.yaml中读取文档ID和公司ID
        extract_file_path = './test_data/bid_generate.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                document_id = extract_data.get('document_id') if extract_data else None
                # 根据项目规则，如果company_id不存在，默认为'112233'
                company_id = extract_data.get('company_id') if extract_data and extract_data.get('company_id') else '112233'
        else:
            document_id = None
            company_id = '112233'

        # 确保文档ID存在
        assert document_id, "Document ID not found in bid_generate.yaml. Please run upload test first."

        print(f"Using document ID: {document_id}")
        print(f"Using company ID: {company_id}")

        # 确保company_id不为None
        if company_id is None:
            company_id = '112233'
            print(f"Company ID was None, setting to default: {company_id}")

        # 准备请求参数
        query_params = {
            "tenderId": document_id,
            "companyId": company_id
        }

        # 发送请求 - 根据HAR文件，这是一个POST请求，参数在查询字符串中
        res = api.request(
            method=data['init_business']['method'],
            path=data['init_business']['path'],
            params=query_params
        )

        # 打印响应结果
        print("Init Business Response:", res.json())

        # 验证响应状态码
        assert res.status_code == 200, f"Init business failed with status code: {res.status_code}, response: {res.json()}"

        # 提取响应信息
        response_data = res.json()
        if response_data.get('code') == 200:
            print(f"Successfully initialized business for tenderId: {document_id} and companyId: {company_id}")
            
            # 更新bid_generate.yaml文件
            existing_data = {}
            if os.path.exists(extract_file_path):
                with open(extract_file_path, 'r', encoding='utf-8') as f:
                    existing_data = yaml.safe_load(f) or {}
            
            existing_data['business_init_status'] = 'success'
            existing_data['business_init_response'] = response_data.get('data')
            
            with open(extract_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(existing_data, f, allow_unicode=True)
            
            print(f"Business init status saved")
        else:
            print(f"Failed to initialize business: {response_data}")

    @pytest.mark.parametrize('data', read_yaml('./test_data/bid_generate_workflow.yaml'))
    def test_06_query_one_tender_user(self, api, data):
        """
        步骤15: 查询单个招标用户信息
        接口: /prod-api/bid/ua/query/oneTenderUser
        """
        print("\n" + "=" * 50)
        print("步骤15: 查询单个招标用户信息")
        print("=" * 50)

        # 从bid_generate.yaml中读取文档ID和公司ID
        extract_file_path = './test_data/bid_generate.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                document_id = extract_data.get('document_id') if extract_data else None
                # 根据项目规则，如果company_id不存在，默认为'112233'
                company_id = extract_data.get('company_id') if extract_data and extract_data.get('company_id') else '112233'
        else:
            document_id = None
            company_id = '112233'

        # 确保文档ID存在
        assert document_id, "Document ID not found in bid_generate.yaml. Please run upload test first."

        print(f"Using document ID: {document_id}")
        print(f"Using company ID: {company_id}")

        # 确保company_id不为None
        if company_id is None:
            company_id = '112233'
            print(f"Company ID was None, setting to default: {company_id}")

        # 准备请求参数 - 从HAR文件看，这是POST请求，参数以multipart/form-data格式发送
        form_data = {
            "tenderId": (None, str(document_id)),
            "companyId": (None, str(company_id))
        }

        # 发送请求
        res = api.request(
            method=data['query_one_tender_user']['method'],
            path=data['query_one_tender_user']['path'],
            save_cookie=True,
            files=form_data
        )

        # 打印响应结果
        print("Query One Tender User Response:", res.json())

        # 验价响应状态码
        assert res.status_code == 200, f"Query one tender user failed with status code: {res.status_code}, response: {res.json()}"

        # 提取响应信息
        response_data = res.json()
        if response_data.get('code') == 200:
            print(f"Successfully queried tender user info for tenderId: {document_id} and companyId: {company_id}")
            
            # 更新bid_generate.yaml文件
            existing_data = {}
            if os.path.exists(extract_file_path):
                with open(extract_file_path, 'r', encoding='utf-8') as f:
                    existing_data = yaml.safe_load(f) or {}
            
            existing_data['tender_user_info'] = response_data.get('data')
            
            with open(extract_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(existing_data, f, allow_unicode=True)
            
            print(f"Tender user info saved")
        else:
            print(f"Failed to query tender user info: {response_data}")

    @pytest.mark.parametrize('data', read_yaml('./test_data/bid_generate_workflow.yaml'))
    def test_07_query_catalogue(self, api, data):
        """
        步骤16: 查询目录
        接口: /prod-api/bid/query/catalogue
        """
        print("\n" + "=" * 50)
        print("步骤16: 查询目录")
        print("=" * 50)

        # 从bid_generate.yaml中读取文档ID和公司ID
        extract_file_path = './test_data/bid_generate.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                document_id = extract_data.get('document_id') if extract_data else None
                # 根据项目规则，如果company_id不存在，默认为'112233'
                company_id = extract_data.get('company_id') if extract_data and extract_data.get('company_id') else '112233'
        else:
            document_id = None
            company_id = '112233'

        # 确保文档ID存在
        assert document_id, "Document ID not found in bid_generate.yaml. Please run upload test first."

        print(f"Using document ID: {document_id}")
        print(f"Using company ID: {company_id}")

        # 确保company_id不为None
        if company_id is None:
            company_id = '112233'
            print(f"Company ID was None, setting to default: {company_id}")

        # 准备请求参数 - 从HAR文件看，这是POST请求，参数以multipart/form-data格式发送
        form_data = {
            "tenderId": (None, str(document_id)),
            "companyId": (None, str(company_id))
        }

        # 发送请求
        res = api.request(
            method=data['query_catalogue']['method'],
            path=data['query_catalogue']['path'],
            save_cookie=True,
            files=form_data
        )

        # 打印响应结果
        print("Query Catalogue Response:", res.json())

        # 验证响应状态码
        assert res.status_code == 200, f"Query catalogue failed with status code: {res.status_code}, response: {res.json()}"

        # 提取响应信息
        response_data = res.json()
        if response_data.get('code') == 200:
            print(f"Successfully queried catalogue for tenderId: {document_id} and companyId: {company_id}")
            
            # 更新bid_generate.yaml文件
            existing_data = {}
            if os.path.exists(extract_file_path):
                with open(extract_file_path, 'r', encoding='utf-8') as f:
                    existing_data = yaml.safe_load(f) or {}
            
            existing_data['catalogue_info'] = response_data.get('data')
            
            with open(extract_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(existing_data, f, allow_unicode=True)
            
            print(f"Catalogue info saved")
        else:
            print(f"Failed to query catalogue: {response_data}")

    @pytest.mark.parametrize('data', read_yaml('./test_data/bid_generate_workflow.yaml'))
    def test_08_query_new_bid_as(self, api, data):
        """
        步骤17: 查询新的投标报价
        接口: /prod-api/bid/query/new/bidAs
        """
        print("\n" + "=" * 50)
        print("步骤17: 查询新的投标报价")
        print("=" * 50)

        # 从bid_generate.yaml中读取文档ID和公司ID
        extract_file_path = './test_data/bid_generate.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                document_id = extract_data.get('document_id') if extract_data else None
                # 根据项目规则，如果company_id不存在，默认为'112233'
                company_id = extract_data.get('company_id') if extract_data and extract_data.get('company_id') else '112233'
        else:
            document_id = None
            company_id = '112233'

        # 确保文档ID存在
        assert document_id, "Document ID not found in bid_generate.yaml. Please run upload test first."

        print(f"Using document ID: {document_id}")
        print(f"Using company ID: {company_id}")

        # 确保company_id不为None
        if company_id is None:
            company_id = '112233'
            print(f"Company ID was None, setting to default: {company_id}")

        # 准备请求参数 - 从HAR文件看，这是POST请求，参数以JSON格式发送
        json_data = {
            "tenderId": str(document_id),
            "companyId": str(company_id)
        }

        # 发送请求
        res = api.request(
            method=data['query_new_bid_as']['method'],
            path=data['query_new_bid_as']['path'],
            json=json_data
        )

        # 打印响应结果
        print("Query New Bid As Response:", res.json())

        # 验证响应状态码
        assert res.status_code == 200, f"Query new bid as failed with status code: {res.status_code}, response: {res.json()}"

        # 提取响应信息
        response_data = res.json()
        if response_data.get('code') == 200:
            print(f"Successfully queried new bid as for tenderId: {document_id} and companyId: {company_id}")
            
            # 更新bid_generate.yaml文件
            existing_data = {}
            if os.path.exists(extract_file_path):
                with open(extract_file_path, 'r', encoding='utf-8') as f:
                    existing_data = yaml.safe_load(f) or {}
            
            existing_data['new_bid_as_info'] = response_data.get('data')
            
            with open(extract_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(existing_data, f, allow_unicode=True)
            
            print(f"New bid as info saved")
        else:
            print(f"Failed to query new bid as: {response_data}")

    @pytest.mark.parametrize('data', read_yaml('./test_data/bid_generate_workflow.yaml'))
    def test_09_gen_busi_task(self, api, data):
        """
        步骤18: 生成业务任务
        接口: /prod-api/bid/gen/busi/task
        """
        print("\n" + "=" * 50)
        print("步骤18: 生成业务任务")
        print("=" * 50)

        # 从bid_generate.yaml中读取文档ID和公司ID
        extract_file_path = './test_data/bid_generate.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                document_id = extract_data.get('document_id') if extract_data else None
                # 根据项目规则，如果company_id不存在，默认为'112233'
                company_id = extract_data.get('company_id') if extract_data and extract_data.get('company_id') else '112233'
        else:
            document_id = None
            company_id = '112233'

        # 确保文档ID存在
        assert document_id, "Document ID not found in bid_generate.yaml. Please run upload test first."

        print(f"Using document ID: {document_id}")
        print(f"Using company ID: {company_id}")

        # 确保company_id不为None
        if company_id is None:
            company_id = '112233'
            print(f"Company ID was None, setting to default: {company_id}")

        # 准备请求参数 - 从HAR文件看，这是POST请求，参数在查询字符串中
        query_params = {
            "tenderId": document_id,
            "companyId": company_id
        }

        # 发送请求
        res = api.request(
            method=data['gen_busi_task']['method'],
            path=data['gen_busi_task']['path'],
            params=query_params
        )

        # 打印响应结果
        print("Gen Busi Task Response:", res.json())

        # 验证响应状态码
        assert res.status_code == 200, f"Gen busi task failed with status code: {res.status_code}, response: {res.json()}"

        # 提取响应信息
        response_data = res.json()
        if response_data.get('code') == 200:
            print(f"Successfully generated business task for tenderId: {document_id} and companyId: {company_id}")
            
            # 更新bid_generate.yaml文件
            existing_data = {}
            if os.path.exists(extract_file_path):
                with open(extract_file_path, 'r', encoding='utf-8') as f:
                    existing_data = yaml.safe_load(f) or {}
            
            existing_data['gen_busi_task_info'] = response_data.get('data')
            
            with open(extract_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(existing_data, f, allow_unicode=True)
            
            print(f"Gen busi task info saved")
        else:
            print(f"Failed to generate business task: {response_data}")

    @pytest.mark.parametrize('data', read_yaml('./test_data/bid_generate_workflow.yaml'))
    def test_10_gen_busi_status(self, api, data):
        """
        步骤19: 查询业务任务状态
        接口: /prod-api/bid/gen/busi/status
        """
        print("\n" + "=" * 50)
        print("步骤19: 查询业务任务状态")
        print("=" * 50)

        # 从bid_generate.yaml中读取文档ID和公司ID
        extract_file_path = './test_data/bid_generate.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                document_id = extract_data.get('document_id') if extract_data else None
                # 根据项目规则，如果company_id不存在，默认为'112233'
                company_id = extract_data.get('company_id') if extract_data and extract_data.get('company_id') else '112233'
        else:
            document_id = None
            company_id = '112233'

        # 确保文档ID存在
        assert document_id, "Document ID not found in bid_generate.yaml. Please run upload test first."

        print(f"Using document ID: {document_id}")
        print(f"Using company ID: {company_id}")

        # 确保company_id不为None
        if company_id is None:
            company_id = '112233'
            print(f"Company ID was None, setting to default: {company_id}")

        # 准备请求参数 - 从HAR文件看，这是GET请求，参数在查询字符串中
        query_params = {
            "tenderId": document_id,
            "companyId": company_id
        }

        # 设置轮询参数
        max_attempts = 60  # 最多尝试60次 (60分钟)
        poll_interval = 60  # 每次间隔60秒 (1分钟)

        # 开始轮询
        for attempt in range(1, max_attempts + 1):
            print(f"\n轮询尝试 #{attempt}/{max_attempts}")
            
            try:
                # 发送请求
                res = api.request(
                    method=data['gen_busi_status']['method'],
                    path=data['gen_busi_status']['path'],
                    params=query_params
                )

                # 打印响应结果
                print("Gen Busi Status Response:", res.json())

                # 验证响应状态码
                if res.status_code != 200:
                    print(f"Gen busi status failed with status code: {res.status_code}, response: {res.json()}")
                    if attempt < max_attempts:
                        print(f"等待{poll_interval}秒后继续轮询...")
                        time.sleep(poll_interval)
                    continue

                # 提取响应信息
                response_data = res.json()
                if response_data.get('code') == 200:
                    # 检查状态是否为'completed'
                    data_field = response_data.get('data')
                    if isinstance(data_field, dict):
                        # 如果data是字典，则从中获取status
                        status = data_field.get('status')
                    elif isinstance(data_field, str):
                        # 如果data是字符串，需要先解析它
                        try:
                            import json
                            parsed_data = json.loads(data_field)
                            status = parsed_data.get('status')
                        except (ValueError, TypeError):
                            # 如果不能解析为JSON，设置为None
                            status = None
                    else:
                        # 其他情况，设置为None
                        status = None
                    
                    if status == 'completed':
                        print(f"业务任务已完成，status: {status}")
                        
                        # 更新bid_generate.yaml文件
                        existing_data = {}
                        if os.path.exists(extract_file_path):
                            with open(extract_file_path, 'r', encoding='utf-8') as f:
                                existing_data = yaml.safe_load(f) or {}
                        
                        existing_data['gen_busi_status_info'] = response_data.get('data')
                        
                        with open(extract_file_path, 'w', encoding='utf-8') as f:
                            yaml.dump(existing_data, f, allow_unicode=True)
                        
                        print(f"Gen busi status info saved")
                        break
                    else:
                        print(f"业务任务尚未完成，当前状态: {status}")
                        if attempt < max_attempts:
                            print(f"等待{poll_interval}秒后继续轮询...")
                            time.sleep(poll_interval)
                        else:
                            print("达到最大轮询次数，任务仍未完成")
                            pytest.fail("业务任务状态查询超时，未达到completed状态")
                else:
                    print(f"Failed to query business status: {response_data}")
                    if attempt < max_attempts:
                        print(f"等待{poll_interval}秒后继续轮询...")
                        time.sleep(poll_interval)
                    else:
                        pytest.fail(f"查询业务状态失败: {response_data}")
            
            except Exception as e:
                print(f"轮询过程中发生异常: {str(e)}")
                if attempt < max_attempts:
                    print(f"等待{poll_interval}秒后继续轮询...")
                    time.sleep(poll_interval)
                else:
                    pytest.fail(f"轮询过程中持续出现异常: {str(e)}")

    @pytest.mark.parametrize('data', read_yaml('./test_data/bid_generate_workflow.yaml'))
    def test_11_query_new_company_id(self, api, data):
        """
        步骤20: 查询新的公司ID
        接口: /prod-api/bid/query/new/company/id
        """
        print("\n" + "=" * 50)
        print("步骤20: 查询新的公司ID")
        print("=" * 50)

        # 从bid_generate.yaml中读取文档ID
        extract_file_path = './test_data/bid_generate.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                
                # 从bid_generate.yaml中获取document_id
                document_id = extract_data.get('document_id', '332211')  # 默认值
                

        else:
            document_id = '332211'

        # 如果仍然找不到document_id，使用默认值进行演示
        if not document_id:
            document_id = '332211'
            print(f"警告: 未找到文档ID，使用默认值: {document_id}")

        print(f"Using document ID: {document_id}")

        # 准备请求参数 - 这是一个GET请求，参数在查询字符串中
        # 注意：接口仍然需要busiId参数，所以我们需要将document_id作为busiId传递
        query_params = {
            "busiId": document_id
        }

        # 发送请求
        res = api.request(
            method=data['query_new_company_id']['method'],
            path=data['query_new_company_id']['path'],
            params=query_params
        )

        # 打印响应结果
        print("Query New Company ID Response:", res.json())

        # 验证响应状态码
        assert res.status_code == 200, f"Query new company ID failed with status code: {res.status_code}, response: {res.json()}"

        # 提取响应信息
        response_data = res.json()
        if response_data.get('code') == 200:
            company_id = response_data.get('data')
            print(f"Successfully queried company ID: {company_id} for documentId: {document_id}")
            
            # 更新bid_generate.yaml文件
            existing_data = {}
            if os.path.exists(extract_file_path):
                with open(extract_file_path, 'r', encoding='utf-8') as f:
                    existing_data = yaml.safe_load(f) or {}
            
            existing_data['new_company_id'] = company_id
            existing_data['queried_document_id'] = document_id
            
            with open(extract_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(existing_data, f, allow_unicode=True)
            
            print(f"New company ID saved: {company_id}")
        else:
            print(f"Failed to query new company ID: {response_data}")
            pytest.fail(f"Failed to query new company ID: {response_data}")

    @pytest.mark.parametrize('data', read_yaml('./test_data/bid_generate_workflow.yaml'))
    def test_12_query_busi_fill_company_is_fill(self, api, data):
        """
        步骤21: 查询业务填充公司是否填充
        接口: /prod-api/bid/query/busiFillCompanyIsFill
        """
        print("\n" + "=" * 50)
        print("步骤21: 查询业务填充公司是否填充")
        print("=" * 50)


        # 从bid_generate.yaml中读取所需参数
        extract_file_path = './test_data/bid_generate.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                
                # 尝试从已有数据中获取参数
                user_id = extract_data.get('user_id', '399')  # 默认值来自HAR数据
                tender_id = extract_data.get('document_id', '176887627456900000')  # 使用文档ID或默认值
                company_id = extract_data.get('company_id', '112233')  # 使用已有公司ID或默认值
                

                
        else:
            # 使用HAR数据中的默认值
            user_id = '399'
            tender_id = '176887627456900000'
            company_id = '112233'

        print(f"Using user ID: {user_id}")
        print(f"Using tender ID: {tender_id}")
        print(f"Using company ID: {company_id}")

        # 准备请求参数 - 这是一个GET请求，参数在查询字符串中
        query_params = {
            "userId": user_id,
            "tenderId": tender_id,
            "companyId": company_id
        }

        # 发送请求
        res = api.request(
            method=data['query_busi_fill_company_is_fill']['method'],
            path=data['query_busi_fill_company_is_fill']['path'],
            params=query_params
        )

        # 打印响应结果
        print("Query Busi Fill Company Is Fill Response:", res.json())

        # 验证响应状态码
        assert res.status_code == 200, f"Query busi fill company is fill failed with status code: {res.status_code}, response: {res.json()}"

        # 提取响应信息
        response_data = res.json()
        if response_data.get('code') == 200:
            is_filled = response_data.get('data')
            message = response_data.get('msg', '')
            print(f"Successfully queried fill status: {is_filled}, message: {message} for tenderId: {tender_id}, userId: {user_id}, companyId: {company_id}")
            
            # 更新bid_generate.yaml文件
            existing_data = {}
            if os.path.exists(extract_file_path):
                with open(extract_file_path, 'r', encoding='utf-8') as f:
                    existing_data = yaml.safe_load(f) or {}
            
            existing_data['busi_fill_company_status'] = is_filled
            existing_data['busi_fill_company_message'] = message
            existing_data['used_user_id_for_fill_check'] = user_id
            existing_data['used_tender_id_for_fill_check'] = tender_id
            existing_data['used_company_id_for_fill_check'] = company_id
            
            with open(extract_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(existing_data, f, allow_unicode=True)
            
            print(f"Busi fill company status saved: {is_filled}")
        else:
            print(f"Failed to query busi fill company is fill: {response_data}")
            pytest.fail(f"Failed to query busi fill company is fill: {response_data}")

    @pytest.mark.parametrize('data', read_yaml('./test_data/bid_generate_workflow.yaml'))
    def test_13_query_new_final_gen(self, api, data):
        """
        步骤22: 查询新的最终生成状态
        接口: /prod-api/bid/query/new/finalGen
        """
        print("\n" + "=" * 50)
        print("步骤22: 查询新的最终生成状态")
        print("=" * 50)

        # 从bid_generate.yaml中读取所需参数
        extract_file_path = './test_data/bid_generate.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                
                # 尝试从已有数据中获取参数
                busi_as_id = extract_data.get('new_company_id', '176887645626100000')  # 使用新公司ID作为busiAsId或默认值
                tender_id = extract_data.get('document_id', '176887627456900000')  # 使用文档ID或默认值
                company_id = extract_data.get('new_company_id', '99917688764845990')  # 使用新公司ID或默认值
                
                # 从前面的查询结果中获取参数
                if not busi_as_id and extract_data.get('new_bid_as_info'):
                    bid_as_info = extract_data['new_bid_as_info']
                    if isinstance(bid_as_info, dict) and 'id' in bid_as_info:
                        busi_as_id = bid_as_info['id']
                    elif isinstance(bid_as_info, dict) and 'busiAsId' in bid_as_info:
                        busi_as_id = bid_as_info['busiAsId']
                
                # 如果tender_id仍然未设置，尝试从其他地方获取
                if not tender_id and extract_data.get('tender_user_info'):
                    tender_info = extract_data['tender_user_info']
                    if isinstance(tender_info, dict) and 'tenderId' in tender_info:
                        tender_id = tender_info['tenderId']
                    elif isinstance(tender_info, dict) and 'id' in tender_info:
                        tender_id = tender_info['id']
                
        else:
            # 使用HAR数据中的默认值
            busi_as_id = '176887645626100000'
            tender_id = '176887627456900000'
            company_id = '99917688764845990'

        # 设置默认的isFillCompany值
        is_fill_company = '0'  # 根据HAR数据显示，值为0

        print(f"Using busiAs ID: {busi_as_id}")
        print(f"Using tender ID: {tender_id}")
        print(f"Using company ID: {company_id}")
        print(f"Using isFillCompany: {is_fill_company}")

        # 准备请求参数 - 这是一个GET请求，参数在查询字符串中
        query_params = {
            "busiAsId": busi_as_id,
            "isFillCompany": is_fill_company,
            "tenderId": tender_id,
            "companyId": company_id
        }

        # 发送请求
        res = api.request(
            method=data['query_new_final_gen']['method'],
            path=data['query_new_final_gen']['path'],
            params=query_params
        )

        # 打印响应结果
        print("Query New Final Gen Response:", res.json())

        # 验证响应状态码
        assert res.status_code == 200, f"Query new final gen failed with status code: {res.status_code}, response: {res.json()}"

        # 提取响应信息
        response_data = res.json()
        if response_data.get('code') == 200:
            result_data = response_data.get('data')
            tech_status = result_data.get('techStatus') if result_data else None
            busi_status = result_data.get('busiStatus') if result_data else None
            print(f"Successfully queried final gen status: techStatus={tech_status}, busiStatus={busi_status} for busiAsId: {busi_as_id}, tenderId: {tender_id}, companyId: {company_id}")
            
            # 更新bid_generate.yaml文件
            existing_data = {}
            if os.path.exists(extract_file_path):
                with open(extract_file_path, 'r', encoding='utf-8') as f:
                    existing_data = yaml.safe_load(f) or {}
            
            existing_data['final_gen_status'] = result_data
            existing_data['tech_status'] = tech_status
            existing_data['busi_status'] = busi_status
            existing_data['used_busi_as_id_for_final_gen'] = busi_as_id
            existing_data['used_tender_id_for_final_gen'] = tender_id
            existing_data['used_company_id_for_final_gen'] = company_id
            
            with open(extract_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(existing_data, f, allow_unicode=True)
            
            print(f"Final gen status saved: techStatus={tech_status}, busiStatus={busi_status}")
        else:
            print(f"Failed to query new final gen: {response_data}")
            pytest.fail(f"Failed to query new final gen: {response_data}")

    @pytest.mark.parametrize('data', read_yaml('./test_data/bid_generate_workflow.yaml'))
    def test_14_query_is_down(self, api, data):
        """
        步骤23: 查询是否可下载
        接口: /prod-api/bid/query/is/down
        """
        print("\n" + "=" * 50)
        print("步骤23: 查询是否可下载")
        print("=" * 50)

        # 从bid_generate.yaml中读取所需参数
        extract_file_path = './test_data/bid_generate.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                
                # 尝试从已有数据中获取参数
                type_param = 'busi_gen'  # 根据HAR数据显示，type为busi_gen
                tender_id = extract_data.get('document_id', '176887627456900000')  # 使用文档ID或默认值
                company_id = extract_data.get('new_company_id', '99917688764845990')  # 使用新公司ID或默认值
                
                # 如果tender_id仍然未设置，尝试从其他地方获取
                if not tender_id and extract_data.get('tender_user_info'):
                    tender_info = extract_data['tender_user_info']
                    if isinstance(tender_info, dict) and 'tenderId' in tender_info:
                        tender_id = tender_info['tenderId']
                    elif isinstance(tender_info, dict) and 'id' in tender_info:
                        tender_id = tender_info['id']
                
        else:
            # 使用HAR数据中的默认值
            type_param = 'busi_gen'
            tender_id = '176887627456900000'
            company_id = '99917688764845990'

        print(f"Using type: {type_param}")
        print(f"Using tender ID: {tender_id}")
        print(f"Using company ID: {company_id}")

        # 准备请求参数 - 这是一个GET请求，参数在查询字符串中
        query_params = {
            "type": type_param,
            "tenderId": tender_id,
            "companyId": company_id
        }

        # 发送请求
        res = api.request(
            method=data['query_is_down']['method'],
            path=data['query_is_down']['path'],
            params=query_params
        )

        # 打印响应结果
        print("Query Is Down Response:", res.json())

        # 验证响应状态码
        assert res.status_code == 200, f"Query is down failed with status code: {res.status_code}, response: {res.json()}"

        # 提取响应信息
        response_data = res.json()
        if response_data.get('code') == 200:
            is_down = response_data.get('data')
            print(f"Successfully queried download status: {is_down} for type: {type_param}, tenderId: {tender_id}, companyId: {company_id}")
            
            # 更新bid_generate.yaml文件
            existing_data = {}
            if os.path.exists(extract_file_path):
                with open(extract_file_path, 'r', encoding='utf-8') as f:
                    existing_data = yaml.safe_load(f) or {}
            
            existing_data['download_status'] = is_down
            existing_data['download_type'] = type_param
            existing_data['used_tender_id_for_download_check'] = tender_id
            existing_data['used_company_id_for_download_check'] = company_id
            
            with open(extract_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(existing_data, f, allow_unicode=True)
            
            print(f"Download status saved: {is_down}")
        else:
            print(f"Failed to query is down: {response_data}")
            pytest.fail(f"Failed to query is down: {response_data}")

    @pytest.mark.parametrize('data', read_yaml('./test_data/bid_generate_workflow.yaml'))
    def test_15_select_all_company(self, api, data):
        """
        步骤24: 查询所有公司
        接口: /prod-api/bid/company/selectAllCompany
        """
        print("\n" + "=" * 50)
        print("步骤24: 查询所有公司")
        print("=" * 50)

        # 从bid_generate.yaml中读取所需参数
        extract_file_path = './test_data/bid_generate.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
        else:
            extract_data = {}

        print("Querying all companies...")

        # 准备请求参数 - 这是一个GET请求，无特殊参数
        query_params = {}

        # 发送请求
        res = api.request(
            method=data['select_all_company']['method'],
            path=data['select_all_company']['path'],
            params=query_params
        )

        # 打印响应结果
        print("Select All Company Response:", res.json())

        # 验证响应状态码
        assert res.status_code == 200, f"Select all company failed with status code: {res.status_code}, response: {res.json()}"

        # 提取响应信息
        response_data = res.json()
        if response_data.get('code') == 200:
            companies = response_data.get('data', [])
            print(f"Successfully queried {len(companies)} companies")
            
            # 如果找到了公司列表，提取第一个公司的ID作为参考
            company_id = None
            company_name = None
            if companies and len(companies) > 0:
                first_company = companies[0]
                company_id = first_company.get('companyId')
                company_name = first_company.get('companyName')
                print(f"First company: ID={company_id}, Name={company_name}")
            
            # 更新bid_generate.yaml文件
            existing_data = extract_data
            if not existing_data:
                existing_data = {}
            
            existing_data['all_companies'] = companies
            existing_data['first_company_id'] = company_id
            existing_data['first_company_name'] = company_name
            existing_data['total_companies_count'] = len(companies)
            
            with open(extract_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(existing_data, f, allow_unicode=True)
            
            print(f"All companies saved: {len(companies)} companies found")
        else:
            print(f"Failed to query all companies: {response_data}")
            pytest.fail(f"Failed to query all companies: {response_data}")

    @pytest.mark.parametrize('data', read_yaml('./test_data/bid_generate_workflow.yaml'))
    def test_16_query_fill_company_list(self, api, data):
        """
        步骤25: 查询填充公司列表
        接口: /prod-api/bid/query/fill/company/list
        """
        print("\n" + "=" * 50)
        print("步骤25: 查询填充公司列表")
        print("=" * 50)

        # 从bid_generate.yaml中读取所需参数
        extract_file_path = './test_data/bid_generate.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                
                # 尝试从已有数据中获取tenderId
                tender_id = extract_data.get('document_id', '176887627456900000')  # 使用文档ID或默认值
                
                # 如果tender_id仍然未设置，尝试从其他地方获取
                if not tender_id and extract_data.get('tender_user_info'):
                    tender_info = extract_data['tender_user_info']
                    if isinstance(tender_info, dict) and 'tenderId' in tender_info:
                        tender_id = tender_info['tenderId']
                    elif isinstance(tender_info, dict) and 'id' in tender_info:
                        tender_id = tender_info['id']
                
        else:
            # 使用HAR数据中的默认值
            tender_id = '176887627456900000'

        print(f"Using tender ID: {tender_id}")

        # 准备请求参数 - 这是一个GET请求，参数在查询字符串中
        query_params = {
            "tenderId": tender_id
        }

        # 发送请求
        res = api.request(
            method=data['query_fill_company_list']['method'],
            path=data['query_fill_company_list']['path'],
            params=query_params
        )

        # 打印响应结果
        print("Query Fill Company List Response:", res.json())

        # 验证响应状态码
        assert res.status_code == 200, f"Query fill company list failed with status code: {res.status_code}, response: {res.json()}"

        # 提取响应信息
        response_data = res.json()
        if response_data.get('code') == 200:
            companies = response_data.get('data', [])
            print(f"Successfully queried fill company list, found {len(companies)} companies")
            
            # 检查返回的公司列表是否为空
            if len(companies) == 0:
                print("No filled companies found for this tender")
            
            # 更新bid_generate.yaml文件
            existing_data = {}
            if os.path.exists(extract_file_path):
                with open(extract_file_path, 'r', encoding='utf-8') as f:
                    existing_data = yaml.safe_load(f) or {}
            
            existing_data['fill_company_list'] = companies
            existing_data['fill_company_count'] = len(companies)
            existing_data['queried_tender_id_for_fill_list'] = tender_id
            
            with open(extract_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(existing_data, f, allow_unicode=True)
            
            print(f"Fill company list saved: {len(companies)} companies found")
        else:
            print(f"Failed to query fill company list: {response_data}")
            pytest.fail(f"Failed to query fill company list: {response_data}")

    @pytest.mark.parametrize('data', read_yaml('./test_data/bid_generate_workflow.yaml'))
    def test_17_query_all_person_no_page(self, api, data):
        """
        步骤26: 查询所有人员不分页
        接口: /prod-api/bid/query/allPerson/noPage
        """
        print("\n" + "=" * 50)
        print("步骤26: 查询所有人员不分页")
        print("=" * 50)

        # 从bid_generate.yaml中读取所需参数
        extract_file_path = './test_data/bid_generate.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                
                # 尝试从已有数据中获取companyId
                company_id = extract_data.get('company_id', '358')  # 使用已有公司ID或默认值
                
                # 如果company_id仍然未设置，尝试从其他地方获取
                if not company_id and extract_data.get('all_companies'):
                    companies = extract_data['all_companies']
                    if companies and len(companies) > 0:
                        first_company = companies[0]
                        company_id = first_company.get('companyId')
                
        else:
            # 使用HAR数据中的默认值
            company_id = '358'

        print(f"Using company ID: {company_id}")

        # 准备请求参数 - 这是一个POST请求，参数在请求体中
        json_data = {
            "companyId": company_id
        }

        # 发送请求
        res = api.request(
            method=data['query_all_person_no_page']['method'],
            path=data['query_all_person_no_page']['path'],
            json=json_data
        )

        # 打印响应结果
        print("Query All Person No Page Response:", res.json())

        # 验证响应状态码
        assert res.status_code == 200, f"Query all person no page failed with status code: {res.status_code}, response: {res.json()}"

        # 提取响应信息
        response_data = res.json()
        if response_data.get('code') == 200:
            persons = response_data.get('data', [])
            print(f"Successfully queried all persons, found {len(persons)} persons")
            
            # 更新bid_generate.yaml文件
            existing_data = {}
            if os.path.exists(extract_file_path):
                with open(extract_file_path, 'r', encoding='utf-8') as f:
                    existing_data = yaml.safe_load(f) or {}
            
            existing_data['all_persons_list'] = persons
            existing_data['persons_count'] = len(persons)
            existing_data['queried_company_id_for_persons'] = company_id
            
            with open(extract_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(existing_data, f, allow_unicode=True)
            
            print(f"All persons list saved: {len(persons)} persons found")
        else:
            print(f"Failed to query all person no page: {response_data}")
            pytest.fail(f"Failed to query all person no page: {response_data}")

    @pytest.mark.parametrize('data', read_yaml('./test_data/bid_generate_workflow.yaml'))
    def test_18_query_bid_filling_list(self, api, data):
        """
        步骤27: 查询投标填写列表
        接口: /prod-api/bid/query/bidFillingList
        """
        print("\n" + "=" * 50)
        print("步骤27: 查询投标填写列表")
        print("=" * 50)

        # 从bid_generate.yaml中读取所需参数
        extract_file_path = './test_data/bid_generate.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                
                # 尝试从已有数据中获取tenderId和companyId
                tender_id = extract_data.get('document_id', '176887627456900000')  # 使用文档ID或默认值
                company_id = extract_data.get('company_id', '358')  # 使用已有公司ID或默认值
                
                # 如果tender_id仍然未设置，尝试从其他地方获取
                if not tender_id and extract_data.get('tender_user_info'):
                    tender_info = extract_data['tender_user_info']
                    if isinstance(tender_info, dict) and 'tenderId' in tender_info:
                        tender_id = tender_info['tenderId']
                    elif isinstance(tender_info, dict) and 'id' in tender_info:
                        tender_id = tender_info['id']
                
                # 如果company_id仍然未设置，尝试从其他地方获取
                if not company_id and extract_data.get('new_company_id'):
                    company_id = extract_data['new_company_id']
                elif not company_id and extract_data.get('all_companies'):
                    companies = extract_data['all_companies']
                    if companies and len(companies) > 0:
                        first_company = companies[0]
                        company_id = first_company.get('companyId')
                
        else:
            # 使用HAR数据中的默认值
            tender_id = '176887627456900000'
            company_id = '358'

        print(f"Using tender ID: {tender_id}")
        print(f"Using company ID: {company_id}")

        # 准备请求参数 - 这是一个GET请求，参数在查询字符串中
        query_params = {
            "tenderId": tender_id,
            "companyId": company_id
        }

        # 发送请求
        res = api.request(
            method=data['query_bid_filling_list']['method'],
            path=data['query_bid_filling_list']['path'],
            params=query_params
        )

        # 打印响应结果
        print("Query Bid Filling List Response:", res.json())

        # 验证响应状态码
        assert res.status_code == 200, f"Query bid filling list failed with status code: {res.status_code}, response: {res.json()}"

        # 提取响应信息
        response_data = res.json()
        if response_data.get('code') == 200:
            filling_list = response_data.get('data', {})
            print(f"Successfully queried bid filling list, data keys: {list(filling_list.keys()) if isinstance(filling_list, dict) else 'N/A'}")
            
            # 更新bid_generate.yaml文件
            existing_data = {}
            if os.path.exists(extract_file_path):
                with open(extract_file_path, 'r', encoding='utf-8') as f:
                    existing_data = yaml.safe_load(f) or {}
            
            existing_data['bid_filling_list'] = filling_list
            existing_data['queried_tender_id_for_filling_list'] = tender_id
            existing_data['queried_company_id_for_filling_list'] = company_id
            
            with open(extract_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(existing_data, f, allow_unicode=True)
            
            print(f"Bid filling list saved, data keys: {list(filling_list.keys()) if isinstance(filling_list, dict) else 'N/A'}")
        else:
            print(f"Failed to query bid filling list: {response_data}")
            pytest.fail(f"Failed to query bid filling list: {response_data}")

    @pytest.mark.parametrize('data', read_yaml('./test_data/bid_generate_workflow.yaml'))
    def test_19_query_all_company_performance(self, api, data):
        """
        步骤28: 查询所有公司业绩
        接口: /prod-api/bid/query/allCompanyPerformance
        """
        print("\n" + "=" * 50)
        print("步骤28: 查询所有公司业绩")
        print("=" * 50)

        # 从bid_generate.yaml中读取所需参数
        extract_file_path = './test_data/bid_generate.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                
                # 尝试从已有数据中获取companyId
                company_id = extract_data.get('company_id', '358')  # 使用已有公司ID或默认值
                
                # 如果company_id仍然未设置，尝试从其他地方获取
                if not company_id and extract_data.get('new_company_id'):
                    company_id = extract_data['new_company_id']
                elif not company_id and extract_data.get('all_companies'):
                    companies = extract_data['all_companies']
                    if companies and len(companies) > 0:
                        first_company = companies[0]
                        company_id = first_company.get('companyId')
                
        else:
            # 使用HAR数据中的默认值
            company_id = '358'

        print(f"Using company ID: {company_id}")

        # 准备请求参数 - 这是一个POST请求，参数在请求体中
        json_data = {
            "projectName": "",
            "beginDate": "",
            "amountRange": "",
            "status": "",
            "pageNum": 1,
            "pageSize": 10,
            "companyId": company_id
        }

        # 发送请求
        res = api.request(
            method=data['query_all_company_performance']['method'],
            path=data['query_all_company_performance']['path'],
            json=json_data
        )

        # 打印响应结果
        print("Query All Company Performance Response:", res.json())

        # 验证响应状态码
        assert res.status_code == 200, f"Query all company performance failed with status code: {res.status_code}, response: {res.json()}"

        # 提取响应信息
        response_data = res.json()
        if response_data.get('code') == 200:
            # 根据API响应结构，数据直接在根级别，而不是在'data'键下
            performance_data = response_data  # 整个响应作为performance_data
            total = response_data.get('total', 0)
            rows = response_data.get('rows', [])  # 直接从response_data获取rows
            print(f"Successfully queried company performance, total: {total}, found {len(rows)} records")
            
            # 更新bid_generate.yaml文件
            existing_data = {}
            if os.path.exists(extract_file_path):
                with open(extract_file_path, 'r', encoding='utf-8') as f:
                    existing_data = yaml.safe_load(f) or {}
            
            existing_data['all_company_performance'] = performance_data
            existing_data['performance_total_count'] = total
            existing_data['performance_rows_count'] = len(rows)
            existing_data['queried_company_id_for_performance'] = company_id
            
            with open(extract_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(existing_data, f, allow_unicode=True)
            
            print(f"Company performance saved, total: {total}, records: {len(rows)}")
        else:
            print(f"Failed to query all company performance: {response_data}")
            pytest.fail(f"Failed to query all company performance: {response_data}")

    @pytest.mark.parametrize('data', read_yaml('./test_data/bid_generate_workflow.yaml'))
    def test_20_query_company_file_page(self, api, data):
        """
        步骤29: 查询公司文件分页
        接口: /prod-api/bid/query/companyFilePage
        """
        print("\n" + "=" * 50)
        print("步骤29: 查询公司文件分页")
        print("=" * 50)

        # 从bid_generate.yaml中读取所需参数
        extract_file_path = './test_data/bid_generate.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                
                # 尝试从已有数据中获取companyId
                company_id = extract_data.get('company_id', '358')  # 使用已有公司ID或默认值
                
                # 如果company_id仍然未设置，尝试从其他地方获取
                if not company_id and extract_data.get('new_company_id'):
                    company_id = extract_data['new_company_id']
                elif not company_id and extract_data.get('all_companies'):
                    companies = extract_data['all_companies']
                    if companies and len(companies) > 0:
                        first_company = companies[0]
                        company_id = first_company.get('companyId')
                
        else:
            # 使用HAR数据中的默认值
            company_id = '358'

        print(f"Using company ID: {company_id}")

        # 准备请求参数 - 这是一个POST请求，参数在请求体中
        json_data = {
            "companyFileName": "",
            "companyFileType": "",
            "pageNum": 1,
            "pageSize": 10,
            "companyId": company_id,
            "status": "有效"
        }

        # 发送请求
        res = api.request(
            method=data['query_company_file_page']['method'],
            path=data['query_company_file_page']['path'],
            json=json_data
        )

        # 打印响应结果
        print("Query Company File Page Response:", res.json())

        # 验证响应状态码
        assert res.status_code == 200, f"Query company file page failed with status code: {res.status_code}, response: {res.json()}"

        # 提取响应信息
        response_data = res.json()
        if response_data.get('code') == 200:
            # 根据API响应结构，数据直接在根级别
            total = response_data.get('total', 0)
            rows = response_data.get('rows', [])
            print(f"Successfully queried company file page, total: {total}, found {len(rows)} records")
            
            # 更新bid_generate.yaml文件
            existing_data = {}
            if os.path.exists(extract_file_path):
                with open(extract_file_path, 'r', encoding='utf-8') as f:
                    existing_data = yaml.safe_load(f) or {}
            
            existing_data['company_file_page_data'] = response_data
            existing_data['company_file_total_count'] = total
            existing_data['company_file_rows_count'] = len(rows)
            existing_data['company_file_rows_list'] = rows
            existing_data['queried_company_id_for_company_files'] = company_id
            
            with open(extract_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(existing_data, f, allow_unicode=True)
            

            
            print(f"Company file page saved, total: {total}, records: {len(rows)}")
            if rows and len(rows) > 0:
                first_file = rows[0]
                print(f"First file - Name: {first_file.get('companyFileName')}, Type: {first_file.get('companyFileType')}, Status: {first_file.get('status')}")
        else:
            print(f"Failed to query company file page: {response_data}")
            pytest.fail(f"Failed to query company file page: {response_data}")

    @pytest.mark.parametrize('data', read_yaml('./test_data/bid_generate_workflow.yaml'))
    def test_21_query_financial_page(self, api, data):
        """
        步骤30: 查询财务分页
        接口: /prod-api/bid/query/financialPage
        """
        print("\n" + "=" * 50)
        print("步骤30: 查询财务分页")
        print("=" * 50)

        # 从bid_generate.yaml中读取所需参数
        extract_file_path = './test_data/bid_generate.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                
                # 尝试从已有数据中获取companyId
                company_id = extract_data.get('company_id', '358')  # 使用已有公司ID或默认值
                
                # 如果company_id仍然未设置，尝试从其他地方获取
                if not company_id and extract_data.get('new_company_id'):
                    company_id = extract_data['new_company_id']
                elif not company_id and extract_data.get('all_companies'):
                    companies = extract_data['all_companies']
                    if companies and len(companies) > 0:
                        first_company = companies[0]
                        company_id = first_company.get('companyId')
                
        else:
            # 使用HAR数据中的默认值
            company_id = '358'

        print(f"Using company ID: {company_id}")

        # 准备请求参数 - 这是一个POST请求，参数在请求体中
        json_data = {
            "financialName": "",
            "financialType": "",
            "financialTime": "",
            "pageNum": 1,
            "pageSize": 10,
            "companyId": company_id
        }

        # 发送请求
        res = api.request(
            method=data['query_financial_page']['method'],
            path=data['query_financial_page']['path'],
            json=json_data
        )

        # 打印响应结果
        print("Query Financial Page Response:", res.json())

        # 验证响应状态码
        assert res.status_code == 200, f"Query financial page failed with status code: {res.status_code}, response: {res.json()}"

        # 提取响应信息
        response_data = res.json()
        if response_data.get('code') == 200:
            # 根据API响应结构，数据直接在根级别
            total = response_data.get('total', 0)
            rows = response_data.get('rows', [])
            print(f"Successfully queried financial page, total: {total}, found {len(rows)} records")
            
            # 更新bid_generate.yaml文件
            existing_data = {}
            if os.path.exists(extract_file_path):
                with open(extract_file_path, 'r', encoding='utf-8') as f:
                    existing_data = yaml.safe_load(f) or {}
            
            existing_data['financial_page_data'] = response_data
            existing_data['financial_total_count'] = total
            existing_data['financial_rows_count'] = len(rows)
            existing_data['financial_rows_list'] = rows
            existing_data['queried_company_id_for_financial'] = company_id
            
            with open(extract_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(existing_data, f, allow_unicode=True)
            

            
            print(f"Financial page saved, total: {total}, records: {len(rows)}")
            if rows and len(rows) > 0:
                first_financial = rows[0]
                print(f"First financial - Name: {first_financial.get('financialName')}, Type: {first_financial.get('financialType')}, Time: {first_financial.get('financialTime')}")
        else:
            print(f"Failed to query financial page: {response_data}")
            pytest.fail(f"Failed to query financial page: {response_data}")

    @pytest.mark.parametrize('data', read_yaml('./test_data/bid_generate_workflow.yaml'))
    def test_22_gen_save_company(self, api, data):
        """
        步骤31: 生成保存公司信息
        数据来源：
        - 公司信息：test_15_select_all_company
        - 人员信息：test_17_query_all_person_no_page
        - 业绩信息：test_19_query_all_company_performance
        - 财务信息：test_21_query_financial_page
        接口: /prod-api/bid/genSaveCompany
        """
        print("\n" + "=" * 50)
        print("步骤31: 生成保存公司信息")
        print("=" * 50)

        # 加载数据
        extract_file_path = './test_data/bid_generate.yaml'
        extract_data = self._load_yaml_data(extract_file_path)

        # 获取基础参数
        tender_id = self._get_value_from_data(extract_data, 'document_id', '176887627456900000')
        company_id = '358'

        print(f"Using tender ID: {tender_id}")
        print(f"Using company ID: {company_id}")

        # ✨ 从前面接口的返回数据中动态构建请求数据
        json_data = self._build_gen_save_company_request(extract_data, company_id, tender_id)

        print(f"📊 数据来源统计：财务数据 {len(json_data.get('financialList', []))} 条，"
              f"业绩数据 {len(json_data.get('performanceList', []))} 条")

        # 发送请求
        res = api.request(
            method=data['gen_save_company']['method'],
            path=data['gen_save_company']['path'],
            json=json_data
        )

        # 打印响应结果
        print("Gen Save Company Response:", res.json())

        # 验证响应状态码
        assert res.status_code == 200, f"Gen save company failed with status code: {res.status_code}, response: {res.json()}"

        # 提取响应信息
        response_data = res.json()
        if response_data.get('code') == 200:
            saved_company_id = response_data.get('data')
            print(f"✅ Successfully saved company information, company ID: {saved_company_id}")

            # 更新bid_generate.yaml文件
            self._update_yaml_data(extract_file_path, {
                'saved_company_info': response_data,
                'saved_company_id': saved_company_id,
                'save_company_request_data': json_data,
                'used_tender_id_for_save_company': tender_id,
                'used_company_id_for_save_company': company_id
            })

            print(f"Company information saved, company ID: {saved_company_id}")
        else:
            print(f"Failed to save company information: {response_data}")
            pytest.fail(f"Failed to save company information: {response_data}")

    @pytest.mark.parametrize('data', read_yaml('./test_data/bid_generate_workflow.yaml'))
    def test_23_fill_busi_company(self, api, data):
        """
        步骤32: 填充业务公司信息
        数据来源：
        - 公司信息：test_15_select_all_company
        - 人员信息：test_17_query_all_person_no_page
        - 业绩信息：test_19_query_all_company_performance
        - 财务信息：test_21_query_financial_page
        接口: /prod-api/bid/fill/busi/company
        """
        print("\n" + "=" * 50)
        print("步骤32: 填充业务公司信息")
        print("=" * 50)

        # 加载数据
        extract_file_path = './test_data/bid_generate.yaml'
        extract_data = self._load_yaml_data(extract_file_path)

        # 获取基础参数
        tender_id = self._get_value_from_data(extract_data, 'document_id', '176838149284700000')
        company_id = 358

        print(f"Using tender ID: {tender_id}")


        # ✨ 从前面接口的返回数据中动态构建请求数据
        today_date = datetime.now().strftime('%Y-%m-%d')

        # 获取动态数据
        financial_list = self._get_financial_list(extract_data, limit=3)
        performance_list = self._get_performance_list(extract_data, limit=1)
        company_file_list = self._get_company_file_list(extract_data, limit=2)
        company_file_ids = self._get_company_files(extract_data, limit=2)
        financial_ids = self._get_financial_ids(extract_data, limit=3)
        project_ids = self._get_project_ids(extract_data, limit=1)
        person_ids = self._get_all_person_ids(extract_data)

        # 从bid_filling_list中获取要求信息
        ent_finance_require = self._get_finance_require(extract_data)
        ent_per_require = self._get_per_require(extract_data)
        ent_cer_require = self._get_cer_require(extract_data)

        # 从tender_user_info中获取招标项目信息
        tender_info = self._get_tender_project_info(extract_data)

        json_data = {
            "companyName": self._get_company_name_from_yaml(company_id, extract_data),
            "legal": self._get_company_legal(company_id, extract_data),
            "legalCard": None,
            "authPersonId": 188,
            "projectPersonId": 187,
            "techPersonId": 188,
            "constructPersonId": 189,
            "designPersonId": 190,
            "bidDate": today_date,
            "personIds": person_ids if person_ids else [],
            "companyFileList": company_file_list if company_file_list else [],
            "financialList": financial_list if financial_list else [],
            "entFinanceRequire": ent_finance_require if ent_finance_require else [],
            "entPerRequire": ent_per_require if ent_per_require else [],

            "performanceList": performance_list if performance_list else [],
            "entCerRequire": ent_cer_require if ent_cer_require else [],

            "companyId": '112233',
            "tenderId": str(tender_id),
            "projectIds": project_ids if project_ids else ["108"],
            "companyFileIds": company_file_ids if company_file_ids else [],

            "financialIds": financial_ids if financial_ids else ["187", "186", "185"],
            "tenderProjectCode": tender_info.get('tenderProjectCode', ''),
            "tenderProjectName": tender_info.get('tenderProjectName', ''),
            "tenderCompanyName": tender_info.get('tenderCompanyName', ''),
            "tenderProjectBudget": tender_info.get('tenderProjectBudget', ''),
            "newCompanyId": str(company_id),
            "skipCompany": "1"
        }

        print(f"📊 数据来源统计：财务数据 {len(json_data.get('financialList', []))} 条，"
              f"业绩数据 {len(json_data.get('performanceList', []))} 条，"
              f"公司文件 {len(json_data.get('companyFileList', []))} 个，"
              f"人员ID {len(json_data.get('personIds', []))} 个")
        print(f"🔍 调试信息：json_data中的companyId = {json_data['companyId']}, newCompanyId = {json_data['newCompanyId']}")
        print(f"👥 人员ID列表：{json_data.get('personIds', [])}")
        print(f"📁 公司文件列表：{len(json_data.get('companyFileList', []))} 个文件")
        print(f"🆔 公司文件ID列表：{json_data.get('companyFileIds', [])}")
        print(f"💰 财务要求：{len(json_data.get('entFinanceRequire', []))} 条")
        print(f"👨‍💼 人员要求：{len(json_data.get('entPerRequire', []))} 条")
        print(f"📜 证书要求：{len(json_data.get('entCerRequire', []))} 条")
        print(f"📋 招标项目信息：")
        print(f"   - tenderProjectCode: {tender_info.get('tenderProjectCode')}")
        print(f"   - tenderProjectName: {tender_info.get('tenderProjectName')}")
        print(f"   - tenderCompanyName: {tender_info.get('tenderCompanyName')}")
        print(f"   - tenderProjectBudget: {tender_info.get('tenderProjectBudget')}")

        # 调试：打印tender_user_info中的原始字段
        print(f"🔍 调试信息（YAML原始字段）：")
        tender_user_info = extract_data.get('tender_user_info', {})
        print(f"   - projectCode: {tender_user_info.get('projectCode', 'NOT_FOUND')}")
        print(f"   - projectName: {tender_user_info.get('projectName', 'NOT_FOUND')}")

        # 输出完整的json_data
        print("\n" + "=" * 80)
        print("📋 完整的请求数据 (json_data):")
        print("=" * 80)
        print(json.dumps(json_data, indent=2, ensure_ascii=False))
        print("=" * 80 + "\n")

        # 发送请求（带重试机制）
        max_retries = 3
        res = None
        request_success = False

        for attempt in range(max_retries):
            try:
                print(f"🔄 发送请求（尝试 {attempt + 1}/{max_retries}）...")
                res = api.request(
                    method=data['fill_busi_company']['method'],
                    path=data['fill_busi_company']['path'],
                    json=json_data
                )

                # 检查响应状态
                if res.status_code == 200:
                    print(f"✅ 请求成功（状态码: {res.status_code}）")
                    request_success = True
                    break
                elif res.status_code == 502:
                    print(f"⚠️  服务器返回 502 Bad Gateway")
                    if attempt < max_retries - 1:
                        wait_time = 5
                        print(f"⏳ 等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                    else:
                        print(f"❌ 已达到最大重试次数 ({max_retries})，放弃重试")
                else:
                    print(f"❌ 请求失败（状态码: {res.status_code}）")
                    break

            except Exception as e:
                print(f"❌ 请求异常: {e}")
                if attempt < max_retries - 1:
                    wait_time = 5
                    print(f"⏳ 等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ 已达到最大重试次数 ({max_retries})，放弃重试")
                    break

        # 检查请求是否最终成功
        if not request_success or res is None:
            error_msg = f"请求失败，状态码: {res.status_code if res else 'N/A'}"
            if res and res.status_code == 502:
                error_msg += "（服务器502错误，可能是服务器过载或网络问题）"
            pytest.fail(error_msg)

        # 打印响应结果
        print("Fill Busi Company Response:", res.json())

        # 验证响应状态码
        assert res.status_code == 200, f"Fill busi company failed with status code: {res.status_code}, response: {res.json()}"

        # 提取响应信息
        response_data = res.json()
        if response_data.get('code') == 200:
            busiId = response_data.get('data')
            print(f"✅ Successfully filled company information, busiId: {busiId}")

            # 更新bid_generate.yaml文件
            self._update_yaml_data(extract_file_path, {
                'filled_company_info': response_data,
                'busiId': busiId,
                'fill_company_request_data': json_data,
                'used_tender_id_for_fill_company': tender_id,
                'used_company_id_for_fill_company': company_id
            })

            print(f"Company fill information saved, busiId: {busiId}")
        else:
            print(f"Failed to fill company information: {response_data}")
            pytest.fail(f"Failed to fill company information: {response_data}")

    @pytest.mark.parametrize('data', read_yaml('./test_data/bid_generate_workflow.yaml'))
    def test_24_generate_catalogue_and_page_stream(self, api, data):
        """
        步骤33: 生成业务目录和页面流
        接口: /prod-api/bid/generate/busi/catalogueAndPage/stream
        """
        print("\n" + "=" * 50)
        print("步骤33: 生成业务目录和页面流")
        print("=" * 50)

        # 从bid_generate.yaml中读取所需参数
        extract_file_path = './test_data/bid_generate.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                
                # 尝试从已有数据中获取参数
                busi_as_id = extract_data.get('busiId', '176897719826900000')  # 使用busiId或默认值
                tender_id = extract_data.get('document_id', '176838149284700000')  # 使用文档ID或默认值
                company_id = extract_data.get('company_id', '358')  # 使用已有公司ID或默认值
                
                # 如果busi_as_id仍然未设置，尝试从其他地方获取
                if not busi_as_id and extract_data.get('busiId'):
                    busi_as_id = extract_data['busiId']
                elif not busi_as_id and extract_data.get('new_bid_as_info'):
                    bid_as_info = extract_data['new_bid_as_info']
                    if isinstance(bid_as_info, dict) and 'id' in bid_as_info:
                        busi_as_id = bid_as_info['id']
                    elif isinstance(bid_as_info, dict) and 'busiAsId' in bid_as_info:
                        busi_as_id = bid_as_info['busiAsId']
                

                
        else:
            # 使用HAR数据中的默认值
            busi_as_id = '176897719826900000'
            tender_id = '176838149284700000'
            company_id = '358'

        print(f"Using busiAs ID: {busi_as_id}")
        print(f"Using tender ID: {tender_id}")
        print(f"Using company ID: {company_id}")

        # 准备请求参数 - 这是一个POST请求，参数以multipart/form-data格式发送
        # 根据HAR数据显示，包含busiAsId, tenderId, companyId, docFormat, isFillCompany
        # docFormat是一个JSON字符串，根据HAR数据编码为URL格式
        doc_format_json = {
            "pageFormat": {
                "top": "2.54",
                "bottom": "2.54",
                "left": "3.18",
                "right": "3.18"
            },
            "level1": {
                "font": "黑体",
                "fontSize": "15",
                "align": "left",
                "bold": True,
                "indent": "0",
                "lineSpace": "1.5"
            },
            "level2": {
                "font": "黑体",
                "fontSize": "14",
                "align": "left",
                "bold": True,
                "indent": "0",
                "lineSpace": "1.5"
            },
            "level3": {
                "font": "黑体",
                "fontSize": "14",
                "align": "left",
                "bold": True,
                "indent": "0",
                "lineSpace": "1.5"
            },
            "level4": {
                "font": "黑体",
                "fontSize": "14",
                "align": "left",
                "bold": True,
                "indent": "0",
                "lineSpace": "1.5"
            },
            "level5": {
                "font": "黑体",
                "fontSize": "14",
                "align": "left",
                "bold": True,
                "indent": "0",
                "lineSpace": "1.5"
            },
            "textFormat": {
                "font": "宋体",
                "fontSize": "12",
                "align": "left",
                "bold": False,
                "indent": "2",
                "lineSpace": "1.5"
            },
            "number": "1",
            "cover": "1",
            "autoNumber": "0"
        }
        
        import json
        doc_format_str = json.dumps(doc_format_json, ensure_ascii=False)
        
        # 准备multipart/form-data参数
        form_data = {
            "busiAsId": (None, str(busi_as_id)),
            "tenderId": (None, str(tender_id)),
            "companyId": (None, str(company_id)),
            "docFormat": (None, doc_format_str),
            "isFillCompany": (None, "1")  # 根据HAR数据，值为1
        }

        # 发送请求 - 这是一个流式请求，返回SSE数据
        res = api.request(
            method=data['generate_catalogue_and_page_stream']['method'],
            path=data['generate_catalogue_and_page_stream']['path'],
            save_cookie=True,  # 根据HAR数据中的cookies信息
            files=form_data
        )

        # 打印响应结果
        print("Generate Catalogue And Page Stream Response:", res.text[:500])  # 只打印前500字符，因为可能是长流数据

        # 验证响应状态码
        assert res.status_code == 200, f"Generate catalogue and page stream failed with status code: {res.status_code}, response: {res.text[:200]}"

        # 处理SSE流数据
        sse_content = res.text
        print(f"Received SSE content, length: {len(sse_content)}")
        
        # 解析SSE事件
        events = self.parse_sse_events(sse_content)
        print(f"Parsed {len(events)} SSE events")
        
        for event in events:
            # 确保中文字符正确显示
            event_data_display = event['data']
            try:
                # 尝试多种编码方式来正确显示中文
                if isinstance(event_data_display, str) and any(ord(char) > 127 for char in event_data_display):
                    # 如果包含非ASCII字符，尝试不同的解码方式
                    try:
                        # 首先尝试检测并修复双重编码的问题
                        event_data_display = event_data_display.encode('raw_unicode_escape').decode('utf-8')
                    except:
                        try:
                            # 尝试unicode转义解码
                            import codecs
                            event_data_display = codecs.decode(event_data_display, 'unicode_escape')
                        except:
                            # 最后尝试直接UTF-8解码
                            event_data_display = event_data_display.encode('latin1').decode('utf-8')
            except Exception as e:
                # 如果所有解码都失败，保持原始数据
                pass
            print(f"Event: {event['event']}, Data: {event_data_display}")
        
        # 提取最终的文档ID
        final_doc_id = None
        for event in events:
            if event['event'] == '生成成功':
                # 尝试从数据中提取文档ID
                data_value = event['data']
                # 查找数字序列，这可能是文档ID
                matches = re.findall(r'\d+', str(data_value))
                if matches:
                    # 使用最长的数字串作为ID（通常生成的ID较长）
                    longest_match = max(matches, key=len)
                    final_doc_id = longest_match
                    break
        
        # 如果没有从SSE中提取到ID，尝试其他方式
        if not final_doc_id:
            # 遍历所有事件，查找包含数字的data字段
            for event in events:
                data_part = event['data']
                matches = re.findall(r'\d+', str(data_part))
                if matches:
                    # 使用最长的匹配项
                    longest_match = max(matches, key=len)
                    if len(longest_match) >= 10:  # 通常文档ID比较长
                        final_doc_id = longest_match
                        break
        
        print(f"Extracted document ID: {final_doc_id}")
        
        # 更新bid_generate.yaml文件
        existing_data = {}
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                existing_data = yaml.safe_load(f) or {}
        
        existing_data['catalogue_and_page_stream_result'] = events
        existing_data['generated_document_id'] = final_doc_id
        existing_data['used_busi_as_id_for_generation'] = busi_as_id
        existing_data['used_tender_id_for_generation'] = tender_id
        existing_data['used_company_id_for_generation'] = company_id
        
        with open(extract_file_path, 'w', encoding='utf-8') as f:
            yaml.dump(existing_data, f, allow_unicode=True)
        

        
        print(f"Catalogue and page generation stream saved, document ID: {final_doc_id}")

    def parse_sse_events(self, sse_content):
        """
        解析SSE（Server-Sent Events）内容
        """
        events = []
        lines = sse_content.strip().split('\n')
        current_event = {'event': '', 'data': ''}
        
        for line in lines:
            line = line.strip()
            if line.startswith('id:'):
                # 提取ID信息，可以用于调试
                continue
            elif line.startswith('event:'): 
                current_event['event'] = line.split(':', 1)[1].strip()
            elif line.startswith('data:'):
                current_event['data'] = line.split(':', 1)[1].strip()
            elif line == '':  # 空行表示事件结束
                if current_event['event'] or current_event['data']:
                    # 解码中文内容 - 处理可能的编码问题
                    raw_data = current_event['data']
                    decoded_data = self._decode_chinese_text(raw_data)
                    
                    events.append({'event': current_event['event'], 'data': decoded_data})
                    current_event = {'event': '', 'data': ''}
        
        # 处理最后一个事件（如果没有以空行结尾）
        if current_event['event'] or current_event['data']:
            raw_data = current_event['data']
            decoded_data = self._decode_chinese_text(raw_data)
            events.append({'event': current_event['event'], 'data': decoded_data})
        
        return events
    
    def _decode_chinese_text(self, text):
        """
        专门用于解码中文文本的方法
        """
        if not isinstance(text, str):
            return text
            
        try:
            # 检查是否是双重编码的UTF-8字节序列
            if all(ord(c) < 256 for c in text):  # 所有字符都在ASCII范围内，可能是编码后的字节串
                # 尝试将其视为Latin-1编码然后解码为UTF-8
                byte_string = text.encode('latin1')
                decoded_text = byte_string.decode('utf-8')
                return decoded_text
        except:
            pass
            
        try:
            # 尝试unicode转义解码
            import codecs
            return codecs.decode(text, 'unicode_escape')
        except:
            pass
            
        try:
            # 尝试raw_unicode_escape然后UTF-8解码
            return text.encode('raw_unicode_escape').decode('utf-8')
        except:
            pass
            
        try:
            # 尝试URL解码
            return unquote(text)
        except:
            pass
            
        # 如果所有方法都失败，返回原文本
        return text
    
    def _get_company_name_from_yaml(self, company_id, extract_data=None):
        """
        从bid_generate.yaml文件中获取指定companyId的companyName

        Args:
            company_id: 公司ID
            extract_data: 可选，如果提供则直接使用，避免重复加载文件
        """
        # 如果没有提供extract_data，自己加载
        if extract_data is None:
            extract_file_path = './test_data/bid_generate.yaml'
            if os.path.exists(extract_file_path):
                with open(extract_file_path, 'r', encoding='utf-8') as f:
                    extract_data = yaml.safe_load(f)
            else:
                return f'Company_{company_id}'

        # 从extract_data中查找公司名称
        if extract_data and 'all_companies' in extract_data:
            all_companies = extract_data['all_companies']
            if isinstance(all_companies, list):
                for company in all_companies:
                    if str(company.get('companyId')) == str(company_id):
                        return company.get('companyName', f'Company_{company_id}')

        # 如果在all_companies中未找到，尝试直接从extract_data中查找
        if extract_data and str(extract_data.get('companyId')) == str(company_id):
            return extract_data.get('companyName', f'Company_{company_id}')

        # 如果未找到对应公司，返回默认值
        return f'Company_{company_id}'

    def _get_company_legal(self, company_id, extract_data=None):
        """
        从all_companies中获取指定companyId的legal（法人）值

        Args:
            company_id: 公司ID
            extract_data: 可选，如果提供则直接使用
        """
        # 如果没有提供extract_data，自己加载
        if extract_data is None:
            extract_file_path = './test_data/bid_generate.yaml'
            if os.path.exists(extract_file_path):
                with open(extract_file_path, 'r', encoding='utf-8') as f:
                    extract_data = yaml.safe_load(f)
            else:
                return ""

        # 从extract_data中查找公司的legal值
        if extract_data and 'all_companies' in extract_data:
            all_companies = extract_data['all_companies']
            if isinstance(all_companies, list):
                for company in all_companies:
                    if str(company.get('companyId')) == str(company_id):
                        return company.get('legal', '')

        # 如果未找到，返回空字符串
        return ""

    def _get_tender_project_info(self, extract_data):
        """
        从tender_user_info中获取招标项目信息

        Args:
            extract_data: bid_generate.yaml中的数据

        Returns:
            dict: 包含tenderProjectCode, tenderProjectName, tenderCompanyName, tenderProjectBudget的字典
        """
        tender_user_info = extract_data.get('tender_user_info', {})

        # 如果tender_user_info是字典，尝试获取字段
        if isinstance(tender_user_info, dict):
            # 优先使用不带前缀的字段名（YAML中的实际字段名）
            project_info = {
                'tenderProjectCode': (
                    tender_user_info.get('projectCode', '') or
                    tender_user_info.get('tenderProjectCode', '')
                ),
                'tenderProjectName': (
                    tender_user_info.get('projectName', '') or
                    tender_user_info.get('tenderProjectName', '')
                ),
                'tenderCompanyName': (
                    tender_user_info.get('tenderCompanyName', '') or
                    tender_user_info.get('bidCompanyName', '')
                ),
                'tenderProjectBudget': (
                    tender_user_info.get('tenderProjectBudget', '') or
                    tender_user_info.get('bidBond', '')
                )
            }

            # 如果直接获取为空，尝试从嵌套的列表中获取（如果有projectList或类似的字段）
            if not any(project_info.values()):
                # 尝试从可能的列表字段中获取第一个项目的信息
                for list_key in ['projectList', 'projects', 'tenderProjects', 'list']:
                    if list_key in tender_user_info and isinstance(tender_user_info[list_key], list):
                        project_list = tender_user_info[list_key]
                        if project_list and len(project_list) > 0:
                            first_project = project_list[0]
                            if isinstance(first_project, dict):
                                project_info = {
                                    'tenderProjectCode': (
                                        first_project.get('projectCode', '') or
                                        first_project.get('tenderProjectCode', '')
                                    ),
                                    'tenderProjectName': (
                                        first_project.get('projectName', '') or
                                        first_project.get('tenderProjectName', '')
                                    ),
                                    'tenderCompanyName': (
                                        first_project.get('tenderCompanyName', '') or
                                        first_project.get('bidCompanyName', '')
                                    ),
                                    'tenderProjectBudget': (
                                        first_project.get('tenderProjectBudget', '') or
                                        first_project.get('bidBond', '')
                                    )
                                }
                                break

            return project_info

        # 如果tender_user_info不是字典或为空，返回空值
        return {
            'tenderProjectCode': '',
            'tenderProjectName': '',
            'tenderCompanyName': '',
            'tenderProjectBudget': ''
        }

    def _load_yaml_data(self, file_path):
        """加载YAML文件数据"""
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}

    def _get_value_from_data(self, data, key, default=None):
        """从数据中获取值，支持多层级查找"""
        if data and key in data:
            return data[key]
        return default

    def _get_company_id_from_data(self, extract_data):
        """从数据中获取公司ID"""
        # 尝试从多个地方获取company_id
        company_id = self._get_value_from_data(extract_data, 'company_id')
        if not company_id:
            company_id = self._get_value_from_data(extract_data, 'new_company_id')
        if not company_id and extract_data.get('all_companies'):
            companies = extract_data['all_companies']
            if companies and len(companies) > 0:
                company_id = companies[0].get('companyId')
        return company_id if company_id else '358'

    def _get_persons_by_role(self, extract_data, role_name=None):
        """从人员列表中获取指定角色的人员，如果未指定角色则返回第一个"""
        persons = extract_data.get('all_persons_list', [])
        if not persons:
            return None

        if role_name:
            # 查找指定角色的人员
            for person in persons:
                if role_name in person.get('personName', ''):
                    return person
            # 如果未找到，返回第一个
            return persons[0] if persons else None
        return persons[0] if persons else None

    def _get_financial_list(self, extract_data, limit=3):
        """从财务数据中获取财务列表"""
        financial_data = extract_data.get('financial_page_data', {})
        if financial_data:
            rows = financial_data.get('rows', [])
            # 转换为API需要的格式
            financial_list = []
            for item in rows[:limit]:
                financial_list.append({
                    "financialId": str(item.get('financialId', '')),
                    "financialTime": item.get('financialTime', ''),
                    "financialType": item.get('financialType', ''),
                    "financialName": item.get('financialName', ''),
                    "entryTime": item.get('entryTime', ''),
                    "financialFileUrl": item.get('financialFileUrl', ''),
                    "note": item.get('note', ''),
                    "companyId": str(item.get('companyId', '')),
                    "createId": str(item.get('createId', '')),
                    "updateTime": item.get('updateTime', ''),
                    "financialFileName": item.get('financialFileName', '')
                })
            return financial_list
        return []

    def _get_performance_list(self, extract_data, limit=1):
        """从业绩数据中获取业绩列表"""
        performance_data = extract_data.get('all_company_performance', {})
        if performance_data:
            rows = performance_data.get('rows', [])
            # 转换为API需要的格式
            performance_list = []
            for item in rows[:limit]:
                performance_list.append({
                    "createBy": item.get('createBy'),
                    "createTime": item.get('createTime'),
                    "updateBy": item.get('updateBy'),
                    "updateTime": item.get('updateTime'),
                    "remark": item.get('remark'),
                    "beginTime": item.get('beginTime'),
                    "endTime": item.get('endTime'),
                    "pageNum": item.get('pageNum'),
                    "pageSize": item.get('pageSize'),
                    "companyId": str(item.get('companyId', '')),
                    "projectId": str(item.get('projectId', '')),
                    "projectName": item.get('projectName', ''),
                    "contractAmount": str(item.get('contractAmount', '')),
                    "constructionOrganizationName": item.get('constructionOrganizationName', ''),
                    "projectLead": str(item.get('projectLead', '')),
                    "projectLeadName": item.get('projectLeadName', ''),
                    "technicalLead": str(item.get('technicalLead', '')),
                    "technicalLeadName": item.get('technicalLeadName', ''),
                    "performanceClassification": item.get('performanceClassification', ''),
                    "projectDate": item.get('projectDate', []),
                    "constructionOrganizationPhone": item.get('constructionOrganizationPhone', ''),
                    "status": item.get('status', ''),
                    "projectCode": item.get('projectCode', ''),
                    "projectAddress": item.get('projectAddress', ''),
                    "constructionOrganizationPerson": item.get('constructionOrganizationPerson', ''),
                    "completionRegistrationNumber": item.get('completionRegistrationNumber', ''),
                    "tenderAmount": str(item.get('tenderAmount', '')),
                    "bidAmount": str(item.get('bidAmount', '')),
                    "settlementAmount": str(item.get('settlementAmount', '')),
                    "actualArea": str(item.get('actualArea', '')),
                    "projectQuality": item.get('projectQuality', ''),
                    "projectCost": str(item.get('projectCost', '')),
                    "otherEngineeringFeatures": item.get('otherEngineeringFeatures', ''),
                    "note": item.get('note', ''),
                    "beginDate": item.get('beginDate', ''),
                    "endDate": item.get('endDate', ''),
                    "noticeOfSuccessfulBidResultRes": item.get('noticeOfSuccessfulBidResultRes'),
                    "noticeOfSuccessfulBidResultFileName": item.get('noticeOfSuccessfulBidResultFileName'),
                    "constructionPermitRes": item.get('constructionPermitRes'),
                    "contractRes": item.get('contractRes'),
                    "acceptanceReportRes": item.get('acceptanceReportRes'),
                    "contractFileName": item.get('contractFileName'),
                    "acceptanceReportFileName": item.get('acceptanceReportFileName'),
                    "amountRange": item.get('amountRange')
                })
            return performance_list
        return []

    def _get_company_files(self, extract_data, limit=2):
        """从公司文件数据中获取文件ID列表"""
        file_data = extract_data.get('company_file_page_data', {})
        if file_data:
            rows = file_data.get('rows', [])
            file_ids = []
            for item in rows[:limit]:
                file_ids.append(str(item.get('companyFileId', '')))
            return file_ids
        return []

    def _get_company_file_list(self, extract_data, limit=2):
        """
        从公司文件数据中获取完整的文件对象列表

        Args:
            extract_data: bid_generate.yaml中的数据
            limit: 最多获取多少个文件

        Returns:
            list: 包含完整文件对象的列表
        """
        file_data = extract_data.get('company_file_page_data', {})
        if file_data:
            rows = file_data.get('rows', [])
            file_list = []
            for item in rows[:limit]:
                file_list.append({
                    "companyFileId": str(item.get('companyFileId', '')),
                    "companyFileType": item.get('companyFileType', ''),
                    "companyFileUrl": item.get('companyFileUrl', ''),
                    "companyId": str(item.get('companyId', '')),
                    "companyFileName": item.get('companyFileName', ''),
                    "issueDate": item.get('issueDate', ''),
                    "validDate": item.get('validDate', ''),
                    "status": item.get('status', ''),
                    "companyFileCode": item.get('companyFileCode', ''),
                    "authority": item.get('authority', ''),
                    "updateTime": item.get('updateTime', ''),
                    "createId": str(item.get('createId', '')),
                    "isValid": item.get('isValid', ''),
                    "fileName": item.get('fileName', '')
                })
            return file_list
        return []

    def _get_financial_ids(self, extract_data, limit=3):
        """从财务数据中获取财务ID列表"""
        financial_data = extract_data.get('financial_page_data', {})
        if financial_data:
            rows = financial_data.get('rows', [])
            financial_ids = []
            for item in rows[:limit]:
                financial_ids.append(str(item.get('financialId', '')))
            return financial_ids
        return []

    def _get_project_ids(self, extract_data, limit=1):
        """从业绩数据中获取项目ID列表"""
        performance_data = extract_data.get('all_company_performance', {})
        if performance_data:
            rows = performance_data.get('rows', [])
            project_ids = []
            for item in rows[:limit]:
                project_ids.append(str(item.get('projectId', '')))
            return project_ids
        return []

    def _get_all_person_ids(self, extract_data):
        """
        从all_persons_list中获取所有人员ID列表

        Args:
            extract_data: bid_generate.yaml中的数据

        Returns:
            list: 包含所有人员ID的列表
        """
        persons_list = extract_data.get('all_persons_list', [])

        if isinstance(persons_list, list) and persons_list:
            person_ids = []
            for person in persons_list:
                person_id = person.get('人员ID')
                if person_id:
                    person_ids.append(str(person_id))
            return person_ids

        return []

    def _get_finance_require(self, extract_data):
        """
        从bid_filling_list中获取财务要求entFinanceRequire

        Args:
            extract_data: bid_generate.yaml中的数据

        Returns:
            list: 财务要求列表
        """
        bid_filling_list = extract_data.get('bid_filling_list', {})

        if isinstance(bid_filling_list, dict):
            ent_finance_require = bid_filling_list.get('entFinanceRequire', [])
            if isinstance(ent_finance_require, list):
                return ent_finance_require

        return []

    def _get_per_require(self, extract_data):
        """
        从bid_filling_list中获取人员要求entPerRequire

        Args:
            extract_data: bid_generate.yaml中的数据

        Returns:
            list: 人员要求列表
        """
        bid_filling_list = extract_data.get('bid_filling_list', {})

        if isinstance(bid_filling_list, dict):
            ent_per_require = bid_filling_list.get('entPerRequire', [])
            if isinstance(ent_per_require, list):
                return ent_per_require

        return []

    def _get_cer_require(self, extract_data):
        """
        从bid_filling_list中获取证书要求entCerRequire

        Args:
            extract_data: bid_generate.yaml中的数据

        Returns:
            list: 证书要求列表
        """
        bid_filling_list = extract_data.get('bid_filling_list', {})

        if isinstance(bid_filling_list, dict):
            ent_cer_require = bid_filling_list.get('entCerRequire', [])
            if isinstance(ent_cer_require, list):
                return ent_cer_require

        return []

    def _build_gen_save_company_request(self, extract_data, company_id, tender_id):
        """
        构建gen_save_company接口的请求数据
        从前面接口的返回数据中动态获取
        """
        today_date = datetime.now().strftime('%Y-%m-%d')

        # 获取公司名称
        company_name = self._get_company_name_from_yaml(company_id)

        # 获取人员信息（如果有的话）
        auth_person = self._get_persons_by_role(extract_data)
        project_person = self._get_persons_by_role(extract_data, '项目')
        tech_person = self._get_persons_by_role(extract_data, '技术')

        # 获取财务列表
        financial_list = self._get_financial_list(extract_data, limit=3)
        # 如果没有财务数据，使用默认示例
        if not financial_list:
            financial_list = [
                {
                    "financialId": "",
                    "financialTime": "2025-11",
                    "financialType": "缴纳社保证明",
                    "financialName": "2025-11缴纳社保证明",
                    "entryTime": "",
                    "financialFileUrl": "",
                    "note": "",
                    "companyId": str(company_id),
                    "createId": "",
                    "updateTime": "",
                    "financialFileName": ""
                }
            ]

        # 获取业绩列表
        performance_list = self._get_performance_list(extract_data, limit=1)
        # 如果没有业绩数据，使用默认示例
        if not performance_list:
            performance_list = [
                {
                    "companyId": str(company_id),
                    "projectId": "",
                    "projectName": "",
                    "contractAmount": "",
                    "constructionOrganizationName": "",
                    "status": ""
                }
            ]

        # 构建请求数据
        json_data = {
            "companyName": company_name,
            "legal": "",
            "legalCard": None,
            "authPersonId": auth_person.get('personId') if auth_person else 187,
            "projectPersonId": project_person.get('personId') if project_person else 187,
            "techPersonId": tech_person.get('personId') if tech_person else 188,
            "constructPersonId": 189,
            "designPersonId": 190,
            "bidDate": today_date,
            "financialList": financial_list,
            "entFinanceRequire": [],
            "entPerRequire": [],
            "performanceList": performance_list,
            "entCerRequire": [],
            "companyId": str(company_id),
            "tenderId": str(tender_id)
        }

        return json_data

    def _update_yaml_data(self, file_path, update_data):
        """更新YAML文件数据"""
        existing_data = self._load_yaml_data(file_path)
        existing_data.update(update_data)

        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(existing_data, f, allow_unicode=True)


