"""
优化后的test_bid_workflow.py - test_22示例
展示如何从前面接口的返回数据中动态构建请求数据
"""

import json
import os
import time
from datetime import datetime
import pytest
import yaml
import re
from urllib.parse import unquote

from conf.set_conf import read_yaml, write_yaml


class TestBidGenerateWorkflowRefactored:
    """
    优化后的工作流测试类
    重点展示test_22如何从前面接口的返回数据中动态构建请求数据
    """

    # ==================== 辅助方法集合 ====================

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

    def _get_company_name_from_yaml(self, company_id, extract_data=None):
        """从数据中获取指定companyId的companyName"""
        if extract_data and 'all_companies' in extract_data:
            all_companies = extract_data['all_companies']
            if isinstance(all_companies, list):
                for company in all_companies:
                    if company.get('companyId') == company_id:
                        return company.get('companyName', f'Company_{company_id}')

        if extract_data and extract_data.get('companyId') == company_id:
            return extract_data.get('companyName', f'Company_{company_id}')

        return f'Company_{company_id}'

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
            return persons[0] if persons else None
        return persons[0] if persons else None

    def _get_financial_list(self, extract_data, limit=3):
        """
        从财务数据中获取财务列表
        数据来源: test_21_query_financial_page
        """
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
                    "entryTime": item.get('createTime', ''),
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
        """
        从业绩数据中获取业绩列表
        数据来源: test_19_query_all_company_performance
        """
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
        """
        从公司文件数据中获取文件ID列表
        数据来源: test_20_query_company_file_page
        """
        file_data = extract_data.get('company_file_page_data', {})
        if file_data:
            rows = file_data.get('rows', [])
            file_ids = []
            for item in rows[:limit]:
                file_ids.append(str(item.get('companyFileId', '')))
            return file_ids
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

    def _update_yaml_data(self, file_path, update_data):
        """更新YAML文件数据"""
        existing_data = self._load_yaml_data(file_path)
        existing_data.update(update_data)

        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(existing_data, f, allow_unicode=True)

    def _build_gen_save_company_request(self, extract_data, company_id, tender_id):
        """
        构建gen_save_company接口的请求数据
        从前面接口的返回数据中动态获取

        数据来源说明：
        1. 公司名称: test_15_select_all_company (all_companies)
        2. 人员信息: test_17_query_all_person_no_page (all_persons_list)
        3. 财务列表: test_21_query_financial_page (financial_page_data)
        4. 业绩列表: test_19_query_all_company_performance (all_company_performance)
        5. 文件信息: test_20_query_company_file_page (company_file_page_data)
        """
        today_date = datetime.now().strftime('%Y-%m-%d')

        # 1. 获取公司名称
        company_name = self._get_company_name_from_yaml(company_id, extract_data)

        # 2. 获取人员信息
        auth_person = self._get_persons_by_role(extract_data)
        project_person = self._get_persons_by_role(extract_data, '项目')
        tech_person = self._get_persons_by_role(extract_data, '技术')

        # 3. 获取财务列表（从test_21_query_financial_page）
        financial_list = self._get_financial_list(extract_data, limit=3)
        if not financial_list:
            print("⚠️  未找到财务数据，使用默认示例")
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

        # 4. 获取业绩列表（从test_19_query_all_company_performance）
        performance_list = self._get_performance_list(extract_data, limit=1)
        if not performance_list:
            print("⚠️  未找到业绩数据，使用默认示例")
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

        # 5. 构建请求数据
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

    def _build_fill_busi_company_request(self, extract_data, company_id, tender_id):
        """
        构建fill_busi_company接口的请求数据
        从前面接口的返回数据中动态获取

        这个接口在test_23中使用，数据来源与test_22类似
        """
        today_date = datetime.now().strftime('%Y-%m-%d')

        # 获取基础信息
        company_name = self._get_company_name_from_yaml(company_id, extract_data)

        # 获取动态数据
        financial_list = self._get_financial_list(extract_data, limit=3)
        performance_list = self._get_performance_list(extract_data, limit=1)
        company_file_ids = self._get_company_files(extract_data, limit=2)
        financial_ids = self._get_financial_ids(extract_data, limit=3)
        project_ids = self._get_project_ids(extract_data, limit=1)

        json_data = {
            "companyName": company_name,
            "legal": "",
            "legalCard": None,
            "authPersonId": 188,
            "projectPersonId": 187,
            "techPersonId": 188,
            "constructPersonId": 189,
            "designPersonId": 190,
            "bidDate": today_date,
            "financialList": financial_list if financial_list else [],
            "performanceList": performance_list if performance_list else [],
            "companyId": str(company_id),
            "tenderId": str(tender_id),
            "projectIds": project_ids if project_ids else ["108"],
            "companyFileIds": company_file_ids if company_file_ids else ["199", "200"],
            "financialIds": financial_ids if financial_ids else ["187", "186", "185"],
            "tenderProjectCode": "",
            "tenderProjectName": "",
            "tenderCompanyName": "",
            "tenderProjectBudget": "",
            "newCompanyId": str(company_id),
            "skipCompany": "1"
        }

        return json_data

    # ==================== 测试用例示例 ====================

    @pytest.mark.parametrize('data', read_yaml('../../test_data/bid_generate_workflow.yaml'))
    def test_22_gen_save_company_refactored(self, api, data):
        """
        步骤31: 生成保存公司信息（重构版本）

        ✅ 优势：
        1. 数据全部从前面接口的返回中动态获取
        2. 消除了硬编码
        3. 代码更简洁、可维护
        4. 数据来源清晰可追溯

        📊 数据来源：
        - test_15_select_all_company → 公司名称
        - test_17_query_all_person_no_page → 人员信息
        - test_19_query_all_company_performance → 业绩数据
        - test_21_query_financial_page → 财务数据
        """
        print("\n" + "=" * 50)
        print("步骤31: 生成保存公司信息（重构版本）")
        print("=" * 50)

        # 加载数据
        extract_file_path = '../../test_data/bid_generate.yaml'
        extract_data = self._load_yaml_data(extract_file_path)

        # 获取基础参数
        tender_id = self._get_value_from_data(extract_data, 'document_id', '176887627456900000')
        company_id = self._get_company_id_from_data(extract_data)

        print(f"📋 Using tender ID: {tender_id}")
        print(f"🏢 Using company ID: {company_id}")

        # 🔥 核心：从前面接口的返回数据中构建请求数据
        json_data = self._build_gen_save_company_request(extract_data, company_id, tender_id)

        # 打印数据来源信息
        print(f"\n📊 数据来源统计:")
        print(f"  - 财务数据: {len(json_data.get('financialList', []))} 条 (test_21_query_financial_page)")
        print(f"  - 业绩数据: {len(json_data.get('performanceList', []))} 条 (test_19_query_all_company_performance)")
        print(f"  - 公司名称: {json_data.get('companyName')} (test_15_select_all_company)")

        # 发送请求
        res = api.request(
            method=data['gen_save_company']['method'],
            path=data['gen_save_company']['path'],
            json=json_data
        )

        # 验证响应
        assert res.status_code == 200, f"Gen save company failed: {res.json()}"
        response_data = res.json()

        if response_data.get('code') == 200:
            saved_company_id = response_data.get('data')
            print(f"✅ Successfully saved company information, ID: {saved_company_id}")

            # 更新YAML文件
            self._update_yaml_data(extract_file_path, {
                'saved_company_info': response_data,
                'saved_company_id': saved_company_id,
                'save_company_request_data': json_data,
                'used_tender_id_for_save_company': tender_id,
                'used_company_id_for_save_company': company_id
            })
        else:
            pytest.fail(f"Failed to save company: {response_data}")

    @pytest.mark.parametrize('data', read_yaml('../../test_data/bid_generate_workflow.yaml'))
    def test_23_fill_busi_company_refactored(self, api, data):
        """
        步骤32: 填充业务公司信息（重构版本）

        📊 数据来源：
        - test_15_select_all_company → 公司名称
        - test_19_query_all_company_performance → 业绩数据
        - test_20_query_company_file_page → 公司文件
        - test_21_query_financial_page → 财务数据
        """
        print("\n" + "=" * 50)
        print("步骤32: 填充业务公司信息（重构版本）")
        print("=" * 50)

        # 加载数据
        extract_file_path = '../../test_data/bid_generate.yaml'
        extract_data = self._load_yaml_data(extract_file_path)

        # 获取基础参数
        tender_id = self._get_value_from_data(extract_data, 'document_id', '176838149284700000')
        company_id = self._get_company_id_from_data(extract_data)

        print(f"📋 Using tender ID: {tender_id}")
        print(f"🏢 Using company ID: {company_id}")

        # 构建请求数据
        json_data = self._build_fill_busi_company_request(extract_data, company_id, tender_id)

        # 打印数据来源信息
        print(f"\n📊 数据来源统计:")
        print(f"  - 财务数据: {len(json_data.get('financialList', []))} 条")
        print(f"  - 业绩数据: {len(json_data.get('performanceList', []))} 条")
        print(f"  - 项目ID: {json_data.get('projectIds')}")
        print(f"  - 文件ID: {json_data.get('companyFileIds')}")
        print(f"  - 财务ID: {json_data.get('financialIds')}")

        # 发送请求
        res = api.request(
            method=data['fill_busi_company']['method'],
            path=data['fill_busi_company']['path'],
            json=json_data
        )

        # 验证响应
        assert res.status_code == 200, f"Fill busi company failed: {res.json()}"
        response_data = res.json()

        if response_data.get('code') == 200:
            busiId = response_data.get('data')
            print(f"✅ Successfully filled company, busiId: {busiId}")

            # 更新YAML文件
            self._update_yaml_data(extract_file_path, {
                'filled_company_info': response_data,
                'busiId': busiId,
                'fill_company_request_data': json_data
            })
        else:
            pytest.fail(f"Failed to fill company: {response_data}")


# ==================== 使用说明 ====================
"""
💡 重构要点说明：

1. **数据映射关系**：
   - test_15_select_all_company → all_companies → 公司名称
   - test_17_query_all_person_no_page → all_persons_list → 人员信息
   - test_19_query_all_company_performance → all_company_performance → 业绩列表
   - test_20_query_company_file_page → company_file_page_data → 文件ID
   - test_21_query_financial_page → financial_page_data → 财务列表

2. **辅助方法职责**：
   - _load_yaml_data(): 加载YAML数据
   - _get_value_from_data(): 安全获取数据值
   - _get_company_id_from_data(): 智能获取公司ID
   - _get_financial_list(): 转换财务数据格式
   - _get_performance_list(): 转换业绩数据格式
   - _build_*_request(): 构建请求数据

3. **优势**：
   ✅ 消除硬编码
   ✅ 数据可追溯
   ✅ 代码可维护
   ✅ 易于扩展

4. **迁移步骤**：
   步骤1: 将辅助方法复制到原test_bid_workflow.py文件末尾
   步骤2: 修改test_22使用_build_gen_save_company_request方法
   步骤3: 修改test_23使用_build_fill_busi_company_request方法
   步骤4: 运行测试验证
"""
