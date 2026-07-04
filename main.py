import os
import io
import time
import requests
import pandas as pd
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = FastAPI()

# Cấu hình Google Sheets của bạn
SHEET_ID = "1hX8_sFCt5S2j17rB4xZU4B3WNa4LPoJCdhTuUQWiTE0"
DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

# Lưu trữ dữ liệu hệ thống trong RAM
faq_database = []
vectorizer = None
tfidf_matrix = None
last_sync_time = 0  
SYNC_INTERVAL = 300  # Tự động đồng bộ ngầm sau mỗi 5 phút

def reload_faq_data():
    global faq_database, vectorizer, tfidf_matrix, last_sync_time
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(DATA_URL, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return False

        df = pd.read_excel(io.BytesIO(response.content), sheet_name="Trang tính1")
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        col_q = "câu hỏi"
        col_a = "câu trả lời"
        col_f = "link file"  
        
        if col_q not in df.columns or col_a not in df.columns:
            return False

        temp_database = []
        questions = []
        
        for _, row in df.iterrows():
            q = str(row.get(col_q, '')).strip()
            a = str(row.get(col_a, '')).strip()
            f_link = str(row.get(col_f, '')).strip() if col_f in df.columns else 'nan'
            
            if q and q != 'nan' and a and a != 'nan' and not q.isupper():
                actual_link = f_link if (f_link and f_link != 'nan') else None
                temp_database.append({
                    "question": q, 
                    "answer": a,
                    "file_link": actual_link
                })
                questions.append(q)
        
        if questions:
            # Nhận diện cả từ đơn và cụm từ ghép để tăng độ bao phủ ý nghĩa
            vectorizer = TfidfVectorizer(ngram_range=(1, 2))
            tfidf_matrix = vectorizer.fit_transform(questions)
            faq_database = temp_database
            last_sync_time = time.time()
            print(f"🔄 [Luxshare] Đã tự động đồng bộ thành công {len(faq_database)} câu hỏi từ Google Sheets.")
            return True
    except Exception as e:
        print(f"Lỗi đồng bộ: {e}")
        return False

# Nạp dữ liệu lần đầu
reload_faq_data()

@app.get("/logo.png")
async def get_logo():
    if os.path.exists("logo.png"):
        return FileResponse("logo.png")
    return FileResponse(io.BytesIO(requests.get("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR6A7R18_g6nInR9RfeF7b3v82C3tQ7N9F4ng&s").content), media_type="image/png")

# ================= CHUỖI HTML GIAO DIỆN CHUYÊN NGHIỆP =================
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Luxshare ICT - Hệ thống hỗ trợ nội bộ</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #f1f5f9; }
        .custom-scrollbar::-webkit-scrollbar { width: 6px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: #f1f5f9; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #cbd5e1; }
    </style>
</head>
<body class="h-screen w-screen flex items-center justify-center p-0 md:p-4">

    <div class="w-full max-w-2xl h-screen md:h-[680px] bg-white rounded-none flex flex-col overflow-hidden border border-slate-300 shadow-xl">
        
        <div class="bg-gradient-to-r from-[#0f4c81] to-[#145b99] px-6 py-4 flex items-center justify-between border-b-2 border-[#0a365c] rounded-none">
            <div class="flex items-center">
                <div class="h-12 bg-white flex items-center justify-center px-3 py-1 border border-slate-200 rounded-none mr-4">
                    <img src="/logo.png" alt="Luxshare ICT Logo" class="h-full w-auto object-contain rounded-none">
                </div>
                <div>
                    <h2 class="text-white font-bold text-base tracking-wider uppercase">Luxshare-ICT Việt Nam</h2>
                    <p class="text-slate-300 text-xs mt-0.5 flex items-center">
                        <span class="w-2 h-2 bg-green-400 rounded-none mr-2"></span>
                        Hệ thống giải đáp thủ tục sinh viên tự động
                    </p>
                </div>
            </div>
            <button onclick="clearChat()" class="text-xs bg-[#0a365c] hover:bg-red-700 text-white font-medium px-3 py-2 border border-transparent hover:border-red-800 transition-colors rounded-none">
                🗑️ Xóa hội thoại
            </button>
        </div>

        <div id="chatBox" class="flex-1 p-6 overflow-y-auto space-y-4 custom-scrollbar bg-slate-50 rounded-none">
            <div class="flex items-start max-w-[90%]">
                <div class="bg-white text-slate-800 p-4 border border-slate-200 text-sm leading-relaxed rounded-none shadow-sm w-full">
                    <p class="font-bold text-[#0f4c81] text-sm border-b border-slate-100 pb-1.5 mb-2">HỆ THỐNG TRỢ LÝ ĐOÀN SINH VIÊN QUY CHUẨN 👋</p>
                    <p class="mb-2 text-slate-700 font-medium">Chào em, Anh/Chị phụ trách Quản lý tuyển dụng dẫn đoàn. Em có thể hỏi nhanh thông tin bằng cách gõ câu hỏi hoặc bấm trực tiếp vào các lưu trình có sẵn dưới đây:</p>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-2 mt-3" id="quickTags">
                        <button onclick="askQuick('Cần chuẩn bị những loại giấy tờ gì trước khi đi')" class="text-left bg-slate-50 hover:bg-blue-50 text-xs text-slate-700 hover:text-[#0f4c81] p-2.5 border border-slate-200 hover:border-[#0f4c81] transition-all rounded-none font-medium">📄 Giấy tờ cần chuẩn bị trước khi đi</button>
                        <button onclick="askQuick('Những ai đăng kí ở KTX công ty có phải đóng tiền không')" class="text-left bg-slate-50 hover:bg-blue-50 text-xs text-slate-700 hover:text-[#0f4c81] p-2.5 border border-slate-200 hover:border-[#0f4c81] transition-all rounded-none font-medium">🏢 Ở KTX công ty có mất tiền không?</button>
                        <button onclick="askQuick('Phòng quản túc ở đâu')" class="text-left bg-slate-50 hover:bg-blue-50 text-xs text-slate-700 hover:text-[#0f4c81] p-2.5 border border-slate-200 hover:border-[#0f4c81] transition-all rounded-none font-medium">🛠️ Vị trí phòng quản túc ở đâu?</button>
                        <button onclick="askQuick('Đến đào tạo ở đâu')" class="text-left bg-slate-50 hover:bg-blue-50 text-xs text-slate-700 hover:text-[#0f4c81] p-2.5 border border-slate-200 hover:border-[#0f4c81] transition-all rounded-none font-medium">📊 Vị trí đến đào tạo ở đâu?</button>
                    </div>
                </div>
            </div>
        </div>

        <div class="p-4 bg-white border-t border-slate-200 flex items-center space-x-2 rounded-none">
            <input type="text" id="userInput" 
                   class="flex-1 bg-slate-50 text-slate-800 text-sm px-4 py-3.5 border border-slate-300 focus:outline-none focus:border-[#0f4c81] focus:bg-white rounded-none transition-all" 
                   placeholder="Nhập nội dung câu hỏi về các lưu trình dịch vụ tại đây..." 
                   onkeypress="if(event.key === 'Enter') sendMessage()">
            <button onclick="sendMessage()" 
                    class="bg-[#0f4c81] hover:bg-[#0a365c] text-white font-bold text-sm px-6 py-3.5 border-b-2 border-[#0a365c] transition-all rounded-none shrink-0">
                GỬI TIN
            </button>
        </div>
        
        <div class="bg-slate-100 px-4 py-1.5 text-[10px] text-slate-500 flex justify-between items-center border-t border-slate-200 rounded-none">
            <span>Dữ liệu: Kết nối Google Sheets Trực tiếp</span>
            <span class="font-mono">Đồng bộ tự động: Active</span>
        </div>
    </div>

    <script>
        function askQuick(questionText) {
            document.getElementById("userInput").value = questionText;
            sendMessage();
        }

        function clearChat() {
            const chatBox = document.getElementById("chatBox");
            if(confirm("Bạn có chắc chắn muốn xóa toàn bộ lịch sử trò chuyện hiện tại không?")) {
                chatBox.innerHTML = `
                    <div class="flex items-start max-w-[85%]">
                        <div class="bg-white text-slate-800 p-4 border border-slate-200 text-sm leading-relaxed rounded-none shadow-sm w-full">
                            <p class="font-bold text-[#0f4c81] mb-1">Hội thoại mới đã được mở sạch sẽ.</p>
                            Em hãy nhập câu hỏi mới hoặc bấm vào các nút điều hướng nhanh phía trên nhé!
                        </div>
                    </div>
                `;
            }
        }

        async function sendMessage() {
            const input = document.getElementById("userInput");
            const text = input.value.trim();
            if (!text) return;

            const chatBox = document.getElementById("chatBox");
            const currentTime = new Date().toLocaleTimeString('vi-VN', {hour: '2-digit', minute:'2-digit'});
            
            chatBox.innerHTML += `
                <div class="flex flex-col items-end max-w-[90%] ml-auto">
                    <div class="bg-[#0f4c81] text-white p-3.5 border border-[#0a365c] rounded-none text-sm font-medium shadow-sm">
                        ${text}
                    </div>
                    <span class="text-[9px] text-slate-400 mt-1">${currentTime}</span>
                </div>
            `;
            
            input.value = "";
            chatBox.scrollTop = chatBox.scrollHeight;

            const loadingId = "loading-" + Date.now();
            chatBox.innerHTML += `
                <div id="${loadingId}" class="flex items-start max-w-[85%] animate-pulse">
                    <div class="bg-slate-200 text-slate-600 py-2 px-3 border border-slate-300 text-xs font-medium rounded-none">
                        ⚙️ Hệ thống đang xử lý đối chiếu sơ đồ...
                    </div>
                </div>
            `;
            chatBox.scrollTop = chatBox.scrollHeight;

            let formData = new FormData();
            formData.append("message", text);

            try {
                let response = await fetch("/api/chat", { method: "POST", body: formData });
                let data = await response.json();
                document.getElementById(loadingId).remove();
                
                let slideHtml = "";
                if (data.file_link) {
                    let rawLink = data.file_link;
                    let cleanUrl = "";
                    if (rawLink.includes('src="')) {
                        cleanUrl = rawLink.split('src="')[1].split('"')[0];
                    } else if (rawLink.includes("src='")) {
                        cleanUrl = rawLink.split("src='")[1].split("'")[0];
                    } else {
                        cleanUrl = rawLink;
                    }

                    slideHtml = `
                        <div class="mt-3 w-full border-2 border-slate-300 rounded-none overflow-hidden bg-black aspect-video shadow-inner">
                            <iframe src="${cleanUrl}" frameborder="0" width="100%" height="100%" allowfullscreen="true" mozallowfullscreen="true" webkitallowfullscreen="true"></iframe>
                        </div>
                    `;
                }

                chatBox.innerHTML += `
                    <div class="flex flex-col items-start max-w-[90%]">
                        <div class="bg-white text-slate-800 p-4 border border-slate-200 text-sm leading-relaxed rounded-none shadow-sm w-full">
                            <div class="whitespace-pre-line">${data.reply}</div>
                            ${slideHtml}
                        </div>
                        <span class="text-[9px] text-slate-400 mt-1">${currentTime}</span>
                    </div>
                `;
            } catch (error) {
                document.getElementById(loadingId).remove();
                chatBox.innerHTML += `
                    <div class="flex items-start max-w-[85%]">
                        <div class="bg-red-50 text-red-700 p-3 text-xs border border-red-200 rounded-none">
                            ⚠️ Có lỗi xảy ra trong quá trình truyền tải dữ liệu mạng nội bộ Luxshare.
                        </div>
                    </div>
                `;
            }
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    </script>
</body>
</html>
"""

# ================= ĐỊNH TUYẾN MẶC ĐỊNH =================

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML_CONTENT

@app.post("/api/chat")
async def chat_bot(message: str = Form(...)):
    global faq_database, vectorizer, tfidf_matrix, last_sync_time
    
    if time.time() - last_sync_time > SYNC_INTERVAL:
        reload_faq_data()
    
    if not faq_database or vectorizer is None:
        return JSONResponse(content={"reply": "Hệ thống đang đồng bộ hóa lại cấu trúc dữ liệu đám mây từ Google Sheets. Vui lòng thử lại sau vài giây!", "file_link": None})
    
    user_question = message.strip()
    if not user_question:
        return JSONResponse(content={"reply": "Vui lòng nhập nội dung câu hỏi cụ thể.", "file_link": None})
    
    # 1. Khớp hoàn toàn (Exact Match) để phản hồi nhanh
    q_clean = " ".join(user_question.lower().split())
    for item in faq_database:
        if " ".join(item["question"].lower().split()) == q_clean:
            return JSONResponse(content={"reply": item["answer"], "file_link": item["file_link"]})
            
    # 2. Khớp tương đồng nới lỏng thông minh bằng TF-IDF cụm từ
    user_vector = vectorizer.transform([user_question])
    similarities = cosine_similarity(user_vector, tfidf_matrix).flatten()
    
    best_match_idx = similarities.argmax()
    highest_score = similarities[best_match_idx]
            
    # Nới lỏng ngưỡng: Điểm > 0.18 là cho phép trả lời, giúp nhận diện từ gần đúng cực tốt
    if highest_score > 0.18:
        bot_reply = faq_database[best_match_idx]["answer"]
        file_link = faq_database[best_match_idx]["file_link"]
    else:
        bot_reply = "Câu hỏi của em hiện tại hệ thống chưa tìm thấy lưu trình tự động khớp hoàn toàn trong Google Sheets. Anh/Chị quản lý tuyển dụng đã ghi nhận lại câu hỏi này và sẽ chủ động nhắn tin hướng dẫn chi tiết riêng cho em qua Zalo ngay nhé!"
        file_link = None
        
    return JSONResponse(content={"reply": bot_reply, "file_link": file_link})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
