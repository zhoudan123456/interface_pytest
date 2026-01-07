import requests
import json

# -------------------------- 1. 接口基础配置 --------------------------
# 完整接口URL
full_url = "https://test.intellibid.cn/prod-api/bid/ua/analysis/tender/sync"

# form-data请求参数（对应截图中的tenderId和type）
form_data = {
    "tenderId": "176491566034300000",  # 与截图参数值一致
    "type": "服务类"                     # 与截图参数值一致
}


# -------------------------- 2. 加载登录后的Cookie --------------------------
def load_login_cookies(cookie_file="cookies.json"):
    """加载之前保存的登录Cookie（字典格式）"""
    try:
        with open(cookie_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"加载Cookie失败：{e}")
        return {}


# -------------------------- 3. 发送POST请求 --------------------------
response = requests.post(
    url=full_url,
    data=form_data,    # 传递form-data格式的普通参数
    cookies=load_login_cookies()  # 携带登录态Cookie
)


# -------------------------- 4. 处理响应 --------------------------
print(f"请求状态码：{response.status_code}")
# 打印原始响应内容（避免JSON解析失败时报错）
print(f"响应内容：{response.text}")
# 若接口返回JSON格式，可解析为字典
try:
    print(f"响应JSON解析：{response.json()}")
except Exception as e:
    print(f"JSON解析失败：{e}")