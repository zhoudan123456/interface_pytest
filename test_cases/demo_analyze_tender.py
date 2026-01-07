import requests
import json
from conf.set_conf import read_yaml, read_conf


def load_login_cookies(cookie_file="cookies.json"):
    """加载之前保存的登录Cookie"""
    try:
        with open(cookie_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"加载Cookie失败：{e}")
        return {}


def analyze_tender_from_yaml():
    """从YAML配置文件读取数据并发起分析招标文件请求"""
    # 读取YAML配置数据
    config_data = read_yaml('../test_data/login.yaml')[0]
    analyze_tender_data = config_data['analyze_tender']
    
    # 构建完整URL
    base_url = "https://test.intellibid.cn"
    full_url = base_url + analyze_tender_data['path']
    
    # 获取请求数据
    form_data = analyze_tender_data['data']
    
    # 发送POST请求
    response = requests.post(
        url=full_url,
        data=form_data,
        cookies=load_login_cookies()
    )
    
    # 处理响应
    print(f"请求状态码：{response.status_code}")
    print(f"响应内容：{response.text}")
    
    try:
        response_json = response.json()
        print(f"响应JSON解析：{response_json}")
        return response_json
    except Exception as e:
        print(f"JSON解析失败：{e}")
        return None


if __name__ == "__main__":
    # 直接运行示例
    result = analyze_tender_from_yaml()