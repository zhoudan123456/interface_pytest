"""
基于类别的智能匹配演示
展示如何根据Excel中的"类别"字段在JSON对应分支下查找
"""

import json

# 模拟JSON结构（类似您的算法输出）
algorithm_json = {
    "data": [
        {
            "id": None,
            "label": "资格评审",
            "children": [
                {
                    "id": None,
                    "label": "资格要求",
                    "children": [
                        {
                            "id": 4424,
                            "label": "2.应答人资格要求\n2.1独立法人...\n2.2财务要求...\n2.3人员要求...",
                            "value": "完整的长文本（包含2.1-2.8所有要求）"
                        }
                    ]
                }
            ]
        },
        {
            "id": None,
            "label": "响应性评审",
            "children": [
                {
                    "id": 1001,
                    "label": "投标文件格式要求",
                    "value": "投标文件必须按照规定格式编制..."
                }
            ]
        },
        {
            "id": None,
            "label": "综合评审",
            "children": [
                {
                    "id": 2001,
                    "label": "技术方案评分",
                    "value": "对技术方案的完整性、可行性进行评分..."
                }
            ]
        }
    ]
}

# 模拟Excel标注数据
annotation_data = [
    {"检查点ID": "CP-001", "检查点文本": "主体资格证明文件：独立法人", "类别": "资格评审"},
    {"检查点ID": "CP-002", "检查点文本": "财务要求：能开具增值税专用发票", "类别": "资格评审"},
    {"检查点ID": "CP-003", "检查点文本": "投标文件格式要求", "类别": "响应性评审"},
]

print("=" * 80)
print("基于类别的智能匹配演示")
print("=" * 80)
print()

# 第一步：构建类别映射
def build_category_mapping(node_list, parent_category=""):
    """
    递归构建类别映射
    返回: {category_name: [nodes_with_id]}
    """
    category_map = {}

    for node in node_list:
        current_label = node.get('label', '')

        # 当前节点有id，是叶子节点（实际检查点）
        if node.get('id') is not None:
            # 使用父级类别作为分类依据
            if parent_category not in category_map:
                category_map[parent_category] = []

            category_map[parent_category].append({
                'id': node['id'],
                'value': node['value'],
                'label': node['label'],
                'parent_category': parent_category
            })

            print(f"  [发现节点] ID={node['id']}, 类别='{parent_category}'")

        # 递归处理子节点
        if node.get('children'):
            child_category = current_label if current_label else parent_category
            child_map = build_category_mapping(node['children'], child_category)

            # 合并类别映射
            for cat, nodes in child_map.items():
                if cat not in category_map:
                    category_map[cat] = []
                category_map[cat].extend(nodes)

    return category_map

print("[第一步] 构建类别映射...")
print()
category_mapping = build_category_mapping(algorithm_json['data'])

print()
print("类别映射结果:")
print("-" * 80)
for category, nodes in category_mapping.items():
    print(f"类别: '{category}'")
    for node in nodes:
        print(f"  - 节点ID: {node['id']}")
        print(f"    标签: {node['label'][:50]}...")
    print()

print("=" * 80)
print()

# 第二步：基于类别进行匹配
print("[第二步] 基于类别进行匹配...")
print()

for checkpoint in annotation_data:
    cp_id = checkpoint['检查点ID']
    cp_text = checkpoint['检查点文本']
    category = checkpoint['类别']

    print(f"处理检查点: {cp_id}")
    print(f"  文本: {cp_text}")
    print(f"  类别: {category}")

    # 获取该类别下的所有节点
    category_nodes = category_mapping.get(category, [])

    if not category_nodes:
        print(f"  [X] 未找到类别 '{category}' 下的节点")
    else:
        print(f"  [OK] 在类别 '{category}' 下找到 {len(category_nodes)} 个节点")

        # 只对该类别下的节点进行LLM判断（而不是所有节点）
        for node in category_nodes:
            print(f"    → 调用LLM判断: CP-{cp_id} vs 节点{node['id']}")

            # 这里会调用智谱AI进行语义判断
            # is_matched = llm_check_if_contained(cp_text, node['value'])

    print()

print("=" * 80)
print()

# 对比说明
print("[对比] 改进前 vs 改进后")
print("-" * 80)
print()

print("改进前（盲目查找）:")
print("  对于 CP-001（资格评审）")
print("    需要遍历所有节点（假设JSON有100个节点）")
print("    调用LLM 100次 ❌")
print()

print("改进后（基于类别）:")
print("  对于 CP-001（资格评审）")
print("    只在'资格评审'类别下查找（假设该类别有10个节点）")
print("    调用LLM 10次 [OK]")
print()

print("优势:")
print("  1. 效率提升 10倍（100次 → 10次）")
print("  2. 减少误匹配（不会把资格要求和综合评审混淆）")
print("  3. 成本降低 10倍")
print()

print("=" * 80)
print("演示完成")
print("=" * 80)
