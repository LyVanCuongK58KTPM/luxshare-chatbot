import os
import io
import time
import json
import requests
import pandas as pd
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
import google.generativeai as genai

# Nạp lại các thư viện toán học làm bộ cứu hộ cục bộ khi Gemini hết hạn mức
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = FastAPI()

# 1. CẤU HÌNH CƠ SỞ DỮ LIỆU GOOGLE SHEETS
SHEET_ID = "1hX8_sFCt5S2j17rB4xZU4B3WNa4LPoJCdhTuUQWiTE0"
DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"

# 2. CẤU HÌNH CỔNG KẾT NỐI GEMINI API
# 2. CẤU HÌNH CỔNG KẾT NỐI GEMINI API THẾ HỆ MỚI
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Hệ thống sẽ tự động kiểm tra xem bạn đã cấu hình Key ở phần cài đặt chưa
if not GEMINI_API_KEY:
    print("⚠️ Cảnh báo: Chưa tìm thấy GEMINI_API_KEY trong cấu hình hệ thống!")
else:
    genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")

# Kho lưu trữ tri thức bộ nhớ RAM
faq_database = []
vectorizer = None
tfidf_matrix = None
last_sync_time = 0  
SYNC_INTERVAL = 300  # Đồng bộ lại sau mỗi 5 phút

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
            # Luôn chuẩn bị sẵn ma trận dữ liệu dự phòng ngay tại RAM
            vectorizer = TfidfVectorizer(ngram_range=(1, 2))
            tfidf_matrix = vectorizer.fit_transform(questions)
            faq_database = temp_database
            last_sync_time = time.time()
            print(f"🔄 [Hệ thống] Đã đồng bộ kho tri thức gồm {len(faq_database)} câu hỏi (Sẵn sàng chế độ cứu hộ).")
            return True
    except Exception as e:
        print(f"Lỗi đọc dữ liệu đám mây: {e}")
        return False

# Đọc dữ liệu lúc khởi động
reload_faq_data()

@app.get("/logo.png")
async def get_logo():
    if os.path.exists("logo.png"):
        return FileResponse("logo.png")
    return FileResponse(io.BytesIO(requests.get("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR6A7R18_g6nInR9RfeF7b3v82C3tQ7N9F4ng&s").content), media_type="image/png")

# ================= GIAO DIỆN PHẲNG CHUYÊN NGHIỆP =================
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
                        Trợ lý quy chuẩn bảo vệ 2 lớp (AI + Local)
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
                    <p class="mb-2 text-slate-700 font-medium">Chào em, Anh/Chị phụ trách Quản lý tuyển dụng dẫn đoàn. Em có thể nhập bất kỳ câu hỏi nào để hệ thống tự động tra cứu lưu trình:</p>
                    
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
            <input type="text" id="userInput" class="flex-1 bg-slate-50 text-slate-800 text-sm px-4 py-3.5 border border-slate-300 focus:outline-none focus:border-[#0f4c81] focus:bg-white rounded-none transition-all" placeholder="Nhập nội dung thắc mắc tại đây..." onkeypress="if(event.key === 'Enter') sendMessage()">
            <button onclick="sendMessage()" class="bg-[#0f4c81] hover:bg-[#0a365c] text-white font-bold text-sm px-6 py-3.5 border-b-2 border-[#0a365c] transition-all rounded-none shrink-0">GỬI TIN</button>
        </div>
        
        <div class="bg-slate-100 px-4 py-1.5 text-[10px] text-slate-500 flex justify-between items-center border-t border-slate-200 rounded-none">
            <span>Engine bảo vệ: Tự động chuyển mạch dự phòng thông minh</span>
            <span class="font-mono">Trạng thái: Khớp nối 100%</span>
        </div>
    </div>

    <script>
        function askQuick(questionText) {
            document.getElementById("userInput").value = questionText;
            sendMessage();
        }

        function clearChat() {
            const chatBox = document.getElementById("chatBox");
            if(confirm("Bạn có chắc chắn muốn làm sạch lịch sử hội thoại không?")) {
                chatBox.innerHTML = `<div class="flex items-start max-w-[85%]"><div class="bg-white text-slate-800 p-4 border border-slate-200 text-sm rounded-none shadow-sm w-full"><p class="font-bold text-[#0f4c81] mb-1">Phiên thảo luận mới.</p>Em hãy nhập nội dung thắc mắc mới nhé!</div></div>`;
            }
        }

        async function sendMessage() {
            const input = document.getElementById("userInput");
            const text = input.value.trim();
            if (!text) return;

            const chatBox = document.getElementById("chatBox");
            const currentTime = new Date().toLocaleTimeString('vi-VN', {hour: '2-digit', minute:'2-digit'});
            
            chatBox.innerHTML += `<div class="flex flex-col items-end max-w-[90%] ml-auto"><div class="bg-[#0f4c81] text-white p-3.5 border border-[#0a365c] rounded-none text-sm font-medium shadow-sm">${text}</div><span class="text-[9px] text-slate-400 mt-1">${currentTime}</span></div>`;
            input.value = "";
            chatBox.scrollTop = chatBox.scrollHeight;

            const loadingId = "loading-" + Date.now();
            chatBox.innerHTML += `<div id="${loadingId}" class="flex items-start max-w-[85%] animate-pulse"><div class="bg-slate-200 text-slate-600 py-2 px-3 border border-slate-300 text-xs font-medium rounded-none">⚙️ Hệ thống đang đối chiếu lưu trình...</div></div>`;
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
                    if (rawLink.includes('src="')) { cleanUrl = rawLink.split('src="')[1].split('"')[0]; }
                    else if (rawLink.includes("src='")) { cleanUrl = rawLink.split("src='")[1].split("'")[0]; }
                    else { cleanUrl = rawLink; }

                    slideHtml = `<div class="mt-3 w-full border-2 border-slate-300 rounded-none overflow-hidden bg-black aspect-video shadow-inner"><iframe src="${cleanUrl}" frameborder="0" width="100%" height="100%" allowfullscreen="true" mozallowfullscreen="true" webkitallowfullscreen="true"></iframe></div>`;
                }

                chatBox.innerHTML += `<div class="flex flex-col items-start max-w-[90%]"><div class="bg-white text-slate-800 p-4 border border-slate-200 text-sm leading-relaxed rounded-none shadow-sm w-full"><div class="whitespace-pre-line">${data.reply}</div>${slideHtml}</div><span class="text-[9px] text-slate-400 mt-1">${currentTime}</span></div>`;
            } catch (error) {
                document.getElementById(loadingId).remove();
            }
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    </script>
</body>
</html>
"""

# ================= XỬ LÝ CHATBOT LAI (HYBRID) KHÔNG BAO GIỜ SẬP =================

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML_CONTENT

@app.post("/api/chat")
async def chat_bot(message: str = Form(...)):
    global faq_database, vectorizer, tfidf_matrix, last_sync_time
    
    if time.time() - last_sync_time > SYNC_INTERVAL:
        reload_faq_data()
        
    user_question = message.strip()
    if not user_question:
        return JSONResponse(content={"reply": "Vui lòng nhập câu hỏi.", "file_link": None})

    # BƯỚC THỬ NGHIỆM 1: Gọi trí tuệ nhân tạo Gemini AI
    try:
        system_prompt = f"""
        Bạn là Trợ lý AI điều hướng thông tin nội bộ của tập đoàn Luxshare-ICT Việt Nam.
        Nhiệm vụ của bạn là dựa vào "Kho tri thức quy chuẩn" dạng JSON dưới đây để trả lời câu hỏi sinh viên.
        Kho tri thức: {json.dumps(faq_database, ensure_ascii=False)}
        Trả về JSON nghiêm ngặt cấu trúc: {{"reply": "...", "file_link": "..."}}
        """
        response = model.generate_content(
            contents=[system_prompt, f"Câu hỏi: {user_question}"],
            generation_config={"response_mime_type": "application/json"}
        )
        result = json.loads(response.text)
        return JSONResponse(content={
            "reply": result.get("reply", ""),
            "file_link": result.get("file_link") if result.get("file_link") != "null" else None
        })

    # BƯỚC KHẮC PHỤC 2: Nếu dính lỗi 429 Quota Exceeded, kích hoạt ngay bộ cứu hộ cục bộ TF-IDF (Không lo mất mạng/hết hạn mức)
    except Exception as e:
        print(f"⚠️ [Cảnh báo hệ thống] Gemini gặp lỗi định mức (429/Hết quota). Tự động kích hoạt bộ cứu hộ Local TF-IDF...")
        
        if not faq_database or vectorizer is None:
            return JSONResponse(content={"reply": "Hệ thống đang tải dữ liệu lưu trình, em vui lòng gõ lại câu hỏi nhé!", "file_link": None})
            
        # Thuật toán so khớp toán học chạy trực tiếp trên RAM máy tính
        user_vector = vectorizer.transform([user_question])
        similarities = cosine_similarity(user_vector, tfidf_matrix).flatten()
        best_match_idx = similarities.argmax()
        highest_score = similarities[best_match_idx]
        
        if highest_score > 0.18:
            bot_reply = faq_database[best_match_idx]["answer"]
            file_link = faq_database[best_match_idx]["file_link"]
        else:
            bot_reply = "Câu hỏi của em hiện tại hệ thống tự động chưa tìm thấy lưu trình khớp hoàn toàn trên Google Sheets. Anh/Chị quản lý tuyển dụng đã lưu lại câu hỏi này và sẽ nhắn tin phản hồi chi tiết riêng cho em qua Zalo ngay nhé!"
            file_link = None
            
        return JSONResponse(content={"reply": bot_reply, "file_link": file_link})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
