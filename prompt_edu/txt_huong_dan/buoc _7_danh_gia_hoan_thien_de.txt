# BƯỚC 7: ĐÁNH GIÁ VÀ HOÀN THIỆN ĐỀ THI

## Mục tiêu

Sau khi Bước 6 hoàn thành, hệ thống đã có:

```text
- Câu hỏi
- Đáp án đúng
- Đáp án nhiễu
- Kết quả kiểm tra từng câu
```

Tuy nhiên:

```text
Câu hỏi tốt ≠ Đề thi tốt
```

Bước 7 có nhiệm vụ đánh giá đề thi ở cấp độ toàn cục nhằm đảm bảo:

* Đúng ma trận đề.
* Đủ độ phủ kiến thức.
* Không trùng lặp nội dung.
* Đúng phân bố độ khó.
* Đúng mục tiêu đánh giá.
* Chất lượng đáp án và bẫy đạt yêu cầu.
* Phù hợp với hồ sơ học sinh.

---

# Vị trí trong Pipeline

```text
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
Đánh giá và hoàn thiện đề thi

↓

Đề thi cuối cùng
```

---

# Input

## 1. Đề thi từ Bước 6

Ví dụ:

```yaml
exam:

  - question_1
  - question_2
  - question_3
  ...
  - question_n
```

---

## 2. Ma trận đề từ Bước 4

Ví dụ:

```yaml
ma_tran_de:

  chương_1:

    tổng_câu: 20

    bài_A: 7

    bài_B: 7

    bài_C: 6

  độ_khó:

    dễ: 8

    trung_bình: 8

    khó: 4
```

---

## 3. Hồ sơ tri thức từ Bước 3

Ví dụ:

```yaml
chương:

  đạo_hàm:

    bài:

      đạo_hàm_đa_thức:

        dạng_bài:
          ...

        mục_tiêu:
          ...

      đạo_hàm_hàm_hợp:

        dạng_bài:
          ...

        mục_tiêu:
          ...
```

---

## 4. Thông tin học sinh từ Bước 1

Ví dụ:

```yaml
target_score: 8

chủ_đề:

  đạo_hàm: 8 điểm

ghi_chú:

  tập trung luyện vận dụng
```

---

# Quy trình xử lý

---

# 7.1 Kiểm tra Blueprint

## Mục tiêu

Kiểm tra đề thi có đúng ma trận đề hay không.

---

Ví dụ

Blueprint:

```yaml
Đạo hàm đa thức:
  7 câu

Đạo hàm hàm hợp:
  7 câu

Cực trị:
  6 câu
```

---

Đề thực tế:

```yaml
Đạo hàm đa thức:
  12 câu

Đạo hàm hàm hợp:
  5 câu

Cực trị:
  3 câu
```

---

Kết quả:

```yaml
blueprint_check:

  status: fail

  reason:

    lệch phân bố chương học
```

---

# 7.2 Kiểm tra phân bố độ khó

## Mục tiêu

Đảm bảo đề đúng mức độ yêu cầu.

---

Ví dụ

Blueprint:

```yaml
dễ: 8

trung_bình: 8

khó: 4
```

---

Đề thực tế:

```yaml
dễ: 15

trung_bình: 3

khó: 2
```

---

Kết quả:

```yaml
difficulty_check:

  status: fail
```

---

# 7.3 Kiểm tra độ phủ kiến thức

## Mục tiêu

Đảm bảo các nội dung quan trọng đều được đánh giá.

---

Ví dụ

Hồ sơ tri thức:

```yaml
bài:

  đạo_hàm_đa_thức:

    dạng_bài:

      - dạng_A

      - dạng_B

      - dạng_C
```

---

Đề thi:

```yaml
đã_xuất_hiện:

  dạng_A

  dạng_A

  dạng_A

  dạng_A
```

---

Kết quả:

```yaml
coverage_check:

  status: fail

  thiếu:

    - dạng_B

    - dạng_C
```

---

# 7.4 Kiểm tra trùng lặp nội dung

## Mục tiêu

Phát hiện các câu hỏi khác nhau về câu chữ nhưng cùng một ý tưởng.

---

Ví dụ

```text
Câu 1:
Tính đạo hàm x²

Câu 7:
Tính đạo hàm x³

Câu 12:
Tính đạo hàm x⁴
```

---

Thực chất:

```text
Cùng một dạng
Cùng một tư duy
Cùng một mức đánh giá
```

---

Phương pháp

### Hard Check

So sánh metadata.

```yaml
dạng_bài

độ_khó

mục_tiêu
```

---

### Embedding Check

Tính:

```text
Cosine Similarity
```

giữa các câu hỏi.

---

Ví dụ

```text
similarity > 0.9
```

---

Kết quả:

```yaml
duplicate_check:

  status: warning

  duplicate_pairs:

    - câu_1
      câu_12
```

---

# 7.5 Kiểm tra chất lượng đáp án

## Mục tiêu

Đảm bảo đáp án hợp lý trên toàn đề.

---

Ví dụ

Đáp án:

```text
A A A A A A A A A
```

---

Kết quả:

```yaml
answer_distribution:

  status: warning
```

---

Hoặc:

```text
2 đáp án cùng đúng
```

---

Kết quả:

```yaml
answer_quality:

  status: fail
```

---

# 7.6 Kiểm tra chất lượng bẫy

## Mục tiêu

Đảm bảo đáp án nhiễu có giá trị đánh giá.

---

Ví dụ

```text
A. 3x²

B. Con mèo

C. Việt Nam

D. 1000
```

---

Mặc dù:

```text
1 đáp án đúng
3 đáp án sai
```

---

Nhưng:

```text
Bẫy vô nghĩa
```

---

LLM Reviewer đánh giá:

```text
Độ hợp lý

Khả năng gây nhầm lẫn

Tính sư phạm
```

---

# 7.7 Kiểm tra tính phù hợp với học sinh

## Mục tiêu

Đề phải phù hợp với hồ sơ người học.

---

Ví dụ

Thông tin học sinh:

```yaml
target_score: 8
```

---

Đề thực tế:

```text
80% câu khó
```

---

Kết quả:

```yaml
student_fit_check:

  status: fail
```

---

# 7.8 Tổng hợp lỗi

Ví dụ:

```yaml
issues:

  - thiếu dạng bài B

  - câu 7 và câu 15 trùng ý tưởng

  - độ khó vượt mục tiêu học sinh

  - đáp án phân bố không đều
```

---

# 7.9 Sửa lỗi tự động (Repair)

## Mục tiêu

Không chỉ phát hiện lỗi mà còn sửa lỗi.

---

Ví dụ

```text
Câu 7 trùng câu 15
```

---

Hệ thống:

```text
Xóa câu 15

↓

Sinh lại câu 15

↓

Kiểm tra lại
```

---

Ví dụ

```text
Thiếu dạng bài B
```

---

Hệ thống:

```text
Sinh bổ sung câu hỏi dạng B

↓

Đánh giá lại đề
```

---

# 7.10 Đánh giá lại

Sau khi sửa:

```text
Review

↓

Repair

↓

Review lại

↓

Repair lại

↓

...
```

---

Cho đến khi:

```yaml
exam_status:

  approved: true
```

---

# Output

## 1. Báo cáo đánh giá

```yaml
exam_review:

  blueprint_check:
    pass

  difficulty_check:
    pass

  coverage_check:
    pass

  duplicate_check:
    pass

  answer_quality_check:
    pass

  distractor_quality_check:
    pass

  student_fit_check:
    pass
```

---

## 2. Đề thi hoàn chỉnh

```yaml
final_exam:

  question_1

  question_2

  question_3

  ...

  question_n
```

---

# Công nghệ đề xuất

## Hard Validation

Dùng code:

```text
- Blueprint
- Số lượng câu
- Phân bố độ khó
- Phân bố đáp án
- Metadata
```

---

## Embedding Validation

Dùng vector similarity:

```text
- Trùng lặp ý tưởng
- Trùng lặp nội dung
```

---

## LLM Validation

Đánh giá:

```text
- Chất lượng bẫy
- Tính sư phạm
- Độ hợp lý
- Độ phù hợp với học sinh
```

---

# Kết quả cuối cùng

Sau khi hoàn thành Bước 7:

```text
Đề thi đã được kiểm tra ở cấp độ toàn cục.

Đề đúng ma trận.

Đề đúng mục tiêu học tập.

Đề phù hợp với học sinh.

Đề không trùng lặp.

Đề có chất lượng đánh giá tốt.

Đề sẵn sàng để sử dụng.
```

Đây là bước đóng vai trò **Exam Reviewer + Exam Repair Agent**, là lớp kiểm soát chất lượng cuối cùng trước khi trả đề thi cho học sinh. 🚀
