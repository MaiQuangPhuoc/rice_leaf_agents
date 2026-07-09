# BƯỚC 6: SINH CÂU HỎI VÀ ĐÁP ÁN

## Mục tiêu

Chuyển đổi từ:

```text
Question Specification (Bước 5)
```

thành:

```text
Câu hỏi hoàn chỉnh
+
Đáp án đúng
+
Đáp án nhiễu
```

đồng thời kiểm tra chất lượng từng câu trước khi đưa vào đề thi.

---

# Vị trí trong Pipeline

```text
Bước 1
Thu thập thông tin học sinh

↓

Bước 2
Truy xuất tài liệu học tập

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
Đánh giá chất lượng toàn bộ đề
```

---

# Mục tiêu chính của Bước 6

Bước này có nhiệm vụ:

```text
Sinh câu hỏi

↓

Sinh đáp án đúng

↓

Sinh đáp án nhiễu

↓

Kiểm tra từng câu

↓

Lưu vào đề thi
```

Lưu ý:

```text
Bước 6 KHÔNG đánh giá toàn bộ đề.
```

Đó là nhiệm vụ của Bước 7.

---

# Input

## 1. Đặc tả câu hỏi (Question Specification)

Đầu ra từ Bước 5.

Ví dụ:

```yaml
question_id: 7

chương:
  Đạo hàm

bài:
  Đạo hàm đa thức

dạng_bài:
  Tính đạo hàm đa thức

độ_khó:
  Trung bình

yêu_cầu:
  Áp dụng công thức đạo hàm đa thức

mục_đích:
  Đánh giá khả năng vận dụng
```

---

## 2. Hồ sơ tri thức (Bước 3)

Ví dụ:

```yaml
bài:
  Đạo hàm đa thức

cần_nắm:
  - Công thức đạo hàm lũy thừa

cần_hiểu:
  - Cách áp dụng công thức

dạng_bài:
  - Tính đạo hàm đa thức

mức_độ:
  Dễ
  Trung bình
  Khó
```

---

## 3. Tài liệu học tập (Bước 2)

Lưu trong VectorDB.

Ví dụ:

```yaml
lý_thuyết:
  ...

công_thức:
  ...

ví_dụ:
  ...

sai_lầm_thường_gặp:
  ...
```

---

## 4. Exam Memory

Lưu lịch sử các câu đã sinh.

Ví dụ:

```yaml
đã_sinh:

  - ý_tưởng:
      Tính đạo hàm đa thức bậc 2

  - ý_tưởng:
      Tính đạo hàm đa thức bậc 3

  - ý_tưởng:
      Đạo hàm hàm hợp cơ bản
```

Mục đích:

```text
Tránh lặp ý tưởng.
```

---

# Chiến lược sinh đề

## Sinh theo Batch

Không sinh toàn bộ đề cùng lúc.

Ví dụ:

```text
20 câu

↓

4 Batch

↓

5 câu / Batch
```

---

Hoặc:

```text
50 câu

↓

10 Batch

↓

5 câu / Batch
```

---

Mục tiêu:

```text
Giảm token

Giảm chi phí

Giảm rủi ro vượt context window
```

---

# Quy trình xử lý

## Bước 6.1

### Chọn nhóm câu cần sinh

Ví dụ:

```yaml
Batch_1:

  câu_1

  câu_2

  câu_3

  câu_4

  câu_5
```

---

## Bước 6.2

### Truy xuất ngữ cảnh liên quan

Từ Question Specification:

```yaml
bài:
  Đạo hàm đa thức

dạng_bài:
  Tính đạo hàm đa thức
```

Retriever truy vấn VectorDB.

---

Lấy:

```yaml
lý_thuyết:
  ...

công_thức:
  ...

ví_dụ:
  ...

sai_lầm_thường_gặp:
  ...
```

---

Không lấy:

```text
Toàn bộ chương

Toàn bộ môn học
```

---

Chỉ lấy:

```text
Những phần liên quan đến câu đang sinh
```

---

## Bước 6.3

### Sinh câu hỏi

LLM nhận:

```text
Question Specification

+

Retrieved Context

+

Exam Memory
```

---

Sinh:

```yaml
question:
  Cho hàm số:

  y = x³ + 2x² − 5x

  Tính y'
```

---

## Bước 6.4

### Sinh đáp án đúng

Ví dụ:

```yaml
correct_answer:
  3x² + 4x − 5
```

---

## Bước 6.5

### Sinh đáp án nhiễu

Nguồn sinh nhiễu:

```text
Sai lầm thường gặp

Lỗi phổ biến của học sinh
```

---

Ví dụ:

```yaml
options:

  A:
    3x² + 4x − 5

  B:
    x² + 4x − 5

  C:
    3x³ + 4x² − 5

  D:
    3x² + 4x + 5
```

---

Các phương án nhiễu phải:

```text
Hợp lý

Có khả năng gây nhầm lẫn

Xuất phát từ lỗi thực tế
```

---

Không được:

```text
Vô nghĩa

Dễ loại bỏ ngay
```

---

# Kiểm tra từng câu

Sau khi sinh xong.

---

## Bước 6.6

### Hard Validation

Kiểm tra bằng code.

---

Kiểm tra:

```text
Đủ trường dữ liệu

Đủ số đáp án

Định dạng hợp lệ

Không có đáp án trùng

Đáp án thuộc A/B/C/D
```

---

Ví dụ:

```yaml
Fail:

A: 5

B: 5

C: 7

D: 8
```

---

## Bước 6.7

### Tool Validation

Kiểm tra bằng công cụ chuyên biệt.

Ví dụ:

```text
Toán học:
SymPy

Lập trình:
Code Runner

Vật lý:
Calculator
```

---

Mục tiêu:

```text
Xác minh đáp án đúng.
```

---

Ví dụ:

```python
diff(x**3 + 2*x**2 - 5*x)
```

---

Kết quả:

```text
3*x**2 + 4*x - 5
```

---

So sánh với đáp án đã sinh.

---

## Bước 6.8

### LLM Validation

Kiểm tra các yếu tố sư phạm.

---

Ví dụ:

```text
Độ khó

Đúng dạng bài

Đúng mục tiêu đánh giá

Chất lượng đáp án nhiễu
```

---

Ví dụ:

```text
Blueprint yêu cầu:

Khó
```

---

Nếu câu sinh ra:

```text
Tính đạo hàm x²
```

---

Kết luận:

```text
Sai độ khó
```

---

# Bước 6.9

### Cập nhật Exam Memory

Sau khi câu đạt yêu cầu.

Lưu:

```yaml
question_id: 7

chương:
  Đạo hàm

bài:
  Đạo hàm đa thức

dạng_bài:
  Tính đạo hàm đa thức

ý_tưởng:
  Tính đạo hàm đa thức bậc 3
```

---

Mục đích:

```text
Tránh sinh trùng trong các batch tiếp theo.
```

---

# Bước 6.10

### Lặp lại

```text
Question tiếp theo

↓

Retrieve

↓

Generate

↓

Validate

↓

Memory

↓

Save
```

---

Cho đến khi hoàn thành toàn bộ Question Specification.

---

# Output

Mỗi câu:

```yaml
question_id: 7

question:
  Cho hàm số:

  y = x³ + 2x² − 5x

  Tính y'

options:

  A:
    3x² + 4x − 5

  B:
    x² + 4x − 5

  C:
    3x³ + 4x² − 5

  D:
    3x² + 4x + 5

correct_answer:
  A

validation:

  schema: pass

  answer_check: pass

  difficulty_check: pass

  duplicate_check: pass
```

---

# Output cuối cùng của Bước 6

```yaml
generated_exam:

  question_1

  question_2

  question_3

  ...

  question_n
```

---

# Kết quả đạt được

Sau khi hoàn thành Bước 6:

```text
Đề thi đã được sinh xong

Đáp án đã được sinh xong

Mỗi câu đã được kiểm tra riêng lẻ

Đã hạn chế trùng lặp

Đã kiểm tra tính hợp lệ của đáp án
```

Tuy nhiên:

```text
Chưa biết toàn bộ đề có tốt hay không.
```

Việc đánh giá:

* Độ phủ kiến thức.
* Đúng ma trận đề.
* Phân bố độ khó.
* Trùng lặp giữa các câu.
* Chất lượng đề tổng thể.

sẽ được thực hiện ở **Bước 7: Đánh giá và hoàn thiện đề thi**.
