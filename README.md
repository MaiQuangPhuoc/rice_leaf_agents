Nghiên cứu ảnh hưởng của pipeline xử lý dataset đến hiệu quả phân loại bệnh lá lúa sử dụng mô hình Deep Learning
Phần 1: Tổng quan dự án
Dự án nghiên cứu ảnh hưởng của pipeline xử lý dataset đến hiệu quả phân loại bệnh lá lúa, sử dụng 8 lớp bệnh với 3 mô hình deep learning là MobileNetV3-Large, ResNet50 và ViT-Base. Thay vì tập trung vào thay đổi mô hình, nghiên cứu chú trọng vào cách chuẩn bị và xử lý dữ liệu đầu vào qua 3 phiên bản pipeline khác nhau, từ đó đánh giá sự cải thiện qua từng bước cải tiến.
Mô tả 3 version
Version 1 — Origin: Ảnh gốc nhiều nguồn, nền nhiễu, kích thước đa dạng, đưa trực tiếp vào model. MobileNetV3 0.91 / ResNet50 0.96 / ViT 0.97.
Version 2 — SAM2: Đánh bbox bằng MakeSense.AI, tách nền hoàn toàn bằng SAM2, resize letterbox 384x384 kèm tiền xử lý. Không cải thiện do nền giả out-of-distribution. MobileNetV3 0.90 / ResNet50 0.95 / ViT 0.97.
Version 3 — Crops: Crop ảnh gốc theo bbox, giữ ngữ cảnh thực xung quanh lá, resize letterbox 384x384 kèm tiền xử lý. Tốt nhất cả 3 model. MobileNetV3 0.93 / ResNet50 0.97 / ViT 0.975.

 
Hình 1 : 3 phiên bản sẽ dùng
________________________________________
 
Phần 2: Dataset gốc
Dataset được tổng hợp từ nhiều nguồn đa dạng bao gồm Google Drive, Kaggle, Google Images và các nghiên cứu trước đó chưa được chuẩn hóa. Do xuất phát từ nhiều nguồn khác nhau nên dataset gốc có chất lượng không đồng đều, ảnh chụp ngoài thực địa nên nền ảnh rất phức tạp chứa đất, cỏ, ngón tay, nhiều lá chồng chéo và các yếu tố nhiễu khác. Kích thước ảnh đa dạng, không thống nhất giữa các nguồn.
Dataset gồm 8 lớp bệnh lá lúa, được chia theo tỉ lệ trung bình 650 : 100 : 150 cho train, val và test, tổng cộng khoảng 7.400 mẫu ảnh
 
Hình 2 : trực quan ảnh gốc trong dataset
 
Hình 3 : phân bố dữ liệu
________________________________________
Phần 3: Version 1 — Pipeline gốc
Dataset gốc được đưa trực tiếp vào 3 mô hình MobileNetV3-Large, ResNet50 và ViT-Base mà không qua bất kỳ bước xử lý nào ngoài resize cơ bản về kích thước đầu vào của model. Đây là version baseline để làm cơ sở so sánh với các version cải tiến sau.
Vấn đề nhận thấy:
Nền nhiễu — ảnh chụp ngoài thực địa chứa đất, cỏ, ngón tay, nhiều lá chồng chéo khiến model phải tốn capacity để học cách ignore nền thay vì tập trung vào đặc trưng bệnh.
Kích thước không đồng đều — ảnh từ nhiều nguồn có size khác nhau, resize thẳng về kích thước cố định làm ảnh bị stretch méo, tỉ lệ lá bị biến dạng, đốm bệnh tròn có thể thành bầu dục, gân lá bị kéo lệch khiến model học trên hình dạng không trung thực.
 
Hình 4 : kết quả pipline1

Phần 4: Version 2 — SAM2 tách nền + Letterbox
Nhận thấy nền nhiễu là vấn đề lớn nhất của Version 1, tiến hành cải tiến dataset bằng cách loại bỏ hoàn toàn nền, chỉ giữ lại vùng lá lúa.
Quy trình thực hiện:
Bước 1 — Đánh bbox thủ công — sử dụng công cụ MakeSense.AI để đánh bounding box thủ công cho toàn bộ dataset, xác định chính xác vùng chứa lá lúa trong từng ảnh. Kết quả xuất ra file label định dạng YOLO.
Bước 2 — Tách nền bằng SAM2 — sử dụng bbox từ bước 1 làm prompt đầu vào cho SAM2 để tạo mask chính xác theo hình dạng thật của lá. Toàn bộ nền bên ngoài mask bị thay thế hoàn toàn bằng nền ( trắng | đen ), chỉ còn lại vùng nền chứa lá lúa.
Bước 3 — Resize + Letterbox + tiền xử lý — ảnh sau tách nền được resize về 384x384 (hợp với size cả 3 mdoel ) theo phương pháp letterbox để tránh méo tỉ lệ, kết hợp các kỹ thuật làm mịn, tăng độ sắc nét và tăng sáng để cải thiện chất lượng ảnh đầu vào.
 
Hình 5 : kết quả pipeline2
Vấn đề nhận thấy:
Nền giả out-of-distribution — nền đen hoặc trắng tuyệt đối không tồn tại trong ImageNet, sau normalize ImageNet các pixel nền trở thành giá trị cực âm hoặc cực dương bất thường, làm lệch feature map của các model pretrained ngay từ những layer đầu tiên.
Lá nhỏ nền nhiều sau letterbox — nhiều ảnh lá lúa có tỉ lệ nhỏ so với toàn bộ ảnh gốc, sau tách nền vùng lá càng nhỏ, letterbox càng thêm nhiều padding nền giả, khiến model nhìn thấy phần lớn là nền trống thay vì đặc trưng bệnh.
Artifact viền — SAM2 dù chính xác cao vẫn tạo ra jagged edge tại viền lá, đặc biệt tại vùng đốm bệnh lan ra viền, khiến model có thể học nhầm artifact viền thay vì texture bệnh thật.

________________________________________
Phần 5: Version 3 — YOLO crop + Letterbox
Nhận thấy các hạn chế của Version 2, tôi tiến hành thiết kế lại pipeline theo hướng không loại bỏ hoàn toàn nền mà chỉ cắt bớt phần nền thừa bên ngoài bbox, giữ lại ngữ cảnh thực xung quanh lá lúa.
Quy trình thực hiện:
Bước 1 — Crop theo bbox YOLO — sử dụng lại file label bbox từ MakeSense.AI đã đánh ở Version 2, tiến hành crop ảnh gốc theo tọa độ bbox, loại bỏ phần lớn nền nhiễu bên ngoài nhưng vẫn giữ nguyên nền thật bên trong vùng bbox bao gồm đất, ánh sáng và ngữ cảnh thực tế xung quanh lá.
Bước 2 — Mở rộng bbox 10% — bbox được mở rộng thêm 10% mỗi chiều trước khi crop để tránh cắt sát mép lá, đảm bảo giữ đủ context xung quanh vùng bệnh.
Bước 3 — Resize + Letterbox + tiền xử lý — tương tự Version 2, ảnh crop được resize về 384x384 theo phương pháp letterbox kết hợp làm mịn, tăng độ sắc nét và tăng sáng.
Ưu điểm so với Version 2:
Giữ nền thật — nền trong bbox là nền thực tế, không phải nền giả out-of-distribution, các model pretrained xử lý tốt hơn vì phân phối pixel gần với ImageNet hơn.
Lá chiếm diện tích lớn hơn — sau crop bbox lá lúa chiếm 80-90% diện tích ảnh, letterbox padding rất ít, gần như toàn bộ pixel đều mang thông tin có ích cho model.
Không có artifact viền — không qua bước tách nền nên không có jagged edge, model học trên texture và hình dạng thật của lá và vùng bệnh.
Giữ context sinh học — màu đất, độ ẩm, ánh sáng xung quanh lá là signal gián tiếp giúp model phân biệt môi trường xuất hiện từng loại bệnh, Version 3 giữ lại được thông tin này trong khi Version 2 loại bỏ hoàn toàn.
Version 3 được kỳ vọng cho kết quả cao nhất trong 3 version nhờ kết hợp được việc giảm nhiễu nền với việc bảo toàn thông tin thực tế của ảnh.


 
Hình 6 : kết quả pipeline3
________________________________________
Phần 6: Kết quả và so sánh
Bảng kết quả
Model	Version	Accuracy	Val Loss
MobileNetV3-Large	Origin	0.91	0.2
MobileNetV3-Large	SAM2	0.9	0.26
MobileNetV3-Large	Crops	0.93	0.18
ResNet50	Origin	0.96	0.07
ResNet50	SAM2	0.95	0.07
ResNet50	Crops	0.97	0.04
ViT-Base	Origin	0.97	0.03
ViT-Base	SAM2	0.97	0.12
ViT-Base	Crops	0.975	0.06

Nhận xét chung:
Version Crops cho kết quả tốt nhất trên cả 3 model về cả accuracy lẫn val loss, xác nhận rằng việc crop bbox kết hợp letterbox là hướng cải tiến đúng đắn.
Version SAM2 không cải thiện so với Origin trên tất cả 3 model, thậm chí tệ hơn ở MobileNetV3-Large và ViT-Base. Điều này phù hợp với phân tích lý thuyết — nền đen/trắng out-of-distribution, artifact viền SAM2 và lá nhỏ sau letterbox là những yếu tố cộng lại làm giảm hiệu quả học của model dù đã loại bỏ nhiễu nền.
ViT-Base nhạy cảm nhất với pipeline — val loss tăng mạnh từ 0.03 lên 0.12 khi dùng SAM2, cho thấy attention mechanism của ViT bị ảnh hưởng nặng bởi các patch nền đen giả. Version Crops đưa val loss về 0.06, thấp hơn Origin nhưng vẫn chưa đạt mức 0.03, cho thấy ViT hưởng lợi từ nền thật nhiều hơn 2 model còn lại.
ResNet50 ổn định nhất — val loss giữ nguyên 0.07 giữa Origin và SAM2, chứng tỏ kiến trúc convolution ít bị ảnh hưởng bởi nền giả hơn ViT. Version Crops giảm val loss xuống 0.04, cải thiện rõ rệt nhất trong 3 model.
MobileNetV3-Large nhạy cảm nhất về accuracy — là model duy nhất có accuracy giảm từ Origin xuống SAM2, từ 0.91 xuống 0.90, cho thấy model nhỏ capacity thấp dễ bị ảnh hưởng tiêu cực bởi nền giả hơn các model lớn hơn.
 
________________________________________
Phần 7: Kết luận
Nghiên cứu đã xây dựng và so sánh 3 phiên bản pipeline xử lý dataset cho bài toán phân loại bệnh lá lúa trên 3 mô hình deep learning. Kết quả cho thấy cải tiến pipeline xử lý dữ liệu có tác động rõ ràng đến hiệu quả phân loại dù dataset còn nhỏ với 600 ảnh mỗi lớp.
Version Crops luôn cho kết quả tốt nhất trên cả 3 model, xác nhận rằng crop bbox kết hợp letterbox là hướng tiếp cận đúng — vừa loại bỏ phần lớn nền nhiễu, vừa giữ lại ngữ cảnh thực tế xung quanh lá, vừa đảm bảo ảnh không bị méo khi resize.
Version SAM2 không mang lại cải thiện so với ảnh gốc dù về mặt trực quan nền đã được loại bỏ hoàn toàn. Điều này cho thấy việc loại bỏ nền triệt để không đồng nghĩa với cải thiện hiệu quả — nền giả out-of-distribution, artifact viền và lá nhỏ sau letterbox là những yếu tố làm giảm chất lượng học của model pretrained trên ImageNet.
Mức cải thiện 1-2% accuracy giữa các version phản ánh đúng giới hạn của dataset nhỏ — xu hướng tăng dần đã được xác nhận nhưng chênh lệch chưa thực sự lớn. Khi dataset được mở rộng hơn, gap giữa các version được kỳ vọng sẽ rõ ràng hơn và củng cố thêm kết luận về hướng cải tiến pipeline.
Hướng phát triển tiếp theo có thể tập trung vào mở rộng dataset, áp dụng augmentation nâng cao như MixUp hay CutMix, hoặc kết hợp ensemble các model để tận dụng thế mạnh của từng kiến trúc.

