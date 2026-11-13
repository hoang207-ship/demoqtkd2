import os
import streamlit as st
import pandas as pd
import plotly.express as px
from data_manager import (
    load_data_from_source,
    get_default_products_df,
    get_default_sales_reps_df,
    export_template_excel,
    DISCOUNT_POLICY
)
DEFAULT_GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6Kq4RQiPtlzO-LaBEpQWvKZDQBUuEnxtsfmTeC-XuCFWg")
from agent_engine import SalesAgentWorkflow

# Cấu hình trang phong cách Modern E-Commerce / Clean Retail SaaS
st.set_page_config(
    page_title="Minh An Tech — B2B Sales & Quote Intelligence",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS phong cách SHOP.CO / Modern Clean E-Commerce
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Cabinet+Grotesk:wght@800;900&display=swap');
    
    /* Toàn bộ nền sáng, sạch sẽ, chuẩn E-commerce hiện đại */
    .stApp {
        background-color: #FAFAFA !important;
        color: #111827;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Hiệu ứng chuyển động mượt mà (Smooth Animation Keyframes) */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(12px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes pulseGlow {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.02); }
    }

    .smooth-fade {
        animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }

    /* Sidebar Clean White */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E5E7EB;
        box-shadow: 2px 0 10px rgba(0,0,0,0.02);
    }
    
    [data-testid="stSidebar"] * {
        color: #1F2937 !important;
    }

    /* Top Announcement Ribbon (Giống ribbon giảm giá đầu trang của Shop.co) */
    .announcement-bar {
        background: #000000;
        color: #FFFFFF;
        text-align: center;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 500;
        border-radius: 8px;
        margin-bottom: 20px;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 8px;
    }

    .announcement-bar b {
        color: #FFC633;
        text-decoration: underline;
    }

    /* Top Navbar Clean */
    .shop-navbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0 24px 0;
        border-bottom: 1px solid #E5E7EB;
        margin-bottom: 28px;
    }

    .shop-logo {
        font-family: 'Cabinet Grotesk', sans-serif;
        font-size: 26px;
        font-weight: 900;
        color: #000000;
        letter-spacing: -1px;
        text-transform: uppercase;
    }

    .shop-logo span {
        color: #2563EB;
    }

    .shop-nav-pills {
        display: flex;
        gap: 10px;
        background: #F3F4F6;
        padding: 4px;
        border-radius: 999px;
    }

    .shop-pill {
        padding: 6px 16px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
        color: #4B5563;
        transition: all 0.25s ease;
        text-decoration: none;
    }

    .shop-pill.active {
        background: #000000;
        color: #FFFFFF !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }

    /* Hero Section Thân Thiện & Sang Trọng */
    .hero-ecommerce-card {
        background: #F2F0F1;
        border-radius: 28px;
        padding: 40px 48px;
        margin-bottom: 28px;
        position: relative;
        overflow: hidden;
        animation: fadeInUp 0.4s ease-out;
    }

    .hero-headline {
        font-family: 'Cabinet Grotesk', sans-serif;
        font-size: 42px;
        font-weight: 900;
        color: #000000;
        line-height: 1.15;
        letter-spacing: -1.5px;
        text-transform: uppercase;
        margin-bottom: 14px;
        max-width: 680px;
    }

    .hero-subtext {
        font-size: 15px;
        color: #4B5563;
        line-height: 1.6;
        max-width: 620px;
        margin-bottom: 24px;
    }

    /* Stats Counter (Shop.co style: 200+ 2,000+ 30,000+) */
    .stats-row {
        display: flex;
        align-items: center;
        gap: 36px;
        margin-top: 24px;
        padding-top: 20px;
        border-top: 1px solid rgba(0,0,0,0.08);
    }

    .stat-item {
        display: flex;
        flex-direction: column;
    }

    .stat-number {
        font-family: 'Cabinet Grotesk', sans-serif;
        font-size: 30px;
        font-weight: 900;
        color: #000000;
        line-height: 1;
    }

    .stat-label {
        font-size: 12px;
        color: #6B7280;
        font-weight: 500;
        margin-top: 4px;
    }

    .stat-divider {
        width: 1px;
        height: 38px;
        background: #D1D5DB;
    }

    /* Brand Bar Đen Sang Trọng (VERSACE, ZARA, GUCCI, PRADA style) */
    .brand-marquee {
        background: #000000;
        border-radius: 16px;
        padding: 18px 28px;
        display: flex;
        justify-content: space-around;
        align-items: center;
        color: #FFFFFF;
        font-family: 'Cabinet Grotesk', sans-serif;
        font-weight: 800;
        font-size: 16px;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 32px;
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.15);
    }

    /* Thẻ Kịch Bản Preset (Bo tròn, đổ bóng êm, hover nâng nhẹ) */
    .card-friendly-preset {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.03);
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .card-friendly-preset:hover {
        transform: translateY(-4px);
        box-shadow: 0 16px 30px -10px rgba(0,0,0,0.08);
        border-color: #111827;
    }

    .badge-pill-tag {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-bottom: 10px;
    }

    .pill-green { background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; }
    .pill-yellow { background: #FFFBEB; color: #D97706; border: 1px solid #FDE68A; }
    .pill-red { background: #FEF2F2; color: #DC2626; border: 1px solid #FECDD3; }

    /* Stepper Thân Thiện E-Commerce Checkout Style */
    .checkout-stepper {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 20px;
        padding: 18px 28px;
        margin-bottom: 28px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }

    .checkout-step {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 13px;
        font-weight: 600;
        color: #9CA3AF;
        transition: all 0.25s ease;
    }

    .checkout-step.done {
        color: #000000;
    }

    .step-number-circle {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        background: #F3F4F6;
        color: #6B7280;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 12px;
        transition: all 0.25s ease;
    }

    .checkout-step.done .step-number-circle {
        background: #000000;
        color: #FFFFFF;
    }

    .checkout-step.warning .step-number-circle {
        background: #F59E0B;
        color: #FFFFFF;
    }

    .checkout-step.danger .step-number-circle {
        background: #EF4444;
        color: #FFFFFF;
    }

    .checkout-connector {
        flex: 1;
        height: 2px;
        background: #E5E7EB;
        margin: 0 12px;
    }

    .checkout-connector.done {
        background: #000000;
    }

    /* KPI Summary Cards E-Commerce */
    .kpi-summary-box {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 18px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        transition: all 0.2s ease;
    }

    .kpi-summary-box:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px -5px rgba(0,0,0,0.05);
    }

    .kpi-title-text {
        font-size: 12px;
        font-weight: 600;
        color: #6B7280;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .kpi-val-text {
        font-family: 'Cabinet Grotesk', sans-serif;
        font-size: 26px;
        font-weight: 800;
        color: #000000;
        margin-top: 4px;
    }

    /* Input TextArea E-commerce Styling */
    .stTextArea textarea {
        background-color: #FFFFFF !important;
        border: 1.5px solid #E5E7EB !important;
        border-radius: 16px !important;
        color: #111827 !important;
        font-size: 14px !important;
        line-height: 1.6 !important;
        padding: 16px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
        transition: all 0.2s ease !important;
    }

    .stTextArea textarea:focus {
        border-color: #000000 !important;
        box-shadow: 0 0 0 3px rgba(0,0,0,0.08) !important;
    }

    /* Nút bấm Đen Tròn sang trọng (Shop.co Pill Button) */
    .stButton > button {
        border-radius: 999px !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        padding: 10px 24px !important;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
        border: 1.5px solid transparent !important;
    }

    .stButton > button[kind="primary"] {
        background: #000000 !important;
        color: #FFFFFF !important;
        border: 1.5px solid #000000 !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15) !important;
    }

    .stButton > button[kind="primary"]:hover {
        background: #2563EB !important;
        border-color: #2563EB !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(37, 99, 235, 0.25) !important;
    }

    .stButton > button[kind="secondary"] {
        background: #FFFFFF !important;
        color: #111827 !important;
        border: 1.5px solid #E5E7EB !important;
    }

    .stButton > button[kind="secondary"]:hover {
        background: #F3F4F6 !important;
        border-color: #111827 !important;
        color: #000000 !important;
        transform: translateY(-2px) !important;
    }

    /* Tabs E-commerce Shop.co Style */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent !important;
        border-bottom: 2px solid #E5E7EB !important;
        gap: 16px;
    }

    .stTabs [data-baseweb="tab"] {
        color: #6B7280 !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        padding: 12px 20px !important;
        border: none !important;
        background: transparent !important;
    }

    .stTabs [aria-selected="true"] {
        color: #000000 !important;
        border-bottom: 2px solid #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

# Khởi tạo session state
if "products_df" not in st.session_state:
    st.session_state.products_df = get_default_products_df()

if "sales_reps_df" not in st.session_state:
    st.session_state.sales_reps_df = get_default_sales_reps_df()

if "gemini_key" not in st.session_state:
    st.session_state.gemini_key = DEFAULT_GEMINI_KEY

if "crm_records" not in st.session_state:
    st.session_state.crm_records = [
        {"Mã": "OPP-202611-1021", "Khách Hàng": "Tập đoàn Vingroup", "NVKD": "Nguyễn Văn An", "Giá Trị (VNĐ)": 520000000, "Trạng Thái": "Đã gửi báo giá", "Thời Gian": "Hôm nay 08:30"},
        {"Mã": "OPP-202611-1022", "Khách Hàng": "Chuỗi Bách Hóa Xanh", "NVKD": "Trần Thị Bích", "Giá Trị (VNĐ)": 185000000, "Trạng Thái": "Chờ duyệt TP", "Thời Gian": "Hôm nay 09:15"},
        {"Mã": "OPP-202611-1023", "Khách Hàng": "FPT Software", "NVKD": "Lê Hoàng Long", "Giá Trị (VNĐ)": 410000000, "Trạng Thái": "Đã gửi báo giá", "Thời Gian": "Hôm nay 10:00"},
        {"Mã": "OPP-202611-1024", "Khách Hàng": "Bệnh viện Vinmec", "NVKD": "Phạm Thu Hà", "Giá Trị (VNĐ)": 95000000, "Trạng Thái": "Chờ KH bổ sung", "Thời Gian": "Hôm nay 10:45"},
        {"Mã": "OPP-202611-1025", "Khách Hàng": "Nhà máy Samsung Thái Nguyên", "NVKD": "Vũ Minh Đức", "Giá Trị (VNĐ)": 890000000, "Trạng Thái": "Chờ duyệt TP", "Thời Gian": "Hôm nay 11:20"},
        {"Mã": "OPP-202611-1026", "Khách Hàng": "Công ty CP Đầu tư Nam Thịnh", "NVKD": "Đỗ Quỳnh Trang", "Giá Trị (VNĐ)": 78000000, "Trạng Thái": "Đã chốt hợp đồng", "Thời Gian": "Hôm qua 16:40"}
    ]

# ----------------- SIDEBAR CLEAN E-COMMERCE -----------------
with st.sidebar:
    st.markdown("""
    <div style="font-family:'Cabinet Grotesk'; font-size:24px; font-weight:900; color:#000000; letter-spacing:-0.5px;">
        MINH AN <span style="color:#2563EB;">TECH</span>
    </div>
    <div style="font-size:12px; color:#6B7280; margin-bottom:16px;">B2B Sales Operations Platform</div>
    """, unsafe_allow_html=True)
    
    # Card trạng thái AI Engine
    st.markdown("""
    <div style="background:#F9FAFB; border:1px solid #E5E7EB; border-radius:14px; padding:14px; margin-bottom:18px;">
        <div style="display:flex; align-items:center; gap:8px;">
            <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#10B981;"></span>
            <b style="font-size:13px; color:#111827;">Gemini 3.5 Flash Active</b>
        </div>
        <div style="font-size:11px; color:#6B7280; margin-top:4px;">
            Trích xuất thông minh & Tự động đối soát kho
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("⚙️ Quản lý API Key", expanded=False):
        api_input = st.text_input("Gemini API Key:", value=st.session_state.gemini_key, type="password")
        if api_input != st.session_state.gemini_key:
            st.session_state.gemini_key = api_input
            st.success("Đã cập nhật API Key!")

    st.divider()

    st.markdown("#### 📂 **Nguồn Bảng Giá & Tồn Kho**")
    data_source_mode = st.radio(
        "Nguồn dữ liệu:",
        ["Dữ liệu Chuẩn Minh An (Mặc định)", "Tải file lên (CSV / XLSX)", "Đồng bộ Google Sheets"],
        label_visibility="collapsed"
    )

    if data_source_mode == "Tải file lên (CSV / XLSX)":
        uploaded_file = st.file_uploader("Upload file:", type=["csv", "xlsx", "xls"])
        if uploaded_file is not None:
            df_loaded, msg = load_data_from_source(uploaded_file=uploaded_file)
            st.session_state.products_df = df_loaded
            st.success(msg)

    elif data_source_mode == "Đồng bộ Google Sheets":
        gsheet_link = st.text_input("Public Sheet URL:", placeholder="https://docs.google.com/spreadsheets/...")
        if st.button("🔄 Đồng bộ Sheet", width='stretch'):
            if gsheet_link:
                df_loaded, msg = load_data_from_source(gsheet_url=gsheet_link)
                st.session_state.products_df = df_loaded
                st.info(msg)
            else:
                st.warning("Vui lòng nhập link hợp lệ.")
    else:
        if st.button("↺ Khôi phục Dữ liệu Chuẩn", width='stretch'):
            st.session_state.products_df = get_default_products_df()
            st.success("Đã hoàn tác dữ liệu gốc!")

    st.markdown("<br>", unsafe_allow_html=True)
    excel_bytes = export_template_excel()
    st.download_button(
        label="📥 Tải Template Excel Mẫu (.xlsx)",
        data=excel_bytes,
        file_name="MinhAn_MasterData_Template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width='stretch'
    )

    st.divider()
    st.markdown("#### 👥 **6 Nhân Viên Kinh Doanh Trực Ban**")
    for _, r in st.session_state.sales_reps_df.iterrows():
        st.markdown(f"""
        <div style="font-size:12px; margin-bottom:8px; border-bottom:1px solid #F3F4F6; padding-bottom:6px;">
            <b style="color:#111827;">{r['ho_ten']}</b> <span style="color:#2563EB; font-size:11px;">[{r['ma_nv']}]</span><br>
            <span style="color:#6B7280; font-size:11px;">{r['chuyen_mon'].split(',')[0]}</span>
        </div>
        """, unsafe_allow_html=True)

# ----------------- TOP ANNOUNCEMENT RIBBON -----------------
st.markdown("""
<div class="announcement-bar">
    <span>✨ Minh An B2B AI Agent v2.5: Tự động hóa 100% từ đọc email đến báo giá & CRM. <b>Trải nghiệm ngay!</b></span>
</div>
""", unsafe_allow_html=True)

# ----------------- TOP NAVBAR -----------------
st.markdown("""
<div class="shop-navbar">
    <div class="shop-logo">
        MINH AN<span>.TECH</span>
    </div>
    <div class="shop-nav-pills">
        <span class="shop-pill active">⚡ Live Processor</span>
        <span class="shop-pill">📦 Bảng Giá & Kho</span>
        <span class="shop-pill">📊 CRM Pipeline</span>
        <span class="shop-pill">⚖️ Phân Quyền Duyệt</span>
    </div>
    <div>
        <span style="background:#ECFDF5; color:#059669; padding:6px 16px; border-radius:999px; font-weight:700; font-size:12px; border:1px solid #A7F3D0;">
            ● Gemini 3.5 Online
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------- HERO BANNER (Phong cách SHOP.CO: "FIND CLOTHES THAT MATCHES YOUR STYLE") -----------------
st.markdown("""
<div class="hero-ecommerce-card">
    <div class="hero-headline">
        B2B SALES AI AGENT THAT CLOSES DEALS FASTER
    </div>
    <div class="hero-subtext">
        Hệ thống AI thông minh hỗ trợ 6 Nhân viên Kinh doanh xử lý 180 yêu cầu/tuần. Tự động kiểm tra tính đầy đủ của thông tin, đối chiếu giá mới nhất, xác nhận tồn khả dụng và lập báo giá chuẩn xác trong tích tắc.
    </div>
    <div class="stats-row">
        <div class="stat-item">
            <div class="stat-number">180+</div>
            <div class="stat-label">Yêu Cầu / Tuần</div>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
            <div class="stat-number">6 NVKD</div>
            <div class="stat-label">Chuyên Trách Theo Ngành</div>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
            <div class="stat-number">100%</div>
            <div class="stat-label">Chuẩn Giá & Tồn Kho Realtime</div>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
            <div class="stat-number">&lt; 3s</div>
            <div class="stat-label">Thời Gian Phản Hồi AI</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------- BRAND BAR ĐEN (VERSACE, ZARA, GUCCI style) -----------------
st.markdown("""
<div class="brand-marquee">
    <span>DELL TECHNOLOGIES</span>
    <span>•</span>
    <span>CISCO NETWORKS</span>
    <span>•</span>
    <span>FORTINET SECURITY</span>
    <span>•</span>
    <span>LENOVO THINKPAD</span>
    <span>•</span>
    <span>APC SCHNEIDER</span>
</div>
""", unsafe_allow_html=True)

# ----------------- TABS WORKFLOW -----------------
tab1, tab2, tab3 = st.tabs([
    "🚀 Xử lý Yêu cầu (AI Agent Live)",
    "📊 Pipeline CRM & Báo cáo Tuần",
    "📋 Danh mục Sản phẩm & Chính sách Giá"
])

# ================= TAB 1: AI LIVE WORKFLOW =================
with tab1:
    st.markdown("#### ⚡ **Chọn Kịch Bản Test Mẫu Nhanh (1 Click):**")
    st.caption("Thử nghiệm ngay 3 luồng xử lý điển hình trong quy trình bán hàng B2B của Minh An:")
    
    col_p1, col_p2, col_p3 = st.columns(3)
    chosen_preset_text = None

    with col_p1:
        st.markdown("""
        <div class="card-friendly-preset">
            <div>
                <span class="badge-pill-tag pill-green">🟢 Hợp lệ & Tự quyết</span>
                <div style="font-family:'Cabinet Grotesk'; font-size:18px; font-weight:800; color:#111827; margin-bottom:6px;">
                    Case 1: Ngân Hàng Nam Á
                </div>
                <div style="font-size:13px; color:#4B5563; line-height:1.5;">
                    Đặt 2 Server Dell R750 + 4 Switch Cisco. Đầy đủ ngân sách 460 triệu, hạn 14 ngày, xin chiết khấu 8% trong thẩm quyền.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Chọn Case 1 (Hợp lệ)", key="btn_c1_clean", width='stretch'):
            chosen_preset_text = """Kính gửi Công ty Công nghệ Minh An,
Tôi là Trần Minh Hoàng - Trưởng phòng CNTT Ngân hàng Thương mại Nam Á (CN Hà Nội).
Email: hoang.tm@namabank.com.vn | SĐT: 0912.456.789.
Chúng tôi đang có kế hoạch nâng cấp trung tâm dữ liệu chi nhánh và cần báo giá các thiết bị sau:
1. 2 bộ Máy chủ Dell PowerEdge R750 2x Xeon Silver 4314, 64GB RAM, 2x 960GB SSD
2. 4 cái Switch Cisco Catalyst C9200L-24P-4G-E 24 cổng PoE+
3. 1 gói Dịch vụ Triển khai, Cài đặt Hệ thống Mạng & Máy chủ Doanh nghiệp

- Ngân sách dự kiến được phê duyệt: 460 triệu VNĐ.
- Thời hạn triển khai và nghiệm thu: Trong vòng 14 ngày tới.
- Chúng tôi đề xuất mức chiết khấu doanh nghiệp: 8% trên tổng giá niêm yết.

Rất mong nhận được báo giá và tiến độ giao hàng sớm nhất từ quý công ty."""

    with col_p2:
        st.markdown("""
        <div class="card-friendly-preset">
            <div>
                <span class="badge-pill-tag pill-yellow">🟡 Thiếu thông tin</span>
                <div style="font-family:'Cabinet Grotesk'; font-size:18px; font-weight:800; color:#111827; margin-bottom:6px;">
                    Case 2: Bán Lẻ Modern Style
                </div>
                <div style="font-size:13px; color:#4B5563; line-height:1.5;">
                    Hỏi mua laptop Dell và switch mạng nhưng KHÔNG nêu rõ số lượng, KHÔNG có ngân sách, thời hạn mơ hồ.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Chọn Case 2 (Thiếu tin)", key="btn_c2_clean", width='stretch'):
            chosen_preset_text = """Chào Minh An,
Bên mình là Công ty CP Bán lẻ Thời trang Modern Style.
Email: contact@modernstyle.vn | SĐT: 0987.654.321.
Hiện tại bên mình đang mở thêm cửa hàng mới nên cần mua một số thiết bị văn phòng như sau:
- Laptop Dell Latitude 5540 cho nhân viên
- Màn hình đồ họa Dell UltraSharp 27 inch
- Switch Cisco cho mạng nội bộ

Minh An gửi giúp mình báo giá tốt nhất nhé. Cảm ơn."""

    with col_p3:
        st.markdown("""
        <div class="card-friendly-preset">
            <div>
                <span class="badge-pill-tag pill-red">🔴 Vượt thẩm quyền</span>
                <div style="font-family:'Cabinet Grotesk'; font-size:18px; font-weight:800; color:#111827; margin-bottom:6px;">
                    Case 3: FDI Foxconn Precision
                </div>
                <div style="font-size:13px; color:#4B5563; line-height:1.5;">
                    Đòi chiết khấu 16% (vượt trần NVKD 10%) và yêu cầu giao gấp trong 3 ngày trong khi kho cần 14 ngày.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Chọn Case 3 (Vượt quyền)", key="btn_c3_clean", width='stretch'):
            chosen_preset_text = """Gửi Bộ phận Kinh doanh Minh An,
Tôi là Lee Sang-min - Giám đốc Mua hàng Công ty TNHH Điện tử Foxconn Precision (KCN Bắc Ninh).
Email: lee.sm@foxconn-precision.vn | SĐT: 0903.111.222.
Chúng tôi cần gấp lô thiết bị sau cho phòng máy chủ xưởng mới:
1. 1 bộ Máy chủ Dell PowerEdge R750
2. 3 tủ Server APC NetShelter SX 42U
3. 3 bộ Lưu điện APC Smart-UPS SRT 3000VA RM 2U
4. 1 cái Tường lửa Fortinet FortiGate FG-80F

Yêu cầu đặc biệt:
- Do dự án khẩn cấp, yêu cầu bàn giao và lắp đặt hoàn tất trong vòng 3 ngày làm việc tới.
- Đề nghị áp dụng chiết khấu đặc biệt dành cho đối tác FDI lớn: 16% trên toàn bộ đơn hàng.
- Ngân sách nội bộ của chúng tôi là: 350 triệu VNĐ.

Đề nghị phản hồi sớm để kịp trình phê duyệt ban điều hành."""

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 📝 **Văn Bản Yêu Cầu Của Khách Hàng (Email / Biểu Mẫu):**")

    default_raw = chosen_preset_text if chosen_preset_text else """Kính gửi Công ty Công nghệ Minh An,
Tôi là Trần Minh Hoàng - Trưởng phòng CNTT Ngân hàng Thương mại Nam Á (CN Hà Nội).
Email: hoang.tm@namabank.com.vn | SĐT: 0912.456.789.
Chúng tôi đang có kế hoạch nâng cấp trung tâm dữ liệu chi nhánh và cần báo giá các thiết bị sau:
1. 2 bộ Máy chủ Dell PowerEdge R750 2x Xeon Silver 4314, 64GB RAM, 2x 960GB SSD
2. 4 cái Switch Cisco Catalyst C9200L-24P-4G-E 24 cổng PoE+
3. 1 gói Dịch vụ Triển khai, Cài đặt Hệ thống Mạng & Máy chủ Doanh nghiệp

- Ngân sách dự kiến được phê duyệt: 460 triệu VNĐ.
- Thời hạn triển khai và nghiệm thu: Trong vòng 14 ngày tới.
- Chúng tôi đề xuất mức chiết khấu doanh nghiệp: 8% trên tổng giá niêm yết.

Rất mong nhận được báo giá và tiến độ giao hàng sớm nhất từ quý công ty."""

    input_text = st.text_area("Yêu cầu:", value=default_raw, height=170, label_visibility="collapsed")

    col_btn_action, _ = st.columns([2, 5])
    with col_btn_action:
        btn_fire = st.button("🚀 KÍCH HOẠT AI AGENT PHÂN TÍCH", type="primary", width='stretch')

    if btn_fire and input_text.strip():
        with st.spinner("🤖 AI Agent đang bóc tách và thực thi quy trình..."):
            agent = SalesAgentWorkflow(
                products_df=st.session_state.products_df,
                sales_reps_df=st.session_state.sales_reps_df,
                gemini_api_key=st.session_state.gemini_key
            )
            result = agent.process_request(input_text)
            st.session_state.clean_res = result

            if "step3" in result["steps"]:
                crm_info = result["steps"]["step7"]["summary_for_crm"]
                st.session_state.crm_records.insert(0, {
                    "Mã": crm_info["Mã Cơ Hội"],
                    "Khách Hàng": crm_info["Khách Hàng"],
                    "NVKD": crm_info["NVKD Phụ Trách"],
                    "Giá Trị (VNĐ)": float(crm_info["Tổng Giá Trị (VAT)"].replace(" VNĐ", "").replace(",", "")),
                    "Trạng Thái": crm_info["Trạng Thái Duyệt"],
                    "Thời Gian": "Vừa tiếp nhận"
                })

    # HIỂN THỊ KẾT QUẢ PHÂN TÍCH (Shop.co Clean Style)
    if "clean_res" in st.session_state:
        res = st.session_state.clean_res
        steps = res["steps"]
        status = res["final_status"]

        st.markdown("<br><hr style='border-color:#E5E7EB;'><br>", unsafe_allow_html=True)

        is_complete = steps["step2"]["is_complete"]
        is_escalated = (status == "CHỜ_DUYỆT_TRƯỞNG_PHÒNG")

        c2 = "done" if is_complete else "warning"
        c3 = "done" if is_complete else ""
        c4 = "done" if is_complete else ""
        c5 = "done" if is_complete else ""
        c6 = "danger" if is_escalated else ("done" if is_complete else "")
        c7 = "done" if is_complete else ""

        # STEPPER CHECKOUT E-COMMERCE STYLE
        st.markdown(f"""
        <div class="checkout-stepper smooth-fade">
            <div class="checkout-step done">
                <div class="step-number-circle">1</div>
                <div>Tiếp nhận</div>
            </div>
            <div class="checkout-connector done"></div>
            <div class="checkout-step {c2}">
                <div class="step-number-circle">2</div>
                <div>Kiểm tra tin</div>
            </div>
            <div class="checkout-connector {'done' if is_complete else ''}"></div>
            <div class="checkout-step {c3}">
                <div class="step-number-circle">3</div>
                <div>Hồ sơ & Gán NVKD</div>
            </div>
            <div class="checkout-connector {'done' if is_complete else ''}"></div>
            <div class="checkout-step {c4}">
                <div class="step-number-circle">4</div>
                <div>Thẩm định kho</div>
            </div>
            <div class="checkout-connector {'done' if is_complete else ''}"></div>
            <div class="checkout-step {c5}">
                <div class="step-number-circle">5</div>
                <div>Báo giá</div>
            </div>
            <div class="checkout-connector {'done' if is_complete else ''}"></div>
            <div class="checkout-step {c6}">
                <div class="step-number-circle">6</div>
                <div>Xét duyệt</div>
            </div>
            <div class="checkout-connector {'done' if is_complete else ''}"></div>
            <div class="checkout-step {c7}">
                <div class="step-number-circle">7</div>
                <div>Đề xuất & CRM</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # BANNER TRẠNG THÁI CUỐI
        if status == "ĐÃ_LẬP_ĐỀ_XUẤT_CHUẨN":
            st.markdown(f"""
            <div style="background:#ECFDF5; border:1.5px solid #10B981; border-radius:18px; padding:18px 24px; margin-bottom:24px; display:flex; justify-content:space-between; align-items:center;" class="smooth-fade">
                <div>
                    <div style="font-family:'Cabinet Grotesk'; font-size:18px; font-weight:900; color:#065F46;">
                        🟢 HỒ SƠ HỢP LỆ — NVKD TỰ QUYẾT PHÊ DUYỆT
                    </div>
                    <div style="font-size:13px; color:#047857; margin-top:3px;">
                        Tồn kho khả dụng đầy đủ • Thời hạn cam kết khả thi • Chiết khấu trong hạn mức quy định.
                    </div>
                </div>
                <div style="background:#10B981; color:#FFFFFF; font-size:12px; font-weight:700; padding:6px 16px; border-radius:999px;">
                    {res['engine_used']}
                </div>
            </div>
            """, unsafe_allow_html=True)

        elif status == "CHỜ_DUYỆT_TRƯỞNG_PHÒNG":
            st.markdown(f"""
            <div style="background:#FEF2F2; border:1.5px solid #EF4444; border-radius:18px; padding:18px 24px; margin-bottom:24px; display:flex; justify-content:space-between; align-items:center;" class="smooth-fade">
                <div>
                    <div style="font-family:'Cabinet Grotesk'; font-size:18px; font-weight:900; color:#991B1B;">
                        🔴 HỒ SƠ VƯỢT THẨM QUYỀN — CẦN TRƯỞNG PHÒNG DUYỆT
                    </div>
                    <div style="font-size:13px; color:#B91C1C; margin-top:3px;">
                        Phát hiện chiết khấu vượt trần NVKD hoặc tiến độ giao hàng quá gấp. Đã tự động lập Tờ trình Trưởng phòng duyệt.
                    </div>
                </div>
                <div style="background:#EF4444; color:#FFFFFF; font-size:12px; font-weight:700; padding:6px 16px; border-radius:999px;">
                    {res['engine_used']}
                </div>
            </div>
            """, unsafe_allow_html=True)

        else:
            st.markdown(f"""
            <div style="background:#FFFBEB; border:1.5px solid #F59E0B; border-radius:18px; padding:18px 24px; margin-bottom:24px; display:flex; justify-content:space-between; align-items:center;" class="smooth-fade">
                <div>
                    <div style="font-family:'Cabinet Grotesk'; font-size:18px; font-weight:900; color:#92400E;">
                        🟡 THIẾU THÔNG TIN THIẾT YẾU — KÍCH HOẠT NHÁNH HỎI LẠI KHÁCH HÀNG
                    </div>
                    <div style="font-size:13px; color:#B45309; margin-top:3px;">
                        Yêu cầu thiếu ngân sách dự kiến, thời hạn hoặc số lượng. Đã tự động soạn Thư chuẩn hóa để NVKD gửi khách.
                    </div>
                </div>
                <div style="background:#F59E0B; color:#FFFFFF; font-size:12px; font-weight:700; padding:6px 16px; border-radius:999px;">
                    {res['engine_used']}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # TRƯỜNG HỢP 1: THIẾU THÔNG TIN
        if not is_complete:
            col_thieu_left, col_thieu_right = st.columns([1, 2])
            with col_thieu_left:
                st.markdown("#### ❌ **Hạng Mục Cần Khách Bổ Sung:**")
                for fld in steps["clarification"]["missing_fields"]:
                    st.markdown(f"""
                    <div style="background:#FFFFFF; border-left:4px solid #F59E0B; border:1px solid #E5E7EB; padding:10px 14px; border-radius:10px; margin-bottom:8px; font-size:13px; font-weight:600; color:#1F2937;">
                        • {fld}
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("""
                <div style="background:#F3F4F6; border-radius:14px; padding:16px; font-size:13px; color:#4B5563; line-height:1.5; margin-top:14px;">
                    💡 <b>Quy tắc Vận hành Minh An:</b> Không để hồ sơ thiếu ngân sách hay chưa rõ cấu hình tồn đọng lòng vòng. NVKD gửi ngay thư phản hồi chuẩn mực này để khách hàng bổ sung.
                </div>
                """, unsafe_allow_html=True)

            with col_thieu_right:
                st.markdown("#### ✉️ **Bản Nháp Thư Yêu Cầu Bổ Sung (Sẵn Sàng Gửi):**")
                c_mail = steps["clarification"]["draft_email"]
                st.text_area("Nội dung thư:", value=c_mail, height=270, label_visibility="collapsed")
                st.download_button(
                    label="📋 Tải Thư Yêu Cầu Bổ Sung (.txt)",
                    data=c_mail,
                    file_name="Thu_yeu_cau_bo_sung_MinhAn.txt",
                    mime="text/plain",
                    width='stretch'
                )

        # TRƯỜNG HỢP 2: ĐẦY ĐỦ THÔNG TIN
        else:
            step3 = steps["step3"]
            step4 = steps["step4"]
            step5 = steps["step5"]
            step6 = steps["step6"]
            step7 = steps["step7"]

            # BƯỚC 3: HỒ SƠ CƠ HỘI
            st.markdown("#### 📌 **Bước 3: Hồ Sơ Cơ Hội B2B & Gắn Người Phụ Trách**")
            col_k1, col_k2, col_k3, col_k4 = st.columns(4)
            with col_k1:
                st.markdown(f"""
                <div class="kpi-summary-box">
                    <div class="kpi-title-text">Mã Cơ Hội</div>
                    <div class="kpi-val-text" style="font-size:20px; color:#2563EB;">{step3['opp_id']}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_k2:
                st.markdown(f"""
                <div class="kpi-summary-box">
                    <div class="kpi-title-text">Khách Hàng</div>
                    <div class="kpi-val-text" style="font-size:16px; line-height:1.2;">{step3['customer_name']}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_k3:
                st.markdown(f"""
                <div class="kpi-summary-box">
                    <div class="kpi-title-text">NVKD Phụ Trách</div>
                    <div class="kpi-val-text" style="font-size:16px; color:#059669;">{step3['assigned_rep']}</div>
                    <div style="font-size:11px; color:#6B7280;">{step3['rep_specialty'].split(',')[0]}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_k4:
                st.markdown(f"""
                <div class="kpi-summary-box">
                    <div class="kpi-title-text">Mức Ưu Tiên</div>
                    <div class="kpi-val-text" style="font-size:20px; color:#D97706;">{step3['priority']}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # BƯỚC 4: THẨM ĐỊNH KHO & GIÁ
            st.markdown("#### 📦 **Bước 4: Thẩm Định Tồn Kho Khả Dụng & Giá Niêm Yết Mới Nhất**")
            if step4["has_deadline_risk"]:
                st.markdown("""
                <div style="background:#FEF2F2; border:1px solid #FECDD3; border-radius:12px; padding:12px 16px; margin-bottom:12px; font-size:13px; color:#991B1B;">
                    🚨 <b>CẢNH BÁO TIẾN ĐỘ:</b> Thời gian chuẩn bị hàng thực tế vượt quá deadline cam kết của khách! (Tránh lỗi hứa thời hạn không đáp ứng được).
                </div>
                """, unsafe_allow_html=True)
                for iss in step4["lead_time_issues"]:
                    st.markdown(f"• **{iss['product']}**: Cần **{iss['required_days']} ngày** (Khách yêu cầu {iss['customer_deadline']} ngày ➔ Trễ {iss['gap']} ngày)")
            else:
                st.markdown("""
                <div style="background:#ECFDF5; border:1px solid #A7F3D0; border-radius:12px; padding:10px 16px; margin-bottom:12px; font-size:13px; color:#065F46;">
                    ✅ <b>TIẾN ĐỘ KHẢ THI:</b> Toàn bộ thiết bị đáp ứng trọn vẹn thời hạn bàn giao của khách hàng.
                </div>
                """, unsafe_allow_html=True)

            table_rows = []
            for it in step4["items"]:
                table_rows.append({
                    "Hạng Mục Yêu Cầu": it["req_item_name"],
                    "Mã & Tên SP Minh An": f"[{it['matched_code']}] {it['matched_name']}",
                    "SL": it["qty"],
                    "Đơn Giá Niêm Yết": f"{it['current_list_price']:,.0f} đ",
                    "Tồn Kho": it["ton_kho"],
                    "Lead Time": f"{it['lead_time_days']} ngày",
                    "Đánh Giá Kho": it["stock_status"]
                })
            st.dataframe(pd.DataFrame(table_rows), width='stretch')

            st.markdown("<br>", unsafe_allow_html=True)

            # BƯỚC 5: TÀI CHÍNH & BÁO GIÁ
            st.markdown("#### 💰 **Bước 5: Lập Báo Giá & Đề Xuất Kinh Doanh (Order Summary)**")
            cf1, cf2, cf3, cf4 = st.columns(4)
            with cf1:
                st.markdown(f"""
                <div class="kpi-summary-box">
                    <div class="kpi-title-text">Tổng Giá Niêm Yết</div>
                    <div class="kpi-val-text">{step5['total_list_price']:,.0f} đ</div>
                </div>
                """, unsafe_allow_html=True)
            with cf2:
                st.markdown(f"""
                <div class="kpi-summary-box">
                    <div class="kpi-title-text">Chiết Khấu ({step5['applied_discount']}%)</div>
                    <div class="kpi-val-text" style="color:#D97706;">-{step5['discount_amount']:,.0f} đ</div>
                </div>
                """, unsafe_allow_html=True)
            with cf3:
                st.markdown(f"""
                <div class="kpi-summary-box">
                    <div class="kpi-title-text">Thuế VAT (10%)</div>
                    <div class="kpi-val-text" style="color:#2563EB;">+{step5['vat_amount']:,.0f} đ</div>
                </div>
                """, unsafe_allow_html=True)
            with cf4:
                st.markdown(f"""
                <div class="kpi-summary-box" style="border:2px solid #000000; background:#000000; color:#FFFFFF;">
                    <div class="kpi-title-text" style="color:#9CA3AF;">TỔNG THANH TOÁN (VAT)</div>
                    <div class="kpi-val-text" style="color:#FFFFFF;">{step5['grand_total']:,.0f} đ</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            if step5["budget_match"]:
                st.markdown(f"""
                <div style="background:#ECFDF5; border:1px solid #A7F3D0; border-radius:12px; padding:12px 16px; font-size:13px; color:#065F46;">
                    🎯 <b>SO KHỚP NGÂN SÁCH:</b> Giá trị đề xuất ({step5['grand_total']:,.0f} đ) nằm trọn trong ngân sách của khách ({step5['customer_budget']:,.0f} đ). Dư ngân sách: {step5['budget_variance']:,.0f} đ.
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background:#FFFBEB; border:1px solid #FDE68A; border-radius:12px; padding:12px 16px; font-size:13px; color:#92400E;">
                    ⚠️ <b>VƯỢT NGÂN SÁCH:</b> Báo giá cao hơn ngân sách dự kiến của khách {abs(step5['budget_variance']):,.0f} đ. Đề xuất NVKD tư vấn giải pháp tối ưu cấu hình.
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # BƯỚC 6: XÉT DUYỆT THẨM QUYỀN
            st.markdown("#### ⚖️ **Bước 6: Thẩm Quyền Phê Duyệt & Chuyển Duyệt Cấp Trên**")
            if step6["requires_approval"]:
                st.markdown(f"""
                <div style="background:#FEF2F2; border-left:5px solid #EF4444; border-radius:12px; padding:16px; margin-bottom:14px;">
                    <div style="color:#991B1B; font-family:'Cabinet Grotesk'; font-size:16px; font-weight:800;">
                        🚨 HỒ SƠ VƯỢT THẨM QUYỀN NVKD — CẦN {step6['approver'].upper()} PHÊ DUYỆT
                    </div>
                </div>
                """, unsafe_allow_html=True)
                for rz in step6["reasons"]:
                    st.markdown(f"• {rz}")

                with st.expander("📄 TỜ TRÌNH NỘI BỘ (AI Agent tự động soạn sẵn cho NVKD)", expanded=True):
                    memo_txt = step6["approval_memo"]
                    st.text_area("Nội dung Tờ trình:", value=memo_txt, height=250, label_visibility="collapsed")
                    st.download_button(
                        label="📥 Tải Tờ Trình Phê Duyệt Cấp Trên (.txt)",
                        data=memo_txt,
                        file_name=f"To_trinh_{step3['opp_id']}.txt",
                        mime="text/plain",
                        width='stretch'
                    )
            else:
                st.markdown("""
                <div style="background:#ECFDF5; border:1px solid #A7F3D0; border-radius:12px; padding:12px 16px; font-size:13px; color:#065F46;">
                    ✅ <b>HỢP LỆ:</b> Mức chiết khấu và thời gian triển khai nằm trong phân quyền tự quyết của NVKD. Không cần chuyển duyệt cấp trên.
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # BƯỚC 7: XUẤT ĐỀ XUẤT
            st.markdown("#### 📬 **Bước 7: Bản Nháp Email Báo Giá & Đề Xuất Chính Thức**")
            quote_mail = step7["customer_email_draft"]
            st.text_area("Email Báo giá gửi Khách:", value=quote_mail, height=290, label_visibility="collapsed")
            st.download_button(
                label="📥 Tải Toàn Bộ Bản Đề Xuất Báo Giá (.txt)",
                data=quote_mail,
                file_name=f"Bao_gia_{step3['opp_id']}_{step3['customer_name']}.txt",
                mime="text/plain",
                width='stretch'
            )

# ================= TAB 2: CRM PIPELINE =================
with tab2:
    st.markdown("#### 📊 **Quản Trị Pipeline Tuần (180 Deals Tiếp Nhận)**")
    st.caption("Minh bạch trạng thái xử lý từng cơ hội, giải quyết triệt để tình trạng bỏ sót yêu cầu hoặc chuyển qua lại không người theo dõi.")

    df_crm = pd.DataFrame(st.session_state.crm_records)

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div class="kpi-summary-box">
            <div class="kpi-title-text">Tổng Cơ Hội</div>
            <div class="kpi-val-text">{len(df_crm)} Deals</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
        <div class="kpi-summary-box">
            <div class="kpi-title-text">Giá Trị Pipeline</div>
            <div class="kpi-val-text" style="color:#2563EB;">{df_crm['Giá Trị (VNĐ)'].sum():,.0f} đ</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        pend = len(df_crm[df_crm["Trạng Thái"].str.contains("duyệt", case=False)])
        st.markdown(f"""
        <div class="kpi-summary-box">
            <div class="kpi-title-text">Đang Chờ Duyệt</div>
            <div class="kpi-val-text" style="color:#D97706;">{pend} Deals</div>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
        <div class="kpi-summary-box">
            <div class="kpi-title-text">Đội Ngũ Vận Hành</div>
            <div class="kpi-val-text">6 NVKD</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    c_g1, c_g2 = st.columns(2)
    with c_g1:
        fig_pie = px.pie(
            df_crm,
            names="NVKD",
            title="Tỷ lệ phân bổ cơ hội cho 6 NVKD",
            color_discrete_sequence=["#111827", "#2563EB", "#10B981", "#F59E0B", "#8B5CF6", "#6B7280"]
        )
        fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_pie, width='stretch')

    with c_g2:
        fig_bar = px.bar(
            df_crm,
            x="Trạng Thái",
            y="Giá Trị (VNĐ)",
            color="Trạng Thái",
            title="Giá trị pipeline theo trạng thái",
            color_discrete_sequence=["#10B981", "#F59E0B", "#EF4444", "#2563EB"]
        )
        fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_bar, width='stretch')

    st.markdown("**📋 Chi Tiết Toàn Bộ Hồ Sơ Cơ Hội:**")
    st.dataframe(df_crm, width='stretch')

# ================= TAB 3: MASTER DATA =================
with tab3:
    st.markdown("#### 📋 **Bảng Giá Niêm Yết & Tồn Kho Khả Dụng Master Data**")
    st.caption("Cơ sở dữ liệu giá và tồn kho khả dụng mới nhất - Chấm dứt lỗi dùng giá cũ và cam kết sai lead time.")

    df_p = st.session_state.products_df.copy()
    if "gia_niem_yet" in df_p.columns:
        df_p["Đơn Giá Niêm Yết"] = df_p["gia_niem_yet"].apply(lambda x: f"{float(x):,.0f} đ" if pd.notnull(x) else "")

    st.dataframe(df_p, width='stretch')

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### ⚖️ **Khung Chính Sách Chiết Khấu & Phân Quyền Phê Duyệt**")
    st.markdown("""
    | Quy mô đơn hàng (VNĐ) | Trần chiết khấu NVKD tự quyết | Thẩm quyền phê duyệt vượt mức |
    |---|---|---|
    | **Dưới 100 triệu** | Tối đa **5.0%** | Trưởng phòng Kinh doanh |
    | **100 triệu – 300 triệu** | Tối đa **8.0%** | Trưởng phòng Kinh doanh |
    | **300 triệu – 1 tỷ** | Tối đa **10.0%** | Trưởng phòng Kinh doanh |
    | **Trên 1 tỷ hoặc CK > 15%** | Tối đa **10.0%** | **Ban Giám Đốc** |
    """)
