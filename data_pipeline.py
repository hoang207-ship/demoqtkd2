import io
import re
import datetime
import uuid
from typing import Dict, Any, Tuple, List, Optional
import pandas as pd
import requests
from schema_mapper import AutoSchemaMapper, normalize_column_name, remove_vietnamese_accents


# ==============================================================================
# HÀM LÀM SẠCH VÀ CHUẨN HÓA TIỀN TỆ & CHIẾN DỊCH
# ==============================================================================

def parse_currency_value(val: Any) -> Tuple[Optional[float], str, str]:
    """
    Chuẩn hóa giá trị tiền tệ từ các dạng định dạng khác nhau:
    - 1.500.000 VNĐ -> 1,500,000
    - 2.5 triệu -> 2,500,000
    - 800000 -> 800,000
    - 3.200.000 VNĐ -> 3,200,000
    - 750000 -> 750,000
    - 2.500 VNĐ -> 2,500 (Không nhầm lẫn với 2.5 triệu)
    - -500000 -> -500,000 (Cảnh báo số âm, giữ nguyên số âm)
    - 'Lỗi dữ liệu' -> None (Đưa vào Exceptions)

    Returns: (parsed_float, status, message)
    """
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None, "EXCEPTION_MISSING", "Giá trị tiền tệ bị bỏ trống"

    # Nếu đã là số nguyên hoặc số thực
    if isinstance(val, (int, float)):
        val_f = float(val)
        if val_f < 0:
            return val_f, "EXCEPTION_NEGATIVE", f"Giá trị tiền tệ bị âm: {val_f:,.0f} đ"
        return val_f, "VALID", f"{val_f:,.0f} đ"

    s = str(val).strip()
    if not s or s.lower() in ["nan", "none", "null", ""]:
        return None, "EXCEPTION_MISSING", "Giá trị tiền tệ bị bỏ trống"

    s_lower = s.lower()

    # Kiểm tra chuỗi chứa thông báo lỗi rõ ràng
    if any(err in s_lower for err in ["lỗi", "loi", "error", "#n/a", "#value!", "null"]):
        return None, "EXCEPTION_INVALID", f"Dữ liệu tiền tệ không hợp lệ: '{s}'"

    # Kiểm tra số âm
    is_negative = s.startswith("-") or (s.startswith("(") and s.endswith(")"))
    s_clean = s.lstrip("-").strip("()").strip()
    s_lower_clean = s_clean.lower()

    # 1. Nhận diện đơn vị 'triệu' / 'trieu' / 'tr'
    m_trieu = re.match(r'^([\d\.\,]+)\s*(triệu|trieu|tr)$', s_lower_clean)
    if m_trieu:
        num_str = m_trieu.group(1).replace(",", ".")
        try:
            val_float = float(num_str) * 1_000_000.0
            final_val = -val_float if is_negative else val_float
            status = "EXCEPTION_NEGATIVE" if is_negative else "AUTO_FIXED"
            desc = f"Quy đổi từ '{s}' sang {final_val:,.0f} VNĐ"
            return final_val, status, desc
        except Exception:
            return None, "EXCEPTION_INVALID", f"Không thể đọc số tiền từ '{s}'"

    # 2. Nhận diện đơn vị 'nghìn' / 'nghin' / 'ngàn' / 'k'
    m_nghin = re.match(r'^([\d\.\,]+)\s*(nghìn|nghin|ngàn|ngan|k)$', s_lower_clean)
    if m_nghin:
        num_str = m_nghin.group(1).replace(",", ".")
        try:
            val_float = float(num_str) * 1_000.0
            final_val = -val_float if is_negative else val_float
            status = "EXCEPTION_NEGATIVE" if is_negative else "AUTO_FIXED"
            desc = f"Quy đổi từ '{s}' sang {final_val:,.0f} VNĐ"
            return final_val, status, desc
        except Exception:
            return None, "EXCEPTION_INVALID", f"Không thể đọc số tiền từ '{s}'"

    # 3. Nhận diện đơn vị 'tỷ' / 'ty' / 'b'
    m_ty = re.match(r'^([\d\.\,]+)\s*(tỷ|ty|b)$', s_lower_clean)
    if m_ty:
        num_str = m_ty.group(1).replace(",", ".")
        try:
            val_float = float(num_str) * 1_000_000_000.0
            final_val = -val_float if is_negative else val_float
            status = "EXCEPTION_NEGATIVE" if is_negative else "AUTO_FIXED"
            desc = f"Quy đổi từ '{s}' sang {final_val:,.0f} VNĐ"
            return final_val, status, desc
        except Exception:
            return None, "EXCEPTION_INVALID", f"Không thể đọc số tiền từ '{s}'"

    # 4. Loại bỏ các hậu tố tiền tệ tiếng Việt: VNĐ, VND, đồng, dong, đ
    s_no_curr = re.sub(r'(vnđ|vnd|đồng|dong|đ)', '', s_lower_clean).strip()

    # Xử lý dấu phân cách hàng nghìn và thập phân
    cleaned_num = s_no_curr
    if '.' in cleaned_num and ',' in cleaned_num:
        if cleaned_num.rfind(',') > cleaned_num.rfind('.'):
            # Định dạng Việt Nam: 1.500.000,50 -> . là nghìn, , là thập phân
            cleaned_num = cleaned_num.replace('.', '').replace(',', '.')
        else:
            # Định dạng Quốc tế: 1,500,000.50 -> , là nghìn, . là thập phân
            cleaned_num = cleaned_num.replace(',', '')
    elif '.' in cleaned_num:
        parts = cleaned_num.split('.')
        # Nếu có từ 2 dấu chấm trở lên (1.500.000) hoặc 1 dấu chấm với đúng 3 chữ số sau (2.500)
        if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3):
            cleaned_num = cleaned_num.replace('.', '')
    elif ',' in cleaned_num:
        parts = cleaned_num.split(',')
        if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3):
            cleaned_num = cleaned_num.replace(',', '')
        else:
            cleaned_num = cleaned_num.replace(',', '.')

    # Bỏ khoảng cách
    cleaned_num = cleaned_num.replace(' ', '')
    try:
        val_float = float(cleaned_num)
        final_val = -val_float if is_negative else val_float
        if is_negative:
            return final_val, "EXCEPTION_NEGATIVE", f"Giá trị tiền tệ bị âm: {final_val:,.0f} VNĐ (Cần đối soát)"
        
        status = "VALID" if str(val).strip() == str(int(val_float)) else "AUTO_FIXED"
        return final_val, status, f"Chuẩn hóa tiền tệ: {final_val:,.0f} VNĐ"
    except Exception:
        return None, "EXCEPTION_INVALID", f"Không thể chuyển đổi giá trị '{s}' sang số tiền hợp lệ"


def parse_campaign_list(val: Any, raw_count: Any = None) -> Tuple[List[str], int, str, str]:
    """
    Chuẩn hóa chuỗi danh sách chiến dịch khi CÓ cột Campaign_List trong nguồn:
    - 'PG01; PG03' -> ['PG01', 'PG03']
    - 'PG01 / PG04' -> ['PG01', 'PG04']
    - 'PG01, PG02' -> ['PG01', 'PG02']
    - 'PG02' -> ['PG02']
    - 'Khong_Co' -> [] (Phân loại NO_CAMPAIGN)
    - 'Lỗi dữ liệu' -> [] (EXCEPTION)
    - Tự tính Campaign_Count = len(clean_campaigns)
    - So sánh với raw_count nếu có; nếu không khớp đưa vào Exceptions.

    Returns: (clean_campaign_ids, count, status, message)
    """
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return [], 0, "NO_CAMPAIGN", "Không có chiến dịch marketing tác động (Tự nhiên / Organic)"

    s = str(val).strip()
    if not s or s.lower() in ["nan", "none", "null", "khong_co", "khong co", "chua_co", "0", "na", "n/a", ""]:
        return [], 0, "NO_CAMPAIGN", "Không có chiến dịch marketing tác động (Tự nhiên / Organic)"

    s_lower = s.lower()
    if any(err in s_lower for err in ["lỗi", "loi", "error", "#value!", "#n/a"]):
        return [], 0, "EXCEPTION_INVALID", f"Dữ liệu chiến dịch bị lỗi định dạng: '{s}'"

    # Phân tách theo dấu ; / , | + và khoảng trắng
    raw_tokens = re.split(r'[\;\/\,\|\+\s]+', s)
    clean_campaigns = []
    for token in raw_tokens:
        clean_token = token.strip().upper()
        if clean_token and clean_token not in ["KHONG_CO", "KHONG", "CO", "NONE", "NA", "N/A"]:
            if clean_token not in clean_campaigns:
                clean_campaigns.append(clean_token)

    if not clean_campaigns:
        return [], 0, "NO_CAMPAIGN", "Không có chiến dịch hợp lệ"

    calc_count = len(clean_campaigns)

    # Kiểm tra sai lệch với Campaign_Count khai báo (nếu có)
    if raw_count is not None and not pd.isna(raw_count) and str(raw_count).strip() != "":
        try:
            r_cnt = int(float(str(raw_count).strip()))
            if r_cnt != calc_count:
                return clean_campaigns, calc_count, "EXCEPTION_COUNT_MISMATCH", (
                    f"Campaign_Count khai báo ({r_cnt}) không khớp số lượng thực tế nhận diện ({calc_count}) trong '{s}'"
                )
        except Exception:
            pass

    status = "AUTO_FIXED" if (";" in s or "/" in s or "," in s or len(clean_campaigns) > 1) else "VALID"
    desc = f"Nhận diện {calc_count} chiến dịch: {', '.join(clean_campaigns)}"
    return clean_campaigns, calc_count, status, desc


def clean_text_value(val: Any) -> Optional[str]:
    """Loại bỏ khoảng trắng thừa; trả về None nếu giá trị rỗng hoặc NaN."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = " ".join(str(val).strip().split())
    if not s or s.lower() in ["nan", "none", "null", "n/a"]:
        return None
    return s


def parse_numeric_value(val: Any, allow_percent: bool = False) -> Tuple[Optional[float], str, str]:
    """Chuẩn hóa giá trị số an toàn, không crash khi gặp chuỗi lỗi."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None, "MISSING", "Giá trị số bị bỏ trống"
    if isinstance(val, (int, float)):
        return float(val), "VALID", f"{float(val)}"

    s = " ".join(str(val).strip().split())
    if not s or s.lower() in ["nan", "none", "null", ""]:
        return None, "MISSING", "Giá trị số bị bỏ trống"

    is_pct = allow_percent and s.endswith("%")
    num_s = s[:-1].strip() if is_pct else s
    # Bỏ đơn vị chữ phổ biến ở cuối như 'ngày', 'chiếc', 'sp' nếu là số thuần phía trước
    m = re.match(r'^(-?[\d\.\,]+)', num_s)
    if not m:
        return None, "EXCEPTION_INVALID", f"Không thể chuyển '{s}' thành số"

    token = m.group(1)
    if "." in token and "," in token:
        if token.rfind(",") > token.rfind("."):
            token = token.replace(".", "").replace(",", ".")
        else:
            token = token.replace(",", "")
    elif "," in token:
        parts = token.split(",")
        if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3):
            token = token.replace(",", "")
        else:
            token = token.replace(",", ".")

    try:
        num_val = float(token)
        if is_pct:
            num_val = num_val / 100.0
        status = "VALID" if s == str(num_val) or s == str(int(num_val)) else "AUTO_FIXED"
        return num_val, status, f"Chuẩn hóa số: {num_val}"
    except Exception:
        return None, "EXCEPTION_INVALID", f"Không thể chuyển '{s}' thành số"


def parse_date_value(val: Any) -> Tuple[Optional[str], str, str]:
    """
    Chuẩn hóa ngày tháng về dạng chuẩn YYYY-MM-DD.
    Hỗ trợ Timestamp/datetime, DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY, YYYY/MM/DD.
    Không tự suy đoán ngày nếu không có dữ liệu.
    """
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None, "NOT_PROVIDED", "Ngày đặt hàng không có trong nguồn"

    if isinstance(val, (datetime.datetime, datetime.date, pd.Timestamp)):
        std_date = pd.Timestamp(val).strftime("%Y-%m-%d")
        return std_date, "VALID", f"Chuẩn hóa ngày: {std_date}"

    s = " ".join(str(val).strip().split())
    if not s or s.lower() in ["nan", "none", "null", ""]:
        return None, "NOT_PROVIDED", "Ngày đặt hàng không có trong nguồn"

    formats = [
        "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d",
        "%d.%m.%Y", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M",
        "%Y-%m-%dT%H:%M:%S", "%d/%m/%y", "%m/%d/%Y"
    ]
    for fmt in formats:
        try:
            dt = datetime.datetime.strptime(s.split(" ")[0] if " " in s and fmt == "%Y-%m-%d" else s, fmt)
            std_date = dt.strftime("%Y-%m-%d")
            status = "VALID" if s == std_date else "AUTO_FIXED"
            return std_date, status, f"Chuẩn hóa ngày: {std_date}"
        except Exception:
            continue

    return None, "EXCEPTION_INVALID_DATE", f"Định dạng ngày không hợp lệ: '{s}'"


# ==============================================================================
# BỘ DỮ LIỆU THỰC TẾ E-COMMERCE NGUỒN CỦA USER (ẢNH 1: 12 TRƯỜNG DỮ LIỆU)
# ==============================================================================

USER_ECOMMERCE_DATASET_ROWS = [
    {
        "Quantity": 2, "Unit_Price_VND": "750.000 VNĐ", "Discount": 0.10, "Sales_VND": "1.500.000 VNĐ",
        "Discount_Amount_VND": "150.000 VNĐ", "Net_Sales_VND": "1.350.000 VNĐ", "Cost_VND": "800.000 VNĐ",
        "Profit_VND": "550.000 VNĐ", "Shipping_Days": 2, "Returned": "No", "Customer_Satisfaction": 5, "Payment_Method": "COD"
    },
    {
        "Quantity": 1, "Unit_Price_VND": "2.5 triệu", "Discount": 0.05, "Sales_VND": "2.5 triệu",
        "Discount_Amount_VND": "125.000 VNĐ", "Net_Sales_VND": "2.375.000 VNĐ", "Cost_VND": "1.4 triệu",
        "Profit_VND": "975.000 VNĐ", "Shipping_Days": 3, "Returned": "No", "Customer_Satisfaction": 4, "Payment_Method": "Credit Card"
    },
    {
        "Quantity": 5, "Unit_Price_VND": 200000, "Discount": 0.00, "Sales_VND": 1000000,
        "Discount_Amount_VND": 0, "Net_Sales_VND": 1000000, "Cost_VND": 550000,
        "Profit_VND": 450000, "Shipping_Days": 1, "Returned": "Yes", "Customer_Satisfaction": 2, "Payment_Method": "Momo"
    },
    {
        "Quantity": 3, "Unit_Price_VND": "1.200.000 VNĐ", "Discount": 0.15, "Sales_VND": "3.600.000 VNĐ",
        "Discount_Amount_VND": "540.000 VNĐ", "Net_Sales_VND": "3.060.000 VNĐ", "Cost_VND": "1.800.000 VNĐ",
        "Profit_VND": "1.260.000 VNĐ", "Shipping_Days": 4, "Returned": "No", "Customer_Satisfaction": 5, "Payment_Method": "Bank Transfer"
    },
    {
        "Quantity": 1, "Unit_Price_VND": "850000", "Discount": 0.00, "Sales_VND": "850000",
        "Discount_Amount_VND": "0", "Net_Sales_VND": "850000", "Cost_VND": "450000",
        "Profit_VND": "400000", "Shipping_Days": 2, "Returned": "No", "Customer_Satisfaction": 4, "Payment_Method": "COD"
    },
    {
        "Quantity": 4, "Unit_Price_VND": "450.000 VNĐ", "Discount": 0.10, "Sales_VND": "1.800.000 VNĐ",
        "Discount_Amount_VND": "180.000 VNĐ", "Net_Sales_VND": "1.620.000 VNĐ", "Cost_VND": "950.000 VNĐ",
        "Profit_VND": "670.000 VNĐ", "Shipping_Days": 3, "Returned": "No", "Customer_Satisfaction": 4, "Payment_Method": "ShopeePay"
    },
    {
        "Quantity": 2, "Unit_Price_VND": "1.600.000 VNĐ", "Discount": 0.05, "Sales_VND": "3.200.000 VNĐ",
        "Discount_Amount_VND": "160.000 VNĐ", "Net_Sales_VND": "3.040.000 VNĐ", "Cost_VND": "1.700.000 VNĐ",
        "Profit_VND": "1.340.000 VNĐ", "Shipping_Days": 5, "Returned": "Yes", "Customer_Satisfaction": 1, "Payment_Method": "COD"
    },
    {
        "Quantity": 1, "Unit_Price_VND": "3.2 triệu", "Discount": 0.20, "Sales_VND": "3.2 triệu",
        "Discount_Amount_VND": "640.000 VNĐ", "Net_Sales_VND": "2.560.000 VNĐ", "Cost_VND": "1.5 triệu",
        "Profit_VND": "1.060.000 VNĐ", "Shipping_Days": 2, "Returned": "No", "Customer_Satisfaction": 5, "Payment_Method": "Credit Card"
    },
    {
        "Quantity": 3, "Unit_Price_VND": "600000", "Discount": 0.00, "Sales_VND": "1.800.000 VNĐ",
        "Discount_Amount_VND": "0", "Net_Sales_VND": "1.800.000 VNĐ", "Cost_VND": "1.000.000 VNĐ",
        "Profit_VND": "800.000 VNĐ", "Shipping_Days": 1, "Returned": "No", "Customer_Satisfaction": 4, "Payment_Method": "Momo"
    },
    {
        "Quantity": 2, "Unit_Price_VND": "1.1 triệu", "Discount": 0.10, "Sales_VND": "2.2 triệu",
        "Discount_Amount_VND": "220.000 VNĐ", "Net_Sales_VND": "1.980.000 VNĐ", "Cost_VND": "1.150.000 VNĐ",
        "Profit_VND": "830.000 VNĐ", "Shipping_Days": 3, "Returned": "No", "Customer_Satisfaction": 5, "Payment_Method": "Bank Transfer"
    }
]

def get_ecommerce_user_data() -> Dict[str, pd.DataFrame]:
    """Trả về bộ dữ liệu E-commerce thực tế của User với 12 cột Net_Sales, Cost, Profit."""
    return {
        "Sales_Data": pd.DataFrame(USER_ECOMMERCE_DATASET_ROWS)
    }


# ==============================================================================
# BỘ DỮ LIỆU KIỂM THỬ GIA HOA RAW MESSY TESTCASE 08
# ==============================================================================

MESSY_TESTCASE_08_ROWS = [
    {"Ma_Don_Hang": "ORD-2001", "Kenh_Ban": "Shopee", "Gia_Tri_Don": "1.500.000 VNĐ", "Danh_Sach_Chien_Dich": "PG01", "Gia_Von_COGS": "650.000 VNĐ", "Ngay_Dat_Hang": "2026-06-01"},
    {"Ma_Don_Hang": "ORD-2002", "Kenh_Ban": "Website Direct", "Gia_Tri_Don": "2.5 triệu", "Danh_Sach_Chien_Dich": "PG02; PG03", "Gia_Von_COGS": "1.1 triệu", "Ngay_Dat_Hang": "02/06/2026"},
    {"Ma_Don_Hang": "ORD-2003", "Kenh_Ban": "TikTok Shop", "Gia_Tri_Don": "800000", "Danh_Sach_Chien_Dich": "PG01 / PG04", "Gia_Von_COGS": "380000", "Ngay_Dat_Hang": "2026-06-03"},
    {"Ma_Don_Hang": "ORD-2003", "Kenh_Ban": "TikTok Shop", "Gia_Tri_Don": "800000", "Danh_Sach_Chien_Dich": "PG01 / PG04", "Gia_Von_COGS": "380000", "Ngay_Dat_Hang": "2026-06-03"},
    {"Ma_Don_Hang": "ORD-2004", "Kenh_Ban": "Lazada", "Gia_Tri_Don": "3.200.000 VNĐ", "Danh_Sach_Chien_Dich": "PG02", "Gia_Von_COGS": "1.450.000 VNĐ", "Ngay_Dat_Hang": "04-06-2026"},
    {"Ma_Don_Hang": "ORD-2005", "Kenh_Ban": "Facebook Messenger", "Gia_Tri_Don": "750000", "Danh_Sach_Chien_Dich": "Khong_Co", "Gia_Von_COGS": "320000", "Ngay_Dat_Hang": "2026-06-05"},
    {"Ma_Don_Hang": "ORD-2006", "Kenh_Ban": "Website Direct", "Gia_Tri_Don": "2.500 VNĐ", "Danh_Sach_Chien_Dich": "PG01", "Gia_Von_COGS": "1200", "Ngay_Dat_Hang": "2026-06-06"},
    {"Ma_Don_Hang": "ORD-2007", "Kenh_Ban": "Hotline", "Gia_Tri_Don": "Lỗi dữ liệu", "Danh_Sach_Chien_Dich": "PG03", "Gia_Von_COGS": "500000", "Ngay_Dat_Hang": "2026-06-07"},
    {"Ma_Don_Hang": "ORD-2008", "Kenh_Ban": "Shopee", "Gia_Tri_Don": "4.5 triệu", "Danh_Sach_Chien_Dich": "Lỗi dữ liệu", "Gia_Von_COGS": "2.0 triệu", "Ngay_Dat_Hang": "2026-06-08"},
    {"Ma_Don_Hang": "ORD-2009", "Kenh_Ban": "Website Direct", "Gia_Tri_Don": "-500000", "Danh_Sach_Chien_Dich": "PG04", "Gia_Von_COGS": "250000", "Ngay_Dat_Hang": "2026-06-09"},
    {"Ma_Don_Hang": "", "Kenh_Ban": "Shopee", "Gia_Tri_Don": "950000", "Danh_Sach_Chien_Dich": "PG05", "Gia_Von_COGS": "400000", "Ngay_Dat_Hang": "2026-06-10"},
    {"Ma_Don_Hang": "ORD-2011", "Kenh_Ban": "TikTok Shop", "Gia_Tri_Don": "1.800.000 VNĐ", "Danh_Sach_Chien_Dich": "PG01; PG02; PG05", "Gia_Von_COGS": "820.000 VNĐ", "Ngay_Dat_Hang": "2026-06-11"},
    {"Ma_Don_Hang": "ORD-2012", "Kenh_Ban": "Lazada", "Gia_Tri_Don": "3.5 triệu", "Danh_Sach_Chien_Dich": "PG03 / PG04", "Gia_Von_COGS": "1.6 triệu", "Ngay_Dat_Hang": "2026-06-12"}
]

def get_messy_testcase_08_data() -> Dict[str, pd.DataFrame]:
    """Trả về dataset thực tế GiaHoa_Raw_Messy_TestCase_08 (1 tab Untitled chứa dữ liệu lộn xộn)."""
    return {
        "Untitled": pd.DataFrame(MESSY_TESTCASE_08_ROWS)
    }


# ==============================================================================
# BỘ DỮ LIỆU MẪU CHUẨN 3 TABS (STANDARD 3-TABS DATASET)
# ==============================================================================

SAMPLE_STANDARD_TRANSACTIONS = [
    {"Order_ID": "ORD-1001", "Order_Date": "2026-06-01", "Order_Value": 1500000, "Campaign_Count": 1, "Campaign_List": "PG01", "Channel": "Shopee", "COGS": 650000},
    {"Order_ID": "ORD-1002", "Order_Date": "2026-06-02", "Order_Value": 2500000, "Campaign_Count": 2, "Campaign_List": "PG02; PG03", "Channel": "Website Direct", "COGS": 1100000},
    {"Order_ID": "ORD-1003", "Order_Date": "2026-06-03", "Order_Value": 800000, "Campaign_Count": 2, "Campaign_List": "PG01; PG04", "Channel": "TikTok Shop", "COGS": 380000},
    {"Order_ID": "ORD-1004", "Order_Date": "2026-06-04", "Order_Value": 3200000, "Campaign_Count": 1, "Campaign_List": "PG02", "Channel": "Lazada", "COGS": 1450000},
    {"Order_ID": "ORD-1005", "Order_Date": "2026-06-05", "Order_Value": 750000, "Campaign_Count": 0, "Campaign_List": "Khong_Co", "Channel": "Facebook Messenger", "COGS": 320000},
    {"Order_ID": "ORD-1006", "Order_Date": "2026-06-06", "Order_Value": 1800000, "Campaign_Count": 3, "Campaign_List": "PG01; PG02; PG05", "Channel": "TikTok Shop", "COGS": 820000},
    {"Order_ID": "ORD-1007", "Order_Date": "2026-06-07", "Order_Value": 3500000, "Campaign_Count": 2, "Campaign_List": "PG03; PG04", "Channel": "Lazada", "COGS": 1600000}
]

SAMPLE_CAMPAIGN_COSTS = [
    {"Campaign_ID": "PG01", "Campaign_Name": "Summer Mega Sale", "Channel": "Facebook Ads", "Direct_Cost": 45000000, "Overhead_Cost": 12000000, "Cost_Driver": "Order_Volume"},
    {"Campaign_ID": "PG02", "Campaign_Name": "Google Search High Intent", "Channel": "Google Ads", "Direct_Cost": 62000000, "Overhead_Cost": 15000000, "Cost_Driver": "Revenue_Weight"},
    {"Campaign_ID": "PG03", "Campaign_Name": "TikTok Influencer Brand", "Channel": "TikTok Ads", "Direct_Cost": 38000000, "Overhead_Cost": 10000000, "Cost_Driver": "Order_Volume"},
    {"Campaign_ID": "PG04", "Campaign_Name": "Email Automation VIP", "Channel": "Email Marketing", "Direct_Cost": 12000000, "Overhead_Cost": 5000000, "Cost_Driver": "Order_Volume"},
    {"Campaign_ID": "PG05", "Campaign_Name": "KOL Unboxing Review", "Channel": "YouTube", "Direct_Cost": 28000000, "Overhead_Cost": 8000000, "Cost_Driver": "Revenue_Weight"}
]

SAMPLE_RETURNS = [
    {"Return_ID": "RET-01", "Order_ID": "ORD-1001", "Return_Date": "2026-06-10", "Return_Amount": 1500000},
    {"Return_ID": "RET-02", "Order_ID": "ORD-1004", "Return_Date": "2026-06-20", "Return_Amount": 1200000},
    {"Return_ID": "RET-03", "Order_ID": "ORD-1006", "Return_Date": "2026-06-25", "Return_Amount": 600000}
]

def get_sample_marketing_data() -> Dict[str, pd.DataFrame]:
    """Trả về bộ dữ liệu mẫu chuẩn 3 tabs."""
    return {
        "Transactions": pd.DataFrame(SAMPLE_STANDARD_TRANSACTIONS),
        "Returns": pd.DataFrame(SAMPLE_RETURNS),
        "Campaign_Costs": pd.DataFrame(SAMPLE_CAMPAIGN_COSTS)
    }


def export_marketing_template_excel() -> bytes:
    """Tạo file Excel 3 sheets mẫu chuẩn để người dùng tải về tham khảo."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pd.DataFrame(SAMPLE_STANDARD_TRANSACTIONS).to_excel(writer, sheet_name='Transactions', index=False)
        pd.DataFrame(SAMPLE_RETURNS).to_excel(writer, sheet_name='Returns', index=False)
        pd.DataFrame(SAMPLE_CAMPAIGN_COSTS).to_excel(writer, sheet_name='Campaign_Costs', index=False)
    return output.getvalue()


# ==============================================================================
# BỘ NẠP DỮ LIỆU ĐA NĂNG (FLEXIBLE DATA LOADER FOR GOOGLE SHEETS & EXCEL)
# ==============================================================================

def extract_sheet_id_from_url(url: str) -> Optional[str]:
    """Trích xuất Google Sheet ID từ URL."""
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
    return match.group(1) if match else None


def load_google_sheet_flexible(sheet_url: str) -> Tuple[bool, Dict[str, pd.DataFrame], Dict[str, Any], str]:
    """
    Nạp dữ liệu từ Google Sheets linh hoạt:
    - Ưu tiên export?format=xlsx để đọc toàn bộ các tab (kể cả 9+ tab với tên tùy biến).
    - Fallback sang gviz CSV (có chống trùng lặp payload khi sheet name không tồn tại).
    """
    sheet_id = extract_sheet_id_from_url(sheet_url)
    if not sheet_id:
        return False, {}, {}, "Định dạng URL Google Sheets không hợp lệ. Vui lòng kiểm tra lại liên kết dạng: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit..."

    loaded_tabs: Dict[str, pd.DataFrame] = {}

    # 1. Thử tải toàn bộ workbook dưới dạng XLSX (đọc chính xác tên và số lượng tất cả các tab)
    xlsx_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    try:
        resp_xlsx = requests.get(xlsx_url, timeout=15)
        ctype = resp_xlsx.headers.get("Content-Type", "").lower()
        if resp_xlsx.status_code == 200 and "html" not in ctype and not resp_xlsx.content[:20].lstrip().startswith(b"<"):
            excel_file = pd.ExcelFile(io.BytesIO(resp_xlsx.content))
            for s_name in excel_file.sheet_names:
                loaded_tabs[s_name] = pd.read_excel(excel_file, sheet_name=s_name)
    except Exception:
        loaded_tabs = {}

    # 2. Fallback sang gviz CSV nếu XLSX export không khả dụng
    if not loaded_tabs:
        seen_payloads = set()
        default_csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"
        try:
            resp = requests.get(default_csv_url, timeout=12)
            if resp.status_code == 200:
                text = resp.text.strip()
                if text.startswith("<!DOCTYPE html") or "<html" in text.lower():
                    return False, {}, {}, "Google Sheet đang ở chế độ Riêng tư (Private). Vui lòng đổi quyền chia sẻ sang 'Bất kỳ ai có đường liên kết đều có thể xem'."
                seen_payloads.add(text)
                df_default = pd.read_csv(io.StringIO(text))
                if not df_default.empty:
                    loaded_tabs["Untitled"] = df_default
        except Exception as e:
            return False, {}, {}, f"Lỗi kết nối máy chủ Google Sheets: {str(e)}"

        common_tab_names = ["Transactions", "Returns", "Campaign_Costs", "Don_Hang", "Hoan_Tra", "Chi_Phi", "Sheet1", "Sales_Data"]
        for t_name in common_tab_names:
            if t_name in loaded_tabs:
                continue
            tab_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={t_name}"
            try:
                r = requests.get(tab_url, timeout=6)
                t_text = r.text.strip()
                if r.status_code == 200 and not t_text.startswith("<!DOCTYPE html") and "<html" not in t_text.lower() and t_text not in seen_payloads:
                    seen_payloads.add(t_text)
                    df_tab = pd.read_csv(io.StringIO(t_text))
                    if not df_tab.empty and len(df_tab.columns) > 1:
                        loaded_tabs[t_name] = df_tab
            except Exception:
                pass

    if not loaded_tabs or all(df.empty for df in loaded_tabs.values()):
        return False, {}, {}, "Không đọc được dữ liệu từ Google Sheets. Vui lòng đảm bảo bảng tính có ít nhất 1 tab dữ liệu và quyền chia sẻ công khai."

    # 3. Phân loại vai trò từng Tab bằng AutoSchemaMapper
    classified_tabs = classify_tabs_and_schemas(loaded_tabs)
    msg = f"Đã kết nối Google Sheets thành công! Phát hiện {len(loaded_tabs)} tab: {', '.join(loaded_tabs.keys())}."
    return True, loaded_tabs, classified_tabs, msg


def load_from_excel_flexible(file_obj) -> Tuple[bool, Dict[str, pd.DataFrame], Dict[str, Any], str]:
    """Nạp dữ liệu từ file Excel tải lên với bất kỳ tên sheet nào."""
    try:
        excel_file = pd.ExcelFile(file_obj)
        loaded_tabs = {}
        for s_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=s_name)
            if not df.empty:
                loaded_tabs[s_name] = df

        if not loaded_tabs:
            return False, {}, {}, "File Excel không có dữ liệu."

        classified_tabs = classify_tabs_and_schemas(loaded_tabs)
        msg = f"Tải file Excel thành công! Phát hiện {len(loaded_tabs)} sheet: {', '.join(loaded_tabs.keys())}."
        return True, loaded_tabs, classified_tabs, msg
    except Exception as e:
        return False, {}, {}, f"Lỗi đọc file Excel: {str(e)}"


def classify_tabs_and_schemas(raw_tabs: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """
    Sử dụng AutoSchemaMapper để phân loại từng Tab vào đúng vai trò:
    Transactions, Returns, Campaign_Costs.
    """
    mapper = AutoSchemaMapper()
    tab_roles: Dict[str, str] = {}
    role_to_tab: Dict[str, str] = {}
    mappings_by_tab: Dict[str, Any] = {}

    for tab_name, df in raw_tabs.items():
        role, score = mapper.detect_tab_type(df, tab_name=tab_name)
        tab_roles[tab_name] = role
        if role != "Unknown" and role not in role_to_tab:
            role_to_tab[role] = tab_name
        mapping_info = mapper.map_columns(list(df.columns), target_tab=role if role != "Unknown" else "Transactions")
        mappings_by_tab[tab_name] = mapping_info

    # Nếu chỉ có 1 tab duy nhất và chưa gán vai trò rõ ràng, mặc định gán Transactions
    if len(raw_tabs) == 1:
        single_tab_name = list(raw_tabs.keys())[0]
        if "Transactions" not in role_to_tab:
            role_to_tab["Transactions"] = single_tab_name
            tab_roles[single_tab_name] = "Transactions"

    has_transactions = "Transactions" in role_to_tab
    has_returns = "Returns" in role_to_tab
    has_costs = "Campaign_Costs" in role_to_tab

    return {
        "tab_roles": tab_roles,
        "role_to_tab": role_to_tab,
        "mappings_by_tab": mappings_by_tab,
        "has_transactions": has_transactions,
        "has_returns": has_returns,
        "has_costs": has_costs,
        "case_type": "CASE_A_FULL_3_TABS" if (has_transactions and has_returns and has_costs) else (
            "CASE_B_TRANSACTIONS_ONLY" if (has_transactions and not has_returns and not has_costs) else "CASE_C_PARTIAL_TABS"
        )
    }


# ==============================================================================
# DATA NORMALIZATION LAYER & RECONCILIATION ENGINE
# ==============================================================================

class DataCleaner:
    """
    Động cơ làm sạch và chuẩn hóa dữ liệu bảo toàn tuyệt đối giá trị gốc:
    - BẢO TOÀN DỮ LIỆU: Không tự chuyển giá trị thiếu thành 0. Không làm mất Net_Sales_VND, Cost_VND, Profit_VND.
    - XỬ LÝ CHIẾN DỊCH: Nếu nguồn không có Campaign_List, đánh dấu MISSING_SOURCE_DATA; không tự gán KHONG_CO.
    - ĐỐI CHIẾU TRƯỚC VÀ SAU: Kiểm tra 6 bất biến (Invariants) bắt buộc trước khi cho phép tiếp tục.
    """

    def __init__(self, raw_tabs: Dict[str, pd.DataFrame], tab_classification: Optional[Dict[str, Any]] = None):
        self.raw_tabs = {k: v.copy(deep=True) for k, v in raw_tabs.items()}
        self.run_id = f"RUN-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:4].upper()}"
        self.mapper = AutoSchemaMapper()

        if tab_classification:
            self.classification = tab_classification
        else:
            self.classification = classify_tabs_and_schemas(self.raw_tabs)

        self.normalized_data: Dict[str, Optional[pd.DataFrame]] = {}
        self.errors_log: List[Dict[str, Any]] = []
        self.exceptions_view: List[Dict[str, Any]] = []
        self.audit_log: List[Dict[str, Any]] = []
        self.tab_statuses: Dict[str, Dict[str, Any]] = {}
        self.quality_summary: Dict[str, Any] = {}
        self.mapping_summary: List[Dict[str, Any]] = []
        self.reconciliation_table: List[Dict[str, Any]] = []

    def _record_audit(
        self,
        tab: str,
        column: str,
        row_idx: int,
        record_id: str,
        raw_val: Any,
        cleaned_val: Any,
        reason: str,
        method: str,
    ) -> None:
        """Ghi nhận mọi thay đổi hoặc phát hiện trong quá trình làm sạch vào Audit Log."""
        self.audit_log.append({
            "Tab": tab,
            "Column": column,
            "Row_Index": row_idx,
            "Record_ID": str(record_id),
            "Raw_Value": "" if raw_val is None else str(raw_val),
            "Cleaned_Value": "" if cleaned_val is None else str(cleaned_val),
            "Reason": reason,
            "Method": method,
            "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    def _clean_auxiliary_tab(self, tab_name: str, raw_df: pd.DataFrame) -> Dict[str, Any]:
        """Làm sạch an toàn cho các tab phụ (không phải Transactions/Returns/Campaign_Costs)."""
        status_info = self.tab_statuses[tab_name]
        status_info["Status"] = "PROCESSING"

        if raw_df is None or raw_df.empty or len(raw_df.columns) == 0:
            status_info["Status"] = "WARNING"
            status_info["Message"] = "Tab không có dữ liệu"
            return {"cleaned_df": None, "auto_fixed": 0, "missing": 0, "duplicates": 0, "warnings": 1}

        df = raw_df.copy(deep=True)
        auto_fixed = 0
        missing_cnt = 0
        warnings_cnt = 0

        # Chuẩn hóa tên cột (bỏ khoảng trắng thừa)
        new_cols = {}
        for c in df.columns:
            clean_c = " ".join(str(c).strip().split())
            if clean_c != str(c):
                auto_fixed += 1
                self._record_audit(tab_name, str(c), 0, "HEADER", c, clean_c, "Chuẩn hóa khoảng trắng tên cột", "COLUMN_NORMALIZED")
            new_cols[c] = clean_c
        df = df.rename(columns=new_cols)

        # Kiểm tra dòng trùng lặp hoàn toàn
        dup_mask = df.duplicated(keep="first")
        dup_cnt = int(dup_mask.sum())
        if dup_cnt > 0:
            warnings_cnt += dup_cnt
            for r_idx in df.index[dup_mask]:
                self.errors_log.append({
                    "Tab": tab_name, "Row_Index": int(r_idx) + 1, "Order_ID": f"ROW-{int(r_idx) + 1}",
                    "Field": "ALL", "Error_Type": "DUPLICATE_ROW", "Severity": "MEDIUM",
                    "Raw_Value": "Duplicate row", "Action_Taken": "Giữ nguyên để đối soát",
                    "Description": f"Phát hiện dòng trùng lặp tại tab '{tab_name}' dòng {int(r_idx) + 1}"
                })

        # Chuẩn hóa giá trị từng cột theo kiểu dữ liệu
        for col in df.columns:
            col_lower = normalize_column_name(col)
            is_date_col = any(k in col_lower for k in ["ngay", "date", "time", "created"])
            for r_idx, val in df[col].items():
                if val is None or (isinstance(val, float) and pd.isna(val)) or (isinstance(val, str) and val.strip() == ""):
                    missing_cnt += 1
                    continue
                if is_date_col:
                    parsed_d, d_stat, _ = parse_date_value(val)
                    if d_stat == "AUTO_FIXED" and parsed_d is not None:
                        df.at[r_idx, col] = parsed_d
                        auto_fixed += 1
                        self._record_audit(tab_name, col, int(r_idx) + 1, f"ROW-{int(r_idx) + 1}", val, parsed_d, "Chuẩn hóa ngày tháng", "DATE_NORMALIZED")
                    elif d_stat == "EXCEPTION_INVALID_DATE":
                        warnings_cnt += 1
                        self.errors_log.append({
                            "Tab": tab_name, "Row_Index": int(r_idx) + 1, "Order_ID": f"ROW-{int(r_idx) + 1}",
                            "Field": col, "Error_Type": d_stat, "Severity": "LOW",
                            "Raw_Value": str(val), "Action_Taken": "Giữ nguyên giá trị gốc",
                            "Description": f"Định dạng ngày không hợp lệ tại '{col}': '{val}'"
                        })
                elif isinstance(val, str):
                    trimmed = " ".join(val.strip().split())
                    if trimmed != val:
                        df.at[r_idx, col] = trimmed
                        auto_fixed += 1
                        self._record_audit(tab_name, col, int(r_idx) + 1, f"ROW-{int(r_idx) + 1}", val, trimmed, "Loại bỏ khoảng trắng thừa", "TRIM_WHITESPACE")

        self.normalized_data[f"Cleaned_{tab_name}"] = df
        status_info["Cleaned_Rows"] = len(df)
        status_info["Auto_Fixed"] = auto_fixed
        status_info["Errors"] = warnings_cnt
        status_info["Status"] = "WARNING" if (warnings_cnt > 0 or missing_cnt > 0 or dup_cnt > 0) else "SUCCESS"
        status_info["Message"] = f"Đã làm sạch {len(df)} dòng (tự sửa {auto_fixed}, thiếu {missing_cnt}, trùng {dup_cnt})"
        return {"cleaned_df": df, "auto_fixed": auto_fixed, "missing": missing_cnt, "duplicates": dup_cnt, "warnings": warnings_cnt}

    def clean_and_normalize(self) -> Tuple[bool, Dict[str, Any], Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Thực thi quy trình làm sạch và chuẩn hóa toàn bộ các Tab.
        Bảo toàn toàn bộ thông tin tài chính và kiểm tra đối chiếu trước/sau.
        """
        self.errors_log = []
        self.exceptions_view = []
        self.audit_log = []
        self.mapping_summary = []
        self.reconciliation_table = []
        self.normalized_data = {
            "Normalized_Transactions": None,
            "Normalized_Returns": None,
            "Normalized_Campaign_Costs": None,
        }

        role_to_tab = self.classification.get("role_to_tab", {})
        tab_roles = self.classification.get("tab_roles", {})
        self.tab_statuses = {
            t_name: {
                "Tab": t_name,
                "Role": tab_roles.get(t_name, "Unknown"),
                "Status": "NOT_STARTED",
                "Raw_Rows": len(df) if isinstance(df, pd.DataFrame) else 0,
                "Cleaned_Rows": 0,
                "Auto_Fixed": 0,
                "Errors": 0,
                "Exceptions": 0,
                "Message": "",
            }
            for t_name, df in self.raw_tabs.items()
        }

        # Khởi tạo đầy đủ toàn bộ biến trước mọi nhánh điều kiện (tránh UnboundLocalError)
        campaign_data_status = "MISSING_SOURCE_DATA"
        auto_fixed_count = 0
        warning_count = 0
        exception_count = 0
        blocking_count = 0
        missing_fields_count = 0
        duplicate_rows_count = 0
        tabs_failed_count = 0

        sum_src_net_sales = 0.0
        sum_src_gross_sales = 0.0
        sum_src_cost = 0.0
        sum_src_profit = 0.0

        sum_norm_order_value = 0.0
        sum_norm_gross_sales = 0.0
        sum_norm_cogs = 0.0
        sum_norm_profit = 0.0

        processed_tab_names = set()

        # --- 1. LÀM SẠCH VÀ CHUẨN HÓA TRANSACTIONS ---
        if "Transactions" in role_to_tab:
            tx_tab_name = role_to_tab["Transactions"]
            processed_tab_names.add(tx_tab_name)
            tx_status = self.tab_statuses[tx_tab_name]
            tx_status["Status"] = "PROCESSING"
            try:
                raw_tx_df = self.raw_tabs[tx_tab_name].copy(deep=True)
                if raw_tx_df.empty:
                    blocking_count += 1
                    tabs_failed_count += 1
                    tx_status["Status"] = "WARNING"
                    tx_status["Message"] = "Tab Transactions không có dữ liệu"
                    self.errors_log.append({
                        "Tab": tx_tab_name, "Row_Index": 0, "Order_ID": "GLOBAL",
                        "Field": "ALL", "Error_Type": "EMPTY_TRANSACTIONS_TAB", "Severity": "CRITICAL",
                        "Raw_Value": "0 rows", "Action_Taken": "Chặn quy trình",
                        "Description": f"Tab '{tx_tab_name}' không có dòng dữ liệu nào."
                    })
                else:
                    mapping_info = self.mapper.map_columns(list(raw_tx_df.columns), target_tab="Transactions")
                    self.mapping_summary.extend(mapping_info["mapping_table"])

                    col_map = mapping_info["mapped_dict"]
                    rev_map = mapping_info["reverse_dict"]

                    has_campaign_col = mapping_info["has_campaign_col"]
                    campaign_data_status = "AVAILABLE" if has_campaign_col else "MISSING_SOURCE_DATA"

                    order_val_col = rev_map.get("Order_Value")
                    gross_sales_col = rev_map.get("Gross_Sales")
                    if not order_val_col and gross_sales_col:
                        order_val_col = gross_sales_col

                    if not order_val_col:
                        blocking_count += 1
                        tx_status["Errors"] += 1
                        self.errors_log.append({
                            "Tab": tx_tab_name, "Row_Index": 0, "Order_ID": "GLOBAL",
                            "Field": "Order_Value", "Error_Type": "MISSING_REQUIRED_COLUMN", "Severity": "CRITICAL",
                            "Raw_Value": ", ".join(map(str, raw_tx_df.columns)), "Action_Taken": "Chặn quy trình",
                            "Description": "Thiếu cột doanh thu bắt buộc (Order_Value / Net_Sales_VND / Sales_VND)."
                        })

                    cogs_col = rev_map.get("COGS")
                    profit_col = rev_map.get("Source_Profit")
                    date_col = rev_map.get("Order_Date")
                    channel_col = rev_map.get("Channel")
                    qty_col = rev_map.get("Quantity")
                    unit_price_col = rev_map.get("Unit_Price")
                    disc_col = rev_map.get("Discount_Rate")
                    disc_amount_col = rev_map.get("Discount_Amount")
                    return_status_col = rev_map.get("Return_Status")
                    ship_days_col = rev_map.get("Shipping_Days")
                    payment_col = rev_map.get("Payment_Method")
                    csat_col = rev_map.get("Customer_Satisfaction")
                    id_col = rev_map.get("Order_ID")

                    if id_col and id_col in raw_tx_df.columns:
                        val_counts = raw_tx_df[id_col].dropna().astype(str).str.strip().value_counts()
                        dup_ids = set(val_counts[val_counts > 1].index) - {"", "nan", "None", "null"}
                    else:
                        dup_ids = set()

                    norm_rows = []
                    tx_auto_fixed = 0
                    tx_errors = 0
                    tx_exceptions = 0

                    for idx, r in raw_tx_df.iterrows():
                        row_has_exception = False

                        # 1.1 Chuẩn hóa Order_ID
                        raw_id_val = r.get(id_col) if id_col else None
                        clean_order_id = clean_text_value(raw_id_val) or ""

                        if not clean_order_id:
                            clean_order_id = f"ORD-{idx+1:04d}" if not id_col else f"TEMP-UNKNOWN-{idx+1}"
                            if id_col:
                                missing_fields_count += 1
                                blocking_count += 1
                                tx_errors += 1
                                tx_exceptions += 1
                                row_has_exception = True
                                self.errors_log.append({
                                    "Tab": tx_tab_name, "Row_Index": idx+1, "Order_ID": clean_order_id,
                                    "Field": "Order_ID", "Error_Type": "MISSING_ORDER_ID", "Severity": "CRITICAL",
                                    "Raw_Value": str(raw_id_val), "Action_Taken": "Gán mã tạm thời & Đưa vào Exceptions",
                                    "Description": "Thiếu mã đơn hàng bắt buộc tại dòng dữ liệu"
                                })
                                self.exceptions_view.append({
                                    "Order_ID": clean_order_id, "Campaign_ID": "N/A", "Error_Type": "MISSING_ORDER_ID",
                                    "Raw_Value": str(raw_id_val), "Normalized_Value": clean_order_id,
                                    "Severity": "CRITICAL", "Error_Description": f"Dòng {idx+1}: Thiếu mã đơn hàng",
                                    "Proposed_Action": "Yêu cầu rà soát đối soát nguồn và bổ sung mã đơn",
                                    "Approval_Status": "PENDING_REVIEW", "Reviewer": "Chưa duyệt", "Review_Time": "N/A", "Note": ""
                                })
                                self._record_audit(tx_tab_name, "Order_ID", idx+1, clean_order_id, raw_id_val, clean_order_id, "Thiếu mã đơn hàng", "NEEDS_APPROVAL")
                        elif clean_order_id in dup_ids:
                            duplicate_rows_count += 1
                            exception_count += 1
                            tx_errors += 1
                            row_has_exception = True
                            self.errors_log.append({
                                "Tab": tx_tab_name, "Row_Index": idx+1, "Order_ID": clean_order_id,
                                "Field": "Order_ID", "Error_Type": "DUPLICATE_ORDER_ID", "Severity": "HIGH",
                                "Raw_Value": str(raw_id_val), "Action_Taken": "Không tự xóa, giữ nguyên và đưa vào Exceptions",
                                "Description": f"Mã đơn hàng {clean_order_id} bị lặp lại trong hệ thống"
                            })
                            if clean_order_id not in [e["Order_ID"] for e in self.exceptions_view if e["Error_Type"] == "DUPLICATE_ORDER_ID"]:
                                tx_exceptions += 1
                                self.exceptions_view.append({
                                    "Order_ID": clean_order_id, "Campaign_ID": "N/A", "Error_Type": "DUPLICATE_ORDER_ID",
                                    "Raw_Value": str(raw_id_val), "Normalized_Value": clean_order_id,
                                    "Severity": "HIGH", "Error_Description": f"Mã đơn {clean_order_id} bị trùng lặp trong dữ liệu",
                                    "Proposed_Action": "Trưởng phòng xác nhận bản ghi hợp lệ hoặc loại trừ đơn trùng",
                                    "Approval_Status": "PENDING_REVIEW", "Reviewer": "Chưa duyệt", "Review_Time": "N/A", "Note": ""
                                })
                                self._record_audit(tx_tab_name, "Order_ID", idx+1, clean_order_id, raw_id_val, clean_order_id, "Phát hiện trùng mã đơn", "DUPLICATE_DETECTED")

                        # 1.2 Chuẩn hóa Doanh thu thuần (Order_Value / Net Sales)
                        raw_order_val = r.get(order_val_col) if order_val_col else None
                        clean_val, val_status, val_desc = parse_currency_value(raw_order_val)
                        if val_status == "AUTO_FIXED":
                            auto_fixed_count += 1
                            tx_auto_fixed += 1
                            self._record_audit(tx_tab_name, "Order_Value", idx+1, clean_order_id, raw_order_val, clean_val, val_desc, "CURRENCY_NORMALIZED")
                        elif "EXCEPTION" in val_status:
                            if val_status == "EXCEPTION_MISSING":
                                missing_fields_count += 1
                            exception_count += 1
                            tx_errors += 1
                            tx_exceptions += 1
                            row_has_exception = True
                            self.errors_log.append({
                                "Tab": tx_tab_name, "Row_Index": idx+1, "Order_ID": clean_order_id,
                                "Field": "Order_Value", "Error_Type": val_status, "Severity": "HIGH",
                                "Raw_Value": str(raw_order_val), "Action_Taken": "Giữ nguyên giá trị và đưa vào Exceptions",
                                "Description": val_desc
                            })
                            self.exceptions_view.append({
                                "Order_ID": clean_order_id, "Campaign_ID": "N/A", "Error_Type": val_status,
                                "Raw_Value": str(raw_order_val), "Normalized_Value": str(clean_val),
                                "Severity": "HIGH", "Error_Description": f"Đơn {clean_order_id}: {val_desc}",
                                "Proposed_Action": "Xác minh giá trị doanh thu chính xác",
                                "Approval_Status": "PENDING_REVIEW", "Reviewer": "Chưa duyệt", "Review_Time": "N/A", "Note": ""
                            })
                            self._record_audit(tx_tab_name, "Order_Value", idx+1, clean_order_id, raw_order_val, clean_val, val_desc, "NEEDS_APPROVAL")

                        actual_norm_val = clean_val if clean_val is not None else 0.0
                        sum_norm_order_value += actual_norm_val
                        if clean_val is not None:
                            sum_src_net_sales += clean_val

                        # 1.3 Chuẩn hóa Doanh thu gộp (Gross_Sales)
                        raw_gross_val = r.get(gross_sales_col) if gross_sales_col else None
                        clean_gross_val, gross_stat, gross_desc = parse_currency_value(raw_gross_val) if raw_gross_val is not None else (actual_norm_val, "VALID", "")
                        if gross_stat == "AUTO_FIXED":
                            auto_fixed_count += 1
                            tx_auto_fixed += 1
                            self._record_audit(tx_tab_name, "Gross_Sales", idx+1, clean_order_id, raw_gross_val, clean_gross_val, gross_desc, "CURRENCY_NORMALIZED")
                        actual_gross = clean_gross_val if clean_gross_val is not None else actual_norm_val
                        sum_norm_gross_sales += actual_gross
                        sum_src_gross_sales += actual_gross

                        # 1.4 Chuẩn hóa Giá vốn (COGS / Cost_VND)
                        raw_cogs_val = r.get(cogs_col) if cogs_col else None
                        clean_cogs, cogs_status, cogs_desc = parse_currency_value(raw_cogs_val) if raw_cogs_val is not None else (None, "NOT_PROVIDED", "")
                        if cogs_status == "AUTO_FIXED":
                            auto_fixed_count += 1
                            tx_auto_fixed += 1
                            self._record_audit(tx_tab_name, "COGS", idx+1, clean_order_id, raw_cogs_val, clean_cogs, cogs_desc, "CURRENCY_NORMALIZED")
                        elif "EXCEPTION" in cogs_status:
                            if cogs_status == "EXCEPTION_MISSING":
                                missing_fields_count += 1
                            warning_count += 1
                            tx_errors += 1
                            self.errors_log.append({
                                "Tab": tx_tab_name, "Row_Index": idx+1, "Order_ID": clean_order_id,
                                "Field": "COGS", "Error_Type": cogs_status, "Severity": "MEDIUM",
                                "Raw_Value": str(raw_cogs_val), "Action_Taken": "Ghi nhận cảnh báo",
                                "Description": cogs_desc
                            })

                        actual_cogs = clean_cogs if clean_cogs is not None else 0.0
                        sum_norm_cogs += actual_cogs
                        if clean_cogs is not None:
                            sum_src_cost += clean_cogs

                        # 1.5 Chuẩn hóa Lợi nhuận nguồn (Source_Profit / Profit_VND)
                        raw_profit_val = r.get(profit_col) if profit_col else None
                        clean_profit, _, _ = parse_currency_value(raw_profit_val) if raw_profit_val is not None else (None, "NOT_PROVIDED", "")
                        actual_profit = clean_profit if clean_profit is not None else (actual_norm_val - actual_cogs)
                        sum_norm_profit += actual_profit
                        sum_src_profit += clean_profit if clean_profit is not None else actual_profit

                        # 1.6 Xử lý Chiến dịch (Campaign_List & Campaign_Count)
                        if not has_campaign_col:
                            clean_cmps = None
                            calc_cnt = None
                            campaign_list_str = "MISSING_SOURCE_DATA"
                        else:
                            row_raw_cmps = r.get(rev_map.get("Campaign_List"))
                            row_raw_cnt = r.get(rev_map.get("Campaign_Count"))
                            clean_cmps, calc_cnt, cmp_status, cmp_desc = parse_campaign_list(row_raw_cmps, row_raw_cnt)
                            campaign_list_str = "; ".join(clean_cmps) if clean_cmps else "KHONG_CO"

                            if cmp_status == "AUTO_FIXED":
                                auto_fixed_count += 1
                                tx_auto_fixed += 1
                                self._record_audit(tx_tab_name, "Campaign_List", idx+1, clean_order_id, row_raw_cmps, campaign_list_str, cmp_desc, "TEXT_NORMALIZED")
                            elif cmp_status == "EXCEPTION_COUNT_MISMATCH":
                                exception_count += 1
                                tx_errors += 1
                                tx_exceptions += 1
                                row_has_exception = True
                                self.errors_log.append({
                                    "Tab": tx_tab_name, "Row_Index": idx+1, "Order_ID": clean_order_id,
                                    "Field": "Campaign_Count", "Error_Type": "CAMPAIGN_COUNT_MISMATCH", "Severity": "MEDIUM",
                                    "Raw_Value": f"List: {row_raw_cmps} | Cnt: {row_raw_cnt}", "Action_Taken": "Sử dụng số đếm thực tế, đưa vào Exceptions",
                                    "Description": cmp_desc
                                })
                                self.exceptions_view.append({
                                    "Order_ID": clean_order_id, "Campaign_ID": ", ".join(clean_cmps), "Error_Type": "CAMPAIGN_COUNT_MISMATCH",
                                    "Raw_Value": f"Declared: {row_raw_cnt}", "Normalized_Value": f"Actual: {calc_cnt}",
                                    "Severity": "MEDIUM", "Error_Description": cmp_desc,
                                    "Proposed_Action": "Xác nhận số lượng chiến dịch thực tế tác động đến đơn hàng",
                                    "Approval_Status": "PENDING_REVIEW", "Reviewer": "Chưa duyệt", "Review_Time": "N/A", "Note": ""
                                })
                                self._record_audit(tx_tab_name, "Campaign_Count", idx+1, clean_order_id, row_raw_cnt, calc_cnt, cmp_desc, "NEEDS_APPROVAL")
                            elif "EXCEPTION" in cmp_status:
                                exception_count += 1
                                tx_errors += 1
                                tx_exceptions += 1
                                row_has_exception = True
                                self.errors_log.append({
                                    "Tab": tx_tab_name, "Row_Index": idx+1, "Order_ID": clean_order_id,
                                    "Field": "Campaign_List", "Error_Type": cmp_status, "Severity": "HIGH",
                                    "Raw_Value": str(row_raw_cmps), "Action_Taken": "Không phân bổ doanh thu, đưa vào Exceptions",
                                    "Description": cmp_desc
                                })
                                self.exceptions_view.append({
                                    "Order_ID": clean_order_id, "Campaign_ID": "UNKNOWN", "Error_Type": "INVALID_CAMPAIGN_FORMAT",
                                    "Raw_Value": str(row_raw_cmps), "Normalized_Value": "[]",
                                    "Severity": "HIGH", "Error_Description": cmp_desc,
                                    "Proposed_Action": "Xác định mã chiến dịch chính xác để phân bổ doanh thu",
                                    "Approval_Status": "PENDING_REVIEW", "Reviewer": "Chưa duyệt", "Review_Time": "N/A", "Note": ""
                                })
                                self._record_audit(tx_tab_name, "Campaign_List", idx+1, clean_order_id, row_raw_cmps, "[]", cmp_desc, "NEEDS_APPROVAL")

                        # 1.7 Chuẩn hóa Ngày đặt hàng (Không tự suy đoán)
                        raw_date_val = r.get(date_col) if date_col else None
                        clean_date, date_status, date_desc = parse_date_value(raw_date_val) if date_col else (None, "NOT_PROVIDED", "")
                        if date_status == "AUTO_FIXED":
                            auto_fixed_count += 1
                            tx_auto_fixed += 1
                            self._record_audit(tx_tab_name, "Order_Date", idx+1, clean_order_id, raw_date_val, clean_date, date_desc, "DATE_NORMALIZED")
                        elif date_status == "EXCEPTION_INVALID_DATE":
                            warning_count += 1
                            tx_errors += 1
                            self.errors_log.append({
                                "Tab": tx_tab_name, "Row_Index": idx+1, "Order_ID": clean_order_id,
                                "Field": "Order_Date", "Error_Type": date_status, "Severity": "MEDIUM",
                                "Raw_Value": str(raw_date_val), "Action_Taken": "Giữ nguyên Raw_Order_Date, Order_Date=None",
                                "Description": date_desc
                            })
                        elif date_col and date_status == "NOT_PROVIDED":
                            missing_fields_count += 1

                        # 1.8 Các trường thương mại mở rộng (parse an toàn, không crash)
                        raw_channel = r.get(channel_col) if channel_col else None
                        clean_channel = clean_text_value(raw_channel) or "E-Commerce Direct"
                        if isinstance(raw_channel, str) and raw_channel != raw_channel.strip():
                            auto_fixed_count += 1
                            tx_auto_fixed += 1
                            self._record_audit(tx_tab_name, "Channel", idx+1, clean_order_id, raw_channel, clean_channel, "Loại bỏ khoảng trắng thừa", "TRIM_WHITESPACE")

                        raw_qty = r.get(qty_col) if qty_col else None
                        parsed_qty, qty_stat, qty_desc = parse_numeric_value(raw_qty) if qty_col else (1.0, "VALID", "")
                        if qty_stat == "EXCEPTION_INVALID":
                            warning_count += 1
                            tx_errors += 1
                            self.errors_log.append({
                                "Tab": tx_tab_name, "Row_Index": idx+1, "Order_ID": clean_order_id,
                                "Field": "Quantity", "Error_Type": "INVALID_NUMERIC", "Severity": "LOW",
                                "Raw_Value": str(raw_qty), "Action_Taken": "Mặc định 1.0 và ghi nhật ký",
                                "Description": qty_desc
                            })
                        clean_qty = parsed_qty if parsed_qty is not None else 1.0

                        clean_unit_price, _, _ = parse_currency_value(r.get(unit_price_col)) if unit_price_col else (actual_norm_val / max(1.0, clean_qty), "VALID", "")
                        parsed_disc_rate, _, _ = parse_numeric_value(r.get(disc_col), allow_percent=True) if disc_col else (0.0, "VALID", "")
                        clean_disc_rate = parsed_disc_rate if parsed_disc_rate is not None else 0.0
                        clean_disc_amt, _, _ = parse_currency_value(r.get(disc_amount_col)) if disc_amount_col else (actual_gross - actual_norm_val, "VALID", "")

                        clean_return_status = clean_text_value(r.get(return_status_col) if return_status_col else None) or "No"
                        parsed_ship_days, _, _ = parse_numeric_value(r.get(ship_days_col)) if ship_days_col else (0.0, "VALID", "")
                        clean_ship_days = int(parsed_ship_days) if parsed_ship_days is not None else 0
                        clean_payment = clean_text_value(r.get(payment_col) if payment_col else None) or "Standard"
                        parsed_csat, _, _ = parse_numeric_value(r.get(csat_col)) if csat_col else (5.0, "VALID", "")
                        clean_csat = parsed_csat if parsed_csat is not None else 5.0

                        # 1.9 Kiểm tra quan hệ phụ thuộc giữa các trường (Gross_Sales - Discount_Amount ~ Order_Value)
                        if gross_sales_col and disc_amount_col and clean_val is not None and clean_gross_val is not None and clean_disc_amt is not None:
                            expected_net = clean_gross_val - clean_disc_amt
                            if abs(expected_net - clean_val) > 1000.0:
                                warning_count += 1
                                tx_errors += 1
                                self.errors_log.append({
                                    "Tab": tx_tab_name, "Row_Index": idx+1, "Order_ID": clean_order_id,
                                    "Field": "Order_Value / Discount_Amount", "Error_Type": "CROSS_FIELD_MISMATCH", "Severity": "MEDIUM",
                                    "Raw_Value": f"Gross={clean_gross_val:,.0f}, Disc={clean_disc_amt:,.0f}, Net={clean_val:,.0f}",
                                    "Action_Taken": "Giữ nguyên số liệu gốc và cảnh báo đối soát",
                                    "Description": f"Chênh lệch công thức Gross - Discount ({expected_net:,.0f}) != Net Sales ({clean_val:,.0f})"
                                })

                        row_dict = {
                            "Order_ID": clean_order_id,
                            "Raw_Order_ID": str(raw_id_val) if raw_id_val is not None else clean_order_id,
                            "Order_Value": actual_norm_val,
                            "Raw_Order_Value": str(raw_order_val) if raw_order_val is not None else "",
                            "Gross_Sales": actual_gross,
                            "Raw_Gross_Sales": str(raw_gross_val) if raw_gross_val is not None else "",
                            "COGS": actual_cogs,
                            "Raw_COGS": str(raw_cogs_val) if raw_cogs_val is not None else "",
                            "Source_Profit": actual_profit,
                            "Raw_Profit": str(raw_profit_val) if raw_profit_val is not None else "",
                            "Discount_Amount": clean_disc_amt if clean_disc_amt is not None else 0.0,
                            "Discount_Rate": clean_disc_rate,
                            "Quantity": clean_qty,
                            "Unit_Price": clean_unit_price if clean_unit_price is not None else actual_norm_val,
                            "Campaign_List": clean_cmps,
                            "Campaign_List_Str": campaign_list_str,
                            "Campaign_Count": calc_cnt,
                            "Campaign_Data_Status": campaign_data_status,
                            "Order_Date": clean_date,
                            "Raw_Order_Date": str(raw_date_val) if raw_date_val is not None else "",
                            "Channel": clean_channel,
                            "Return_Status": clean_return_status,
                            "Shipping_Days": clean_ship_days,
                            "Payment_Method": clean_payment,
                            "Customer_Satisfaction": clean_csat,
                            "Has_Exception": row_has_exception,
                            "Run_ID": self.run_id
                        }

                        for col in raw_tx_df.columns:
                            if col not in col_map and f"Extra_{col}" not in row_dict:
                                row_dict[f"Extra_{col}"] = r.get(col)

                        norm_rows.append(row_dict)

                    self.normalized_data["Normalized_Transactions"] = pd.DataFrame(norm_rows)

                    # --- KIỂM TRA CÁC BẤT BIẾN TÀI CHÍNH ---
                    diff_net_sales = abs(sum_src_net_sales - sum_norm_order_value)
                    diff_cogs = abs(sum_src_cost - sum_norm_cogs)
                    diff_profit = abs(sum_src_profit - sum_norm_profit)
                    diff_gross = abs(sum_src_gross_sales - sum_norm_gross_sales)
                    rows_match = (len(raw_tx_df) == len(norm_rows))

                    self.reconciliation_table = [
                        {
                            "Metric": "Tổng Doanh Thu Thuần (Net Sales)",
                            "Source_Field": str(order_val_col or "N/A"),
                            "Source_Value": f"{sum_src_net_sales:,.0f} đ",
                            "Normalized_Field": "Order_Value",
                            "Normalized_Value": f"{sum_norm_order_value:,.0f} đ",
                            "Difference": f"{diff_net_sales:.2f} đ",
                            "Status": "MATCH (Khớp 100%)" if diff_net_sales < 0.01 else "MISMATCH (Sai lệch)"
                        },
                        {
                            "Metric": "Tổng Giá Vốn (COGS / Cost)",
                            "Source_Field": str(cogs_col or "N/A"),
                            "Source_Value": f"{sum_src_cost:,.0f} đ" if cogs_col else "Chưa có cột Cost",
                            "Normalized_Field": "COGS",
                            "Normalized_Value": f"{sum_norm_cogs:,.0f} đ",
                            "Difference": f"{diff_cogs:.2f} đ",
                            "Status": "MATCH (Khớp 100%)" if diff_cogs < 0.01 else "MISMATCH (Sai lệch)"
                        },
                        {
                            "Metric": "Tổng Lợi Nhuận Gộp (Profit)",
                            "Source_Field": str(profit_col or "N/A"),
                            "Source_Value": f"{sum_src_profit:,.0f} đ" if profit_col else f"{sum_norm_profit:,.0f} đ (Tính từ Net-COGS)",
                            "Normalized_Field": "Source_Profit",
                            "Normalized_Value": f"{sum_norm_profit:,.0f} đ",
                            "Difference": f"{diff_profit:.2f} đ",
                            "Status": "MATCH (Khớp 100%)" if diff_profit < 0.01 else "MISMATCH (Sai lệch)"
                        },
                        {
                            "Metric": "Tổng Doanh Thu Trước Giảm (Gross Sales)",
                            "Source_Field": str(gross_sales_col or "N/A"),
                            "Source_Value": f"{sum_src_gross_sales:,.0f} đ" if gross_sales_col else "N/A",
                            "Normalized_Field": "Gross_Sales",
                            "Normalized_Value": f"{sum_norm_gross_sales:,.0f} đ",
                            "Difference": f"{diff_gross:.2f} đ",
                            "Status": "MATCH (Khớp 100%)" if diff_gross < 0.01 else "MISMATCH (Sai lệch)"
                        },
                        {
                            "Metric": "Tổng Số Bản Ghi (Record Count)",
                            "Source_Field": "Raw Records Count",
                            "Source_Value": f"{len(raw_tx_df)} dòng",
                            "Normalized_Field": "Normalized Records Count",
                            "Normalized_Value": f"{len(norm_rows)} dòng",
                            "Difference": f"{len(raw_tx_df) - len(norm_rows)} dòng",
                            "Status": "MATCH (Khớp 100%)" if rows_match else "MISMATCH (Mất bản ghi)"
                        }
                    ]

                    if sum_src_net_sales > 0 and sum_norm_order_value == 0:
                        blocking_count += 1
                        tx_errors += 1
                        self.errors_log.append({
                            "Tab": tx_tab_name, "Row_Index": 0, "Order_ID": "GLOBAL",
                            "Field": "Order_Value", "Error_Type": "DATA_NORMALIZATION_VALUE_LOSS", "Severity": "CRITICAL",
                            "Raw_Value": f"{sum_src_net_sales:,.0f}", "Action_Taken": "Chặn quy trình",
                            "Description": "Lỗi nghiêm trọng: Dữ liệu nguồn có doanh thu nhưng Order_Value sau chuẩn hóa bằng 0!"
                        })

                    if sum_src_cost > 0 and sum_norm_cogs == 0:
                        blocking_count += 1
                        tx_errors += 1
                        self.errors_log.append({
                            "Tab": tx_tab_name, "Row_Index": 0, "Order_ID": "GLOBAL",
                            "Field": "COGS", "Error_Type": "DATA_NORMALIZATION_COST_LOSS", "Severity": "CRITICAL",
                            "Raw_Value": f"{sum_src_cost:,.0f}", "Action_Taken": "Chặn quy trình",
                            "Description": "Lỗi nghiêm trọng: Dữ liệu nguồn có giá vốn nhưng COGS sau chuẩn hóa bằng 0!"
                        })

                    tx_status["Cleaned_Rows"] = len(norm_rows)
                    tx_status["Auto_Fixed"] = tx_auto_fixed
                    tx_status["Errors"] = tx_errors
                    tx_status["Exceptions"] = tx_exceptions
                    if blocking_count > 0:
                        tx_status["Status"] = "FAILED"
                    elif tx_exceptions > 0:
                        tx_status["Status"] = "NEEDS_APPROVAL"
                    elif tx_errors > 0:
                        tx_status["Status"] = "WARNING"
                    else:
                        tx_status["Status"] = "SUCCESS"
                    tx_status["Message"] = f"Chuẩn hóa {len(norm_rows)} giao dịch (tự sửa {tx_auto_fixed}, ngoại lệ {tx_exceptions})"
            except Exception as exc:
                blocking_count += 1
                tabs_failed_count += 1
                tx_status["Status"] = "FAILED"
                tx_status["Errors"] += 1
                tx_status["Message"] = f"Lỗi xử lý tab '{tx_tab_name}': {exc}"
                self.errors_log.append({
                    "Tab": tx_tab_name, "Row_Index": 0, "Order_ID": "GLOBAL",
                    "Field": "ALL", "Error_Type": "TAB_PROCESSING_ERROR", "Severity": "CRITICAL",
                    "Raw_Value": "", "Action_Taken": "Ghi nhận lỗi tab và tiếp tục các tab độc lập",
                    "Description": f"Lỗi khi xử lý tab '{tx_tab_name}': {exc}"
                })
        else:
            blocking_count += 1
            self.errors_log.append({
                "Tab": "GLOBAL", "Row_Index": 0, "Order_ID": "GLOBAL",
                "Field": "Transactions", "Error_Type": "MISSING_TRANSACTIONS_TAB", "Severity": "CRITICAL",
                "Raw_Value": ", ".join(self.raw_tabs.keys()), "Action_Taken": "Chặn quy trình",
                "Description": "Không nhận diện được tab Transactions (thiếu cột doanh thu như Order_Value / Net_Sales_VND / Sales_VND)."
            })

        # --- 2. LÀM SẠCH VÀ CHUẨN HÓA RETURNS (NẾU CÓ) ---
        if "Returns" in role_to_tab:
            ret_tab_name = role_to_tab["Returns"]
            processed_tab_names.add(ret_tab_name)
            ret_status = self.tab_statuses[ret_tab_name]
            ret_status["Status"] = "PROCESSING"
            try:
                raw_ret_df = self.raw_tabs[ret_tab_name].copy(deep=True)
                if raw_ret_df.empty:
                    warning_count += 1
                    ret_status["Status"] = "WARNING"
                    ret_status["Message"] = "Tab Returns không có dữ liệu"
                    self.normalized_data["Normalized_Returns"] = None
                else:
                    mapping_ret = self.mapper.map_columns(list(raw_ret_df.columns), target_tab="Returns")
                    self.mapping_summary.extend(mapping_ret["mapping_table"])
                    rev_ret_map = mapping_ret["reverse_dict"]

                    norm_ret_rows = []
                    ret_auto_fixed = 0
                    ret_errors = 0
                    for idx, r in raw_ret_df.iterrows():
                        r_id_raw = r.get(rev_ret_map.get("Return_ID", "Return_ID"))
                        r_oid_raw = r.get(rev_ret_map.get("Return_Order_ID", rev_ret_map.get("Order_ID", "Order_ID")))
                        r_id = clean_text_value(r_id_raw) or f"RET-{idx+1:04d}"
                        r_oid = clean_text_value(r_oid_raw) or ""
                        if not r_oid:
                            missing_fields_count += 1
                            warning_count += 1
                            ret_errors += 1
                        r_val_raw = r.get(rev_ret_map.get("Return_Value", "Return_Value"))
                        r_date_raw = r.get(rev_ret_map.get("Return_Date", "Return_Date"))

                        clean_ret_val, ret_val_stat, ret_val_desc = parse_currency_value(r_val_raw)
                        if ret_val_stat == "AUTO_FIXED":
                            auto_fixed_count += 1
                            ret_auto_fixed += 1
                            self._record_audit(ret_tab_name, "Return_Amount", idx+1, r_id, r_val_raw, clean_ret_val, ret_val_desc, "CURRENCY_NORMALIZED")
                        clean_ret_date, ret_date_stat, ret_date_desc = parse_date_value(r_date_raw)
                        if ret_date_stat == "AUTO_FIXED":
                            auto_fixed_count += 1
                            ret_auto_fixed += 1
                            self._record_audit(ret_tab_name, "Return_Date", idx+1, r_id, r_date_raw, clean_ret_date, ret_date_desc, "DATE_NORMALIZED")

                        norm_ret_rows.append({
                            "Return_ID": r_id,
                            "Order_ID": r_oid,
                            "Return_Amount": clean_ret_val if clean_ret_val is not None else 0.0,
                            "Raw_Return_Amount": "" if r_val_raw is None else str(r_val_raw),
                            "Return_Date": clean_ret_date,
                            "Raw_Return_Date": "" if r_date_raw is None else str(r_date_raw),
                            "Run_ID": self.run_id
                        })
                    self.normalized_data["Normalized_Returns"] = pd.DataFrame(norm_ret_rows)
                    ret_status["Cleaned_Rows"] = len(norm_ret_rows)
                    ret_status["Auto_Fixed"] = ret_auto_fixed
                    ret_status["Errors"] = ret_errors
                    ret_status["Status"] = "WARNING" if ret_errors > 0 else "SUCCESS"
                    ret_status["Message"] = f"Chuẩn hóa {len(norm_ret_rows)} phiếu hoàn trả"
            except Exception as exc:
                tabs_failed_count += 1
                ret_status["Status"] = "FAILED"
                ret_status["Errors"] += 1
                ret_status["Message"] = f"Lỗi xử lý tab '{ret_tab_name}': {exc}"
                self.errors_log.append({
                    "Tab": ret_tab_name, "Row_Index": 0, "Order_ID": "GLOBAL",
                    "Field": "ALL", "Error_Type": "TAB_PROCESSING_ERROR", "Severity": "HIGH",
                    "Raw_Value": "", "Action_Taken": "Bỏ qua tab lỗi, tiếp tục tab khác",
                    "Description": f"Lỗi khi xử lý tab '{ret_tab_name}': {exc}"
                })
        else:
            self.normalized_data["Normalized_Returns"] = None

        # --- 3. LÀM SẠCH VÀ CHUẨN HÓA CAMPAIGN_COSTS (NẾU CÓ) ---
        if "Campaign_Costs" in role_to_tab:
            cost_tab_name = role_to_tab["Campaign_Costs"]
            processed_tab_names.add(cost_tab_name)
            cost_status = self.tab_statuses[cost_tab_name]
            cost_status["Status"] = "PROCESSING"
            try:
                raw_cost_df = self.raw_tabs[cost_tab_name].copy(deep=True)
                if raw_cost_df.empty:
                    warning_count += 1
                    cost_status["Status"] = "WARNING"
                    cost_status["Message"] = "Tab Campaign_Costs không có dữ liệu"
                    self.normalized_data["Normalized_Campaign_Costs"] = None
                else:
                    mapping_cost = self.mapper.map_columns(list(raw_cost_df.columns), target_tab="Campaign_Costs")
                    self.mapping_summary.extend(mapping_cost["mapping_table"])
                    rev_cost_map = mapping_cost["reverse_dict"]

                    norm_cost_rows = []
                    cost_auto_fixed = 0
                    cost_errors = 0
                    for idx, r in raw_cost_df.iterrows():
                        cid_raw = r.get(rev_cost_map.get("Campaign_ID", "Campaign_ID"))
                        cid = (clean_text_value(cid_raw) or f"CMP-{idx+1:03d}").upper()
                        cname = clean_text_value(r.get(rev_cost_map.get("Campaign_Name", "Campaign_Name"))) or cid
                        channel = clean_text_value(r.get(rev_cost_map.get("Channel", "Channel"))) or "General"
                        d_cost_raw = r.get(rev_cost_map.get("Direct_Cost", "Direct_Cost"))
                        ovh_cost_raw = r.get(rev_cost_map.get("Overhead_Cost", "Overhead_Cost"))
                        driver = clean_text_value(r.get(rev_cost_map.get("Cost_Driver", "Cost_Driver"))) or "Order_Volume"

                        clean_d_cost, d_stat, d_desc = parse_currency_value(d_cost_raw)
                        if d_stat == "AUTO_FIXED":
                            auto_fixed_count += 1
                            cost_auto_fixed += 1
                            self._record_audit(cost_tab_name, "Direct_Cost", idx+1, cid, d_cost_raw, clean_d_cost, d_desc, "CURRENCY_NORMALIZED")
                        clean_ovh_cost, o_stat, o_desc = parse_currency_value(ovh_cost_raw)
                        if o_stat == "AUTO_FIXED":
                            auto_fixed_count += 1
                            cost_auto_fixed += 1
                            self._record_audit(cost_tab_name, "Overhead_Cost", idx+1, cid, ovh_cost_raw, clean_ovh_cost, o_desc, "CURRENCY_NORMALIZED")

                        norm_cost_rows.append({
                            "Campaign_ID": cid,
                            "Campaign_Name": cname,
                            "Channel": channel,
                            "Direct_Cost": clean_d_cost if clean_d_cost is not None else 0.0,
                            "Raw_Direct_Cost": "" if d_cost_raw is None else str(d_cost_raw),
                            "Overhead_Cost": clean_ovh_cost if clean_ovh_cost is not None else 0.0,
                            "Raw_Overhead_Cost": "" if ovh_cost_raw is None else str(ovh_cost_raw),
                            "Cost_Driver": driver,
                            "Run_ID": self.run_id
                        })
                    self.normalized_data["Normalized_Campaign_Costs"] = pd.DataFrame(norm_cost_rows)
                    cost_status["Cleaned_Rows"] = len(norm_cost_rows)
                    cost_status["Auto_Fixed"] = cost_auto_fixed
                    cost_status["Errors"] = cost_errors
                    cost_status["Status"] = "WARNING" if cost_errors > 0 else "SUCCESS"
                    cost_status["Message"] = f"Chuẩn hóa {len(norm_cost_rows)} chiến dịch chi phí"
            except Exception as exc:
                tabs_failed_count += 1
                cost_status["Status"] = "FAILED"
                cost_status["Errors"] += 1
                cost_status["Message"] = f"Lỗi xử lý tab '{cost_tab_name}': {exc}"
                self.errors_log.append({
                    "Tab": cost_tab_name, "Row_Index": 0, "Order_ID": "GLOBAL",
                    "Field": "ALL", "Error_Type": "TAB_PROCESSING_ERROR", "Severity": "HIGH",
                    "Raw_Value": "", "Action_Taken": "Bỏ qua tab lỗi, tiếp tục tab khác",
                    "Description": f"Lỗi khi xử lý tab '{cost_tab_name}': {exc}"
                })
        else:
            self.normalized_data["Normalized_Campaign_Costs"] = None

        # --- 4. LÀM SẠCH TẤT CẢ CÁC TAB PHỤ CÒN LẠI (VD: BẢNG 9 TAB GOOGLE SHEETS) ---
        for t_name, raw_df in self.raw_tabs.items():
            if t_name in processed_tab_names:
                continue
            processed_tab_names.add(t_name)
            try:
                aux_res = self._clean_auxiliary_tab(t_name, raw_df)
                auto_fixed_count += aux_res["auto_fixed"]
                missing_fields_count += aux_res["missing"]
                duplicate_rows_count += aux_res["duplicates"]
                warning_count += aux_res["warnings"]
            except Exception as exc:
                tabs_failed_count += 1
                self.tab_statuses[t_name]["Status"] = "FAILED"
                self.tab_statuses[t_name]["Errors"] += 1
                self.tab_statuses[t_name]["Message"] = f"Lỗi xử lý tab '{t_name}': {exc}"
                self.errors_log.append({
                    "Tab": t_name, "Row_Index": 0, "Order_ID": "GLOBAL",
                    "Field": "ALL", "Error_Type": "TAB_PROCESSING_ERROR", "Severity": "HIGH",
                    "Raw_Value": "", "Action_Taken": "Ghi nhận lỗi tab độc lập",
                    "Description": f"Lỗi khi xử lý tab '{t_name}': {exc}"
                })

        # --- 5. TỔNG HỢP QUALITY SUMMARY ---
        total_records = sum(len(df) for df in self.raw_tabs.values() if isinstance(df, pd.DataFrame))
        norm_tx_df = self.normalized_data.get("Normalized_Transactions")
        clean_tx_count = len(norm_tx_df) if norm_tx_df is not None else 0
        total_normalized_rows = sum(
            len(df) for df in self.normalized_data.values() if isinstance(df, pd.DataFrame)
        )
        total_issues = len(self.errors_log)
        critical_issues = len([e for e in self.errors_log if e["Severity"] == "CRITICAL"])

        quality_score = max(0.0, min(100.0, 100.0 - (total_issues / max(1, total_records)) * 40.0))
        can_proceed = (critical_issues == 0 and clean_tx_count > 0 and sum_norm_order_value > 0)

        if not can_proceed or critical_issues > 0 or tabs_failed_count > 0:
            overall_status = "FAILED"
        elif len(self.exceptions_view) > 0:
            overall_status = "NEEDS_APPROVAL"
        elif total_issues > 0 or missing_fields_count > 0 or duplicate_rows_count > 0 or any(
            s["Status"] == "WARNING" for s in self.tab_statuses.values()
        ):
            overall_status = "WARNING"
        else:
            overall_status = "SUCCESS"

        self.quality_summary = {
            "Run_ID": self.run_id,
            "Total_Tabs_Count": len(self.raw_tabs),
            "Tabs_Processed_Count": len(processed_tab_names),
            "Tabs_Failed_Count": tabs_failed_count,
            "Total_Raw_Records": total_records,
            "Normalized_Transactions_Count": clean_tx_count,
            "Normalized_Rows_Count": total_normalized_rows,
            "Auto_Fixed_Count": auto_fixed_count,
            "Warning_Count": warning_count,
            "Missing_Fields_Count": missing_fields_count,
            "Duplicate_Rows_Count": duplicate_rows_count,
            "Total_Errors_Count": total_issues,
            "Exceptions_Count": len(self.exceptions_view),
            "Critical_Issues_Count": critical_issues,
            "Audit_Log_Count": len(self.audit_log),
            "Data_Quality_Score": round(quality_score, 1),
            "Can_Proceed_Process": can_proceed,
            "Status": overall_status,
            "Has_Returns_Data": self.normalized_data["Normalized_Returns"] is not None,
            "Has_Costs_Data": self.normalized_data["Normalized_Campaign_Costs"] is not None,
            "Campaign_Data_Status": campaign_data_status,
            "Total_Net_Sales_VND": sum_norm_order_value,
            "Total_COGS_VND": sum_norm_cogs,
            "Total_Profit_VND": sum_norm_profit,
            "Reconciliation_Table": self.reconciliation_table,
            "Tab_Statuses": list(self.tab_statuses.values()),
            "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        return can_proceed, self.normalized_data, self.quality_summary, self.errors_log, self.exceptions_view

    def export_cleaned_data_excel(self) -> bytes:
        """Xuất bộ dữ liệu sạch đã chuẩn hóa và Audit Log ra file Excel để người dùng tải về."""
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for key, df in self.normalized_data.items():
                if isinstance(df, pd.DataFrame) and not df.empty:
                    sheet_name = str(key)[:31]
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            if self.audit_log:
                pd.DataFrame(self.audit_log).to_excel(writer, sheet_name='Audit_Log', index=False)
            if self.errors_log:
                pd.DataFrame(self.errors_log).to_excel(writer, sheet_name='Errors_Log', index=False)
            if self.reconciliation_table:
                pd.DataFrame(self.reconciliation_table).to_excel(writer, sheet_name='Audit_Reconciliation', index=False)
            if self.errors_log:
                pd.DataFrame(self.errors_log).to_excel(writer, sheet_name='Cleaning_Audit_Log', index=False)
            if self.mapping_summary:
                pd.DataFrame(self.mapping_summary).to_excel(writer, sheet_name='Schema_Mapping_Table', index=False)
        return output.getvalue()
