from sentence_transformers import CrossEncoder

# BAAI/bge-reranker-v2-m3
# BAAI/bge-reranker-v2-minicpm-layerwise
# BAAI/bge-reranker-base
class VietnameseReranker:
    def __init__(self, model_name="BAAI/bge-reranker-base"):
        self.model = CrossEncoder(model_name,max_length=512)

    def rerank(self, query, docs, top_k=5):
        # docs: danh sách string
        pairs = [[query, doc] for doc in docs]   # tạo cặp query–document
        scores = self.model.predict(pairs)

        ranked = sorted(
            zip(docs, scores),
            key=lambda x: x[1],
            reverse=True
        )

        return ranked[:top_k]
# from sentence_transformers import CrossEncoder
# reranker = CrossEncoder("keepitreal/vietnamese-reranker")