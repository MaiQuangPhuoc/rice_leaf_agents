# Bước 5: Xây dựng đặc tả câu hỏi (Question Specification)

## Mục tiêu

Chuyển đổi **ma trận đề kiểm tra** thành một **danh sách các câu hỏi cần được sinh ra**, trong đó mỗi câu đã được xác định rõ:

* Thuộc chương nào.
* Thuộc bài nào.
* Thuộc dạng bài nào.
* Độ khó nào.
* Kiểm tra điều gì.
* Đánh giá năng lực nào.
* Sử dụng ngữ cảnh nào để sinh câu hỏi.

⚠️ Lưu ý:

Bước này **không sinh câu hỏi**.

Bước này **không sinh đáp án**.

Bước này chỉ tạo ra một **bản đặc tả chi tiết cho từng câu hỏi**.

---

# Vai trò trong pipeline

```text id="t7i3k5"
Bước 1
Thu thập thông tin học sinh

↓

Bước 2
Truy xuất tài liệu

↓

Bước 3
Xây dựng hồ sơ tri thức

↓

Bước 4
Xây dựng ma trận đề

↓

Bước 5
Xây dựng đặc tả câu hỏi

↓

Bước 6
Sinh câu hỏi và đáp án

↓

Bước 7
Kiểm tra chất lượng đề
```

---

# Đầu vào (Input)

## 1. Kết quả từ Bước 4 (Ma trận đề)

Ví dụ:

```yaml id="o6dwmf"
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

Bước 4 chỉ cho biết:

```text id="9u7xut"
Cần sinh bao nhiêu câu
```

---

## 2. Kết quả từ Bước 3 (Hồ sơ tri thức)

Ví dụ:

```yaml id="0jxv8n"
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

# Quy trình xử lý

## Bước 5.1: Mở rộng ma trận đề thành danh sách câu hỏi

Ví dụ:

Từ:

```yaml id="8v8f52"
Dạng A1

Dễ: 2 câu
```

Sinh thành:

```yaml id="jkshzh"
Câu 1

Câu 2
```

---

Từ:

```yaml id="9zjclt"
Dạng A2

Trung bình: 2 câu
```

Sinh thành:

```yaml id="i4lw8l"
Câu 3

Câu 4
```

---

Kết quả:

```text id="gtgg2v"
20 dòng đặc tả

=
20 câu cần sinh
```

---

## Bước 5.2: Gắn thông tin bài học

Ví dụ:

```yaml id="9g7hgf"
câu_1:

  chương:
    Đạo hàm

  bài:
    Đạo hàm đa thức
```

---

## Bước 5.3: Gắn dạng bài

Ví dụ:

```yaml id="v61nn7"
câu_1:

  dạng_bài:
    Tính đạo hàm đa thức
```

---

## Bước 5.4: Gắn độ khó

Ví dụ:

```yaml id="xcktz4"
câu_1:

  độ_khó:
    Dễ
```

---

## Bước 5.5: Sinh yêu cầu đánh giá

Dựa trên:

```text id="v8e1u7"
Hồ sơ tri thức
```

Ví dụ:

```yaml id="xqj4az"
câu_1:

  yêu_cầu:
    Học sinh nhận biết được công thức đạo hàm lũy thừa.
```

---

## Bước 5.6: Sinh mục đích đánh giá

Ví dụ:

```yaml id="3hr8zl"
câu_1:

  mục_đích:
    Kiểm tra khả năng ghi nhớ công thức cơ bản.
```

---

## Bước 5.7: Gắn ngữ cảnh tham chiếu

Đây là phần rất quan trọng.

Từ Bước 2 lấy ra các chunk liên quan.

Ví dụ:

```yaml id="tt7wrj"
câu_1:

  ngữ_cảnh:

    - Công thức đạo hàm lũy thừa

    - Ví dụ tính đạo hàm cơ bản
```

---

Mục đích:

Khi sang Bước 6:

```text id="s7z4nr"
LLM không phải tìm lại tài liệu
```

mà đã có sẵn.

---

# Đầu ra (Output)

Ví dụ:

```yaml id="o8xv27"
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

Ví dụ câu khác:

```yaml id="t1ngrp"
id: 7

chương:
  Đạo hàm

bài:
  Đạo hàm đa thức

dạng_bài:
  Bài toán biến đổi

độ_khó:
  Khó

yêu_cầu:
  Học sinh kết hợp nhiều quy tắc đạo hàm.

mục_đích:
  Đánh giá khả năng vận dụng tổng hợp.

ngữ_cảnh:

  - Quy tắc đạo hàm tổng

  - Quy tắc đạo hàm tích

  - Ví dụ nâng cao
```

---

# Đầu ra cuối cùng của Bước 5

```text id="v79xvn"
Danh sách đặc tả của từng câu hỏi
```

Ví dụ:

```text id="eb5eg4"
Câu 1 → kiểm tra gì

Câu 2 → kiểm tra gì

Câu 3 → kiểm tra gì

...

Câu 20 → kiểm tra gì
```

Nhưng:

```text id="v10d7k"
Chưa có câu hỏi

Chưa có đáp án

Chưa có lựa chọn A/B/C/D
```

---

# Kết quả đạt được

Sau Bước 5, hệ thống đã có một **Question Plan hoàn chỉnh**, trong đó mỗi câu hỏi đã được mô tả đầy đủ về mục tiêu đánh giá và nguồn tri thức sử dụng.

Bước 6 chỉ còn nhiệm vụ:

```text id="1kkwkl"
Đọc đặc tả câu hỏi
↓
Đọc ngữ cảnh tham chiếu
↓
Sinh câu hỏi
↓
Sinh đáp án
```

thay vì phải tự suy luận toàn bộ từ đầu. Điều này giúp đề thi ổn định hơn, dễ kiểm soát chất lượng hơn và giảm đáng kể sai lệch của LLM.
