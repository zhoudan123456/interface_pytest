import json
import pandas as pd
from datetime import datetime


def analyze_har_sequence(har_file_path):
    with open(har_file_path, 'r', encoding='utf-8') as f:
        har_data = json.load(f)

    entries = []
    for entry in har_data['log']['entries']:
        req = entry['request']
        resp = entry['response']
        # 解析时间，格式例如："2023-11-01T10:00:00.123Z"
        start_time = datetime.fromisoformat(entry['startedDateTime'].replace('Z', '+00:00'))

        entries.append({
            'time': start_time,
            'method': req['method'],
            'url': req['url'],
            'status': resp.get('status', 0),
            # 提取可能的关键参数，用于后续分析依赖
            'params': req.get('queryString', []),
            'bodySize': req.get('bodySize', 0)
        })

    # 按时间排序
    df = pd.DataFrame(entries)
    df = df.sort_values(by='time').reset_index(drop=True)

    print("=== 接口调用时间序列 ===")
    for i, row in df.iterrows():
        print(
            f"{i + 1}. [{row['time'].strftime('%H:%M:%S.%f')[:-3]}] {row['method']} {row['url']} (状态码: {row['status']})")

    return df


# 使用你的 .har 文件
df_sequence = analyze_har_sequence(r'E:\temp2\Untitled.har')