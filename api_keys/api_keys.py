import os

import allure
import jsonpath

from requests import request, Session

from conf.set_conf import read_conf, write_conf


class ApiKeys:

    def __init__(self,env):
        self.env = env
        self.session = Session()
        # 设置默认headers

        # 初始化存储提取的变量（跨步骤共享，比如token、user_id）
        self.extracted_vars = {}

    def get_env_var(self, var_name, default_value=None):
        """
        读取环境变量，支持默认值（解决${变量:-默认值}的解析）
        :param var_name: 变量名
        :param default_value: 默认值
        :return: 环境变量值/默认值
        """
        return os.getenv(var_name, default_value)

    def replace_var(self, content):
        """
        递归替换内容中的变量（支持${VAR}或${VAR:-默认值}格式）
        :param content: 需要替换的内容（字符串/字典/列表）
        :return: 替换后的内容
        """
        if isinstance(content, str):
            # 处理 ${VAR:-默认值} 格式
            import re
            # 匹配 ${变量名:-默认值} 或 ${变量名}
            pattern = r"\$\{([a-zA-Z0-9_]+)(:-([^}]+))?\}"
            matches = re.findall(pattern, content)
            for match in matches:
                var_name = match[0]
                default_val = match[2] if match[2] else None

                # 优先用已提取的变量（如token），再读环境变量，最后用默认值
                var_value = self.extracted_vars.get(
                    var_name,
                    self.get_env_var(var_name, default_val)
                )
                # 替换变量
                if var_value is not None:
                    content = content.replace(f"${{{var_name}{match[1]}}}", str(var_value))
            return content

        elif isinstance(content, dict):
            # 递归替换字典中的值
            return {k: self.replace_var(v) for k, v in content.items()}

        elif isinstance(content, list):
            # 递归替换列表中的元素
            return [self.replace_var(item) for item in content]

        else:
            return content

    def extract_field(self, response_json, extract_rule):
        """
        按JSONPath规则提取字段，带容错（支持 || 语法，如 $.data.token || ''）
        :param response_json: 接口响应JSON
        :param extract_rule: 提取规则（如 $.data.token || ''）
        :return: 提取的值/默认值
        """
        # 拆分提取规则和默认值
        if "||" in extract_rule:
            jsonpath_rule, default_val = [x.strip() for x in extract_rule.split("||")]
        else:
            jsonpath_rule = extract_rule
            default_val = None

        # 执行JSONPath提取
        result = jsonpath(response_json, jsonpath_rule)
        # 容错：提取结果为空则返回默认值
        return result[0] if result and len(result) > 0 else default_val


    def request(self, method, path=None, headers=None, save_cookie=False, **kwargs):
        url = self.set_url(path)
        # 更新session的headers
        if headers:
            self.session.headers.update(headers)
        
        # 如果有token，添加到Authorization header
        if read_conf('data', 'token'):
            token = read_conf('data', 'token')
            self.session.headers.update({'Authorization': token})
        
        res = self.session.request(method=method, url=url, **kwargs)
        allure.attach(res.text,"响应内容")

        return res

    def set_url(self, path):
        host = read_conf(self.env, 'host')
        # 确保host没有末尾的斜杠
        if host.endswith('/'):
            host = host[:-1]
        # 确保path有开头的斜杠
        if path and not path.startswith('/'):
            path = '/' + path
        elif not path:
            path = ''
        url = host + path
        return url




    def get_values(self, res, key):

        values = jsonpath.jsonpath(res, f'$..{key}')

        if len(values) == 1:
            return values[0]

        else:
            return values

    def execute_validate(self, response, validate_rules):
        """
        执行断言规则
        :param response: 响应对象
        :param validate_rules: 断言规则列表（如 [- eq: [status_code, 200]]）
        """
        response_json = response.json() if response.status_code != 500 else {}

        for rule in validate_rules:
            for assert_type, assert_params in rule.items():
                actual = None
                expected = assert_params[1]

                # 解析断言的实际值
                if assert_params[0] == "status_code":
                    actual = response.status_code
                elif assert_params[0].startswith("$"):
                    # JSONPath提取实际值（如 $.code）
                    actual = self.extract_field(response_json, assert_params[0])
                else:
                    # 直接取变量（如 token）
                    actual = self.extracted_vars.get(assert_params[0])

                # 执行断言
                with allure.step(f"断言：{assert_type} {actual} {expected}"):
                    if assert_type == "eq":
                        assert actual == expected, f"预期{expected}，实际{actual}"
                    elif assert_type == "ne":
                        assert actual != expected, f"预期不等于{expected}，实际{actual}"
                    elif assert_type == "gt":
                        assert actual > expected, f"预期大于{expected}，实际{actual}"
                    elif assert_type == "ge":
                        assert actual >= expected, f"预期大于等于{expected}，实际{actual}"
                    elif assert_type == "in":
                        assert actual in expected, f"预期{actual}在{expected}中，实际不在"
                    elif assert_type == "regex_match":
                        import re
                        assert re.match(expected, actual), f"预期匹配正则{expected}，实际{actual}"
                    else:
                        raise ValueError(f"不支持的断言类型：{assert_type}")

    def run_test_case(self, yaml_data):
        """
        执行完整的YAML测试用例
        :param yaml_data: 加载后的YAML用例数据
        """


        # 记录用例元信息到Allure报告
        allure.dynamic.title(yaml_data.get("case_desc", "无描述"))
        allure.dynamic.label("case_id", yaml_data.get("case_id", "无ID"))
        allure.dynamic.label("priority", yaml_data.get("priority", "P3"))
        allure.dynamic.label("tags", ",".join(yaml_data.get("tags", [])))

        # 执行每个测试步骤
        for step in yaml_data.get("teststeps", []):
            with allure.step(step.get("step_desc", step.get("name"))):
                # 1. 替换步骤中的所有变量（包括公共配置、请求参数）
                step = self.replace_var(step)

                # 2. 发送请求
                response = self.send_request(step["request"])

                # 3. 提取字段（如token、user_id）并缓存
                if "extract" in step:
                    extract_rules = step["extract"]
                    for var_name, extract_rule in extract_rules.items():
                        extracted_val = self.extract_field(response.json(), extract_rule)
                        self.extracted_vars[var_name] = extracted_val
                        allure.attach(f"{var_name} = {extracted_val}", "提取字段")

                # 4. 执行断言
                if "validate" in step:
                    self.execute_validate(response, step["validate"])


