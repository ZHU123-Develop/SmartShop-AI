"""向量存储封装 - 基于 ChromaDB 的持久化知识库。"""

import os
import uuid
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rag_data")
COLLECTION_NAME = "ecommerce_kb"


class VectorStore:
    """ChromaDB 向量存储封装类。"""

    def __init__(self, persist_directory=None):
        """初始化向量存储。

        Args:
            persist_directory: ChromaDB 持久化目录路径，默认使用 rag_data/
        """
        self.persist_dir = persist_directory or DATA_DIR
        os.makedirs(self.persist_dir, exist_ok=True)

        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.embedding_fn = DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(self, texts, metadatas=None, ids=None):
        """批量添加文档到知识库。

        Args:
            texts: 文本块列表
            metadatas: 元数据列表（包含 source、filename、chunk_index 等）
            ids: 文档 ID 列表，不传则自动生成 UUID

        Returns:
            list: 实际使用的 ID 列表
        """
        if ids is None:
            ids = [uuid.uuid4().hex[:16] for _ in texts]

        self.collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids,
        )
        return ids

    def query(self, text, top_k=3, similarity_threshold=0.0):
        """查询最相关的文档片段。

        Args:
            text: 查询文本
            top_k: 返回结果数量
            similarity_threshold: 最低相似度阈值（0-1），低于此值的结果会被过滤

        Returns:
            list[dict]: 包含 chunk、source、distance、score 的列表
        """
        if self.collection.count() == 0:
            return []

        results = self.collection.query(
            query_texts=[text],
            n_results=top_k,
        )

        chunks = results["documents"][0] if results["documents"] else []
        metadatas = results["metadatas"][0] if results["metadatas"] else []
        distances = results["distances"][0] if results["distances"] else []

        filtered = []
        for chunk, meta, dist in zip(chunks, metadatas, distances):
            score = 1 - dist  # 转为相似度分数
            if score >= similarity_threshold:
                filtered.append(
                    {
                        "chunk": chunk,
                        "source": meta.get("source", "未知"),
                        "filename": meta.get("filename", ""),
                        "score": round(score, 4),
                    }
                )
        return filtered

    def delete_by_source(self, source):
        """删除指定来源的所有文档。

        Args:
            source: 来源标识（通常是文件名或 document_id）
        """
        results = self.collection.get(where={"source": source}, include=[])
        ids_to_delete = results["ids"]
        if ids_to_delete:
            self.collection.delete(ids=ids_to_delete)

    def delete_by_id(self, doc_id):
        """删除单个文档（按 doc_id 元数据）。"""
        results = self.collection.get(where={"doc_id": doc_id}, include=[])
        ids_to_delete = results["ids"]
        if ids_to_delete:
            self.collection.delete(ids=ids_to_delete)

    def get_all_documents(self):
        """获取知识库中所有文档的元数据概览。

        Returns:
            list[dict]: 包含 id、source、filename 等信息
        """
        results = self.collection.get(include=["metadatas"])
        seen = set()
        unique_docs = []
        for meta in results["metadatas"] or []:
            doc_id = meta.get("doc_id")
            if doc_id and doc_id not in seen:
                seen.add(doc_id)
                unique_docs.append(
                    {
                        "doc_id": doc_id,
                        "source": meta.get("source", "未知"),
                        "filename": meta.get("filename", ""),
                    }
                )
        return unique_docs

    def count(self):
        """获取知识库中文档块数量。"""
        return self.collection.count()
