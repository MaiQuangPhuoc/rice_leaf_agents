# import torch

# from PIL import Image

# from torchvision import transforms
# import timm   
# # print("ok")
# # 1. Load model ViT
# model_path = r"D:\VKU\Nam_4\ky_I\computer_vision\model\best_vit_rice_leaf.pth"
# num_classes = 8  

# # Tạo model ViT tương ứng, ví dụ vit_base_patch16_224
# model = timm.create_model('vit_base_patch16_224', pretrained=False, num_classes=num_classes)

# # Load weights
# model.load_state_dict(torch.load(model_path, map_location='cpu'))
# model.eval()


 
# # 2. Chuẩn bị transform cho ảnh input (đảm bảo trùng với training)
# transform = transforms.Compose([
#     transforms.Resize((224, 224)),
#     transforms.ToTensor(),
#     transforms.Normalize(
#         mean=[0.485, 0.456, 0.406],  # chuẩn ImageNet
#         std=[0.229, 0.224, 0.225]
#     )
# ])

# # 3. Load ảnh, transform và thêm batch dim
# def predict_image(image_path):
#     image = Image.open(image_path).convert('RGB')
#     input_tensor = transform(image).unsqueeze(0)  # shape: (1, 3, 224, 224)

#     with torch.no_grad():
#         outputs = model(input_tensor)  # raw logits
#         scores = torch.softmax(outputs, dim=1).cpu().numpy()[0]  # xác suất từng lớp
    
#     return scores

# # # D:\VKU\Nam_4\ky_I\computer_vision\dataset\test
# image_path = r"D:\VKU\Nam_4\ky_I\computer_vision\dataset\test\scald_2.jpg"   


# class_names = [
#     'Bacterial Leaf Blight',
#     'Brown Spot',
#     'Healthy Rice Leaf',
#     'Leaf Blast',
#     'Leaf scald',
#     'Narrow Brown Leaf Spot',
#     'Rice Hispa',
#     'Sheath Blight'
# ]

# scores = predict_image(image_path)

# print("Scores cho từng lớp:")
# for name, score in zip(class_names, scores):
#     print(f"{name}: {score:.4f}")

# predicted_idx = scores.argmax()
# print(f"\n\nLớp dự đoán: {class_names[predicted_idx]} ")


# print("ok")



import torch
from PIL import Image
from torchvision import transforms
import timm
import numpy as np




# Load model 1 lần duy nhất (không load lại mỗi lần gọi hàm)
model_path = r"D:\VKU\Nam_4\ky_I\computer_vision\model\best_vit_rice_leaf.pth"
num_classes = 8

model = timm.create_model('vit_base_patch16_224', pretrained=False, num_classes=num_classes)
model.load_state_dict(torch.load(model_path, map_location='cpu'))
model.eval()

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

class_names = [
    'Bacterial Leaf Blight',
    'Brown Spot',
    'Healthy Rice Leaf',
    'Leaf Blast',
    'Leaf scald',
    'Narrow Brown Leaf Spot',
    'Rice Hispa',
    'Sheath Blight'
]

def predict_image(image_path):
    image = Image.open(image_path).convert('RGB')
    input_tensor = transform(image).unsqueeze(0)
    with torch.no_grad():
        outputs = model(input_tensor)
        scores = torch.softmax(outputs, dim=1).cpu().numpy()[0]
    return scores

# def CV(full_path):
#     scores = predict_image(full_path)
#     predicted_idx = np.argmax(scores)
#     predicted_class = class_names[predicted_idx]
#     # Trả về tên lớp dự đoán, hoặc có thể thêm cả xác suất
#     return predicted_class
def CV(full_path):
    scores = predict_image(full_path)          # shape: (num_classes,)
    
    predicted_idx = int(np.argmax(scores))
    predicted_class = class_names[predicted_idx]
    predicted_score = float(scores[predicted_idx])

    # Tạo dict {class_name: score}
    all_scores = {
        class_names[i]: float(scores[i])
        for i in range(len(class_names))
    }

    return {
        "predicted_class": predicted_class,
        "predicted_score": predicted_score,
        "all_scores": all_scores
    }
