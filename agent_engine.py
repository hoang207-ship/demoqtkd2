import os
import re
import json
import datetime
import random
from typing import Dict, Any, List, Optional
import pandas as pd
from data_manager import DISCOUNT_POLICY, DEFAULT_SALES_REPS

DEFAULT_GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6Kq4RQiPtlzO-LaBEpQWvKZDQBUuEnxtsfmTeC-XuCFWg")

class SalesAgentWorkflow:
    def __init__(self, products_df: pd.DataFrame, sales_reps_df: pd.DataFrame, gemini_api_key: Optional[str] = None):
        self.products_df = products_df
        self.sales_reps_df = sales_reps_df
        self.gemini_api_key = gemini_api_key or DEFAULT_GEMINI_KEY
        self.client = None
        self.ai_model_name = "gemini-3.5-flash-lite"
        self.is_gemini_active = False

        if self.gemini_api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.gemini_api_key)
                self.is_gemini_active = True
            except Exception:
                self.client = None
                self.is_gemini_active = False

    def process_request(self, raw_text: str, auto_assign_rep: Optional[str] = None) -> Dict[str, Any]:
        """
        Thực hiện toàn bộ 7 bước quy trình xử lý cơ hội bán hàng B2B theo sơ đồ Minh An Company.
        """
        result = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "raw_input": raw_text,
            "engine_used": f"Gemini AI ({self.ai_model_name})" if self.is_gemini_active else "Rule-based Smart Parser",
            "steps": {}
        }

        # BƯỚC 1: TIẾP NHẬN YÊU CẦU
        step1_info = self._step1_intake(raw_text)
        result["steps"]["step1"] = step1_info

        # BƯỚC 2: PHÂN LOẠI & KIỂM TRA THÔNG TIN (Có đủ thông tin?)
        step2_info = self._step2_classify_and_verify(step1_info["parsed_data"])
        result["steps"]["step2"] = step2_info

        # Nếu THIẾU THÔNG TIN -> Nhánh: Yêu cầu KH làm rõ / bổ sung
        if not step2_info["is_complete"]:
            clarification_draft = self._generate_clarification_email(step1_info["parsed_data"], step2_info["missing_fields"])
            result["steps"]["clarification"] = {
                "triggered": True,
                "reason": "Thiếu thông tin quan trọng để thẩm định và lập báo giá",
                "missing_fields": step2_info["missing_fields"],
                "draft_email": clarification_draft,
                "next_action": "Chờ khách hàng làm rõ / bổ sung để tiếp tục tiếp nhận lại"
            }
            result["final_status"] = "CHỜ_BỔ_SUNG_THÔNG_TIN"
            return result

        # BƯỚC 3: TẠO HỒ SƠ CƠ HỘI & GẮN NGƯỜI PHỤ TRÁCH
        step3_info = self._step3_create_opportunity(step1_info["parsed_data"], auto_assign_rep)
        result["steps"]["step3"] = step3_info

        # BƯỚC 4: THẨM ĐỊNH TỒN KHO & GIÁ
        step4_info = self._step4_inventory_and_pricing(step1_info["parsed_data"]["items"], step1_info["parsed_data"].get("deadline_days"))
        result["steps"]["step4"] = step4_info

        # BƯỚC 5: LẬP BÁO GIÁ & DỰ THẢO ĐỀ XUẤT
        step5_info = self._step5_quote_and_proposal(step4_info, step1_info["parsed_data"])
        result["steps"]["step5"] = step5_info

        # BƯỚC 6: CÓ VƯỢT THẨM QUYỀN / CẦN CHIẾT KHẤU ĐẶC BIỆT?
        step6_info = self._step6_approval_check(step4_info, step5_info, step1_info["parsed_data"])
        result["steps"]["step6"] = step6_info

        # BƯỚC 7: KẾT THÚC: CẬP NHẬT & THEO DÕI
        step7_info = self._step7_finalize_and_track(step3_info, step4_info, step5_info, step6_info, step1_info["parsed_data"])
        result["steps"]["step7"] = step7_info

        result["final_status"] = "CHỜ_DUYỆT_TRƯỞNG_PHÒNG" if step6_info["requires_approval"] else "ĐÃ_LẬP_ĐỀ_XUẤT_CHUẨN"
        return result

    # --- Step 1 ---
    def _step1_intake(self, text: str) -> Dict[str, Any]:
        """Tiếp nhận văn bản yêu cầu và bóc tách thông tin ban đầu (kết hợp Gemini AI & Regex)."""
        parsed = None
        used_ai = False

        if self.is_gemini_active:
            parsed = self._extract_request_data_with_gemini(text)
            if parsed:
                used_ai = True

        if not parsed:
            parsed = self._extract_request_data_regex(text)

        return {
            "name": "Bắt đầu: Tiếp nhận yêu cầu",
            "status": "SUCCESS",
            "used_ai": used_ai,
            "parsed_data": parsed,
            "intake_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }

    # --- Step 2 ---
    def _step2_classify_and_verify(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Phân loại & Kiểm tra thông tin: Đánh giá có đủ thông tin để định giá và giao hàng không."""
        missing = []

        # 1. Kiểm tra công ty / khách hàng
        c_name = parsed.get("customer_name")
        if not c_name or c_name in ["Chưa rõ", "Khách hàng Doanh nghiệp"] or len(str(c_name).strip()) < 3:
            missing.append("Tên doanh nghiệp / Khách hàng liên hệ cụ thể")

        # 2. Kiểm tra danh mục sản phẩm & số lượng
        items = parsed.get("items", [])
        if not items:
            missing.append("Danh sách thiết bị / dịch vụ công nghệ cụ thể kèm số lượng")
        else:
            for it in items:
                if not it.get("qty") or int(it.get("qty", 0)) <= 0:
                    missing.append(f"Số lượng cho hạng mục '{it.get('name')}'")

        # 3. Kiểm tra ngân sách (điểm cốt lõi trong bối cảnh Minh An)
        budget = parsed.get("budget")
        if not budget or float(budget) <= 0:
            missing.append("Ngân sách dự kiến được phê duyệt của dự án (hoặc khoảng ngân sách)")

        # 4. Kiểm tra thời hạn triển khai / deadline
        deadline = parsed.get("deadline_days")
        if not deadline or int(deadline) <= 0:
            missing.append("Thời hạn triển khai / hạn chót bàn giao nghiệm thu mong muốn")

        is_complete = (len(missing) == 0)

        return {
            "name": "Phân loại & Kiểm tra thông tin",
            "is_complete": is_complete,
            "missing_fields": missing,
            "completeness_score": max(0, 100 - len(missing) * 25),
            "customer_type": parsed.get("industry", "Doanh nghiệp thương mại / Doanh nghiệp chung")
        }

    # --- Step 3 ---
    def _step3_create_opportunity(self, parsed: Dict[str, Any], assigned_rep: Optional[str] = None) -> Dict[str, Any]:
        """Tạo Hồ sơ Cơ hội & Gắn người phụ trách (1 trong 6 NVKD Minh An)."""
        opp_id = f"OPP-{datetime.datetime.now().strftime('%Y%m')}-{random.randint(1000, 9999)}"

        if assigned_rep:
            rep = self.sales_reps_df[self.sales_reps_df["ho_ten"] == assigned_rep].iloc[0].to_dict()
        else:
            # Tự động gán theo lĩnh vực hoặc load balancing (ít deal nhất)
            industry = str(parsed.get("industry", "")).lower()
            matched_rep = None
            for _, r in self.sales_reps_df.iterrows():
                chuyen_mon = r["chuyen_mon"].lower()
                if any(w in industry for w in ["ngân hàng", "tài chính", "enterprise", "bank"]) and "tài chính" in chuyen_mon:
                    matched_rep = r.to_dict()
                    break
                elif any(w in industry for w in ["bán lẻ", "f&b", "chuỗi", "retail"]) and "bán lẻ" in chuyen_mon:
                    matched_rep = r.to_dict()
                    break
                elif any(w in industry for w in ["công nghệ", "it", "phần mềm", "telecom"]) and "công nghệ" in chuyen_mon:
                    matched_rep = r.to_dict()
                    break
                elif any(w in industry for w in ["y tế", "bệnh viện", "trường học", "giáo dục"]) and "y tế" in chuyen_mon:
                    matched_rep = r.to_dict()
                    break
                elif any(w in industry for w in ["nhà máy", "sản xuất", "fdi", "kcn"]) and "sản xuất" in chuyen_mon:
                    matched_rep = r.to_dict()
                    break
            
            if not matched_rep:
                min_deals_idx = self.sales_reps_df["so_deal_hien_tai"].astype(int).idxmin()
                matched_rep = self.sales_reps_df.loc[min_deals_idx].to_dict()
            
            rep = matched_rep

        priority = "Cao" if (float(parsed.get("budget") or 0) > 300_000_000 or float(parsed.get("requested_discount") or 0) > 10) else "Trung bình"

        return {
            "name": "Tạo Hồ sơ Cơ hội & Gắn người phụ trách",
            "opp_id": opp_id,
            "customer_name": parsed.get("customer_name"),
            "contact_person": parsed.get("contact_person", "Chưa rõ"),
            "contact_email": parsed.get("contact_email", "Chưa rõ"),
            "contact_phone": parsed.get("contact_phone", "Chưa rõ"),
            "assigned_rep": rep["ho_ten"],
            "assigned_rep_email": rep["email"],
            "rep_specialty": rep["chuyen_mon"],
            "priority": priority,
            "created_date": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        }

    # --- Step 4 ---
    def _step4_inventory_and_pricing(self, items: List[Dict[str, Any]], deadline_days: int) -> Dict[str, Any]:
        """Thẩm định tồn kho & giá mới nhất với Bộ phận Vận hành."""
        verified_items = []
        overall_stock_ready = True
        max_required_lead_time = 0
        lead_time_issues = []

        for req in items:
            req_name = str(req.get("name", "")).lower()
            req_qty = int(req.get("qty", 1))

            matched_product = None
            best_score = 0
            
            for _, prod in self.products_df.iterrows():
                p_name = str(prod.get("ten_sp", "")).lower()
                p_code = str(prod.get("ma_sp", "")).lower()
                
                score = 0
                for kw in req_name.split():
                    if len(kw) > 2 and (kw in p_name or kw in p_code):
                        score += 1
                
                if score > best_score:
                    best_score = score
                    matched_product = prod.to_dict()

            if not matched_product or best_score == 0:
                matched_product = {
                    "ma_sp": "CUSTOM-IT-ITEM",
                    "ten_sp": req.get("name"),
                    "danh_muc": "Thiết bị Công nghệ Tùy chọn",
                    "don_vi": "Cái",
                    "gia_niem_yet": 20000000,
                    "ton_kho": 0,
                    "lead_time_co_hang": 2,
                    "lead_time_nhap_hang": 14,
                    "ghi_chu": "Cần Vận hành xác nhận mã chính xác"
                }

            ton_kha_dung = int(matched_product.get("ton_kho", 0))
            is_in_stock = (ton_kha_dung >= req_qty)
            
            if is_in_stock:
                item_lead_time = int(matched_product.get("lead_time_co_hang", 1))
                stock_status = f"Đủ tồn kho ({ton_kha_dung}/{req_qty})"
            else:
                overall_stock_ready = False
                item_lead_time = int(matched_product.get("lead_time_nhap_hang", 14))
                stock_status = f"Thiếu hàng tồn (Hiện có: {ton_kha_dung}, Cần: {req_qty}) - Cần nhập ({item_lead_time} ngày)"

            if item_lead_time > max_required_lead_time:
                max_required_lead_time = item_lead_time

            if deadline_days and item_lead_time > deadline_days:
                lead_time_issues.append({
                    "product": matched_product.get("ten_sp"),
                    "required_days": item_lead_time,
                    "customer_deadline": deadline_days,
                    "gap": item_lead_time - deadline_days
                })

            list_price = float(matched_product.get("gia_niem_yet", 0))
            total_list_item = list_price * req_qty

            verified_items.append({
                "req_item_name": req.get("name"),
                "matched_code": matched_product.get("ma_sp"),
                "matched_name": matched_product.get("ten_sp"),
                "unit": matched_product.get("don_vi", "Cái"),
                "qty": req_qty,
                "current_list_price": list_price,
                "total_list_price": total_list_item,
                "ton_kho": ton_kha_dung,
                "is_in_stock": is_in_stock,
                "lead_time_days": item_lead_time,
                "stock_status": stock_status
            })

        has_deadline_risk = (len(lead_time_issues) > 0)

        return {
            "name": "Thẩm định tồn kho & giá",
            "items": verified_items,
            "overall_stock_ready": overall_stock_ready,
            "max_required_lead_time": max_required_lead_time,
            "has_deadline_risk": has_deadline_risk,
            "lead_time_issues": lead_time_issues
        }

    # --- Step 5 ---
    def _step5_quote_and_proposal(self, step4_info: Dict[str, Any], parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Lập Báo giá & Dự thảo đề xuất (Áp dụng chính sách chiết khấu chuẩn)."""
        items = step4_info["items"]
        total_list_price = sum(item["total_list_price"] for item in items)

        allowed_nvkd_discount = 5.0
        for tier in DISCOUNT_POLICY["tiers"]:
            if tier["min_val"] <= total_list_price <= tier["max_val"]:
                allowed_nvkd_discount = tier["max_nvkd_discount"]
                break

        requested_discount = float(parsed.get("requested_discount") or 0.0)
        applied_discount = requested_discount if requested_discount > 0 else allowed_nvkd_discount
        discount_amount = total_list_price * (applied_discount / 100.0)
        net_amount = total_list_price - discount_amount
        vat_amount = net_amount * 0.10
        grand_total = net_amount + vat_amount

        customer_budget = float(parsed.get("budget") or 0.0)
        budget_variance = customer_budget - grand_total
        budget_match = (budget_variance >= 0)

        for item in items:
            item["discount_rate"] = applied_discount
            item["unit_price_after_discount"] = item["current_list_price"] * (1 - applied_discount / 100.0)
            item["total_after_discount"] = item["unit_price_after_discount"] * item["qty"]

        return {
            "name": "Lập Báo giá & Dự thảo đề xuất",
            "total_list_price": total_list_price,
            "allowed_nvkd_discount": allowed_nvkd_discount,
            "applied_discount": applied_discount,
            "discount_amount": discount_amount,
            "net_amount": net_amount,
            "vat_amount": vat_amount,
            "grand_total": grand_total,
            "customer_budget": customer_budget,
            "budget_match": budget_match,
            "budget_variance": budget_variance
        }

    # --- Step 6 ---
    def _step6_approval_check(self, step4_info: Dict[str, Any], step5_info: Dict[str, Any], parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Kiểm tra: Có vượt thẩm quyền / Cần chiết khấu đặc biệt?"""
        triggers = []

        applied_discount = step5_info["applied_discount"]
        allowed_nvkd_discount = step5_info["allowed_nvkd_discount"]
        if applied_discount > allowed_nvkd_discount:
            triggers.append(f"Mức chiết khấu đề nghị {applied_discount}% vượt trần thẩm quyền của NVKD ({allowed_nvkd_discount}% cho đơn hàng quy mô này).")

        if step4_info["has_deadline_risk"]:
            for issue in step4_info["lead_time_issues"]:
                triggers.append(f"Mặt hàng '{issue['product']}' cần {issue['required_days']} ngày chuẩn bị, vượt quá hạn giao cam kết của khách ({issue['customer_deadline']} ngày). Cần duyệt phương án express.")

        if not step5_info["budget_match"] and abs(step5_info["budget_variance"]) > (step5_info["customer_budget"] * 0.15):
            triggers.append(f"Tổng giá trị ({step5_info['grand_total']:,.0f} VNĐ) vượt ngân sách dự kiến của khách ({step5_info['customer_budget']:,.0f} VNĐ) hơn 15%. Cần tối ưu cấu hình.")

        requires_approval = (len(triggers) > 0)
        approval_memo = None
        if requires_approval:
            approval_memo = self._generate_internal_approval_memo(step4_info, step5_info, parsed, triggers)

        return {
            "name": "Kiểm tra Thẩm quyền & Phê duyệt",
            "requires_approval": requires_approval,
            "approver": "Trưởng phòng Kinh doanh" if applied_discount <= 15.0 else "Ban Giám Đốc",
            "reasons": triggers,
            "approval_memo": approval_memo
        }

    # --- Step 7 ---
    def _step7_finalize_and_track(self, step3_info: Dict[str, Any], step4_info: Dict[str, Any], step5_info: Dict[str, Any], step6_info: Dict[str, Any], parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Kết thúc: Cập nhật & Theo dõi, tạo Bản nháp phản hồi khách hàng hoàn chỉnh."""
        customer_email_draft = self._generate_customer_quote_email(step3_info, step4_info, step5_info, step6_info, parsed)

        return {
            "name": "Kết thúc: Cập nhật & Theo dõi",
            "tracking_status": "CHỜ_DUYỆT_NỘI_BỘ" if step6_info["requires_approval"] else "SẴN_SÀNG_GỬI_KHÁCH",
            "customer_email_draft": customer_email_draft,
            "summary_for_crm": {
                "Mã Cơ Hội": step3_info["opp_id"],
                "Khách Hàng": step3_info["customer_name"],
                "NVKD Phụ Trách": step3_info["assigned_rep"],
                "Tổng Giá Trị (VAT)": f"{step5_info['grand_total']:,.0f} VNĐ",
                "Chiết Khấu": f"{step5_info['applied_discount']}%",
                "Khả Năng Đáp Ứng Deadline": "Cảnh báo trễ hạn" if step4_info["has_deadline_risk"] else "Đạt yêu cầu",
                "Trạng Thái Duyệt": "Cần Trưởng phòng duyệt" if step6_info["requires_approval"] else "NVKD tự quyết",
                "Ngày Tiếp Nhận": step3_info["created_date"]
            }
        }

    # --- Gemini AI Extraction Helper ---
    def _extract_request_data_with_gemini(self, text: str) -> Optional[Dict[str, Any]]:
        """Sử dụng Gemini API để bóc tách thực thể nâng cao từ ngôn ngữ tự nhiên."""
        try:
            prompt = f"""Bạn là trợ lý AI chuyên xử lý yêu cầu báo giá B2B của Công ty Công nghệ Minh An.
Hãy phân tích văn bản yêu cầu của khách hàng sau và trả về DUY NHẤT một chuỗi JSON hợp lệ (không kèm giải thích, không kèm markdown code block):
{{
  "customer_name": "Tên công ty hoặc khách hàng (nếu không rõ ghi null)",
  "contact_person": "Tên người liên hệ (nếu không rõ ghi null)",
  "contact_email": "Email liên hệ (nếu không rõ ghi null)",
  "contact_phone": "Số điện thoại liên hệ (nếu không rõ ghi null)",
  "industry": "Lĩnh vực hoạt động phù hợp (Tài chính & Ngân hàng / Công nghệ thông tin & Viễn thông / Y tế & Dược phẩm / Sản xuất & Khu công nghiệp / Bán lẻ & Chuỗi cung ứng / Doanh nghiệp chung)",
  "budget": <ngân sách dự kiến bằng số VNĐ nguyên thủy, ví dụ 460000000, nếu không đề cập thì null>,
  "deadline_days": <thời hạn tính bằng số ngày, ví dụ 14, nếu không đề cập thì null>,
  "requested_discount": <chiết khấu mong muốn tính bằng số %, ví dụ 8.0, nếu không đề cập thì 0.0>,
  "items": [
    {{"name": "Tên thiết bị hoặc dịch vụ", "qty": <số lượng số nguyên>}}
  ]
}}

Văn bản yêu cầu:
{text}
"""
            response = self.client.models.generate_content(
                model=self.ai_model_name,
                contents=prompt
            )
            raw_out = response.text.strip()
            if raw_out.startswith("```"):
                raw_out = re.sub(r"^```(?:json)?\n?", "", raw_out)
                raw_out = re.sub(r"\n?```$", "", raw_out)
            data = json.loads(raw_out)
            return data
        except Exception:
            return None

    # --- Fallback Regex Extraction Helper ---
    def _extract_request_data_regex(self, text: str) -> Dict[str, Any]:
        """Bóc tách thông tin bằng NLP Regex dự phòng ổn định cao."""
        data = {
            "customer_name": None,
            "contact_person": None,
            "contact_email": None,
            "contact_phone": None,
            "industry": "Doanh nghiệp",
            "items": [],
            "budget": None,
            "deadline_days": None,
            "requested_discount": 0.0
        }

        # Email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        if email_match:
            data["contact_email"] = email_match.group(0)

        # Phone
        phone_match = re.search(r'(0\d{9,10}|\+84\d{9,10})', text)
        if phone_match:
            data["contact_phone"] = phone_match.group(0)

        # Tên công ty / khách hàng
        comp_match = re.search(r'(?:công ty|cty|doanh nghiệp|khách hàng|tập đoàn|ngân hàng)\s+([^\n,\.]+)', text, re.IGNORECASE)
        if comp_match:
            data["customer_name"] = comp_match.group(0).strip()
        else:
            first_line = text.strip().split("\n")[0]
            if len(first_line) < 60 and any(w in first_line.lower() for w in ["công ty", "tập đoàn", "ngân hàng", "nam á", "foxconn", "retail"]):
                data["customer_name"] = first_line.strip()
            else:
                data["customer_name"] = "Khách hàng Doanh nghiệp"

        # Lĩnh vực
        t_low = text.lower()
        if any(w in t_low for w in ["ngân hàng", "tài chính", "chứng khoán", "bảo hiểm", "nam á"]):
            data["industry"] = "Tài chính & Ngân hàng"
        elif any(w in t_low for w in ["phần mềm", "it", "công nghệ", "telecom"]):
            data["industry"] = "Công nghệ Thông tin & Viễn thông"
        elif any(w in t_low for w in ["bệnh viện", "y tế", "dược", "phòng khám"]):
            data["industry"] = "Y tế & Dược phẩm"
        elif any(w in t_low for w in ["sản xuất", "nhà máy", "khu công nghiệp", "fdi", "foxconn"]):
            data["industry"] = "Sản xuất & Khu công nghiệp"
        elif any(w in t_low for w in ["bán lẻ", "siêu thị", "chuỗi", "style"]):
            data["industry"] = "Bán lẻ & Thương mại"

        # Ngân sách
        budget_match = re.search(r'(?:ngân sách|budget|tài chính|dự toán|khoảng)[:\s]*([0-9\.\,]+)\s*(triệu|tỷ|m|trieu|vnd|đ)?', t_low)
        if budget_match:
            num_str = budget_match.group(1).replace('.', '').replace(',', '')
            unit = budget_match.group(2) or ''
            try:
                val = float(num_str)
                if 'tỷ' in unit:
                    val *= 1_000_000_000
                elif 'triệu' in unit or 'trieu' in unit or 'm' in unit or val < 10000:
                    val *= 1_000_000
                data["budget"] = val
            except ValueError:
                pass

        # Thời hạn
        deadline_match = re.search(r'(?:thời hạn|deadline|tiến độ|triển khai|giao trong|cần trong|bàn giao|trong vòng|trong)[:\s]*([0-9]+)\s*(ngày|tuần|tháng|day)?', t_low)
        if deadline_match:
            num = int(deadline_match.group(1))
            unit = deadline_match.group(2) or 'ngày'
            if 'tuần' in unit:
                num *= 7
            elif 'tháng' in unit:
                num *= 30
            data["deadline_days"] = num

        # Chiết khấu yêu cầu
        discount_match = re.search(r'(?:chiết khấu|chiet khau|giảm giá|ck)[:\s]*([0-9\.]+)\s*%', t_low)
        if discount_match:
            data["requested_discount"] = float(discount_match.group(1))

        # Nhận diện sản phẩm
        found_items = []
        keywords_map = [
            ("Dell PowerEdge R750", ["dell poweredge", "r750", "máy chủ dell", "server dell"]),
            ("Switch Cisco Catalyst C9200L-24P-4G", ["cisco", "c9200l", "switch cisco"]),
            ("Tường lửa Fortinet FortiGate 80F", ["fortinet", "fortigate", "fg-80f", "80f", "tường lửa"]),
            ("Laptop Dell Latitude 5540", ["latitude 5540", "laptop dell", "latitude"]),
            ("Laptop Lenovo ThinkPad T14 Gen 4", ["thinkpad", "thinkpad t14", "t14"]),
            ("Màn hình Dell UltraSharp U2724D", ["ultrasharp", "u2724d", "màn hình dell", "màn hình đồ họa"]),
            ("Tủ mạng Server APC 42U NetShelter", ["tủ server apc", "rack 42u", "tủ rack", "netshelter"]),
            ("Bộ lưu điện APC Smart-UPS SRT 3000VA", ["smart-ups", "ups 3kva", "bộ lưu điện", "srt 3000va"]),
            ("Dịch vụ Triển khai Mạng & Máy chủ", ["dịch vụ triển khai", "triển khai mạng", "cài đặt hệ thống"]),
            ("Gói Bảo trì Minh An Care 24/7", ["minh an care", "gói bảo trì", "bảo trì 24/7"])
        ]

        for line in text.split("\n"):
            line_str = line.strip()
            if not line_str:
                continue
            for prod_label, kw_list in keywords_map:
                if any(kw in line_str.lower() for kw in kw_list):
                    qty_m = re.search(r'([0-9]+)\s*(?:bộ|cái|chiếc|gói|tủ|chiếc máy|máy)?', line_str)
                    qty = int(qty_m.group(1)) if qty_m else 1
                    if not any(it["name"] == prod_label for it in found_items):
                        found_items.append({"name": prod_label, "qty": qty})

        if not found_items:
            for prod_label, kw_list in keywords_map:
                for kw in kw_list:
                    m = re.search(r'([0-9]+)\s*(?:bộ|cái|chiếc|gói|tủ)?\s*(?:máy|thiết bị)?\s*' + re.escape(kw), t_low)
                    if m:
                        qty = int(m.group(1))
                        if not any(it["name"] == prod_label for it in found_items):
                            found_items.append({"name": prod_label, "qty": qty})
                        break
                    elif kw in t_low:
                        if not any(it["name"] == prod_label for it in found_items):
                            found_items.append({"name": prod_label, "qty": 1})
                        break

        data["items"] = found_items
        return data

    def _generate_clarification_email(self, parsed: Dict[str, Any], missing_fields: List[str]) -> str:
        """Tạo email yêu cầu khách hàng bổ sung/làm rõ thông tin theo nhánh quy trình."""
        cust_name = parsed.get("customer_name") or "Quý Khách hàng"
        email_body = f"""Kính gửi: Ban Giám đốc & Phòng Mua hàng {cust_name},

Lời đầu tiên, Công ty Cổ phần Công nghệ Minh An xin gửi lời cảm ơn chân thành đến Quý Công ty đã tin tưởng gửi yêu cầu báo giá trang thiết bị & giải pháp CNTT đến chúng tôi.

Để đảm bảo quyền lợi tối ưu, áp dụng chính sách chiết khấu chuẩn xác nhất và cam kết thời gian giao hàng/triển khai chuẩn mực, Bộ phận Kinh doanh Minh An xin phép xác nhận thêm các thông tin sau:

"""
        for i, field in enumerate(missing_fields, 1):
            email_body += f"{i}. {field}\n"

        email_body += f"""
Ngay khi nhận được thông tin bổ sung, chuyên viên kinh doanh phụ trách của Minh An sẽ hoàn thiện Hồ sơ Cơ hội, thẩm định tồn kho khả dụng và gửi lại Bảng Báo Giá & Đề Xuất Kỹ Thuật chính thức trong vòng 04 giờ làm việc.

Rất mong sớm nhận được phản hồi từ Quý Anh/Chị!

Trân trọng cảm ơn,
--------------------------------------------------
PHÒNG KINH DOANH DOANH NGHIỆP - MINH AN COMPANY
Trụ sở: Tòa nhà Công nghệ Minh An, TP. Hà Nội
Hotline: 1900 6868 | Email: b2b-sales@minhan.com.vn
Website: https://minhan.com.vn
"""
        return email_body

    def _generate_internal_approval_memo(self, step4_info: Dict[str, Any], step5_info: Dict[str, Any], parsed: Dict[str, Any], triggers: List[str]) -> str:
        """Tạo Tờ trình Phê duyệt Nội bộ gửi Trưởng phòng Kinh doanh."""
        memo = f"""TỜ TRÌNH PHÊ DUYỆT ĐỀ XUẤT CƠ HỘI BÁN HÀNG VƯỢT THẨM QUYỀN
--------------------------------------------------------------------------------
Kính gửi: TRƯỞNG PHÒNG KINH DOANH (MINH AN COMPANY)
Đồng kính gửi: BỘ PHẬN VẬN HÀNH & KHO VẬN

1. THÔNG TIN KHÁCH HÀNG & CƠ HỘI:
- Khách hàng: {parsed.get('customer_name')} ({parsed.get('industry')})
- Người liên hệ: {parsed.get('contact_person', 'Chưa rõ')} | Email: {parsed.get('contact_email', 'Chưa rõ')}
- Ngân sách dự kiến của KH: {step5_info['customer_budget']:,.0f} VNĐ
- Thời hạn KH yêu cầu: {parsed.get('deadline_days')} ngày

2. TỔNG QUAN TÀI CHÍNH & ĐỀ XUẤT GIÁ:
- Tổng giá trị niêm yết (List Price): {step5_info['total_list_price']:,.0f} VNĐ
- Hạn mức chiết khấu NVKD tự quyết: {step5_info['allowed_nvkd_discount']}%
- Mức chiết khấu khách hàng đề nghị: {step5_info['applied_discount']}% (Giá trị giảm: {step5_info['discount_amount']:,.0f} VNĐ)
- Tổng giá trị báo giá dự kiến (bao gồm VAT): {step5_info['grand_total']:,.0f} VNĐ

3. CÁC ĐIỂM CẦN TRƯỞNG PHÒNG PHÊ DUYỆT (TRIGGERS):
"""
        for i, trig in enumerate(triggers, 1):
            memo += f"   [{i}] {trig}\n"

        memo += f"""
4. Ý KIẾN ĐỀ XUẤT CỦA NVKD PHỤ TRÁCH:
- Đánh giá khách hàng: Thuộc nhóm đối tác chiến lược, có tiềm năng tái ký các giai đoạn tiếp theo.
- Kiến nghị Trưởng phòng duyệt mức chiết khấu {step5_info['applied_discount']}% để giữ chân khách hàng.
- Về thời hạn triển khai: Đề xuất phối hợp Vận hành ưu tiên điều chuyển hàng express từ kho vệ tinh.

Kính trình Trưởng phòng xem xét và phê duyệt!
"""
        return memo

    def _generate_customer_quote_email(self, step3_info: Dict[str, Any], step4_info: Dict[str, Any], step5_info: Dict[str, Any], step6_info: Dict[str, Any], parsed: Dict[str, Any]) -> str:
        """Tạo bản nháp Báo giá & Thư đề xuất chính thức gửi Khách hàng."""
        cust_name = step3_info["customer_name"]
        rep_name = step3_info["assigned_rep"]
        rep_email = step3_info["assigned_rep_email"]
        opp_id = step3_info["opp_id"]

        email = f"""Kính gửi: Ban Giám đốc & Phòng Mua hàng {cust_name},

Công ty Cổ phần Công nghệ Minh An xin trân trọng gửi tới Quý Công ty lời chúc sức khỏe và thành công!
Chúng tôi đã tiếp nhận và hoàn tất thẩm định kỹ thuật cho yêu cầu của Quý Công ty theo mã hồ sơ: [{opp_id}].

Dưới đây là Bảng Đề xuất Cung cấp Thiết bị & Báo giá Ưu đãi dành riêng cho Quý Công ty:

----------------------------------------------------------------------------------------------------------
DANH MỤC THIẾT BỊ & DỊCH VỤ CÔNG NGHỆ CHÍNH HÃNG MINH AN
----------------------------------------------------------------------------------------------------------
"""
        for idx, it in enumerate(step4_info["items"], 1):
            email += f"{idx}. {it['matched_name']}\n"
            email += f"   - Số lượng: {it['qty']} {it['unit']}\n"
            email += f"   - Đơn giá niêm yết: {it['current_list_price']:,.0f} VNĐ\n"
            email += f"   - Chiết khấu áp dụng: {it['discount_rate']}%\n"
            email += f"   - Thành tiền (sau CK): {it['total_after_discount']:,.0f} VNĐ\n"
            email += f"   - Tình trạng & Thời gian bàn giao: {it['stock_status']}\n\n"

        email += f"""----------------------------------------------------------------------------------------------------------
TỔNG HỢP GIÁ TRỊ ĐỀ XUẤT:
- Tổng tiền trước chiết khấu: {step5_info['total_list_price']:,.0f} VNĐ
- Tỷ lệ chiết khấu ưu đãi: {step5_info['applied_discount']}% (-{step5_info['discount_amount']:,.0f} VNĐ)
- Tiền hàng sau chiết khấu: {step5_info['net_amount']:,.0f} VNĐ
- Thuế VAT (10%): {step5_info['vat_amount']:,.0f} VNĐ
- TỔNG THANH TOÁN (ĐÃ GỒM VAT): {step5_info['grand_total']:,.0f} VNĐ
----------------------------------------------------------------------------------------------------------

ĐIỀU KHOẢN THỰC HIỆN & BẢO HÀNH:
1. Cam kết chất lượng: 100% thiết bị mới, nguyên đai nguyên kiện chính hãng, đầy đủ CO/CQ từ nhà sản xuất.
2. Thời gian triển khai: Minh An cam kết bàn giao và lắp đặt hoàn tất trong vòng {step4_info['max_required_lead_time']} ngày làm việc.
3. Hỗ trợ kỹ thuật: Miễn phí gói hỗ trợ kỹ thuật và kiểm tra vận hành hệ thống trong tháng đầu tiên.
4. Hiệu lực báo giá: Báo giá có hiệu lực trong vòng 15 ngày kể từ ngày gửi.

Chuyên viên Kinh doanh phụ trách trực tiếp:
- Ông/Bà: {rep_name}
- Email: {rep_email} | Hotline hỗ trợ 24/7: 1900 6868

Rất hân hạnh được đồng hành và hợp tác cùng Quý Công ty!

Trân trọng,
PHÒNG KINH DOANH DOANH NGHIỆP - MINH AN COMPANY
"""
        return email
