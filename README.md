# GROWTHMETRIC — MARKETING CAMPAIGN ANALYTICS AGENT

Hệ thống Web SaaS Dashboard tự động hóa phân tích hiệu quả Marketing Campaign toàn diện, tích hợp Google Sheets, Multi-touch Attribution, Return Reconciliation, Activity Based Costing (ABC) và Human-in-the-Loop Approval.

---

## 🎯 Kiến Trúc Quy Trình Nghiệp Vụ (5 Giai Đoạn & 6 Bước Xử Lý)

Hệ thống hoạt động chuẩn xác theo sơ đồ kiến trúc quy trình:

```
[BẮT ĐẦU]
   │
   ▼
[1. Google Sheets Connection] ──── (Lỗi) ───► [Ghi log & Báo người dùng chỉnh sửa]
   │ (Hợp lệ)
   ▼
[2. Data Cleaning & Audit] ────── (Lỗi nặng) ──► [Dừng quy trình & Báo người dùng]
   │ (Hợp lệ)
   ▼
[3. PROCESS - 6 Bước Xử Lý]
   ├─ Bước 1: Data Centralization (Transactions - Returns - Campaign_Costs)
   ├─ Bước 2: Revenue Attribution (Multi-touch: Order_Value / Campaign_Count)
   ├─ Bước 3: Return Reconciliation (Return Window 15-30 ngày, Net Sales)
   ├─ Bước 4: Cost Allocation (Activity Based Costing - Direct & Overhead ABC)
   ├─ Bước 5: Process Automation (Report_Result, Exceptions_View, Processing_Log)
   └─ Bước 6: Human-in-the-Loop (Phát hiện ngoại lệ)
   │
   ▼
[Trưởng phòng phê duyệt?] ─── (Từ chối) ───► [Ghi nhận lý do & Yêu cầu điều chỉnh]
   │ (Đã duyệt)
   ▼
[4. VERIFICATION] ─────────── (Chưa đạt) ──► [Feedback về Process & Xử lý lại]
   │ (Đạt 7/7 Tests)
   ▼
[5. HTML REPORT EXPORT]
   │
   ▼
[HOÀN THÀNH - Standalone Dashboard HTML]
```

---

## 🚀 Các Tính Năng Nổi Bật

1. **Giao diện SaaS Dashboard hiện đại (Linear / Stripe / Notion style)**:
   - Sidebar 8 mục điều hướng trực quan:
     - 📊 **Tổng quan**: KPI tổng hợp, biểu đồ doanh thu và lợi nhuận từng chiến dịch.
     - 🔗 **Kết nối Google Sheets**: Nhập URL Google Sheets 3 tabs, kiểm tra quyền và schema, tải template Excel.
     - 🧹 **Data Cleaning**: Tự động rà soát Missing, Duplicates, Mismatches, tính Quality Score.
     - ⚙️ **Process Workflow**: Stepper trực quan 6 bước, theo dõi chi tiết từng công thức tính toán.
     - ⚠️ **Exceptions**: Khu vực Human-in-the-Loop dành cho Trưởng phòng phê duyệt đơn ngoài hạn và chiến dịch lỗ.
     - ✅ **Verification**: Bộ 7 bài kiểm toán tự động, cổng bảo vệ trước khi xuất báo cáo.
     - 📈 **Reports**: Trình xem trước và tải về file báo cáo HTML Standalone (11 mục + 3 phương án kinh doanh).
     - ⚙️ **Settings**: Cấu hình Return Window (15–30 ngày), Cost Driver phân bổ chi phí, vai trò duyệt.

2. **Quy chuẩn dữ liệu Google Sheets (3 Tabs bắt buộc)**:
   - **`Transactions`**: `Order_ID`, `Order_Date`, `Order_Value`, `Campaign_Count`, `Campaign_List`.
   - **`Returns`**: `Return_ID`, `Order_ID`, `Return_Date`, `Return_Amount`.
   - **`Campaign_Costs`**: `Campaign_ID`, `Campaign_Name`, `Channel`, `Direct_Cost`, `Overhead_Cost`, `Cost_Driver`.

3. **Multi-touch Attribution & ABC Costing**:
   - `Attributed Revenue = Order_Value / Campaign_Count`.
   - `Net Sales = Attributed Revenue - Attributed Return`.
   - `Total Cost = Direct Cost + Allocated Overhead`.
   - `Net Contribution = Net Sales - Total Cost`.
   - `ROAS = Attributed Revenue / Total Cost` & `ROI (%) = (Net Contribution / Total Cost) * 100`.

---

## 💻 Hướng Dẫn Khởi Chạy

Ứng dụng đang chạy sẵn tại địa chỉ: **http://localhost:8501**

Để khởi chạy lại bất kỳ lúc nào:

```powershell
& ".\.venv\Scripts\streamlit.exe" run app.py --server.port 8501 --server.headless true
```

Chạy kiểm thử end-to-end tự động:
```powershell
& ".\.venv\Scripts\python.exe" test_e2e.py
```
