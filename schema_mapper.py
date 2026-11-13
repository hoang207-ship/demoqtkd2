import re
import unicodedata
from difflib import SequenceMatcher
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd


def remove_vietnamese_accents(text: str) -> str:
    """Loại bỏ dấu tiếng Việt và chuẩn hóa thành chuỗi ASCII không dấu."""
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    text = text.replace("đ", "d").replace("Đ", "D")
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c))


def normalize_column_name(col_name: str) -> str:
    """Chuẩn hóa tên cột: bỏ dấu, chữ thường, bỏ ký tự đặc biệt, chuẩn hóa khoảng trắng."""
    no_accent = remove_vietnamese_accents(str(col_name).strip().lower())
    clean_str = re.sub(r'[\_\-\.\:\;\/\(\)\[\]\{\}\#\$\%\^\&\*\+\=]+', ' ', no_accent)
    return " ".join(clean_str.split())


# ==============================================================================
# TỪ ĐIỂN TÊN CỘT TƯƠNG ĐƯƠNG TOÀN DIỆN (COMPREHENSIVE SCHEMA SYNONYMS)
# ==============================================================================
SCHEMA_SYNONYMS: Dict[str, Dict[str, Any]] = {
    # --- 1. Tab Transactions (Bán hàng & Đơn hàng) ---
    "Order_ID": {
        "required": False, # Có thể tự tạo mã đơn nếu nguồn là bảng log
        "tab": "Transactions",
        "priority": 10,
        "description": "Mã đơn hàng duy nhất",
        "synonyms": [
            "ma don hang", "ma don", "don hang", "order id", "orderid", "order no",
            "order number", "id don hang", "so hoa don", "so don hang", "ma dh",
            "order", "ma hoa don", "order code", "transaction id", "trans id", "id"
        ],
        "keywords": ["ma", "don"]
    },
    "Order_Date": {
        "required": False,
        "tab": "Transactions",
        "priority": 8,
        "description": "Ngày đặt hàng",
        "synonyms": [
            "ngay dat hang", "ngay dat", "ngay ban", "ngay don", "ngay tao",
            "ngay", "order date", "orderdate", "date", "created at", "trans date",
            "thoi gian dat", "thoi gian", "ngay giao dich"
        ],
        "keywords": ["ngay", "date"]
    },
    "Order_Value": {
        "required": True,
        "tab": "Transactions",
        "priority": 10,
        "description": "Giá trị đơn hàng / Doanh thu thuần (Net Sales sau giảm giá)",
        "synonyms": [
            "net sales vnd", "net sales", "netsales", "net sales amount", "net revenue",
            "doanh thu thuan", "doanh thu sau giam gia", "doanh thu sau chiet khau",
            "gia tri don", "gia tri don hang", "doanh thu don", "doanh thu", "gia tri",
            "tong tien", "thanh tien", "tien hang", "order value", "ordervalue",
            "amount", "order amount", "total amount", "tong gia tri", "revenue"
        ],
        "keywords": ["net", "sales", "gia", "tri", "don"]
    },
    "Gross_Sales": {
        "required": False,
        "tab": "Transactions",
        "priority": 9,
        "description": "Doanh thu gộp trước giảm giá (Sales VND)",
        "synonyms": [
            "sales vnd", "sales", "gross sales", "gross sales vnd", "gross revenue",
            "doanh thu truoc giam gia", "tong doanh thu goc", "tien hang truoc chiet khau",
            "gia niem yet tong", "tong doanh thu"
        ],
        "keywords": ["sales", "gross"]
    },
    "COGS": {
        "required": False,
        "tab": "Transactions",
        "priority": 9,
        "description": "Giá vốn hàng bán (Cost VND / Cost of Goods Sold)",
        "synonyms": [
            "cost vnd", "cost", "total cost vnd", "cost price", "cogs", "gia von",
            "gia von cogs", "gia von hang ban", "cost of goods sold", "cost of goods",
            "von hang", "tien von", "chi phi gia von", "chi phi von"
        ],
        "keywords": ["cost", "gia", "von"]
    },
    "Source_Profit": {
        "required": False,
        "tab": "Transactions",
        "priority": 9,
        "description": "Lợi nhuận từ nguồn (Profit VND) để đối chiếu",
        "synonyms": [
            "profit vnd", "profit", "net profit vnd", "gross profit", "loi nhuan",
            "loi nhuan gop", "loi nhuan thuan", "tien lai", "lai gop"
        ],
        "keywords": ["profit", "loi", "nhuan"]
    },
    "Discount_Amount": {
        "required": False,
        "tab": "Transactions",
        "priority": 8,
        "description": "Số tiền giảm giá (Discount Amount VND)",
        "synonyms": [
            "discount amount vnd", "discount amount", "tien giam gia", "tien chiet khau",
            "so tien giam gia", "giam gia vnd", "discount vnd"
        ],
        "keywords": ["discount", "amount", "giam", "gia"]
    },
    "Discount_Rate": {
        "required": False,
        "tab": "Transactions",
        "priority": 8,
        "description": "Tỷ lệ giảm giá (Discount Rate / %)",
        "synonyms": [
            "discount", "discount rate", "ty le giam gia", "ty le chiet khau",
            "chiet khau", "giam gia", "phan tram giam"
        ],
        "keywords": ["discount", "chiet", "khau"]
    },
    "Quantity": {
        "required": False,
        "tab": "Transactions",
        "priority": 8,
        "description": "Số lượng sản phẩm bán",
        "synonyms": [
            "quantity", "so luong", "qty", "sl", "so luong ban", "so luong sp"
        ],
        "keywords": ["quantity", "so", "luong"]
    },
    "Unit_Price": {
        "required": False,
        "tab": "Transactions",
        "priority": 8,
        "description": "Đơn giá sản phẩm (Unit Price VND)",
        "synonyms": [
            "unit price vnd", "unit price", "don gia", "gia don vi", "gia ban le",
            "gia san pham", "price vnd", "price"
        ],
        "keywords": ["unit", "price", "don", "gia"]
    },
    "Channel": {
        "required": False,
        "tab": "Transactions",
        "priority": 7,
        "description": "Kênh bán hàng",
        "synonyms": [
            "kenh ban", "kenh", "kenh phan phoi", "channel", "sales channel",
            "source", "nguon", "nguon don", "kenh ban hang"
        ],
        "keywords": ["kenh", "channel"]
    },
    "Campaign_List": {
        "required": False, # Không bắt buộc, nếu thiếu sẽ đánh dấu MISSING_SOURCE_DATA
        "tab": "Transactions",
        "priority": 9,
        "description": "Danh sách mã chiến dịch marketing tác động",
        "synonyms": [
            "danh sach chien dich", "danh sach ma chien dich", "ma chien dich",
            "chien dich", "campaign list", "campaigns", "campaign ids", "campaign id",
            "ds chien dich", "chien dich marketing", "campaign", "campaigns list",
            "cac chien dich", "ma cd", "marketing campaign"
        ],
        "keywords": ["chien", "dich", "campaign"]
    },
    "Campaign_Count": {
        "required": False,
        "tab": "Transactions",
        "priority": 7,
        "description": "Số lượng chiến dịch tác động đến đơn hàng",
        "synonyms": [
            "so luong chien dich", "so chien dich", "campaign count", "count campaign",
            "so cd", "sl chien dich", "sl cd", "tong chien dich", "campaign cnt"
        ],
        "keywords": ["so", "luong", "chien", "dich"]
    },
    "Return_Status": {
        "required": False,
        "tab": "Transactions",
        "priority": 8,
        "description": "Trạng thái đơn hàng có bị hoàn trả hay không (Returned)",
        "synonyms": [
            "returned", "is returned", "hoan tra", "tra hang", "da hoan tra",
            "tinh trang hoan", "trang thai hoan tra", "co tra hang khong"
        ],
        "keywords": ["returned", "hoan", "tra"]
    },
    "Shipping_Days": {
        "required": False,
        "tab": "Transactions",
        "priority": 7,
        "description": "Số ngày giao hàng / Lead time",
        "synonyms": [
            "shipping days", "so ngay giao", "thoi gian giao", "delivery days",
            "so ngay van chuyen", "lead time", "ngay ship"
        ],
        "keywords": ["shipping", "days", "giao", "hang"]
    },
    "Payment_Method": {
        "required": False,
        "tab": "Transactions",
        "priority": 7,
        "description": "Phương thức thanh toán",
        "synonyms": [
            "payment method", "phuong thuc thanh toan", "hinh thuc thanh toan",
            "thanh toan", "payment type", "kenh thanh toan"
        ],
        "keywords": ["payment", "method", "thanh", "toan"]
    },
    "Customer_Satisfaction": {
        "required": False,
        "tab": "Transactions",
        "priority": 7,
        "description": "Độ hài lòng của khách hàng (CSAT / Rating)",
        "synonyms": [
            "customer satisfaction", "csat", "danh gia khach hang", "do hai long",
            "rating", "diem danh gia", "diem csat"
        ],
        "keywords": ["customer", "satisfaction", "hai", "long"]
    },

    # --- 2. Tab Returns ---
    "Return_ID": {
        "required": True,
        "tab": "Returns",
        "priority": 10,
        "description": "Mã phiếu hoàn trả duy nhất",
        "synonyms": [
            "ma hoan tra", "ma hoan", "ma tra hang", "return id", "returnid",
            "refund id", "ma don hoan", "phieu hoan", "so phieu hoan"
        ],
        "keywords": ["ma", "hoan"]
    },
    "Return_Order_ID": {
        "required": True,
        "tab": "Returns",
        "priority": 10,
        "description": "Mã đơn hàng gốc bị hoàn trả",
        "synonyms": [
            "ma don hang", "ma don goc", "ma don hoan", "order id", "orderid",
            "return order id", "original order id"
        ],
        "keywords": ["ma", "don"]
    },
    "Return_Date": {
        "required": False,
        "tab": "Returns",
        "priority": 8,
        "description": "Ngày tiếp nhận hoàn trả",
        "synonyms": [
            "ngay hoan tra", "ngay hoan", "ngay tra", "return date", "returndate",
            "refund date", "ngay nhan hoan"
        ],
        "keywords": ["ngay", "hoan"]
    },
    "Return_Value": {
        "required": True,
        "tab": "Returns",
        "priority": 10,
        "description": "Số tiền hoàn trả",
        "synonyms": [
            "gia tri hoan tra", "gia tri hoan", "tien hoan", "so tien hoan",
            "return amount", "return value", "refund amount", "refund value",
            "tong tien hoan", "so tien tra"
        ],
        "keywords": ["gia", "tri", "hoan"]
    },

    # --- 3. Tab Campaign_Costs ---
    "Campaign_ID": {
        "required": True,
        "tab": "Campaign_Costs",
        "priority": 10,
        "description": "Mã định danh chiến dịch",
        "synonyms": [
            "ma chien dich", "ma cd", "campaign id", "campaignid", "id chien dich",
            "code chien dich"
        ],
        "keywords": ["ma", "chien", "dich"]
    },
    "Campaign_Name": {
        "required": False,
        "tab": "Campaign_Costs",
        "priority": 8,
        "description": "Tên gọi của chiến dịch",
        "synonyms": [
            "ten chien dich", "ten cd", "campaign name", "campaignname", "ten chuong trinh",
            "campaign title"
        ],
        "keywords": ["ten", "chien", "dich"]
    },
    "Direct_Cost": {
        "required": True,
        "tab": "Campaign_Costs",
        "priority": 10,
        "description": "Chi phí trực tiếp (Ad spend, booking...)",
        "synonyms": [
            "chi phi truc tiep", "cp truc tiep", "direct cost", "direct costs",
            "chi phi chay ads", "ad spend", "ngan sach truc tiep", "tien quang cao"
        ],
        "keywords": ["chi", "phi", "truc", "tiep"]
    },
    "Overhead_Cost": {
        "required": False,
        "tab": "Campaign_Costs",
        "priority": 8,
        "description": "Chi phí gián tiếp / chi phí chung",
        "synonyms": [
            "chi phi chung", "cp chung", "chi phi gian tiep", "overhead cost",
            "overhead", "indirect cost", "chi phi quan ly", "chi phi van hanh"
        ],
        "keywords": ["chi", "phi", "chung"]
    },
    "Cost_Driver": {
        "required": False,
        "tab": "Campaign_Costs",
        "priority": 7,
        "description": "Tiêu thức phân bổ chi phí ABC",
        "synonyms": [
            "tieu thuc phan bo", "cost driver", "tieu chi phan bo", "driver",
            "phuong thuc phan bo"
        ],
        "keywords": ["tieu", "thuc", "driver"]
    },
    "Budget": {
        "required": False,
        "tab": "Campaign_Costs",
        "priority": 7,
        "description": "Ngân sách dự kiến được phê duyệt",
        "synonyms": [
            "ngan sach", "budget", "ngan sach du kien", "dinh muc ngan sach"
        ],
        "keywords": ["ngan", "sach"]
    }
}


class AutoSchemaMapper:
    """
    Module tự động nhận diện và ánh xạ cột dữ liệu tiếng Việt / tiếng Anh về Schema chuẩn nội bộ.
    Bảo toàn toàn bộ thông tin nguồn, không làm mất dữ liệu.
    """

    def __init__(self, confidence_threshold: float = 0.75):
        self.confidence_threshold = confidence_threshold

    def calculate_match_score(self, raw_col_norm: str, standard_field: str, field_meta: Dict[str, Any]) -> Tuple[float, str]:
        """
        Tính điểm tin cậy (0.0 đến 1.0) khi so khớp cột thô với trường chuẩn.
        """
        synonyms = field_meta.get("synonyms", [])
        keywords = field_meta.get("keywords", [])

        # 1. So khớp chính xác tuyệt đối
        if raw_col_norm in synonyms:
            return 1.0, "EXACT_SYNONYM"

        # 2. Xử lý trường hợp đặc biệt:
        # Nếu là Net_Sales_VND -> Ưu tiên tuyệt đối cho Order_Value (hoặc Net_Sales)
        if "net sales" in raw_col_norm:
            if standard_field == "Order_Value":
                return 0.98, "SPECIFIC_NET_SALES_MATCH"
            elif standard_field == "Gross_Sales":
                return 0.4, "LOWER_MATCH"

        # Nếu là Sales_VND (không có chữ 'net') -> Ưu tiên Gross_Sales (nếu Order_Value đã có Net_Sales)
        if "sales" in raw_col_norm and "net" not in raw_col_norm:
            if standard_field == "Gross_Sales":
                return 0.95, "SPECIFIC_GROSS_SALES_MATCH"
            elif standard_field == "Order_Value":
                return 0.90, "SALES_AS_ORDER_VALUE_FALLBACK"

        # Nếu là Cost_VND -> Ưu tiên COGS
        if "cost" in raw_col_norm and "overhead" not in raw_col_norm and "direct" not in raw_col_norm:
            if standard_field == "COGS":
                return 0.98, "SPECIFIC_COST_MATCH"

        # Nếu là Profit_VND -> Ưu tiên Source_Profit
        if "profit" in raw_col_norm:
            if standard_field == "Source_Profit":
                return 0.98, "SPECIFIC_PROFIT_MATCH"

        # 3. So khớp nếu chuỗi thô chứa hoàn toàn một từ đồng nghĩa quan trọng
        for syn in synonyms:
            if syn in raw_col_norm or raw_col_norm in syn:
                ratio = len(syn) / max(len(raw_col_norm), len(syn))
                if ratio >= 0.65:
                    return 0.90, "SUBSTRING_SYNONYM"

        # 4. So khớp bộ từ khóa (keywords)
        matched_kw = sum(1 for kw in keywords if kw in raw_col_norm.split())
        if keywords and matched_kw == len(keywords):
            return 0.88, "ALL_KEYWORDS_MATCH"

        # 5. So khớp mờ (Fuzzy matching)
        best_sim = 0.0
        for syn in synonyms:
            sim = SequenceMatcher(None, raw_col_norm, syn).ratio()
            if sim > best_sim:
                best_sim = sim

        if best_sim >= self.confidence_threshold:
            return round(best_sim, 2), "FUZZY_MATCH"

        return 0.0, "NO_MATCH"

    def map_columns(self, raw_columns: List[str], target_tab: str = "Transactions") -> Dict[str, Any]:
        """
        Nhận danh sách cột thô và thực hiện ánh xạ tối ưu về Schema của Tab mục tiêu.
        Đảm bảo nguyên tắc: Không tự ánh xạ 2 cột khác nhau vào cùng 1 trường chuẩn.
        """
        candidate_fields = {
            f_name: meta for f_name, meta in SCHEMA_SYNONYMS.items()
            if meta.get("tab") == target_tab or target_tab == "ALL"
        }

        # Lưu ma trận điểm: (raw_col, standard_field, score, match_type)
        scores = []
        for raw_col in raw_columns:
            raw_norm = normalize_column_name(raw_col)
            for std_field, meta in candidate_fields.items():
                score, m_type = self.calculate_match_score(raw_norm, std_field, meta)
                if score >= self.confidence_threshold:
                    scores.append({
                        "raw_col": raw_col,
                        "raw_norm": raw_norm,
                        "std_field": std_field,
                        "score": score,
                        "priority": meta.get("priority", 5),
                        "match_type": m_type
                    })

        # Sắp xếp theo score giảm dần, sau đó theo priority giảm dần
        scores.sort(key=lambda x: (x["score"], x["priority"]), reverse=True)

        mapped_fields: Dict[str, str] = {}  # {raw_col: std_field}
        used_std_fields: set = set()
        used_raw_cols: set = set()
        mapping_details = []

        for item in scores:
            raw_c = item["raw_col"]
            std_f = item["std_field"]
            if raw_c not in used_raw_cols and std_f not in used_std_fields:
                used_raw_cols.add(raw_c)
                used_std_fields.add(std_f)
                mapped_fields[raw_c] = std_f
                mapping_details.append({
                    "Original_Column": raw_c,
                    "Normalized_Name": item["raw_norm"],
                    "Mapped_Field": std_f,
                    "Field_Description": candidate_fields[std_f]["description"],
                    "Confidence_Score": f"{item['score'] * 100:.0f}%",
                    "Match_Type": item["match_type"],
                    "Status": "CONFIRMED" if item["score"] >= 0.85 else "NEEDS_REVIEW"
                })

        unmapped_cols = [c for c in raw_columns if c not in used_raw_cols]
        required_missing = [
            f for f, meta in candidate_fields.items()
            if meta.get("required") and f not in used_std_fields
        ]

        # Kiểm tra xem có cột doanh thu nào được ánh xạ hay không (Order_Value hoặc Gross_Sales)
        has_revenue_col = ("Order_Value" in used_std_fields or "Gross_Sales" in used_std_fields)

        return {
            "mapped_dict": mapped_fields,          # {raw_col_name: standard_field_name}
            "reverse_dict": {v: k for k, v in mapped_fields.items()}, # {standard_field_name: raw_col_name}
            "mapping_table": mapping_details,     # Danh sách chi tiết hiển thị UI
            "unmapped_columns": unmapped_cols,    # Cột không ánh xạ được
            "missing_required": required_missing, # Cột bắt buộc bị thiếu
            "has_revenue_col": has_revenue_col,
            "has_campaign_col": "Campaign_List" in used_std_fields,
            "is_valid": has_revenue_col # Hợp lệ nếu có ít nhất trường doanh thu để phân tích
        }

    def detect_tab_type(self, df: pd.DataFrame, tab_name: str = "") -> Tuple[str, float]:
        """
        Tự động nhận diện vai trò của Tab (Transactions, Returns, Campaign_Costs)
        dựa trên cấu trúc cột và tên tab, không phụ thuộc tên tab cứng nhắc.
        """
        cols = list(df.columns)
        tab_norm = normalize_column_name(tab_name)

        # 1. Điểm tên Tab gợi ý
        name_hint_trans = 0.3 if any(k in tab_norm for k in ["trans", "don hang", "order", "ban hang", "raw", "messy", "testcase", "sales"]) else 0.0
        name_hint_ret = 0.4 if any(k in tab_norm for k in ["return", "hoan tra", "tra hang", "refund"]) else 0.0
        name_hint_cost = 0.4 if any(k in tab_norm for k in ["cost", "chi phi", "campaign", "chien dich", "ngan sach"]) else 0.0

        # 2. Ánh xạ thử với từng schema
        trans_res = self.map_columns(cols, target_tab="Transactions")
        ret_res = self.map_columns(cols, target_tab="Returns")
        cost_res = self.map_columns(cols, target_tab="Campaign_Costs")

        trans_score = (len(trans_res["mapped_dict"]) / max(1, len(cols))) + name_hint_trans
        ret_score = (len(ret_res["mapped_dict"]) / max(1, len(cols))) + name_hint_ret
        cost_score = (len(cost_res["mapped_dict"]) / max(1, len(cols))) + name_hint_cost

        rev_mapped = trans_res["reverse_dict"]
        # Nếu có Order_Value hoặc Net_Sales_VND hoặc Sales_VND thì là Transactions
        if "Order_Value" in rev_mapped or "Gross_Sales" in rev_mapped:
            trans_score += 2.0

        if "Return_ID" in ret_res["reverse_dict"] and "Return_Value" in ret_res["reverse_dict"]:
            ret_score += 2.0

        if "Campaign_ID" in cost_res["reverse_dict"] and "Direct_Cost" in cost_res["reverse_dict"]:
            cost_score += 2.0

        scores = [
            ("Transactions", trans_score),
            ("Returns", ret_score),
            ("Campaign_Costs", cost_score)
        ]
        scores.sort(key=lambda x: x[1], reverse=True)
        best_type, best_score = scores[0]

        if best_score < 0.5:
            return "Unknown", best_score
        return best_type, best_score
