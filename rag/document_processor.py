"""文档处理器 - 解析文本/PDF/DOCX 文件，分块处理。"""

import os
import uuid


class DocumentProcessor:
    """文档解析与分块处理器。"""

    CHUNK_SIZE = 500  # 每块最大字符数
    CHUNK_OVERLAP = 50  # 块间重叠字符数

    def __init__(self, chunk_size=None, chunk_overlap=None):
        """初始化处理器。

        Args:
            chunk_size: 每块最大字符数，默认 500
            chunk_overlap: 块间重叠字符数，默认 50
        """
        self.chunk_size = chunk_size or self.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or self.CHUNK_OVERLAP

    def parse_file(self, file_path):
        """解析文件内容为纯文本。

        Args:
            file_path: 文件绝对路径

        Returns:
            str: 解析后的纯文本内容

        Raises:
            ValueError: 不支持的文件类型
        """
        ext = file_path.rsplit(".", 1)[-1].lower()

        if ext == "txt":
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        elif ext == "pdf":
            return self._parse_pdf(file_path)
        elif ext == "docx":
            return self._parse_docx(file_path)
        else:
            raise ValueError(f"不支持的文件类型: .{ext}")

    def chunk_text(self, text):
        """将文本分割为重叠的块。

        按段落边界智能切分，优先保持语义完整性。

        Args:
            text: 完整文本

        Returns:
            list[str]: 文本块列表
        """
        if not text or not text.strip():
            return []

        # 先按段落分割
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [text.strip()]

        chunks = []
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
            else:
                if current_chunk:
                    chunks.append(current_chunk)

                # 如果单个段落超过 chunk_size，强制切分
                if len(para) > self.chunk_size:
                    sub_chunks = self._hard_split(para)
                    if len(sub_chunks) > 1:
                        current_chunk = sub_chunks[-1]
                        chunks.extend(sub_chunks[:-1])
                    else:
                        current_chunk = sub_chunks[0]
                else:
                    current_chunk = para

        if current_chunk:
            chunks.append(current_chunk)

        # 添加重叠
        if self.chunk_overlap > 0 and len(chunks) > 1:
            overlapped = [chunks[0]]
            for i in range(1, len(chunks)):
                tail = chunks[i - 1][-self.chunk_overlap :]
                if not chunks[i].startswith(tail):
                    overlap_text = tail + "\n\n" + chunks[i]
                else:
                    overlap_text = chunks[i]
                overlapped.append(overlap_text)
            chunks = overlapped

        return chunks

    def _hard_split(self, text):
        """强制按固定大小切分超长文本。"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            if end < len(text):
                # 尝试在句子边界断开
                for sep in ["。", "！", "？", "\n", "，", " "]:
                    pos = text.rfind(sep, start, end)
                    if pos > start + self.chunk_size // 2:
                        end = pos + 1
                        break
            chunks.append(text[start:end].strip())
            start = end - self.chunk_overlap if end < len(text) else end
        return [c for c in chunks if c]

    def _parse_pdf(self, file_path):
        """解析 PDF 文件。"""
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(file_path)
            text = "\n".join(page.get_text() for page in doc)
            doc.close()
            return text
        except ImportError:
            pass

        try:
            import pdfplumber

            text_parts = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            return "\n".join(text_parts)
        except ImportError:
            raise RuntimeError("PDF 解析需要安装 PyMuPDF 或 pdfplumber")

    def _parse_docx(self, file_path):
        """解析 DOCX 文件。"""
        try:
            from docx import Document

            doc = Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except ImportError:
            raise RuntimeError("DOCX 解析需要安装 python-docx")

    def process_file(self, file_path):
        """完整处理流程：解析 -> 分块。

        Args:
            file_path: 文件路径

        Returns:
            dict: {doc_id, filename, chunks, chunk_count}
        """
        filename = os.path.basename(file_path)
        text = self.parse_file(file_path)
        chunks = self.chunk_text(text)
        doc_id = uuid.uuid4().hex[:16]

        return {
            "doc_id": doc_id,
            "filename": filename,
            "chunks": chunks,
            "chunk_count": len(chunks),
        }
