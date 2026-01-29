"""
算法模型API客户端封装
用于调用招标文件解析算法
"""
import json
from typing import Dict, List, Optional
from api_keys.api_keys import ApiKeys


class AlgorithmClient:
    """算法模型API客户端"""

    def __init__(self, env: str = 'Test_Env'):
        """
        初始化算法客户端
        :param env: 环境配置(Test_Env/Prod_Env)
        """
        self.api = ApiKeys(env)

    def parse_bid_document(self, document_id: str, **kwargs) -> List[Dict]:
        """
        解析招标文件
        :param document_id: 文档ID
        :return: 解析结果(检查点列表)
        """
        from conf.set_conf import read_conf

        # 构建请求参数
        query_params = {
            "tenderId": document_id
        }

        # 从配置读取API路径
        # 默认使用 /api/tender/checkBidFile 接口
        path = kwargs.get('path', '/api/tender/checkBidFile')

        try:
            # 发送请求
            response = self.api.request(
                method='GET',
                path=path,
                params=query_params
            )

            # 检查响应状态
            if response.status_code != 200:
                print(f"算法API请求失败: {response.status_code}")
                return []

            # 解析响应
            result = response.json()
            if result.get('code') == 200:
                # 提取检查点数据
                data = result.get('data', {})
                return self._extract_checkpoints(data)
            else:
                print(f"算法API返回错误: {result.get('msg', 'Unknown error')}")
                return []

        except Exception as e:
            print(f"调用算法API失败: {str(e)}")
            return []

    def parse_bid_document_from_text(self, document_text: str) -> List[Dict]:
        """
        直接从文本解析招标文件(如果API支持)
        :param document_text: 文档文本内容
        :return: 解析结果(检查点列表)
        """
        # 注意:这个方法需要根据实际的API接口实现
        # 如果API不支持直接文本输入,可以先上传文档获取ID再解析
        raise NotImplementedError("此方法需要根据实际API接口实现")

    def _extract_checkpoints(self, data: Dict) -> List[Dict]:
        """
        从API响应数据中提取检查点
        :param data: API响应数据
        :return: 检查点列表
        """
        checkpoints = []

        # 根据实际的API响应结构提取检查点
        # 这里需要根据实际API返回的数据结构调整
        if isinstance(data, list):
            # 如果data是列表,直接返回
            checkpoints = data
        elif isinstance(data, dict):
            # 如果data是字典,尝试提取checkpoints字段
            checkpoints = data.get('checkpoints', [])
            # 或者从其他字段提取
            if not checkpoints:
                # 尝试从其他可能包含检查点的字段提取
                for key in ['items', 'results', 'data']:
                    if key in data:
                        value = data[key]
                        if isinstance(value, list):
                            checkpoints = value
                            break

        # 标准化检查点格式
        normalized_checkpoints = []
        for cp in checkpoints:
            if isinstance(cp, dict):
                normalized_cp = {
                    'id': cp.get('id', cp.get('checkpointId', '')),
                    'category': cp.get('category', cp.get('type', '未知')),
                    'content': cp.get('content', cp.get('description', cp.get('text', ''))),
                    'importance': cp.get('importance', cp.get('level', '中'))
                }
                normalized_checkpoints.append(normalized_cp)

        return normalized_checkpoints

    def get_parse_result(self, task_id: str) -> Dict:
        """
        获取解析结果(用于异步任务)
        :param task_id: 任务ID
        :return: 解析结果
        """
        # 这个方法用于轮询获取异步任务的解析结果
        # 需要根据实际API实现
        raise NotImplementedError("此方法需要根据实际API接口实现")
