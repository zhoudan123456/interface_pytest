"""
层次化匹配原理演示脚本
展示三种匹配模式的具体工作过程
"""
from rapidfuzz import fuzz, process

# 模拟数据
ground_truth = [
    {'id': 'CP-001', 'text': '主体资格证明文件：本项目要求应答人必须为中国境内依法注册的独立法人'},
    {'id': 'CP-002', 'text': '总报价不超过项目(分包)预算金额或最高限价'},
    {'id': 'CP-003', 'text': '投标文件未按磋商文件要求盖章或签字(签章)'},
]

algorithm_result = [
    {
        'id': 1,
        'value': '2.应答人资格要求\n2.1本项目要求应答人必须为中国境内依法注册的独立法人或依法成立的其他组织。提供营业执照扫描件或其他有效证明文件。\n2.2财务要求:应答人能开具增值税专用发票...'
    },
    {
        'id': 2,
        'value': '磋商报价：总报价不超过项目(分包)预算金额或最高限价'
    },
    {
        'id': 3,
        'value': '响应文件编制：未按磋商文件要求盖章或签字(签章)'
    },
]

print("=" * 80)
print("Hierarchical Matching Demo")
print("=" * 80)
print()

matched_algo = set()

for gt in ground_truth:
    gt_id = gt['id']
    gt_text = gt['text']

    print(f"[Processing] {gt_id}")
    print(f"Text: {gt_text[:50]}...")
    print()

    # ===== Method 1: Similarity Matching =====
    print("  [Method 1] Similarity Matching...")
    matches = process.extract(
        gt_text,
        [algo['value'] for algo in algorithm_result],
        scorer=fuzz.token_sort_ratio,
        limit=1
    )

    best_match_score = matches[0][1] if matches else 0
    best_match_idx = matches[0][2] if matches else -1

    print(f"    Best Similarity: {best_match_score:.1f}%")
    print(f"    Threshold: 85%")

    is_matched = False
    match_type = None
    matched_algo_checkpoint = None

    if best_match_score >= 85:
        is_matched = True
        match_type = 'exact'
        matched_algo_checkpoint = algorithm_result[best_match_idx]
        print(f"    [OK] 完全匹配！")

    # ===== Method 2: Containment Matching =====
    if not is_matched:
        print("  [Method 2] Containment Matching...")
        for idx, algo in enumerate(algorithm_result):
            if idx in matched_algo:
                continue  # Skip already matched

            algo_text = algo['value']

            # Check: gt_text in algo_text
            if gt_text in algo_text:
                containment_ratio = len(gt_text) / len(algo_text)
                print(f"    Checking algo output #{idx}")
                print(f"      GT text length: {len(gt_text)}")
                print(f"      Algo text length: {len(algo_text)}")
                print(f"      Containment ratio: {containment_ratio:.2f}")
                print(f"      Threshold: 0.80")

                if containment_ratio <= 0.8:
                    is_matched = True
                    match_type = 'contained'
                    matched_algo_checkpoint = algo
                    best_match_idx = idx
                    print(f"      [OK] Containment match!")
                    break
                else:
                    print(f"      [X] Ratio too high, not a containment")

            # Check: algo_text in gt_text
            elif algo_text in gt_text:
                is_matched = True
                match_type = 'contains'
                matched_algo_checkpoint = algo
                best_match_idx = idx
                print(f"    [OK] Reverse containment match!")
                break

    print()

    # ===== Matching Result =====
    if is_matched:
        matched_algo.add(best_match_idx)
        match_type_zh = {
            'exact': 'Exact Match',
            'contained': 'Contained (Algo contains GT)',
            'contains': 'Contains (GT contains Algo)'
        }.get(match_type, 'Unknown')

        print(f"  [SUCCESS] Matched!")
        print(f"     Type: {match_type_zh}")
        print(f"     Matched to algo output #{best_match_idx}")
        print()
    else:
        print(f"  [FAILED] Not matched (Missed)")
        print()

    print("-" * 80)
    print()

# ===== False Positive Detection =====
print("[False Positive Detection]")
print("Checking unmatched algorithm outputs...")
print()

for i, algo in enumerate(algorithm_result):
    if i not in matched_algo:
        print(f"  FP-#{algo['id']}: {algo['value'][:50]}...")
        print()

print("=" * 80)
print("Demo End")
print("=" * 80)
