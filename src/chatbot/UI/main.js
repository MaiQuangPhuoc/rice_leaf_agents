/**
 * LúaXanh AI - Script xử lý chính
 * Kết nối với Python Backend (Flask) tại http://127.0.0.1:5000/chat
 */

// Khởi tạo các biểu tượng Lucide
lucide.createIcons();

// --- KHAI BÁO CÁC PHẦN TỬ GIAO DIỆN ---
const fileInput = document.getElementById('fileInput');
const dropZone = document.getElementById('dropZone');
const uploadUI = document.getElementById('uploadUI');
const previewImg = document.getElementById('previewImg');
const actionArea = document.getElementById('actionArea');
const loadingUI = document.getElementById('loadingUI');
const resultArea = document.getElementById('resultArea');
const diagnosisContent = document.getElementById('diagnosisContent');
const btnAnalyze = document.getElementById('btnAnalyze');
const btnReset = document.getElementById('btnReset');

const chatInput = document.getElementById('chatInput');
const chatMessages = document.getElementById('chatMessages');
const btnSend = document.getElementById('btnSend');
const chatFileInput = document.getElementById('chatFileInput');
const btnChatFile = document.getElementById('btnChatFile');
const chatImagePreviewArea = document.getElementById('chatImagePreviewArea');
const chatImgPreview = document.getElementById('chatImgPreview');
const btnRemoveChatImg = document.getElementById('btnRemoveChatImg');

// --- CẤU HÌNH KẾT NỐI PYTHON ---
const PYTHON_API_URL = "http://127.0.0.1:5000/chat";

// --- XỬ LÝ LỖI CLICK VÙNG CHỌN ẢNH ---
dropZone.addEventListener('click', () => {
    fileInput.click();
});

// --- HÀM HIỂN THỊ TIN NHẮN VÀO KHUNG CHAT ---
function appendMessage(role, content, isImage = false) {
    const div = document.createElement("div");
    div.className = `flex ${role === "user" ? "justify-end" : "justify-start"}`;

    let messageHtml = `<div class="max-w-[90%] rounded-2xl px-4 py-3 shadow-sm text-sm ${
        role === "user" 
        ? "bg-[#4a7c2c] text-white rounded-tr-none" 
        : "bg-white border border-[#e2e8d0] text-[#2d3a1a] rounded-tl-none"
    }">`;

    if (isImage) {
        messageHtml += `<img src="${content}" class="w-full rounded-lg mb-2 max-h-40 object-cover shadow-sm" />`;
    } else {
        messageHtml += `<p class="whitespace-pre-wrap">${content}</p>`;
    }
    
    messageHtml += `</div>`;
    div.innerHTML = messageHtml;

    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// --- HÀM GỬI DỮ LIỆU VỀ PYTHON ---
async function sendToPython(text) {
    try {
        const response = await fetch(PYTHON_API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text })
        });
        
        if (!response.ok) throw new Error('Kết nối thất bại');
        
        const data = await response.json();
        // Nếu Python trả về kết quả dự đoán (prediction), gọi hàm render riêng
        if (data.prediction) {
            renderDiagnosisResults(data.prediction);
        } else {
            appendMessage("assistant", data.reply);
        }
    } catch (err) {
        console.error(err);
        appendMessage("assistant", "Lỗi: Không kết nối được với máy chủ Python. Bà con kiểm tra lại Flask nhé!");
    }
}

// --- HÀM HIỂN THỊ KẾT QUẢ DỰ ĐOÁN (SIÊU ĐƠN GIẢN) ---
function renderDiagnosisResults(predictionData) {
    const { label, confidence, others } = predictionData;

    let html = `
        <div class="space-y-2 p-1">
            <!-- Kết quả chính: Gọn, nhẹ -->
            <div class="flex items-center justify-between bg-emerald-50 px-3 py-2 rounded-md border border-emerald-100">
                <span class="font-bold text-emerald-800 text-sm">${label}</span>
                <span class="font-black text-emerald-600 text-sm">${confidence}%</span>
            </div>

            <!-- Các khả năng khác: Chữ nhỏ, tối giản -->
            ${others && others.length > 0 ? `
                <div class="space-y-1 px-1">
                    ${others.map(item => `
                        <div class="flex justify-between text-[11px] text-gray-400">
                            <span>${item.label}</span>
                            <span>${item.confidence}%</span>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
        </div>
    `;

    diagnosisContent.innerHTML = html;
    resultArea.classList.remove('hidden');
}

// --- XỬ LÝ PHẦN CHẨN ĐOÁN BỆNH (BÊN TRÁI) ---

fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(event) {
            uploadUI.classList.add('hidden');
            previewImg.src = event.target.result;
            previewImg.classList.remove('hidden');
            actionArea.classList.remove('hidden');
            
            appendMessage("user", event.target.result, true);
            sendToPython(`image:${file.name}`);
        };
        reader.readAsDataURL(file);
    }
});

btnAnalyze.addEventListener('click', () => {
    loadingUI.classList.remove('hidden');
    actionArea.classList.add('hidden');
    resultArea.classList.add('hidden');
    
    // Giả lập dữ liệu từ Flask
    setTimeout(() => {
        const mockResult = {
            label: "Bệnh Đạo Ôn",
            confidence: 94,
            others: [
                { label: "Bệnh Bạc Lá", confidence: 4 },
                { label: "Bệnh Đốm Nâu", confidence: 2 }
            ]
        };
        
        loadingUI.classList.add('hidden');
        actionArea.classList.remove('hidden');
        renderDiagnosisResults(mockResult);
    }, 1000);
});

btnReset.addEventListener('click', () => {
    previewImg.classList.add('hidden');
    uploadUI.classList.remove('hidden');
    actionArea.classList.add('hidden');
    resultArea.classList.add('hidden');
    fileInput.value = '';
    diagnosisContent.innerHTML = '';
});

// --- XỬ LÝ PHẦN CHATBOT (BÊN PHẢI) ---

async function handleSendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    if (!text.toLowerCase().endsWith('.jpg') && !text.toLowerCase().endsWith('.png')) {
        appendMessage("user", text);
    }

    chatInput.value = "";
    chatInput.style.height = "auto";
    
    await sendToPython(text);
}

btnSend.addEventListener('click', handleSendMessage);

chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
    }
});

chatFileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(event) {
            appendMessage("user", event.target.result, true);
            sendToPython(`image:${file.name}`);
        };
        reader.readAsDataURL(file);
    }
});

btnChatFile.addEventListener('click', () => chatFileInput.click());

chatInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});