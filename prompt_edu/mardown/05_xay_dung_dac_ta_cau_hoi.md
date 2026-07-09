# 05. Xây dựng đặc tả câu hỏi (Question Specification)

## Mục tiêu

Chuyển đổi ma trận đề kiểm tra thành danh sách các câu hỏi cần được sinh ra.

Mỗi câu hỏi được xác định rõ:

- Chương học
- Bài học
- Dạng bài
- Độ khó
- Yêu cầu đánh giá
- Mục đích đánh giá
- Ngữ cảnh tham chiếu

> Bước này không sinh câu hỏi và không sinh đáp án.

---

## Vai trò trong Pipeline

```text
Bước 1: Thu thập thông tin học sinh
↓
Bước 2: Truy xuất tài liệu
↓
Bước 3: Xây dựng hồ sơ tri thức
↓
Bước 4: Xây dựng ma trận đề
↓
Bước 5: Xây dựng đặc tả câu hỏi
↓
Bước 6: Sinh câu hỏi và đáp án
↓
Bước 7: Đánh giá chất lượng đề
```

---

## Đầu vào

### 1. Ma trận đề (Bước 4)

Ví dụ:

```yaml
chương: Đạo hàm

tổng_số_câu: 20

bài:
  - Đạo hàm đa thức

    dạng_A1:
      dễ: 2

    dạng_A2:
      dễ: 1
      trung_bình: 2

    dạng_A3:
      khó: 2
```

### 2. Hồ sơ tri thức (Bước 3)

```yaml
Đạo hàm đa thức

cần_nắm:
  - Công thức đạo hàm lũy thừa

cần_hiểu:
  - Cách áp dụng công thức

dạng_bài:
  - Tính đạo hàm đa thức
  - Tính đạo hàm nhiều hạng tử
```

---

## Quy trình xử lý

### Bước 5.1 - Mở rộng ma trận đề

Từ:

```yaml
Dạng A1
Dễ: 2 câu
```

Sinh thành:

```yaml
Câu 1
Câu 2
```

### Bước 5.2 - Gắn thông tin bài học

```yaml
câu_1:
  chương: Đạo hàm
  bài: Đạo hàm đa thức
```

### Bước 5.3 - Gắn dạng bài

```yaml
câu_1:
  dạng_bài: Tính đạo hàm đa thức
```

### Bước 5.4 - Gắn độ khó

```yaml
câu_1:
  độ_khó: Dễ
```

### Bước 5.5 - Sinh yêu cầu đánh giá

```yaml
câu_1:
  yêu_cầu:
    Học sinh nhận biết được công thức đạo hàm lũy thừa.
```

### Bước 5.6 - Sinh mục đích đánh giá

```yaml
câu_1:
  mục_đích:
    Kiểm tra khả năng ghi nhớ công thức cơ bản.
```

### Bước 5.7 - Gắn ngữ cảnh tham chiếu

```yaml
câu_1:

  ngữ_cảnh:

    - Công thức đạo hàm lũy thừa
    - Ví dụ tính đạo hàm cơ bản
```

Mục tiêu:

- Giảm suy luận không cần thiết ở Bước 6.
- Giúp quá trình sinh câu hỏi ổn định hơn.
- Kiểm soát chất lượng đề dễ hơn.

---

## Đầu ra

Ví dụ:

```yaml
id: 1

chương:
  Đạo hàm

bài:
  Đạo hàm đa thức

dạng_bài:
  Tính đạo hàm đa thức

độ_khó:
  Dễ

yêu_cầu:
  Học sinh nhận biết được công thức đạo hàm lũy thừa.

mục_đích:
  Kiểm tra khả năng ghi nhớ công thức.

ngữ_cảnh:

  - Công thức đạo hàm lũy thừa

  - Ví dụ cơ bản
```

---

## Kết quả cuối cùng

Đầu ra của Bước 5 là:

```text
Danh sách đặc tả của từng câu hỏi
``

Ví dụ:

```text
Câu 1 → kiểm tra gì
Câu 2 → kiểm tra gì
Câu 3 → kiểm tra gì
...
Câu N → kiểm tra gì
```

Sau bước này hệ thống đã có Question Plan hoàn chỉnh để Bước 6 sinh câu hỏi và đáp án.
