"""
文档处理器
用于加载和预处理招标文件
"""
import os
from pathlib import Path
from typing import Dict, List, Optional


class DocumentProcessor:
    """招标文件处理器"""

    def __init__(self):
        """初始化文档处理器"""
        self.supported_formats = ['.txt', '.pdf', '.docx', '.doc']

    def load_and_preprocess(self, file_path: str) -> str:
        """
        加载并预处理文档
        :param file_path: 文档文件路径
        :return: 文档文本内容
        """
        file_path = Path(file_path)

        # 检查文件是否存在
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 检查文件格式
        suffix = file_path.suffix.lower()
        if suffix not in self.supported_formats:
            raise ValueError(f"不支持的文件格式: {suffix}")

        # 根据文件类型加载
        if suffix == '.txt':
            return self._load_txt(file_path)
        elif suffix == '.pdf':
            return self._load_pdf(file_path)
        elif suffix in ['.docx', '.doc']:
            return self._load_docx(file_path)
        else:
            raise ValueError(f"未实现的文件格式处理: {suffix}")

    def _load_txt(self, file_path: Path) -> str:
        """
        加载文本文件
        :param file_path: 文件路径
        :return: 文本内容
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self._clean_text(content)
        except UnicodeDecodeError:
            # 尝试其他编码
            with open(file_path, 'r', encoding='gbk') as f:
                content = f.read()
            return self._clean_text(content)

    def _load_pdf(self, file_path: Path) -> str:
        """
        加载PDF文件
        :param file_path: 文件路径
        :return: 文本内容
        """
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
            return self._clean_text(text)
        except ImportError:
            print("警告: 未安装PyPDF2,无法处理PDF文件")
            print("请运行: pip install PyPDF2")
            return ""
        except Exception as e:
            print(f"加载PDF文件失败: {str(e)}")
            return ""

    def _load_docx(self, file_path: Path) -> str:
        """
        加载Word文档
        :param file_path: 文件路径
        :return: 文本内容
        """
        try:
            from docx import Document
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return self._clean_text(text)
        except ImportError:
            print("警告: 未安装python-docx,无法处理Word文档")
            print("请运行: pip install python-docx")
            return ""
        except Exception as e:
            print(f"加载Word文档失败: {str(e)}")
            return ""

    def _clean_text(self, text: str) -> str:
        """
        清理文本内容
        :param text: 原始文本
        :return: 清理后的文本
        """
        # 去除多余的空白字符
        text = ' '.join(text.split())

        # 去除特殊字符(根据需要调整)
        # text = text.replace('\x0c', '')  # PDF分页符

        return text.strip()

    def load_batch(self, directory: str, pattern: str = "*") -> List[Dict[str, str]]:
        """
        批量加载目录下的文档
        :param directory: 目录路径
        :param pattern: 文件匹配模式(如 "*.txt")
        :return: 文档列表,每个元素包含 {'path': str, 'content': str}
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            raise FileNotFoundError(f"目录不存在: {directory}")

        documents = []
        for file_path in dir_path.glob(pattern):
            if file_path.suffix.lower() in self.supported_formats:
                try:
                    content = self.load_and_preprocess(str(file_path))
                    documents.append({
                        'path': str(file_path),
                        'filename': file_path.name,
                        'content': content
                    })
                except Exception as e:
                    print(f"加载文件失败 {file_path}: {str(e)}")

        return documents

    def extract_text_sections(self, text: str, sections: List[str]) -> Dict[str, str]:
        """
        提取文档的特定章节
        :param text: 文档文本
        :param sections: 要提取的章节标题列表
        :return: 章节内容字典
        """
        sections_dict = {}
        lines = text.split('\n')
        current_section = None
        current_content = []

        for line in lines:
            # 检查是否是章节标题
            if any(section in line for section in sections):
                # 保存上一个章节
                if current_section:
                    sections_dict[current_section] = '\n'.join(current_content).strip()

                # 开始新章节
                current_section = line.strip()
                current_content = []
            else:
                if current_section:
                    current_content.append(line)

        # 保存最后一个章节
        if current_section:
            sections_dict[current_section] = '\n'.join(current_content).strip()

        return sections_dict

    def truncate_text(self, text: str, max_length: int = 6000,
                     strategy: str = 'middle') -> str:
        """
        截断文本到指定长度
        :param text: 原始文本
        :param max_length: 最大长度
        :param strategy: 截断策略 ('start', 'middle', 'end')
        :return: 截断后的文本
        """
        if len(text) <= max_length:
            return text

        if strategy == 'start':
            return text[:max_length]
        elif strategy == 'end':
            return text[-max_length:]
        elif strategy == 'middle':
            # 保留开头和结尾
            half_length = max_length // 2
            return text[:half_length] + "\n...\n" + text[-half_length:]
        else:
            return text[:max_length]
