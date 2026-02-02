"""
投标文件检查工具 - GUI界面
用于简化文件选择和命令执行流程
"""
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
import subprocess
import os
import threading
import pathlib

# 加载 .env 文件中的环境变量
try:
    from dotenv import load_dotenv
    # 获取项目根目录
    project_root = pathlib.Path(__file__).parent.resolve()
    env_file = project_root / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print(f"[OK] 已加载环境变量: {env_file}")
except ImportError:
    pass  # python-dotenv 未安装，跳过


class BidCheckGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("投标文件检查工具")
        self.root.geometry("800x700")

        # 文件路径变量
        self.zb_file_path = tk.StringVar()
        self.tb_file_path = tk.StringVar()
        self.excel_file_path = tk.StringVar()
        self.json_file_path = tk.StringVar()

        self.create_widgets()

    def create_widgets(self):
        """创建界面组件"""
        # 标题
        title_label = tk.Label(
            self.root,
            text="投标文件检查工具",
            font=("微软雅黑", 16, "bold")
        )
        title_label.pack(pady=10)

        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # === 步骤1：pytest测试 ===
        step1_frame = ttk.LabelFrame(main_frame, text="步骤1：执行pytest测试", padding="10")
        step1_frame.pack(fill=tk.X, pady=5)

        # 招标文件选择
        ttk.Label(step1_frame, text="招标文件(PDF):").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(step1_frame, textvariable=self.zb_file_path, width=50).grid(row=0, column=1, pady=5, padx=5)
        ttk.Button(step1_frame, text="选择文件", command=self.select_zb_file).grid(row=0, column=2, pady=5)

        # 投标文件选择
        ttk.Label(step1_frame, text="投标文件(PDF):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(step1_frame, textvariable=self.tb_file_path, width=50).grid(row=1, column=1, pady=5, padx=5)
        ttk.Button(step1_frame, text="选择文件", command=self.select_tb_file).grid(row=1, column=2, pady=5)

        # 执行pytest按钮
        ttk.Button(
            step1_frame,
            text="执行pytest测试",
            command=self.run_pytest_test
        ).grid(row=2, column=0, columnspan=3, pady=10)

        # === 步骤2：LLM匹配 ===
        step2_frame = ttk.LabelFrame(main_frame, text="步骤2：执行LLM匹配", padding="10")
        step2_frame.pack(fill=tk.X, pady=5)

        # Excel模板文件选择
        ttk.Label(step2_frame, text="Excel模板:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(step2_frame, textvariable=self.excel_file_path, width=50).grid(row=0, column=1, pady=5, padx=5)
        ttk.Button(step2_frame, text="选择文件", command=self.select_excel_file).grid(row=0, column=2, pady=5)

        # JSON响应文件选择
        ttk.Label(step2_frame, text="JSON响应文件:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(step2_frame, textvariable=self.json_file_path, width=50).grid(row=1, column=1, pady=5, padx=5)
        ttk.Button(step2_frame, text="选择文件", command=self.select_json_file).grid(row=1, column=2, pady=5)

        # 执行LLM匹配按钮
        ttk.Button(
            step2_frame,
            text="执行LLM匹配",
            command=self.run_llm_matcher
        ).grid(row=2, column=0, columnspan=3, pady=10)

        # === 执行日志 ===
        log_frame = ttk.LabelFrame(main_frame, text="执行日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=90)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 底部按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)

        ttk.Button(button_frame, text="清空日志", command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="退出", command=self.root.quit).pack(side=tk.RIGHT, padx=5)

    def select_zb_file(self):
        """选择招标文件"""
        filename = filedialog.askopenfilename(
            title="选择招标文件",
            filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
        )
        if filename:
            self.zb_file_path.set(filename)
            self.log(f"已选择招标文件: {filename}")

    def select_tb_file(self):
        """选择投标文件"""
        filename = filedialog.askopenfilename(
            title="选择投标文件",
            filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
        )
        if filename:
            self.tb_file_path.set(filename)
            self.log(f"已选择投标文件: {filename}")

    def select_excel_file(self):
        """选择Excel模板文件"""
        filename = filedialog.askopenfilename(
            title="选择Excel模板文件",
            filetypes=[("Excel文件", "*.xlsx;*.xls"), ("所有文件", "*.*")]
        )
        if filename:
            self.excel_file_path.set(filename)
            self.log(f"已选择Excel模板: {filename}")

    def select_json_file(self):
        """选择JSON响应文件"""
        filename = filedialog.askopenfilename(
            title="选择JSON响应文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if filename:
            self.json_file_path.set(filename)
            self.log(f"已选择JSON文件: {filename}")

    def run_pytest_test(self):
        """执行pytest测试"""
        if not self.zb_file_path.get() or not self.tb_file_path.get():
            self.log("错误: 请先选择招标文件和投标文件!")
            return

        self.log("=" * 60)
        self.log("开始执行pytest测试...")

        cmd = [
            "pytest",
            "test_cases/workflows/test_bid_check_workflow.py",
            "-v",
            f"--zb-file={self.zb_file_path.get()}",
            f"--tb-file={self.tb_file_path.get()}"
        ]

        # 在新线程中执行命令，避免界面卡死
        thread = threading.Thread(target=self._run_command, args=(cmd,))
        thread.daemon = True
        thread.start()

    def run_llm_matcher(self):
        """执行LLM匹配"""
        if not self.excel_file_path.get() or not self.json_file_path.get():
            self.log("错误: 请先选择Excel模板和JSON响应文件!")
            return

        self.log("=" * 60)
        self.log("开始执行LLM匹配...")
        self.log(f"[DEBUG] Excel: {self.excel_file_path.get()}")
        self.log(f"[DEBUG] JSON: {self.json_file_path.get()}")

        cmd = [
            "python",
            "ai_test_scripts/llm_matcher_zhipuai.py",
            self.excel_file_path.get(),
            self.json_file_path.get()
        ]

        # 在新线程中执行命令，避免界面卡死
        thread = threading.Thread(target=self._run_command, args=(cmd,))
        thread.daemon = True
        thread.start()

    def _run_command(self, cmd):
        """在后台线程中执行命令"""
        try:
            # 确保环境变量被传递
            env = os.environ.copy()

            # 确保 ZHIPUAI_API_KEY 在环境变量中
            if 'ZHIPUAI_API_KEY' not in env or not env['ZHIPUAI_API_KEY']:
                # 从 .env 文件读取
                try:
                    project_root = pathlib.Path(__file__).parent.resolve()
                    env_file = project_root / '.env'
                    if env_file.exists():
                        # 读取 .env 文件并解析
                        with open(env_file, 'r', encoding='utf-8') as f:
                            for line in f:
                                line = line.strip()
                                if line.startswith('ZHIPUAI_API_KEY='):
                                    api_key = line.split('=', 1)[1].strip()
                                    env['ZHIPUAI_API_KEY'] = api_key
                                    self.log(f"[DEBUG] 从 .env 读取 API key")
                                    break
                except Exception as e:
                    self.log(f"[WARNING] 无法读取 .env 文件: {e}")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env  # 明确传递环境变量
            )

            # 实时读取输出
            for line in process.stdout:
                self.log(line.rstrip())

            process.wait()
            self.log(f"\n命令执行完成，退出码: {process.returncode}")

        except Exception as e:
            self.log(f"执行出错: {str(e)}")

    def log(self, message):
        """添加日志信息"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)


def main():
    """主函数"""
    root = tk.Tk()
    app = BidCheckGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
