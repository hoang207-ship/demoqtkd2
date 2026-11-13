import os
import io
import pandas as pd
import requests

# Dữ liệu mặc định chuẩn cho Công ty Minh An
DEFAULT_PRODUCTS = [
    {
        "ma_sp": "SRV-DELL-R750",
        "ten_sp": "Máy chủ Dell PowerEdge R750 2x Xeon Silver 4314, 64GB RAM, 2x 960GB SSD",
        "danh_muc": "Máy chủ & Lưu trữ",
        "don_vi": "Bộ",
        "gia_niem_yet": 135000000,
        "ton_kho": 4,
        "lead_time_co_hang": 2,
        "lead_time_nhap_hang": 14,
        "ghi_chu": "Bảo hành chính hãng 36 tháng ProSupport"
    },
    {
        "ma_sp": "SW-CISCO-C9200L",
        "ten_sp": "Switch Cisco Catalyst C9200L-24P-4G-E 24 cổng PoE+, 4x 1G SFP",
        "danh_muc": "Thiết bị mạng",
        "don_vi": "Cái",
        "gia_niem_yet": 42000000,
        "ton_kho": 10,
        "lead_time_co_hang": 1,
        "lead_time_nhap_hang": 21,
        "ghi_chu": "Bao gồm Network Essentials License"
    },
    {
        "ma_sp": "FW-FORTI-80F",
        "ten_sp": "Tường lửa Fortinet FortiGate FG-80F Hardware Plus 1 Yr UTP",
        "danh_muc": "Bảo mật & An ninh mạng",
        "don_vi": "Cái",
        "gia_niem_yet": 48500000,
        "ton_kho": 6,
        "lead_time_co_hang": 1,
        "lead_time_nhap_hang": 14,
        "ghi_chu": "Bao gồm license bảo mật UTP 1 năm"
    },
    {
        "ma_sp": "LAP-DELL-L5540",
        "ten_sp": "Laptop Doanh nghiệp Dell Latitude 5540 Core i7-1365U, 16GB, 512GB SSD",
        "danh_muc": "Thiết bị văn phòng",
        "don_vi": "Chiếc",
        "gia_niem_yet": 24500000,
        "ton_kho": 25,
        "lead_time_co_hang": 1,
        "lead_time_nhap_hang": 7,
        "ghi_chu": "Windows 11 Pro, bảo hành tận nơi 3 năm"
    },
    {
        "ma_sp": "LAP-THINK-T14",
        "ten_sp": "Laptop Lenovo ThinkPad T14 Gen 4 Core i5-1335U, 16GB RAM, 512GB SSD",
        "danh_muc": "Thiết bị văn phòng",
        "don_vi": "Chiếc",
        "gia_niem_yet": 26800000,
        "ton_kho": 3,
        "lead_time_co_hang": 1,
        "lead_time_nhap_hang": 10,
        "ghi_chu": "Tiêu chuẩn độ bền quân đội MIL-STD-810H"
    },
    {
        "ma_sp": "MON-DELL-U2724D",
        "ten_sp": "Màn hình chuyên nghiệp Dell UltraSharp U2724D 27 inch 2K 120Hz IPS Black",
        "danh_muc": "Thiết bị văn phòng",
        "don_vi": "Chiếc",
        "gia_niem_yet": 11500000,
        "ton_kho": 18,
        "lead_time_co_hang": 1,
        "lead_time_nhap_hang": 5,
        "ghi_chu": "Chuẩn màu đồ họa 98% DCI-P3"
    },
    {
        "ma_sp": "RACK-APC-42U",
        "ten_sp": "Tủ mạng Server APC NetShelter SX 42U 600mm x 1070mm Enclosure",
        "danh_muc": "Hạ tầng Trung tâm dữ liệu",
        "don_vi": "Tủ",
        "gia_niem_yet": 32000000,
        "ton_kho": 2,
        "lead_time_co_hang": 2,
        "lead_time_nhap_hang": 15,
        "ghi_chu": "Đầy đủ phụ kiện thanh PDU & quản lý cáp"
    },
    {
        "ma_sp": "UPS-APC-3KVA",
        "ten_sp": "Bộ lưu điện APC Smart-UPS SRT 3000VA RM 230V 2U On-Line",
        "danh_muc": "Hạ tầng Trung tâm dữ liệu",
        "don_vi": "Bộ",
        "gia_niem_yet": 54000000,
        "ton_kho": 5,
        "lead_time_co_hang": 1,
        "lead_time_nhap_hang": 14,
        "ghi_chu": "Thời gian lưu điện mở rộng"
    },
    {
        "ma_sp": "SRV-IMPL-01",
        "ten_sp": "Dịch vụ Triển khai, Cài đặt Hệ thống Mạng & Máy chủ Doanh nghiệp",
        "danh_muc": "Dịch vụ Công nghệ",
        "don_vi": "Gói",
        "gia_niem_yet": 15000000,
        "ton_kho": 999,
        "lead_time_co_hang": 1,
        "lead_time_nhap_hang": 2,
        "ghi_chu": "Kỹ sư chuyên môn của Minh An thực hiện onsite"
    },
    {
        "ma_sp": "SRV-CARE-12M",
        "ten_sp": "Gói Bảo trì & Hỗ trợ Kỹ thuật Minh An Care 24/7 (12 tháng)",
        "danh_muc": "Dịch vụ Công nghệ",
        "don_vi": "Gói",
        "gia_niem_yet": 18000000,
        "ton_kho": 999,
        "lead_time_co_hang": 1,
        "lead_time_nhap_hang": 1,
        "ghi_chu": "Cam kết phản hồi trong 2 giờ"
    }
]

# 6 Nhân viên Kinh doanh của Minh An
DEFAULT_SALES_REPS = [
    {
        "ma_nv": "NVKD01",
        "ho_ten": "Nguyễn Văn An",
        "email": "an.nv@minhan.com.vn",
        "chuyen_mon": "Tài chính, Ngân hàng & Doanh nghiệp Lớn (Enterprise)",
        "so_deal_hien_tai": 14
    },
    {
        "ma_nv": "NVKD02",
        "ho_ten": "Trần Thị Bích",
        "email": "bich.tt@minhan.com.vn",
        "chuyen_mon": "Bán lẻ, Chuỗi cung ứng & Thương mại Điện tử",
        "so_deal_hien_tai": 12
    },
    {
        "ma_nv": "NVKD03",
        "ho_ten": "Lê Hoàng Long",
        "email": "long.lh@minhan.com.vn",
        "chuyen_mon": "Công nghệ Thông tin, Phần mềm & Viễn thông",
        "so_deal_hien_tai": 16
    },
    {
        "ma_nv": "NVKD04",
        "ho_ten": "Phạm Thu Hà",
        "email": "ha.pt@minhan.com.vn",
        "chuyen_mon": "Y tế, Giáo dục & Dược phẩm",
        "so_deal_hien_tai": 11
    },
    {
        "ma_nv": "NVKD05",
        "ho_ten": "Vũ Minh Đức",
        "email": "duc.vm@minhan.com.vn",
        "chuyen_mon": "Sản xuất, Khu công nghiệp & Doanh nghiệp FDI",
        "so_deal_hien_tai": 15
    },
    {
        "ma_nv": "NVKD06",
        "ho_ten": "Đỗ Quỳnh Trang",
        "email": "trang.dq@minhan.com.vn",
        "chuyen_mon": "Doanh nghiệp Vừa và Nhỏ (SMB) & Khách hàng mới",
        "so_deal_hien_tai": 13
    }
]

# Chính sách chiết khấu và thẩm quyền phê duyệt
DISCOUNT_POLICY = {
    "tiers": [
        {"min_val": 0, "max_val": 100_000_000, "max_nvkd_discount": 5.0, "desc": "Đơn hàng dưới 100 triệu: NVKD tối đa 5%"},
        {"min_val": 100_000_000, "max_val": 300_000_000, "max_nvkd_discount": 8.0, "desc": "Đơn hàng 100 - 300 triệu: NVKD tối đa 8%"},
        {"min_val": 300_000_000, "max_val": 1_000_000_000, "max_nvkd_discount": 10.0, "desc": "Đơn hàng 300 triệu - 1 tỷ: NVKD tối đa 10%"},
        {"min_val": 1_000_000_000, "max_val": float("inf"), "max_nvkd_discount": 10.0, "desc": "Đơn hàng trên 1 tỷ: NVKD tối đa 10%"}
    ],
    "manager_approval_threshold": 10.0,   # Trên 10% cần Trưởng phòng duyệt
    "director_approval_threshold": 15.0  # Trên 15% cần Ban Giám đốc duyệt
}

def get_default_products_df() -> pd.DataFrame:
    """Trả về DataFrame danh mục sản phẩm chuẩn."""
    return pd.DataFrame(DEFAULT_PRODUCTS)

def get_default_sales_reps_df() -> pd.DataFrame:
    """Trả về DataFrame danh sách 6 NVKD."""
    return pd.DataFrame(DEFAULT_SALES_REPS)

def convert_google_sheet_url_to_csv(url: str) -> str:
    """
    Chuyển đổi URL Google Sheets thông thường thành URL tải CSV trực tiếp.
    Ví dụ: https://docs.google.com/spreadsheets/d/SHEET_ID/edit#gid=0 -> export?format=csv
    """
    url = url.strip()
    if "docs.google.com/spreadsheets/d/" in url:
        parts = url.split("/spreadsheets/d/")
        sheet_id = parts[1].split("/")[0]
        # Tìm gid nếu có
        gid = "0"
        if "gid=" in url:
            gid = url.split("gid=")[1].split("&")[0].split("#")[0]
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    return url

def load_data_from_source(uploaded_file=None, gsheet_url=None) -> tuple[pd.DataFrame, str]:
    """
    Tải dữ liệu từ File Upload (Excel/CSV) hoặc Link Google Sheet.
    Nếu không có, fallback về dữ liệu mẫu Minh An.
    """
    if uploaded_file is not None:
        try:
            filename = uploaded_file.name.lower()
            if filename.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
                return df, f"Đã tải thành công từ file CSV: {uploaded_file.name}"
            elif filename.endswith((".xlsx", ".xls")):
                df = pd.read_excel(uploaded_file)
                return df, f"Đã tải thành công từ file Excel: {uploaded_file.name}"
            else:
                return get_default_products_df(), "Định dạng file không hỗ trợ, sử dụng dữ liệu mặc định."
        except Exception as e:
            return get_default_products_df(), f"Lỗi đọc file ({e}), chuyển sang dữ liệu mặc định."
    
    if gsheet_url and gsheet_url.strip():
        try:
            csv_export_url = convert_google_sheet_url_to_csv(gsheet_url)
            df = pd.read_csv(csv_export_url)
            return df, f"Đã đồng bộ thành công dữ liệu từ Google Sheet!"
        except Exception as e:
            return get_default_products_df(), f"Không thể tải từ Google Sheet ({e}). Đảm bảo sheet được chia sẻ quyền xem công khai (Anyone with link can view). Sử dụng dữ liệu mặc định."

    return get_default_products_df(), "Đang sử dụng Dữ liệu Danh mục Sản phẩm & Bảng giá chuẩn của Công ty Minh An."

def export_template_excel() -> bytes:
    """Tạo file Excel mẫu để người dùng tải về tham khảo hoặc chỉnh sửa."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        get_default_products_df().to_excel(writer, sheet_name='Danh_Muc_San_Pham', index=False)
        get_default_sales_reps_df().to_excel(writer, sheet_name='Nhan_Vien_Kinh_Doanh', index=False)
        # Bảng chính sách
        policy_data = [
            {"Gia_Tri_Tu": 0, "Gia_Tri_Den": 100000000, "Chiet_Khau_NVKD_Max_%": 5.0, "Tham_Quyen": "NVKD"},
            {"Gia_Tri_Tu": 100000000, "Gia_Tri_Den": 300000000, "Chiet_Khau_NVKD_Max_%": 8.0, "Tham_Quyen": "NVKD"},
            {"Gia_Tri_Tu": 300000000, "Gia_Tri_Den": 1000000000, "Chiet_Khau_NVKD_Max_%": 10.0, "Tham_Quyen": "NVKD"},
            {"Gia_Tri_Tu": 0, "Gia_Tri_Den": 1000000000, "Chiet_Khau_NVKD_Max_%": 15.0, "Tham_Quyen": "Trưởng phòng Kinh doanh"},
            {"Gia_Tri_Tu": 1000000000, "Gia_Tri_Den": 9999999999, "Chiet_Khau_NVKD_Max_%": 20.0, "Tham_Quyen": "Ban Giám Đốc"}
        ]
        pd.DataFrame(policy_data).to_excel(writer, sheet_name='Chinh_Sach_Chiet_Khau', index=False)
    return output.getvalue()

