"""
招投标解析生成流程测试
流程：解析 → 轮询进度 → 生成目录 → 轮询结果
"""
import os

import pytest
import time
import json


import yaml

from conf.set_conf import read_yaml, write_yaml


class TestParseGenerateWorkflow:
    """解析生成完整流程测试"""

    @pytest.mark.parametrize('data', read_yaml('../../test_data/login.yaml'))
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
                # 保存文档ID到extract.yaml文件，供后续接口使用
                document_data = {'document_id': str(document_id)}
                write_yaml('../../test_data/extract.yaml', document_data)
                print(f"Document ID saved: {document_id}")
            else:
                pytest.fail(f"Upload failed with response: {response_data}")

        finally:
            # 确保文件句柄被关闭
            files['file'].close()

    @pytest.mark.parametrize('data', read_yaml('../../test_data/login.yaml'))
    def test_02_check_bid_file(self, api, data):
        """检查招标文件"""
        # 从extract.yaml中读取上传后保存的文档ID
        extract_file_path = '../../test_data/extract.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                document_id = extract_data.get('document_id') if extract_data else None
        else:
            document_id = None

        # 确保文档ID存在
        assert document_id, "Document ID not found in extract.yaml. Please run upload test first."

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


    @pytest.mark.parametrize('data', read_yaml('../../test_data/login.yaml'))
    def test_03_analyze_tender_sync(self, api, data):
        """测试解析招标文件接口"""
        # 获取分析招标文件的配置数据
        analyze_tender_data = data['analyze_tender']
        type_param = data['upload']['data']['type']


        print(f"Using type: {type_param}")

        # 从extract.yaml中读取上传后保存的文档ID
        extract_file_path = '../../test_data/extract.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                document_id = extract_data.get('document_id') if extract_data else None
        else:
            document_id = None

        # 确保文档ID存在
        assert document_id, "Document ID not found in extract.yaml. Please run upload test first."

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

    @pytest.mark.parametrize('data', read_yaml('../../test_data/login.yaml'))
    def test_04_poll_parse_progress(self, api, data):
        """
        步骤4: 轮询解析进度
        接口: /prod-api/bid/ua/query/oneTenderProgressUser
        """
        print("\n" + "=" * 50)
        print("步骤3: 轮询解析进度")
        print("=" * 50)

        # 从extract.yaml中读取上传后保存的文档ID
        extract_file_path = '../../test_data/extract.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                document_id = extract_data.get('document_id') if extract_data else None
        else:
            document_id = None

        # 确保文档ID存在
        assert document_id, "Document ID not found in extract.yaml. Please run upload test first."

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
                # 保存解析结果到 extract.yaml
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

    @pytest.mark.parametrize('data', read_yaml('../../test_data/login.yaml'))
    def test_05_generate_toc(self, api, data):
        """
        步骤3: 生成技术标目录
        """
        print("\n" + "=" * 50)
        print("步骤3: 生成技术标目录")
        print("=" * 50)

        # 检查解析是否已完成
        # 从extract.yaml中读取上传后保存的文档ID
        extract_file_path = '../../test_data/extract.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                document_id = extract_data.get('document_id') if extract_data else None
                parse_result = extract_data.get('parse_result') if extract_data else None

                companyId = extract_data.get('companyId') if extract_data and 'companyId' in extract_data else "112233"
        else:
            document_id = None
            parse_result = None
            companyId = "112233"  # 默认公司ID

        # 检查parse_result是否为True，如果不是则跳过测试
        if parse_result != 'True' and parse_result != True:
            pytest.skip("Parse result is not True, skipping generate TOC step")

        # 确保文档ID存在
        assert document_id, "Document ID not found in extract.yaml. Please run upload test first."

        print(f"Using document ID: {document_id}")
        print(f"Using company ID: {companyId}")

        json_data = {
            "tenderId": str(document_id),
            "companyId": str(companyId)
        }




        try:
            response = api.request(save_cookie=True, json=json_data, **data['generate_tech_catalogue'])
            print(f"状态码: {response.status_code}")

            result = response.json()
            print(f"响应结果: {json.dumps(result, indent=2, ensure_ascii=False)}")

            assert response.status_code == 200, f"目录生成请求失败"


        except Exception as e:
            pytest.fail(f"目录生成请求异常: {str(e)}")

    @pytest.mark.parametrize('data', read_yaml('../../test_data/login.yaml'))
    def test_06_poll_toc_result(self, api, data):
        """
        步骤6: 轮询目录生成结果

        """
        print("\n" + "=" * 50)
        print("步骤6: 轮询目录结果")
        print("=" * 50)



        # 从extract.yaml中读取上传后保存的文档ID
        extract_file_path = '../../test_data/extract.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                document_id = extract_data.get('document_id') if extract_data else None
                companyId = extract_data.get('companyId') if extract_data and 'companyId' in extract_data else "112233"
        else:
            document_id = None
            companyId = "112233"  # 默认公司ID

        # JSON格式请求体
        json_body = {
            "tenderId": str(document_id),
            "companyId": str(companyId)
        }

        # 轮询配置
        max_attempts = 30  # 最多尝试30次 (30分钟)
        poll_interval = 60  # 每次间隔60秒 (1分钟)
        max_wait_time = 1800  # 最多等待1800秒 (30分钟)

        start_time = time.time()

        for attempt in range(1, max_attempts + 1):
            print(f"\n轮询尝试 #{attempt}/{max_attempts}")

            try:
                response = api.request(save_cookie=True, json=json_body,**data['catalogue_progress'])

                if response.status_code != 200:
                    print(f"⚠️  状态码异常: {response.status_code}")
                    time.sleep(poll_interval)
                    continue

                resp_data = response.json()
                print(f"目录结果响应: {json.dumps(resp_data, indent=2, ensure_ascii=False)}")


                # 提取progress字段并判断
                # 逐层获取，避免字段不存在时报错
                progress = resp_data.get("data", {}).get("progress", -1)
                print(f"提取到的progress值：{progress}")

                # 仅当progress等于100时停止轮询并执行后续测试
                if progress == 100:
                    print("✅ 目录生成完成! Progress值为100，停止轮询")
                    # 这里可以添加额外的处理逻辑
                    break  # 退出轮询循环，继续执行后续代码

            except Exception as e:
                print(f"轮询请求异常: {str(e)}")

            # 检查超时
            elapsed_time = time.time() - start_time
            if elapsed_time > max_wait_time:
                pytest.fail(f"目录轮询超时，等待时间超过{max_wait_time}秒")

            # 等待下一次轮询
            if attempt < max_attempts:
                print(f"等待{poll_interval}秒后继续轮询...")
                time.sleep(poll_interval)

        # 当progress为100时，会提前break跳出循环，然后执行下面的代码
        print("轮询结束，准备执行下一个测试用例")

    @pytest.mark.parametrize('data', read_yaml('../../test_data/login.yaml'))
    def test_07_query_catalogue(self, api, data):
        # 从extract.yaml中读取上传后保存的文档ID
        extract_file_path = '../../test_data/extract.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                document_id = extract_data.get('document_id') if extract_data else None
                companyId = extract_data.get('companyId') if extract_data and 'companyId' in extract_data else "112233"
        else:
            document_id = None
            companyId = "112233"  # 默认公司ID


        # 格式：{参数名: (None, 参数值)}（None表示该参数不是文件类型）
        form_data = {
            "tenderId": (None, str(document_id)),
            "companyId": (None, str(companyId))
        }
        response = api.request(files=form_data,save_cookie=True,**data['query_catalogue'])
        response.raise_for_status()  # 捕获HTTP错误（如401、500）
        resp_data = response.json()  # 解析接口响应JSON

        # 3. 逐层提取技术标下的catalogue（安全取值，避免字段缺失报错）
        # 第一步：取data字段，无则返回空字典
        data = resp_data.get("data", {})
        # 第二步：取技术标字段，无则返回空字典
        tech_bid = data.get("技术标", {})
        # 第三步：取catalogue值，无则返回空字符串
        tech_catalogue_str = tech_bid.get("catalogue", "")

        print("=== 提取的技术标catalogue原始字符串 ===")
        print(tech_catalogue_str)

        # 提取"商务标"和"技术标"下的catalogueId
        data = resp_data.get("data", {})
        # 商务标的catalogueId
        business_catalogue_id = data.get("商务标", {}).get("catalogueId")
        # 技术标的catalogueId
        tech_catalogue_id = data.get("技术标", {}).get("catalogueId")

        # 打印结果
        print(f"商务标catalogueId：{business_catalogue_id}")
        print(f"技术标catalogueId：{tech_catalogue_id}")
        
        # 将tech_catalogue_str和tech_catalogue_id更新到extract.yaml中
        updated_data = {
            'catalogue': tech_catalogue_str,
            'tech_catalogue_id': tech_catalogue_id
        }
        
        # 读取现有数据并合并
        existing_data = {}
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                existing_data = yaml.safe_load(f) or {}
        
        # 合并数据
        existing_data.update(updated_data)
        
        # 写回文件
        with open(extract_file_path, 'w', encoding='utf-8') as f:
            yaml.dump(existing_data, f, default_flow_style=False, allow_unicode=True, indent=2)
        
        print("技术标catalogue和tech_catalogue_id已保存到extract.yaml")

    @pytest.mark.parametrize('data', read_yaml('../../test_data/login.yaml'))
    def test_08_query_one_tender_user(self, api, data):
        # 从extract.yaml中读取上传后保存的文档ID
        extract_file_path = '../../test_data/extract.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                document_id = extract_data.get('document_id') if extract_data else None
                companyId = extract_data.get('companyId') if extract_data and 'companyId' in extract_data else "112233"
        else:
            document_id = None
            companyId = "112233"  # 默认公司ID

        # 格式：{参数名: (None, 参数值)}（None表示该参数不是文件类型）
        form_data = {
            "tenderId": (None, str(document_id)),
            "companyId": (None, str(companyId))
        }
        response = api.request(files=form_data, save_cookie=True, **data['query_oneTenderUser'])
        response.raise_for_status()  # 捕获HTTP错误（如401、500）
        resp_data = response.json()  # 解析接口响应JSON
        
        # 提取data下的多个字段（兼容data为空或字段不存在的情况）
        data_obj = resp_data.get("data", {})  # 若data不存在，取空字典
        
        project_code = data_obj.get("projectCode")  # 若projectCode不存在，返回None
        project_name = data_obj.get("projectName")  # 若projectName不存在，返回None
        tender_company_name = data_obj.get("tenderCompanyName")  # 若tenderCompanyName不存在，返回None
        tender_project_budget = data_obj.get("tenderProjectBudget")  # 若tenderProjectBudget不存在，返回None

        # 打印结果
        if project_code is not None:
            print(f"提取到projectCode：{project_code}")
            # 更新YAML文件中的tenderProjectCode
            updated_data = {'tenderProjectCode': project_code}
            
            # 读取现有数据并合并
            existing_data = {}
            if os.path.exists(extract_file_path):
                with open(extract_file_path, 'r', encoding='utf-8') as f:
                    existing_data = yaml.safe_load(f) or {}
            
            # 合并数据
            existing_data.update(updated_data)
            
            # 写回文件
            with open(extract_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(existing_data, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            print("tenderProjectCode已保存到extract.yaml")
        else:
            print("⚠️ 响应的data中未找到projectCode字段")
            
        if project_name is not None:
            print(f"提取到projectName：{project_name}")
            # 更新YAML文件中的tenderProjectName
            updated_data = {'tenderProjectName': project_name}
            
            # 读取现有数据并合并
            existing_data = {}
            if os.path.exists(extract_file_path):
                with open(extract_file_path, 'r', encoding='utf-8') as f:
                    existing_data = yaml.safe_load(f) or {}
            
            # 合并数据
            existing_data.update(updated_data)
            
            # 写回文件
            with open(extract_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(existing_data, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            print("tenderProjectName已保存到extract.yaml")
        else:
            print("⚠️ 响应的data中未找到projectName字段")
            
        if tender_company_name is not None:
            print(f"提取到tenderCompanyName：{tender_company_name}")
            # 更新YAML文件中的tenderCompanyName
            updated_data = {'tenderCompanyName': tender_company_name}
            
            # 读取现有数据并合并
            existing_data = {}
            if os.path.exists(extract_file_path):
                with open(extract_file_path, 'r', encoding='utf-8') as f:
                    existing_data = yaml.safe_load(f) or {}
            
            # 合并数据
            existing_data.update(updated_data)
            
            # 写回文件
            with open(extract_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(existing_data, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            print("tenderCompanyName已保存到extract.yaml")
        else:
            print("⚠️ 响应的data中未找到tenderCompanyName字段")
            
        if tender_project_budget is not None:
            print(f"提取到tenderProjectBudget：{tender_project_budget}")
            # 更新YAML文件中的tenderProjectBudget
            updated_data = {'tenderProjectBudget': tender_project_budget}
            
            # 读取现有数据并合并
            existing_data = {}
            if os.path.exists(extract_file_path):
                with open(extract_file_path, 'r', encoding='utf-8') as f:
                    existing_data = yaml.safe_load(f) or {}
            
            # 合并数据
            existing_data.update(updated_data)
            
            # 写回文件
            with open(extract_file_path, 'w', encoding='utf-8') as f:
                yaml.dump(existing_data, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            print("tenderProjectBudget已保存到extract.yaml")
        else:
            print("⚠️ 响应的data中未找到tenderProjectBudget字段")

    @pytest.mark.parametrize('data', read_yaml('../../test_data/login.yaml'))
    def test_09_tech_content(self, api, data):
        """
        步骤9: 获取技术标内容
        """
        print("\n" + "=" * 50)
        print("步骤9: 获取技术标内容")
        print("=" * 50)

        # 从extract.yaml中读取所需参数
        extract_file_path = '../../test_data/extract.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                # 读取技术标目录ID或其他必要参数

                tenderId = extract_data.get('document_id') if extract_data else None
                companyId = extract_data.get('companyId') if extract_data and 'companyId' in extract_data else "112233"
                catalogue = extract_data.get('catalogue') if extract_data else None
                cataId = extract_data.get('tech_catalogue_id') if extract_data else None
                tenderProjectCode = extract_data.get('tenderProjectCode') if extract_data else None
                tenderProjectName = extract_data.get('tenderProjectName') if extract_data else None
                tenderCompanyName = extract_data.get('tenderCompanyName') if extract_data else None
                tenderProjectBudget = extract_data.get('tenderProjectBudget') if extract_data else None
                imageText = extract_data.get('imageText') if extract_data else None
                isTable = extract_data.get('isTable') if extract_data else None
                isInterImg = extract_data.get('isInterImg') if extract_data else None
                bidType = extract_data.get('bidType') if extract_data else None


        else:
            cataId = None
            tenderId = None
            companyId = "112233"  # 默认公司ID
            catalogue = None
            tenderProjectCode = None
            tenderProjectName = None
            tenderCompanyName = None
            tenderProjectBudget = None
            imageText = None
            isTable = None
            isInterImg = None
            bidType = None


        print(f"Using document ID: {tenderId}")
        print(f"Using company ID: {companyId}")
        print(f"Using tech catalogue ID: {cataId}")

        json_body = {
            "tenderId": str(tenderId),
            "companyId": str(companyId),
            "catalogue": str(catalogue),
            "cataId": str(cataId),
            "tenderProjectCode": str(tenderProjectCode),
            "tenderProjectName": str(tenderProjectName),
            "tenderCompanyName": str(tenderCompanyName),
            "tenderProjectBudget": str(tenderProjectBudget),
            "imageText": str(imageText),
            "isTable": isTable,
            "isInterImg": str(isInterImg),
            "bidType": bidType
        }


        response = api.request(json=json_body, save_cookie=True, **data['tech_content'])
        response.raise_for_status()  # 捕获HTTP错误（如401、500）
        resp_data = response.json()  # 解析接口响应JSON

        print("=== 技术标内容响应 ===")
        print(json.dumps(resp_data, indent=2, ensure_ascii=False))

    @pytest.mark.parametrize('data', read_yaml('../../test_data/login.yaml'))
    def test_10_content_progress(self, api, data):
        """
                步骤10: 轮询文档生成结果

                """
        print("\n" + "=" * 50)
        print("步骤10: 轮询文档生成结果")
        print("=" * 50)

        # 从extract.yaml中读取上传后保存的文档ID
        extract_file_path = '../../test_data/extract.yaml'
        if os.path.exists(extract_file_path):
            with open(extract_file_path, 'r', encoding='utf-8') as f:
                extract_data = yaml.safe_load(f)
                document_id = extract_data.get('document_id') if extract_data else None
                companyId = extract_data.get('companyId') if extract_data and 'companyId' in extract_data else "112233"
        else:
            document_id = None
            companyId = "112233"  # 默认公司ID

        # JSON格式请求体
        json_body = {
            "tenderId": str(document_id),
            "companyId": str(companyId)
        }

        # 轮询配置
        max_attempts = 30  # 最多尝试30次 (30分钟)
        poll_interval = 60  # 每次间隔60秒 (1分钟)
        max_wait_time = 1800  # 最多等待1800秒 (30分钟)

        start_time = time.time()

        for attempt in range(1, max_attempts + 1):
            print(f"\n轮询尝试 #{attempt}/{max_attempts}")

            try:
                response = api.request(save_cookie=True, json=json_body, **data['content_progress'])

                if response.status_code != 200:
                    print(f"⚠️  状态码异常: {response.status_code}")
                    time.sleep(poll_interval)
                    continue

                resp_data = response.json()
                print(f"文档生成结果响应: {json.dumps(resp_data, indent=2, ensure_ascii=False)}")

                # 提取progress字段并判断
                # 逐层获取，避免字段不存在时报错
                progress = resp_data.get("data", {}).get("progress", -1)
                print(f"提取到的progress值：{progress}")

                # 仅当progress等于100时停止轮询并执行后续测试
                if progress == 100:
                    print("✅ 文档生成完成! Progress值为100，停止轮询")
                    # 这里可以添加额外的处理逻辑
                    break  # 退出轮询循环，继续执行后续代码

            except Exception as e:
                print(f"轮询请求异常: {str(e)}")

            # 检查超时
            elapsed_time = time.time() - start_time
            if elapsed_time > max_wait_time:
                pytest.fail(f"文档轮询超时，等待时间超过{max_wait_time}秒")

            # 等待下一次轮询
            if attempt < max_attempts:
                print(f"等待{poll_interval}秒后继续轮询...")
                time.sleep(poll_interval)

        # 当progress为100时，会提前break跳出循环，然后执行下面的代码
        print("轮询结束，准备执行下一个测试用例")



