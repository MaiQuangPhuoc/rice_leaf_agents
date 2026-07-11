const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const imageInput = document.getElementById("image-input");
// const imageInput = document.getElementById("imageInput");

function addMessage(content, sender = "user", isImage = false) {
    const msg = document.createElement("div");
    msg.classList.add("message");
    msg.classList.add(sender === "user" ? "user-msg" : "bot-msg");

    if (isImage) {
        const img = document.createElement("img");
        img.src = content;
        img.style.maxWidth = "180px";
        img.style.borderRadius = "10px";
        msg.appendChild(img);
    } else {
        msg.textContent = content;
    }

    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// ------------------ GỬI TEXT ------------------

// function sendText() {
//     const text = userInput.value.trim();
//     if (!text) return;

//     addMessage(text, "user");
//     userInput.value = "";

//     fetch("http://127.0.0.1:5000/chat", {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({ text })
//     })
//         .then(res => res.json())
//         .then(data => {
//             addMessage(data.reply, "bot");
//         });
// }


function sendText() {
    const text = userInput.value.trim();
    if (!text) return;

    // Nếu text không kết thúc bằng .jpg hoặc .png mới hiển thị lên màn hình
    if (!text.toLowerCase().endsWith('.jpg') && !text.toLowerCase().endsWith('.png')) {
        addMessage(text, "user");
    }

    userInput.value = "";

    fetch("http://127.0.0.1:5000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
    })
    .then(res => res.json())
    .then(data => {
        addMessage(data.reply, "bot");
    });
}

sendBtn.onclick = sendText;



// ------------------ GỬI ẢNH ------------------

// imageInput.onchange = () => {
//     const file = imageInput.files[0];
//     if (!file) return;

//     const reader = new FileReader();
//     reader.onload = () => {
//         addMessage(reader.result, "user", true);
//     };
//     reader.readAsDataURL(file);
// };

// ------------------ GỬI ẢNH ------------------
imageInput.onchange = () => {
    const file = imageInput.files[0];
    if (!file) return;

    // Lấy tên file gốc (ví dụ: "ảnh đẹp.jpg")
    const fileName = file.name;

    // Tạo tin nhắn dạng "image:tên_ảnh" (có thể giữ cả đuôi hoặc bỏ đuôi tùy bạn)
    // Cách 1: Giữ nguyên tên file + đuôi (khuyến nghị)
    const messageText = `image:${fileName}`;

    // Cách 2: Chỉ lấy tên không đuôi
    // const nameWithoutExt = fileName.replace(/\.[^/.]+$/, "");
    // const messageText = `image:${nameWithoutExt}`;

    // Hiển thị preview ảnh
    const reader = new FileReader();
    reader.onload = () => {
        addMessage(reader.result, "user", true); // hiển thị ảnh
    };
    reader.readAsDataURL(file);

    // Tự động gửi tin nhắn text "image:tên_ảnh" lên server
    // (giống như người dùng gõ tay và nhấn Enter)
    userInput.value = messageText;   // điền vào ô input (tùy chọn)
    sendText();                      // gọi hàm gửi ngay lập tức
    userInput.value = "";            // xóa ô input sau khi gửi
};


// ------------------ NHẤN ENTER ĐỂ GỬI ------------------

userInput.addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
        e.preventDefault();  // tránh xuống dòng
        sendText();
    }
});