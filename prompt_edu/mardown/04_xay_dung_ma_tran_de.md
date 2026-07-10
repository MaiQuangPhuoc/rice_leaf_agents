# 04. Xây dựng ma trận đề

## Mục tiêu
Chuyển hồ sơ tri thức thành blueprint đề kiểm tra.

## Đầu vào
- Hồ sơ học sinh
- Hồ sơ tri thức chương học

## Công việc thực hiện

### 1. Phân bổ số câu theo bài học
```yaml
Bài A: 7 câu
Bài B: 6 câu
Bài C: 7 câu
```

### 2. Phân bổ độ khó
```yaml
dễ: 3
trung_bình: 2
khó: 2
```

### 3. Phân bổ theo dạng bài
```yaml
Dạng 1:
  dễ: 2
  trung_bình: 1
  khó: 0
```

### 4. Kiểm tra tính hợp lệ
- Tổng số câu khớp
- Đủ độ khó
- Đủ dạng bài

## Đầu ra
```yaml
chương:
tổng_số_câu:
bài_học:
  - tên:
    số_câu:
    độ_khó:
    dạng_bài:
```

## Vai trò
Đầu vào trực tiếp cho bước sinh sườn đề và sinh câu hỏi.
