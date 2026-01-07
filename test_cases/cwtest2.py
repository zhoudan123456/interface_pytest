import time

import requests
import os
import json


def download_business_document(input_json, save_path="./downloads"):
    """
    从指定接口获取任务ID并下载对应的docx文件到本地

    参数:
        save_path (str): 文件保存路径，默认当前目录下的downloads文件夹

    返回:
        str: 成功时返回保存的文件路径，失败时返回None
    """

    try:
        # 第一步：获取任务ID
        generate_url = "http://192.168.0.87:5005/generate_document?type=busi_gen"
        gen_response = requests.post(generate_url, json=input_json)
        gen_response.raise_for_status()  # 检查HTTP请求是否成功（状态码200）

        # 解析任务ID（假设接口返回JSON格式，如：{"task_id": "xxx"}）
        try:
            task_data = gen_response.json()
            task_id = task_data["task_id"]
        except (json.JSONDecodeError, KeyError) as e:
            print(f"解析任务ID失败: {str(e)}")
            return None

        # 循环检查状态
        while True:
            check_state_url = f"http://192.168.0.87:5005/status/{task_id}"
            check_state_response = requests.get(check_state_url)
            check_state_response.raise_for_status()  # 检查HTTP请求是否成功（状态码200）
            check_state_data = check_state_response.json()
            check_state = check_state_data.get("status")
            if check_state == "completed":
                break
            # 等待一分钟
            print(f"任务 {task_id} 正在处理中")
            time.sleep(60)

        # 第二步：构造下载链接并获取文件流
        download_url = f"http://192.168.0.87:5005/download/{task_id}"
        download_response = requests.get(download_url, stream=True)  # 使用stream模式处理大文件
        download_response.raise_for_status()

        # 验证文件类型（可选，根据实际接口返回的Content-Type调整）
        # content_type = download_response.headers.get("Content-Type", "")
        # if "application/vnd.openxmlformats-officedocument.wordprocessingml.document" not in content_type:
        #     print(f"下载的文件类型不正确，预期docx，实际: {content_type}")
        #     return None

        # 第三步：保存文件到本地
        os.makedirs(save_path, exist_ok=True)  # 自动创建目录（若不存在）
        file_name = f"{task_id}.docx"  # 可根据需求修改文件名规则
        save_file_path = os.path.join(save_path, file_name)

        with open(save_file_path, "wb") as f:
            for chunk in download_response.iter_content(chunk_size=8192):  # 分块写入（适合大文件）
                if chunk:  # 过滤空块
                    f.write(chunk)

        print(f"文件保存成功，路径: {save_file_path}")
        return save_file_path

    except requests.exceptions.RequestException as e:
        print(f"HTTP请求失败: {str(e)}")
        return None
    except Exception as e:
        print(f"发生未知错误: {str(e)}")
        return None


def download_test(save_path="./downloads"):
    # 第二步：构造下载链接并获取文件流
    download_url = f"http://192.168.0.87:5005/download/busi_gen_f11139c3-41b5-4bf5-a70b-e3246bea67ef"
    download_response = requests.get(download_url, stream=True)  # 使用stream模式处理大文件
    download_response.raise_for_status()

    # 验证文件类型（可选，根据实际接口返回的Content-Type调整）
    # content_type = download_response.headers.get("Content-Type", "")
    # if "application/vnd.openxmlformats-officedocument.wordprocessingml.document" not in content_type:
    #     print(f"下载的文件类型不正确，预期docx，实际: {content_type}")
    #     return None

    # 第三步：保存文件到本地
    os.makedirs(save_path, exist_ok=True)  # 自动创建目录（若不存在）
    file_name = f"busi_gen_f11139c3-41b5-4bf5-a70b-e3246bea67ef.docx"  # 可根据需求修改文件名规则
    save_file_path = os.path.join(save_path, file_name)

    with open(save_file_path, "wb") as f:
        for chunk in download_response.iter_content(chunk_size=8192):  # 分块写入（适合大文件）
            if chunk:  # 过滤空块
                f.write(chunk)


# 使用示例
if __name__ == "__main__":
    json_data = {
        "招标人": {
            "项目名称": "会泽县冷链物流园区学校食堂食材配送中心蔬菜冷库设备及工程施工安装采购项目（二次）",
            "标段名称": "会泽县冷链物流园区学校食堂食材配送中心蔬菜冷库设备及工程施工安装采购项目（二次）",
            "项目编号": "YNZFCG2021-02",
            "招标单位名称": "会泽县道成扶贫开发投资经营管理有限公司",
            "项目预算": "5500000",
            "名称": "会泽县道成扶贫开发投资经营管理有限公司",
            "工期": "空",
            "工程质量": "空",
            "补充说明": "空",
            "投标保证金": "",
            "代理机构名称": "云南帜丰招标有限公司"
        },
        "标书类型": "工程类",
        "上一任务编号": "1",
        "偏离表": {
            "file_list": [],
            "requirement_list": "空"
        },
        "投标人": {
            "法定代表人": "空",
            "授权委托人": "",
            "统一社会信用码": None,
            "注册资金": None,
            "公司类型": None,
            "注册地址": None,
            "注册机构": None,
            "公司邮箱": None,
            "成立日期": None,
            "登记日期": None,
            "营业截止时长": None,
            "经营范围": None,
            "名称": "测试公司",
            "地址": None,
            "网址": None,
            "电话": None,
            "传真": None,
            "邮政编码": None,
            "开户名称": None,
            "开户银行": None,
            "开户账号": None,
            "银行地址": None,
            "银行电话": None,
            "行业分类": None,
            "公司规模": None,
            "投标员工总人数": None,
            "投标高级职称人数": None,
            "投标中级职称人数": None,
            "投标初级职称人数": None,
            "投标技工人数": None,
            "投标项目经理人数": None,
            "安全生产许可证生效时间": None,
            "安全生产许可证失效时间": None,
            "填写时间": [
                "2025",
                "6",
                "30"
            ],
            "项目经理": "空"
        },
        "文档": {
            "招标解析文件": "https://intellibid-bid.oss-cn-hangzhou.aliyuncs.com/analysis/174842625356300000/3f81a9c68be045d981f576dcb4c9931e?Expires=1751311786&OSSAccessKeyId=REMOVED_ACCESS_KEY&Signature=sbwAy3eBqGdHCm0L%2FKghD%2BJH44Q%3D",
            "营业执照": "空",
            "审计报告": "空",
            "招标文件": "https://intellibid-bid.oss-cn-hangzhou.aliyuncs.com/test/2024-%E6%B9%96%E5%8C%97-%E6%B9%96%E5%8C%97%E7%9C%81%E7%A6%8F%E5%88%A9%E5%BD%A9%E7%A5%A8%E5%8F%91%E8%A1%8C%E4%B8%AD%E5%BF%83%E6%99%BA%E6%85%A7%E9%97%A8%E5%BA%97%E8%BF%90%E8%90%A5%E7%AE%A1%E7%90%86%E7%B3%BB%E7%BB%9F%E5%BB%BA%E8%AE%BE%E9%A1%B9%E7%9B%AE.docx?Expires=1751459624&OSSAccessKeyId=TMP.3KqzenEptGy7Hi56qr58ozB5Qtu3XLaVwwkE5vRSNDZGd7vYCUEFqqLcziiL9eiMa7QUXTRiYKrKdhZEznFgWFvWdTPgr1&Signature=CfA0qpytGZdo%2BPonV9iNty1XKyg%3D",
            "开户文件": "",
            "法人身份证": [],
            "授权委托人身份证": [],
            "企业业绩": [
                {
                    "采购单位": "中国石油",
                    "项目名称": "中国石油项目第一期",
                    "项目金额": 1000.0,
                    "项目开工时间": "2019-01-01",
                    "项目竣工时间": "2020-12-31",
                    "项目负责人": "张三",
                    "采购单位联系人": "赵一",
                    "竣工备案": "132213",
                    "中标结果通知书": "",
                    "合同委托书": "",
                    "施工许可证": "",
                    "验收报告": ""
                },
                {
                    "采购单位": "中国石化",
                    "项目名称": "中国石油项目第二期",
                    "项目金额": 500.0,
                    "项目开工时间": "2021-01-01",
                    "项目竣工时间": "2022-12-31",
                    "项目负责人": "李四",
                    "采购单位联系人": "钱二",
                    "竣工备案": "138001",
                    "中标结果通知书": "",
                    "合同委托书": "",
                    "施工许可证": "",
                    "验收报告": ""
                }
            ],
            "企业财务信息": "",
            "企业证书": "",
            "人员信息": {
                "项目负责人": {
                    "人员姓名": "张三",
                    "人员职位": "总经理",
                    "性别": "男",
                    "身份证号": "311111198602132222",
                    "联系电话": "13800138000",
                    "人员类型": "岗位类",
                    "身份证": [],
                    "社保材料": [],
                    "证书材料": [],
                    "劳动合同": []
                },
                "技术负责人": {
                    "人员姓名": "李四",
                    "人员职位": "普通员工",
                    "性别": "男",
                    "身份证号": "311111199502132222",
                    "联系电话": "13800138111",
                    "人员类型": "岗位类",
                    "身份证": [],
                    "社保材料": [],
                    "证书材料": [],
                    "劳动合同": []
                },
                "施工负责人": {
                    "人员姓名": "王五",
                    "人员职位": "普通员工",
                    "性别": "男",
                    "身份证号": "311111200002132222",
                    "联系电话": "13800138222",
                    "人员类型": "岗位类",
                    "身份证": [],
                    "社保材料": [],
                    "证书材料": [],
                    "劳动合同": []
                },
                "设计负责人": ""
            },
            "需要填充": "True"
        },
        "目录": {
            "完整目录": [
                {
                    "name": "投标函",
                    "parentid": "0",
                    "id": "1",
                    "children": [
                        {
                            "name": "投标函",
                            "parentid": "1",
                            "id": "1-1"
                        },
                        {
                            "name": "投标保证书",
                            "parentid": "1",
                            "id": "1-2"
                        }
                    ]
                },
                {
                    "name": "投标报价（唱标）一览表",
                    "parentid": "0",
                    "id": "2"
                },
                {
                    "name": "产品质量承诺书",
                    "parentid": "0",
                    "id": "3",
                    "children": [
                        {
                            "name": "产品质量承诺书",
                            "parentid": "3",
                            "id": "3-1"
                        },
                        {
                            "name": "售后服务及承诺",
                            "parentid": "3",
                            "id": "3-2"
                        }
                    ]
                },
                {
                    "name": "投标人资格及资信证明文件",
                    "parentid": "0",
                    "id": "4"
                },
                {
                    "name": "法定代表人证明书格式",
                    "parentid": "0",
                    "id": "5",
                    "children": [
                        {
                            "name": "法定代表人证明书格式",
                            "parentid": "5",
                            "id": "5-1"
                        },
                        {
                            "name": "法定代表人授权书格式",
                            "parentid": "5",
                            "id": "5-2"
                        }
                    ]
                },
                {
                    "name": "投标人基本情况表（企业简介）",
                    "parentid": "0",
                    "id": "6",
                    "children": [
                        {
                            "name": "投标人基本情况表（企业简介）",
                            "parentid": "6",
                            "id": "6-1"
                        },
                        {
                            "name": "财务状况表",
                            "parentid": "6",
                            "id": "6-2"
                        }
                    ]
                },
                {
                    "name": "财务状况表",
                    "parentid": "0",
                    "id": "7",
                    "children": [
                        {
                            "name": "财务状况表",
                            "parentid": "7",
                            "id": "7-1"
                        },
                        {
                            "name": "投标人类似项目采购中标情况表",
                            "parentid": "7",
                            "id": "7-2"
                        }
                    ]
                },
                {
                    "name": "投标人认为需要的其他资料",
                    "parentid": "0",
                    "id": "8",
                    "children": [
                        {
                            "name": "投标人认为需要的其他资料",
                            "parentid": "8",
                            "id": "8-1"
                        },
                        {
                            "name": "承诺书",
                            "parentid": "8",
                            "id": "8-2"
                        }
                    ]
                },
                {
                    "name": "承诺书",
                    "parentid": "0",
                    "id": "9"
                }
            ]
        }
    }
    saved_path = download_business_document(json_data, save_path="D:/files")
    if saved_path:
        print(f"操作成功，文件保存在: {saved_path}")
    else:
        print("操作失败")
