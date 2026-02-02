"""
创建简化版标注Excel模板
"""
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

def create_annotation_template():
    """创建标注Excel模板"""

    # 创建Excel Writer
    writer = pd.ExcelWriter('d:/python_project/ai_test/templates/checkpoint_annotation_template_simple.xlsx',
                            engine='openpyxl')

    # Sheet 1: 检查点标注
    df_checkpoints = pd.DataFrame(columns=[
        '序号', '检查点ID', '检查点文本', '类别', '页码', '是否必需', '备注'
    ])
    # 添加示例行
    df_checkpoints.loc[0] = [1, 'CP-001', '投标人注册资本不低于1000万元',
                              '资格评审', 3, '是', '硬性要求']
    df_checkpoints.loc[1] = [2, 'CP-002', '项目经理须具有一级建造师资格证书',
                              '资格评审', 3, '是', '']

    df_checkpoints.to_excel(writer, sheet_name='检查点标注', index=False)

    # Sheet 2: 文件信息
    df_file_info = pd.DataFrame(columns=[
        '文件ID', '文件名', '标注员', '标注日期', '总检查点数'
    ])
    df_file_info.loc[0] = ['F001', 'XX项目.pdf', '测试员', '2026-01-30', 15]
    df_file_info.to_excel(writer, sheet_name='文件信息', index=False)

    # Sheet 3: 类别说明
    df_categories = pd.DataFrame(columns=[
        '类别代码', '类别名称', '说明'
    ])
    df_categories.loc[0] = ['1', '响应性评审', '符合性检查、报价、文件编制等']
    df_categories.loc[1] = ['2', '形式评审', '封面、签字、法定代表人等']
    df_categories.loc[2] = ['3', '综合评审', '各评分项']
    df_categories.loc[3] = ['4', '资格评审', '资格要求、资格审查']
    df_categories.to_excel(writer, sheet_name='类别说明', index=False)

    # 保存文件
    writer.close()

    print("[OK] Annotation template created: d:/python_project/ai_test/templates/checkpoint_annotation_template_simple.xlsx")
    return 'd:/python_project/ai_test/templates/checkpoint_annotation_template_simple.xlsx'

if __name__ == '__main__':
    create_annotation_template()
