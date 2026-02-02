"""
调试脚本：测试包含匹配是否工作
使用用户实际的标注数据
"""

# 模拟你的实际数据
ground_truth_texts = [
    "主体资格证明文件：本项目要求应答人必须为中国境内依法注册的独立法人或依法成立的其他组织。提供营业执照扫描件或其他有效证明文件。",
    "财务要求：应答人能开具增值税专用发票，且未处于被责令停业、财产被接管、冻结、破产状态。提供承诺书。",
    "联合体：本项目不接受联合体应答。",
]

algorithm_text = """2.应答人资格要求
2.1本项目要求应答人必须为中国境内依法注册的独立法人或依法成立的其他组织。提供营业执照扫描件或其他有效证明文件。
2.2财务要求:应答人能开具增值税专用发票,且未处于被责令停业、财产被接管、冻结、破产状态。提供承诺书。
2.3人员要求:为本项目提供1个服务团队,不少于5名值班人员须具有中专及以上学历和高压电工证,值班人员中有1名担任值班组长,值班组长须具有中专及以上学历和高压电工证及从事通信机房或相关领域动力设备代(运)维或施工技术工作5年以上相关管理经验(提供团队人员名单、毕业证扫描件或学信网查询截图、证书扫描件、值班组长简历(工作经验以毕业时间起算)、身份证扫描件及由应答人为其缴纳社保局出具的2022年至今任意连续6个月的社保缴纳证明扫描件。(值班人员社保如为第三方代缴还需提供应答人与第三方代缴公司的协议文件扫描件)。
2.4业绩要求:应答人须提供2020年1月1日至本公告发布之日止(以合同或订单签订日期为准)类似机房维护或值守代维项目业绩。提供合同关键页复印件,能体现采购金额、内容、买方等信息,如为框架合同,需提供订单或发票等证明材料(需加盖应答人单位公章,并对其真实性负责,原件备查)。
2.5本项目不接受联合体应答。
2.6单位负责人为同一人或者存在控股、管理关系的不同单位,不得参加同一比选项目应答。同一项目不同应答人高级管理人员之间存在交叉任职的,视为单位负责人为同一人,相关应答均无效。
1单位负责人是指单位法定代表人或者法律、行政法规规定代表单位行使单位职权的主要负责人,以资格审查评审日查询"国家企业信用信息公示系统"等平台的主要人员信息为准。
2同一项目不同应答人之间存在控股关系的,不限于股份占比超过50%或为占比最大股东。
2.7未处于中国联通集团公司或江苏联通供应商黑名单禁入期内或预警期内;处于中国联通集团公司或江苏联通供应商黑名单禁入期内或预警期内的供应商所注册设立的与其现有经营业务相似的其他法人或组织不得参与应答。
2.8应答人不得存在下列情形之一:
(1)为采购人不具有独立法人资格的附属机构(单位);
(2)被责令停业的;
(3)被暂停或者取消参选资格的;
(4)财产被接管或者冻结的;
(5)在最近三年内有骗取中选、严重违约、重大工程质量或者安全问题的;
(6)法律法规限定的其他情形。"""

print("=" * 80)
print("Containment Matching Test")
print("=" * 80)
print()

print(f"Algorithm text length: {len(algorithm_text)}")
print(f"Algorithm text preview: {algorithm_text[:100]}...")
print()

for i, gt_text in enumerate(ground_truth_texts, 1):
    print(f"[Test {i}]")
    print(f"GT text: {gt_text[:80]}...")
    print(f"GT length: {len(gt_text)}")
    print()

    # Test 1: Direct substring check
    print("  [Test 1] Direct substring check:")
    is_contained = gt_text in algorithm_text
    print(f"    gt_text in algorithm_text: {is_contained}")

    if is_contained:
        ratio = len(gt_text) / len(algorithm_text)
        print(f"    Containment ratio: {ratio:.4f}")
        print(f"    Threshold: 0.80")
        if ratio <= 0.8:
            print(f"    [SUCCESS] Would match! (ratio <= 0.8)")
        else:
            print(f"    [FAILED] Ratio too high")
    else:
        print(f"    [FAILED] Not contained")

    print()

    # Test 2: Check for slight variations
    print("  [Test 2] Checking for text variations:")

    # Remove punctuation and spaces
    gt_clean = gt_text.replace("：", ":").replace("，", ",").replace("。", ".").replace("\n", "").replace(" ", "")
    algo_clean = algorithm_text.replace("：", ":").replace("，", ",").replace("。", ".").replace("\n", "").replace(" ", "")

    print(f"    GT text (cleaned): {gt_clean[:80]}...")
    print(f"    GT length (cleaned): {len(gt_clean)}")

    is_contained_clean = gt_clean in algo_clean
    print(f"    gt_clean in algo_clean: {is_contained_clean}")

    if is_contained_clean:
        ratio = len(gt_clean) / len(algo_clean)
        print(f"    Containment ratio (cleaned): {ratio:.4f}")
        if ratio <= 0.8:
            print(f"    [SUCCESS] Would match after cleaning!")
        else:
            print(f"    [FAILED] Ratio still too high")

    print()
    print("-" * 80)
    print()

print("=" * 80)
print("Test Complete")
print("=" * 80)
