"""
编码兼容性工具
解决Windows终端中文乱码问题
"""
import sys
import os

# Windows终端编码兼容
if sys.platform == 'win32':
    # 设置标准输出编码为UTF-8
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

def safe_print(text, **kwargs):
    """
    安全打印函数，自动处理编码问题

    Args:
        text: 要打印的文本
        **kwargs: 传递给print的其他参数
    """
    try:
        print(text, **kwargs)
    except UnicodeEncodeError:
        # 如果UTF-8编码失败，尝试GBK编码
        try:
            print(text.encode('gbk', errors='replace').decode('gbk'), **kwargs)
        except:
            # 最后的备选方案：移除非ASCII字符
            print(text.encode('ascii', errors='replace').decode('ascii'), **kwargs)

def get_console_encoding():
    """获取控制台编码"""
    encoding = sys.stdout.encoding or 'utf-8'
    return encoding
