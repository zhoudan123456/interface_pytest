"""
HAR文件解析器
用于从HAR文件中提取用户操作序列和业务流程
"""
import json
from typing import Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlparse, parse_qs


@dataclass
class UserAction:
    """用户操作记录"""
    timestamp: datetime
    url: str
    method: str
    action_type: str  # click, input, navigate, submit, etc.
    element_info: Dict[str, Any] = field(default_factory=dict)
    request_data: Dict[str, Any] = field(default_factory=dict)
    response_data: Dict[str, Any] = field(default_factory=dict)
    wait_time: float = 0.0
    status_code: int = 0
    success: bool = False

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'url': self.url,
            'method': self.method,
            'action_type': self.action_type,
            'element_info': self.element_info,
            'request_data': self.request_data,
            'response_data': self.response_data,
            'wait_time': self.wait_time,
            'status_code': self.status_code,
            'success': self.success
        }


class HARProcessor:
    """HAR文件处理器"""

    def __init__(self, har_file_path: str = None, har_data: Dict = None):
        """
        初始化HAR处理器
        :param har_file_path: HAR文件路径
        :param har_data: HAR数据字典(与file_path二选一)
        """
        if har_file_path:
            with open(har_file_path, 'r', encoding='utf-8') as f:
                self.har_data = json.load(f)
        elif har_data:
            self.har_data = har_data
        else:
            raise ValueError("必须提供har_file_path或har_data")

        self.entries = self.har_data.get('log', {}).get('entries', [])
        self.business_keywords = {
            'login': ['login', 'signin', 'auth', 'token'],
            'logout': ['logout', 'signout'],
            'register': ['register', 'signup'],
            'search': ['search', 'query', 'filter', 'list'],
            'add': ['add', 'create', 'new', 'save'],
            'edit': ['edit', 'update', 'modify'],
            'delete': ['delete', 'remove', 'destroy'],
            'view': ['view', 'detail', 'info', 'get'],
            'download': ['download', 'export', 'csv', 'excel'],
            'upload': ['upload', 'import', 'file', 'attachment'],
            'submit': ['submit', 'approve', 'confirm'],
            'check': ['check', 'validate', 'verify']
        }

    def extract_user_journey(self, filter_static: bool = True) -> List[UserAction]:
        """
        提取用户旅程
        :param filter_static: 是否过滤静态资源请求
        :return: 用户操作列表
        """
        actions = []

        for entry in self.entries:
            try:
                # 解析请求和响应
                request = entry.get('request', {})
                response = entry.get('response', {})
                timings = entry.get('timings', {})

                url = request.get('url', '')

                # 过滤静态资源
                if filter_static and self._is_static_resource(url):
                    continue

                # 识别用户操作类型
                action_type = self._identify_action_type(request, response)

                # 提取关键信息
                user_action = UserAction(
                    timestamp=self._parse_timestamp(entry.get('startedDateTime')),
                    url=url,
                    method=request.get('method', ''),
                    action_type=action_type,
                    element_info=self._extract_element_info(request),
                    request_data=self._extract_request_data(request),
                    response_data=self._extract_response_data(response),
                    wait_time=timings.get('wait', 0) + timings.get('receive', 0),
                    status_code=response.get('status', 0),
                    success=response.get('status', 0) in [200, 201, 204]
                )

                actions.append(user_action)
            except Exception as e:
                print(f"解析条目失败: {e}")
                continue

        # 按时间排序
        actions.sort(key=lambda x: x.timestamp)
        return actions

    def _is_static_resource(self, url: str) -> bool:
        """判断是否是静态资源"""
        static_extensions = ['.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.woff', '.woff2', '.ttf']
        url_lower = url.lower()
        return any(url_lower.endswith(ext) for ext in static_extensions)

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """解析时间戳"""
        try:
            # 尝试ISO格式
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            # 如果失败,返回当前时间
            return datetime.now()

    def _identify_action_type(self, request: Dict, response: Dict) -> str:
        """识别操作类型"""
        url = request.get('url', '').lower()
        method = request.get('method', '').upper()

        # 基于URL路径的业务关键词识别
        for action_type, keywords in self.business_keywords.items():
            if any(keyword in url for keyword in keywords):
                return action_type

        # 基于HTTP方法的识别
        if method == 'GET':
            if '/api/' in url or '.json' in url:
                return 'data_fetch'
            else:
                return 'page_load'
        elif method == 'POST':
            return 'create'
        elif method == 'PUT':
            return 'update'
        elif method == 'DELETE':
            return 'delete'
        else:
            return 'unknown'

    def _extract_request_data(self, request: Dict) -> Dict:
        """提取请求数据"""
        data = {}

        # 提取POST数据
        post_data = request.get('postData', {}) or {}
        if post_data:
            mime_type = post_data.get('mimeType') or ''
            if isinstance(mime_type, str) and mime_type.startswith('application/json'):
                try:
                    text = post_data.get('text') or '{}'
                    data = json.loads(text)
                except:
                    data = {'raw': (post_data.get('text') or '')[:100]}
            elif isinstance(mime_type, str) and mime_type.startswith('application/x-www-form-urlencoded'):
                params = post_data.get('params') or []
                data = {item.get('name'): item.get('value')
                       for item in params}
            elif isinstance(mime_type, str) and mime_type.startswith('multipart/form-data'):
                params = post_data.get('params') or []
                for item in params:
                    data[item.get('name', '')] = '[文件]' if 'filename' in item else item.get('value', '')

        # 提取查询参数
        url = request.get('url', '')
        if '?' in url:
            try:
                query_params = parse_qs(url.split('?')[1])
                data.update({k: v[0] if len(v) == 1 else v for k, v in query_params.items()})
            except:
                pass

        return data

    def _extract_response_data(self, response: Dict) -> Dict:
        """提取响应数据"""
        content = response.get('content', {}) or {}
        mime_type = content.get('mimeType') or ''

        if isinstance(mime_type, str) and mime_type.startswith('application/json'):
            try:
                text = content.get('text') or '{}'
                return json.loads(text)
            except:
                return {'raw': (content.get('text') or '')[:100]}
        return {}

    def _extract_element_info(self, request: Dict) -> Dict:
        """提取页面元素信息"""
        headers = {h['name'].lower(): h['value'] for h in request.get('headers', [])}

        return {
            'referer': headers.get('referer', ''),
            'user_agent': headers.get('user-agent', ''),
            'content_type': headers.get('content-type', ''),
            'accept': headers.get('accept', '')
        }

    def generate_narrative(self, actions: List[UserAction]) -> str:
        """生成自然语言叙述"""
        if not actions:
            return "未检测到用户操作记录"

        narrative = "# 业务流程记录\n\n"
        narrative += f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        narrative += f"操作总数: {len(actions)}\n\n"
        narrative += "---\n\n"

        for i, action in enumerate(actions, 1):
            narrative += f"## 步骤{i}: {self._get_action_description(action)}\n\n"

            narrative += f"**操作类型**: {action.action_type}\n\n"
            narrative += f"**请求方法**: {action.method}\n\n"

            # 简化URL显示
            simplified_url = self._simplify_url(action.url)
            narrative += f"**请求路径**: `{simplified_url}`\n\n"

            # 请求参数
            if action.request_data:
                narrative += f"**请求参数**: {self._summarize_data(action.request_data)}\n\n"

            # 响应结果
            if action.response_data:
                narrative += f"**响应结果**: {self._summarize_response(action.response_data)}\n\n"

            # 状态信息
            status_icon = "✅" if action.success else "❌"
            narrative += f"**状态**: {status_icon} {action.status_code}\n\n"
            narrative += f"**耗时**: {action.wait_time:.2f}ms\n\n"

            narrative += "---\n\n"

        # 添加统计摘要
        narrative += self._generate_summary(actions)

        return narrative

    def _get_action_description(self, action: UserAction) -> str:
        """获取操作描述"""
        descriptions = {
            'login': '用户登录系统',
            'logout': '用户退出登录',
            'register': '用户注册账号',
            'search': '用户搜索数据',
            'add': '创建新记录',
            'edit': '更新记录',
            'delete': '删除记录',
            'view': '查看详情',
            'download': '下载数据',
            'upload': '上传文件',
            'submit': '提交表单',
            'check': '验证/检查数据',
            'page_load': '加载页面',
            'data_fetch': '获取数据',
            'create': '创建资源',
            'update': '更新资源',
            'unknown': '执行操作'
        }
        return descriptions.get(action.action_type, '执行操作')

    def _simplify_url(self, url: str) -> str:
        """简化URL显示"""
        try:
            parsed = urlparse(url)
            return parsed.path if not parsed.query else f"{parsed.path}?{parsed.query[:50]}..."
        except:
            return url[:80]

    def _summarize_data(self, data: Dict) -> str:
        """摘要化数据"""
        if not data:
            return "无"

        items = []
        for k, v in list(data.items())[:3]:
            if isinstance(v, str) and len(v) > 30:
                v = v[:30] + "..."
            items.append(f"{k}: {v}")

        summary = ", ".join(items)
        if len(data) > 3:
            summary += f" (共{len(data)}个字段)"

        return summary

    def _summarize_response(self, response: Dict) -> str:
        """摘要化响应"""
        if 'message' in response:
            return response['message']
        elif 'msg' in response:
            return response['msg']
        elif 'data' in response:
            data = response['data']
            if isinstance(data, list):
                return f"返回{len(data)}条记录"
            elif isinstance(data, dict):
                return "返回数据对象"
        elif 'code' in response:
            return f"状态码: {response['code']}"
        return "完成"

    def _generate_summary(self, actions: List[UserAction]) -> str:
        """生成统计摘要"""
        summary = "## 统计摘要\n\n"

        # 按操作类型统计
        type_counts = {}
        for action in actions:
            type_counts[action.action_type] = type_counts.get(action.action_type, 0) + 1

        summary += "**操作类型分布**:\n\n"
        for action_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            summary += f"- {action_type}: {count}次\n"

        # 成功率统计
        success_count = sum(1 for a in actions if a.success)
        success_rate = success_count / len(actions) * 100 if actions else 0
        summary += f"\n**成功率**: {success_rate:.1f}% ({success_count}/{len(actions)})\n"

        # 总耗时
        total_time = sum(a.wait_time for a in actions)
        avg_time = total_time / len(actions) if actions else 0
        summary += f"**总耗时**: {total_time:.2f}ms\n"
        summary += f"**平均耗时**: {avg_time:.2f}ms\n"

        return summary

    def export_actions_to_json(self, actions: List[UserAction], output_path: str):
        """导出操作到JSON文件"""
        actions_data = [action.to_dict() for action in actions]
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(actions_data, f, ensure_ascii=False, indent=2)

    def get_api_endpoints(self, actions: List[UserAction]) -> List[Dict]:
        """提取所有API端点"""
        endpoints = {}
        for action in actions:
            if '/api/' in action.url or action.action_type in ['data_fetch', 'create', 'update', 'delete']:
                endpoint = self._get_endpoint(action.url)
                if endpoint not in endpoints:
                    endpoints[endpoint] = {
                        'path': endpoint,
                        'method': action.method,
                        'action_type': action.action_type,
                        'call_count': 0,
                        'success_count': 0
                    }
                endpoints[endpoint]['call_count'] += 1
                if action.success:
                    endpoints[endpoint]['success_count'] += 1

        return list(endpoints.values())

    def _get_endpoint(self, url: str) -> str:
        """提取API端点"""
        try:
            parsed = urlparse(url)
            return parsed.path.split('?')[0]
        except:
            return url
