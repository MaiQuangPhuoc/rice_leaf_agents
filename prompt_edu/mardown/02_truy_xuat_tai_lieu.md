# 02. Truy xuất tài liệu

## Mục tiêu
Truy xuất các phần kiến thức liên quan đến phạm vi kiểm tra.

## Đầu vào
- Hồ sơ học sinh từ Bước 1
- Kho tri thức (Vector Store)

## Cấu trúc dữ liệu
```text
Môn học
 └── Chương
      └── Bài học
           └── Phần kiến thức
                └── Chunk
```

## Metadata chuẩn
```json
{
  "subject": "...",
  "grade": 11,
  "chapter": "...",
  "lesson": "...",
  "section": "...",
  "content_type": "...",
  "content": "..."
}
```

## Công việc thực hiện
1. Phân tích yêu cầu đề.
2. Retriever tìm kiếm tài liệu liên quan.
3. Trả về tập chunk phù hợp.

## Đầu ra
```text
Chunk 1: Lý thuyết
Chunk 2: Công thức
Chunk 3: Dạng bài
Chunk 4: Ví dụ
```
