"""
调试脚本：检查类别映射是否正确构建
"""
import json

# 读取您的实际JSON文件
json_file = "D:/python_project/ai_test/data/check_point_response_20260129_152013.json"

with open(json_file, 'r', encoding='utf-8') as f:
    algo_data = json.load(f)

print("=" * 80)
print("调试类别映射")
print("=" * 80)
print()

# 递归打印JSON树结构
def print_tree(node_list, indent=0, path=""):
    """打印树形结构"""
    for node in node_list:
        current_path = f"{path} / {node.get('label', '')}" if path else node.get('label', '')

        # 打印当前节点
        id_str = f"ID:{node['id']}" if node.get('id') is not None else "ID:null"
        has_children = "HAS_CHILDREN" if node.get('children') else "LEAF"

        print("  " * indent + f"├─ [{id_str}] {node.get('label', '')} ({has_children})")
        print("  " * indent + f"   Path: {current_path}")

        # 递归打印子节点
        if node.get('children'):
            print_tree(node['children'], indent + 1, current_path)

print("[JSON树形结构]")
print("-" * 80)
print_tree(algo_data.get('data', []))
print()

# 测试当前的映射逻辑
print("\n[测试当前映射逻辑]")
print("-" * 80)

def build_category_mapping_OLD(node_list, parent_category=""):
    """当前的映射逻辑（有问题的版本）"""
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
                'value': node['value'][:50] + '...' if len(node['value']) > 50 else node['value'],
                'label': node['label'],
                'parent_category': parent_category
            })

            print(f"  添加节点 ID:{node['id']} → 类别:'{parent_category}'")

        # 递归处理子节点
        if node.get('children'):
            # 子节点的父级类别可能是当前标签
            child_category = current_label if current_label else parent_category
            child_map = build_category_mapping_OLD(node['children'], child_category)

            # 合并类别映射
            for cat, nodes in child_map.items():
                if cat not in category_map:
                    category_map[cat] = []
                category_map[cat].extend(nodes)

    return category_map

category_mapping_old = build_category_mapping_OLD(algo_data.get('data', []))

print(f"\n当前逻辑构建的类别映射: {len(category_mapping_old)} 个类别")
for cat, nodes in category_mapping_old.items():
    print(f"  '{cat}': {len(nodes)} 个节点")

# 测试改进后的映射逻辑
print("\n[测试改进后的映射逻辑]")
print("-" * 80)

def build_category_mapping_NEW(node_list, category_stack=""):
    """
    改进后的映射逻辑
    使用完整路径作为类别，而不仅仅是直接父节点
    """
    category_map = {}

    for node in node_list:
        current_label = node.get('label', '')

        # 构建当前节点的完整路径
        if category_stack:
            current_path = f"{category_stack} > {current_label}" if current_label else category_stack
        else:
            current_path = current_label

        # 当前节点有id，是叶子节点（实际检查点）
        if node.get('id') is not None:
            # 使用完整路径中的第一级作为类别
            top_level_category = category_stack.split(' > ')[0] if ' > ' in category_stack else category_stack

            if top_level_category not in category_map:
                category_map[top_level_category] = []

            category_map[top_level_category].append({
                'id': node['id'],
                'value': node['value'][:50] + '...' if len(node['value']) > 50 else node['value'],
                'label': node['label'],
                'top_level_category': top_level_category
            })

            print(f"  添加节点 ID:{node['id']}")
            print(f"    完整路径: {current_path}")
            print(f"    顶级类别: '{top_level_category}'")

        # 递归处理子节点
        if node.get('children'):
            child_map = build_category_mapping_NEW(node['children'], current_path)

            # 合并类别映射
            for cat, nodes in child_map.items():
                if cat not in category_map:
                    category_map[cat] = []
                category_map[cat].extend(nodes)

    return category_map

category_mapping_new = build_category_mapping_NEW(algo_data.get('data', []))

print(f"\n改进后逻辑构建的类别映射: {len(category_mapping_new)} 个类别")
for cat, nodes in category_mapping_new.items():
    print(f"  '{cat}': {len(nodes)} 个节点")
    for node in nodes:
        print(f"    - ID:{node['id']}")

print()
print("=" * 80)
print("结论:")
print("-" * 80)

# 检查Excel中的类别
excel_categories = ["资格评审", "响应性评审", "综合评审"]

print("Excel中的类别:")
for cat in excel_categories:
    in_old = cat in category_mapping_old
    in_new = cat in category_mapping_new
    print(f"  '{cat}':")
    print(f"    旧逻辑找到: {'是' if in_old else '否'}")
    print(f"    新逻辑找到: {'是' if in_new else '否'}")

print()
print("=" * 80)
