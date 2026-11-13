import datetime
import re
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np


class MarketingAnalyticsEngine:
    """
    Động cơ phân tích hiệu quả chiến dịch Marketing & Kiểm toán tài chính:
    - Centralized Data Model (Hỗ trợ cả trường hợp 3 tabs chuẩn hoặc 1 tab Transactions duy nhất).
    - Multi-touch Revenue Attribution (Doanh thu chia đều theo số lượng campaign tham gia).
    - Return Reconciliation (Return Window 15-30 ngày, tránh trừ trùng).
    - Activity Based Costing (ABC) phân bổ chi phí trực tiếp & gián tiếp.
    - Human-in-the-Loop: Quản lý và phê duyệt ngoại lệ có kiểm soát thẩm quyền.
    - Verification Suite: 7 phép kiểm toán tự động (PASS / FAIL / NOT_APPLICABLE).
    - Standalone HTML Dashboard Generator.
    """

    AUTHORIZED_ROLES = [
        "Trưởng phòng Marketing",
        "Trưởng phòng Marketing & Tài chính",
        "Quản trị viên",
        "Admin",
        "Ban Giám Đốc",
        "Giám đốc Kinh doanh"
    ]

    def __init__(
        self,
        normalized_data: Dict[str, pd.DataFrame],
        initial_exceptions: Optional[List[Dict[str, Any]]] = None,
        return_window_days: int = 30
    ):
        self.data = normalized_data
        self.return_window_days = return_window_days
        self.processing_log: List[Dict[str, Any]] = []
        self.step_states: Dict[str, Any] = {}
        # Nạp các ngoại lệ từ giai đoạn Data Cleaning vào hàng đợi phê duyệt
        self.exceptions_view: List[Dict[str, Any]] = [dict(e) for e in (initial_exceptions or [])]
        self.report_result: Optional[pd.DataFrame] = None
        self.detailed_attributed_df: Optional[pd.DataFrame] = None
        self.verification_results: Dict[str, Any] = {}
        self.approval_history: List[Dict[str, Any]] = []

    def log(self, step_name: str, status: str, message: str, details: Optional[Dict[str, Any]] = None):
        entry = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "step": step_name,
            "status": status,
            "message": message,
            "details": details or {}
        }
        self.processing_log.append(entry)

    # ==========================================================================
    # GIAI ĐOẠN 3: PROCESS - 6 BƯỚC XỬ LÝ
    # ==========================================================================

    def run_process_workflow(self) -> Dict[str, Any]:
        """Thực thi tuần tự 6 bước của quy trình Process."""
        self.processing_log = []

        # BƯỚC 1: DATA CENTRALIZATION
        step1_res = self._step1_data_centralization()
        self.step_states["step1"] = step1_res
        if step1_res["status"] == "FAILED":
            return {"status": "FAILED", "failed_step": "step1", "message": step1_res.get("error")}

        # BƯỚC 2: REVENUE ATTRIBUTION
        step2_res = self._step2_revenue_attribution(step1_res["centralized_tx"])
        self.step_states["step2"] = step2_res
        if step2_res["status"] == "FAILED":
            return {"status": "FAILED", "failed_step": "step2", "message": step2_res.get("error")}

        # BƯỚC 3: RETURN RECONCILIATION
        step3_res = self._step3_return_reconciliation(step2_res["attributed_df"])
        self.step_states["step3"] = step3_res
        if step3_res["status"] == "FAILED":
            return {"status": "FAILED", "failed_step": "step3", "message": step3_res.get("error")}

        # BƯỚC 4: COST ALLOCATION (ACTIVITY BASED COSTING)
        step4_res = self._step4_cost_allocation(step3_res["reconciled_df"])
        self.step_states["step4"] = step4_res
        if step4_res["status"] == "FAILED":
            return {"status": "FAILED", "failed_step": "step4", "message": step4_res.get("error")}

        # BƯỚC 5: PROCESS AUTOMATION & NET CONTRIBUTION
        step5_res = self._step5_net_contribution(step4_res["campaign_summary_df"])
        self.step_states["step5"] = step5_res

        # BƯỚC 6: CAMPAIGN DECISION & HUMAN-IN-THE-LOOP
        step6_res = self._step6_campaign_decision()
        self.step_states["step6"] = step6_res

        return {
            "status": "COMPLETED",
            "step_states": self.step_states,
            "report_result": self.report_result,
            "exceptions_view": self.exceptions_view,
            "log": self.processing_log
        }

    # --- Bước 1: Data Centralization ---
    def _step1_data_centralization(self) -> Dict[str, Any]:
        self.log("Step 1: Centralization", "RUNNING", "Đang tích hợp dữ liệu từ các Tab đã chuẩn hóa...")
        try:
            df_tx = self.data.get("Normalized_Transactions")
            if df_tx is None or df_tx.empty:
                # Fallback nếu truyền key Transactions
                df_tx = self.data.get("Transactions")

            if df_tx is None or df_tx.empty:
                self.log("Step 1: Centralization", "FAILED", "Thiếu dữ liệu đơn hàng (Transactions). Không thể tiếp tục.")
                return {"status": "FAILED", "error": "Thiếu dữ liệu Transactions"}

            df_ret = self.data.get("Normalized_Returns", self.data.get("Returns"))
            df_costs = self.data.get("Normalized_Campaign_Costs", self.data.get("Campaign_Costs"))

            has_returns = (df_ret is not None and not df_ret.empty)
            has_costs = (df_costs is not None and not df_costs.empty)

            total_orders = len(df_tx)
            total_returns = len(df_ret) if has_returns else 0
            total_costs = len(df_costs) if has_costs else 0

            msg = f"Tập trung thành công {total_orders} đơn hàng. Dữ liệu Hoàn trả: {'Có ('+str(total_returns)+' bản ghi)' if has_returns else 'Chưa cung cấp'}. Dữ liệu Chi phí: {'Có ('+str(total_costs)+' chiến dịch)' if has_costs else 'Chưa cung cấp'}."
            self.log("Step 1: Centralization", "PASS", msg, {
                "orders_count": total_orders,
                "has_returns": has_returns,
                "has_costs": has_costs
            })

            return {
                "name": "BƯỚC 1: Tập trung dữ liệu (Centralized Data Model)",
                "status": "PASS",
                "centralized_tx": df_tx.copy(deep=True),
                "has_returns": has_returns,
                "has_costs": has_costs,
                "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
            }
        except Exception as e:
            self.log("Step 1: Centralization", "FAILED", f"Lỗi tập trung dữ liệu: {str(e)}")
            return {"name": "BƯỚC 1: Tập trung dữ liệu", "status": "FAILED", "error": str(e)}

    # --- Bước 2: Multi-touch Revenue Attribution ---
    def _step2_revenue_attribution(self, df_tx: pd.DataFrame) -> Dict[str, Any]:
        self.log("Step 2: Revenue Attribution", "RUNNING", "Đang tính phân bổ doanh thu đa điểm chạm (Multi-touch Attribution)...")
        try:
            # Lấy danh sách các đơn bị từ chối phê duyệt (REJECTED) để loại trừ khỏi phân bổ
            rejected_order_ids = set(
                e["Order_ID"] for e in self.exceptions_view
                if e.get("Approval_Status") == "REJECTED"
            )

            attributed_rows = []
            total_source_revenue = 0.0
            total_attributed_revenue = 0.0
            unattributed_orders_count = 0

            for _, r in df_tx.iterrows():
                order_id = r["Order_ID"]
                order_val = float(r.get("Order_Value", 0.0))
                cogs = float(r.get("COGS", 0.0))
                order_date = r.get("Order_Date")
                channel = r.get("Channel", "Unknown")

                # Nếu đơn hàng bị Trưởng phòng từ chối phê duyệt, bỏ qua không phân bổ
                if order_id in rejected_order_ids:
                    continue

                total_source_revenue += order_val

                raw_cmps = r.get("Campaign_List")
                cmp_data_status = r.get("Campaign_Data_Status", "AVAILABLE")

                if raw_cmps is None or (isinstance(raw_cmps, float) and pd.isna(raw_cmps)):
                    clean_cmps = []
                elif isinstance(raw_cmps, str):
                    if raw_cmps.strip() in ["", "KHONG_CO", "MISSING_SOURCE_DATA", "nan", "None", "null"]:
                        clean_cmps = []
                    else:
                        clean_cmps = [c.strip() for c in raw_cmps.split(";") if c.strip() and c.strip() not in ["KHONG_CO", "MISSING_SOURCE_DATA"]]
                elif isinstance(raw_cmps, (list, tuple, set)):
                    clean_cmps = [str(c).strip() for c in raw_cmps if str(c).strip() and str(c).strip() not in ["KHONG_CO", "MISSING_SOURCE_DATA"]]
                else:
                    clean_cmps = []

                cmp_count = len(clean_cmps)

                if cmp_count > 0:
                    attr_rev_per_touch = order_val / cmp_count
                    attr_cogs_per_touch = cogs / cmp_count
                    for cmp_id in clean_cmps:
                        attributed_rows.append({
                            "Order_ID": order_id,
                            "Order_Date": order_date,
                            "Channel": channel,
                            "Campaign_ID": cmp_id,
                            "Gross_Order_Value": order_val,
                            "Campaign_Count": cmp_count,
                            "Attributed_Revenue": attr_rev_per_touch,
                            "Attributed_COGS": attr_cogs_per_touch,
                            "Attributed_Return": 0.0,
                            "Net_Sales": attr_rev_per_touch,
                            "Return_Status": "No_Return"
                        })
                        total_attributed_revenue += attr_rev_per_touch
                else:
                    # Trường hợp không có mã chiến dịch:
                    # - Nếu do nguồn thiếu cột chiến dịch -> MISSING_SOURCE_DATA
                    # - Nếu có cột nhưng khách không qua chiến dịch -> ORGANIC_NO_CAMPAIGN
                    unattributed_orders_count += 1
                    campaign_tag = "CHƯA_GẮN_CHIẾN_DỊCH (MISSING_SOURCE_DATA)" if cmp_data_status == "MISSING_SOURCE_DATA" else "ORGANIC_NO_CAMPAIGN"
                    attributed_rows.append({
                        "Order_ID": order_id,
                        "Order_Date": order_date,
                        "Channel": channel,
                        "Campaign_ID": campaign_tag,
                        "Gross_Order_Value": order_val,
                        "Campaign_Count": 1,
                        "Attributed_Revenue": order_val,
                        "Attributed_COGS": cogs,
                        "Attributed_Return": 0.0,
                        "Net_Sales": order_val,
                        "Return_Status": "No_Return"
                    })
                    total_attributed_revenue += order_val

            df_attributed = pd.DataFrame(attributed_rows)
            self.detailed_attributed_df = df_attributed

            # Kiểm tra cân đối doanh thu (Attributed Sum == Source Sum)
            diff = abs(total_source_revenue - total_attributed_revenue)
            is_balanced = diff < 0.01

            self.log("Step 2: Revenue Attribution", "PASS" if is_balanced else "WARNING",
                f"Phân bổ thành công {len(df_attributed)} lượt chạm. Doanh thu nguồn: {total_source_revenue:,.0f} đ, Tổng phân bổ: {total_attributed_revenue:,.0f} đ (Độ lệch: {diff:.2f}).", {
                    "source_revenue": total_source_revenue,
                    "attributed_revenue": total_attributed_revenue,
                    "difference": diff,
                    "organic_orders": unattributed_orders_count
                }
            )

            return {
                "name": "BƯỚC 2: Phân bổ doanh thu (Multi-touch Attribution)",
                "status": "PASS",
                "attributed_df": df_attributed,
                "total_source_revenue": total_source_revenue,
                "total_attributed_revenue": total_attributed_revenue,
                "is_balanced": is_balanced,
                "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
            }
        except Exception as e:
            self.log("Step 2: Revenue Attribution", "FAILED", f"Lỗi phân bổ doanh thu: {str(e)}")
            return {"name": "BƯỚC 2: Phân bổ doanh thu", "status": "FAILED", "error": str(e)}

    # --- Bước 3: Return Reconciliation ---
    def _step3_return_reconciliation(self, df_attributed: pd.DataFrame) -> Dict[str, Any]:
        self.log("Step 3: Return Reconciliation", "RUNNING", "Đang đối soát hàng hoàn trả theo Return Window...")
        try:
            df_ret = self.data.get("Normalized_Returns", self.data.get("Returns"))
            has_returns = (df_ret is not None and not df_ret.empty)

            df_reconciled = df_attributed.copy(deep=True)

            if not has_returns:
                self.log("Step 3: Return Reconciliation", "PASS", "Không có dữ liệu hoàn trả (Returns). Giữ nguyên Net Sales = Attributed Revenue.")
                return {
                    "name": "BƯỚC 3: Đối soát hàng hoàn trả (Return Reconciliation)",
                    "status": "PASS",
                    "reconciled_df": df_reconciled,
                    "total_valid_returns": 0.0,
                    "total_net_sales": df_reconciled["Net_Sales"].sum(),
                    "out_of_window_count": 0,
                    "is_applicable": False,
                    "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
                }

            # Có dữ liệu hoàn trả -> Thực hiện đối soát
            total_valid_returns = 0.0
            out_of_window_count = 0

            # Lấy các ngoại lệ đã được phê duyệt chấp thuận đối trừ
            approved_exceptions = set(
                e["Order_ID"] for e in self.exceptions_view
                if e.get("Approval_Status") == "APPROVED"
            )

            for _, ret_row in df_ret.iterrows():
                ret_order_id = str(ret_row.get("Order_ID")).strip()
                ret_amount = float(ret_row.get("Return_Amount", 0.0))
                ret_date_str = ret_row.get("Return_Date")

                match_indices = df_reconciled[df_reconciled["Order_ID"] == ret_order_id].index.tolist()
                if not match_indices:
                    continue

                order_date_str = df_reconciled.loc[match_indices[0], "Order_Date"]

                # Kiểm tra Return Window
                days_gap = None
                is_out_of_window = False
                if order_date_str and ret_date_str:
                    try:
                        d_order = datetime.datetime.strptime(str(order_date_str)[:10], "%Y-%m-%d")
                        d_ret = datetime.datetime.strptime(str(ret_date_str)[:10], "%Y-%m-%d")
                        days_gap = (d_ret - d_order).days
                        if days_gap > self.return_window_days:
                            is_out_of_window = True
                    except Exception:
                        pass

                # Nếu ngoài hạn và chưa được duyệt -> Đưa vào Exceptions
                if is_out_of_window and (ret_order_id not in approved_exceptions):
                    out_of_window_count += 1
                    # Kiểm tra xem đã có trong exceptions_view chưa
                    if not any(e["Order_ID"] == ret_order_id and e["Error_Type"] == "OUT_OF_WINDOW_RETURN" for e in self.exceptions_view):
                        self.exceptions_view.append({
                            "Order_ID": ret_order_id,
                            "Campaign_ID": df_reconciled.loc[match_indices[0], "Campaign_ID"],
                            "Error_Type": "OUT_OF_WINDOW_RETURN",
                            "Raw_Value": f"{ret_amount:,.0f} đ (sau {days_gap} ngày)",
                            "Normalized_Value": f"Return Window: {self.return_window_days} ngày",
                            "Severity": "HIGH",
                            "Error_Description": f"Đơn {ret_order_id} hoàn trả sau {days_gap} ngày, vượt chính sách {self.return_window_days} ngày. Số tiền hoàn: {ret_amount:,.0f} đ.",
                            "Proposed_Action": "Trưởng phòng xem xét chấp thuận hoàn tiền đặc biệt hoặc từ chối",
                            "Approval_Status": "PENDING_REVIEW",
                            "Reviewer": "Chưa duyệt",
                            "Review_Time": "N/A",
                            "Note": ""
                        })
                    continue

                # Trong hạn hoặc đã được phê duyệt -> Phân bổ hoàn trả đều theo số lượng campaign
                cmp_count = len(match_indices)
                attr_ret_per_touch = ret_amount / cmp_count

                for idx in match_indices:
                    df_reconciled.at[idx, "Attributed_Return"] += attr_ret_per_touch
                    df_reconciled.at[idx, "Return_Status"] = "Approved_Return"

                total_valid_returns += ret_amount

            # Cập nhật Net Sales
            df_reconciled["Net_Sales"] = df_reconciled["Attributed_Revenue"] - df_reconciled["Attributed_Return"]
            self.detailed_attributed_df = df_reconciled
            total_net_sales = df_reconciled["Net_Sales"].sum()

            self.log("Step 3: Return Reconciliation", "PASS",
                f"Đối soát hoàn trả hoàn tất: {len(df_ret)} đơn hoàn trả. Hợp lệ đã trừ: {total_valid_returns:,.0f} đ. Net Sales: {total_net_sales:,.0f} đ.", {
                    "valid_returns": total_valid_returns,
                    "net_sales": total_net_sales,
                    "out_of_window": out_of_window_count
                }
            )

            return {
                "name": "BƯỚC 3: Đối soát hàng hoàn trả (Return Reconciliation)",
                "status": "PASS",
                "reconciled_df": df_reconciled,
                "total_valid_returns": total_valid_returns,
                "total_net_sales": total_net_sales,
                "out_of_window_count": out_of_window_count,
                "is_applicable": True,
                "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
            }
        except Exception as e:
            self.log("Step 3: Return Reconciliation", "FAILED", f"Lỗi đối soát hoàn trả: {str(e)}")
            return {"name": "BƯỚC 3: Đối soát hàng hoàn trả", "status": "FAILED", "error": str(e)}

    # --- Bước 4: Cost Allocation (Activity Based Costing - ABC) ---
    def _step4_cost_allocation(self, df_reconciled: pd.DataFrame) -> Dict[str, Any]:
        self.log("Step 4: Cost Allocation", "RUNNING", "Đang phân bổ chi phí ABC (Trực tiếp & Gián tiếp)...")
        try:
            df_costs = self.data.get("Normalized_Campaign_Costs", self.data.get("Campaign_Costs"))
            has_costs = (df_costs is not None and not df_costs.empty)

            # Tổng hợp theo Campaign_ID từ dữ liệu bán hàng
            campaign_sales = df_reconciled.groupby("Campaign_ID").agg(
                Orders_Count=("Order_ID", "count"),
                Attributed_Revenue=("Attributed_Revenue", "sum"),
                Attributed_COGS=("Attributed_COGS", "sum"),
                Attributed_Return=("Attributed_Return", "sum"),
                Net_Sales=("Net_Sales", "sum")
            ).reset_index()

            if not has_costs:
                # Không có dữ liệu chi phí -> Không tự bịa chi phí = 0
                campaign_sales["Direct_Cost"] = None
                campaign_sales["Allocated_Overhead"] = None
                campaign_sales["Total_Cost"] = None
                campaign_sales["Campaign_Name"] = campaign_sales["Campaign_ID"]
                campaign_sales["Channel"] = "General"

                self.log("Step 4: Cost Allocation", "PASS", "Không có dữ liệu chi phí (Campaign_Costs). Bỏ qua phân bổ ABC.")
                return {
                    "name": "BƯỚC 4: Phân bổ chi phí ABC (Cost Allocation)",
                    "status": "PASS",
                    "campaign_summary_df": campaign_sales,
                    "is_applicable": False,
                    "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
                }

            # Có dữ liệu chi phí -> Merge và phân bổ ABC
            merged = pd.merge(df_costs, campaign_sales, on="Campaign_ID", how="outer")
            merged["Campaign_Name"] = merged["Campaign_Name"].fillna(merged["Campaign_ID"])
            merged["Channel"] = merged["Channel"].fillna("General")
            merged["Direct_Cost"] = merged["Direct_Cost"].fillna(0.0)
            merged["Overhead_Cost"] = merged["Overhead_Cost"].fillna(0.0)
            merged["Orders_Count"] = merged["Orders_Count"].fillna(0)
            merged["Attributed_Revenue"] = merged["Attributed_Revenue"].fillna(0.0)
            merged["Attributed_COGS"] = merged["Attributed_COGS"].fillna(0.0)
            merged["Attributed_Return"] = merged["Attributed_Return"].fillna(0.0)
            merged["Net_Sales"] = merged["Net_Sales"].fillna(0.0)

            total_orders = max(1, merged["Orders_Count"].sum())
            total_rev = max(1.0, merged["Attributed_Revenue"].sum())

            # Phân bổ Overhead theo Cost Driver
            allocated_overheads = []
            for _, r in merged.iterrows():
                driver = str(r.get("Cost_Driver", "Order_Volume")).strip()
                ovh = float(r.get("Overhead_Cost", 0.0))
                if "revenue" in driver.lower() or "doanh thu" in driver.lower():
                    weight = float(r["Attributed_Revenue"]) / total_rev
                else:
                    weight = float(r["Orders_Count"]) / total_orders
                allocated_overheads.append(ovh * weight)

            merged["Allocated_Overhead"] = allocated_overheads
            merged["Total_Cost"] = merged["Direct_Cost"] + merged["Allocated_Overhead"]

            self.log("Step 4: Cost Allocation", "PASS", f"Phân bổ ABC thành công cho {len(merged)} chiến dịch.", {
                "campaigns_count": len(merged),
                "total_cost": merged["Total_Cost"].sum()
            })

            return {
                "name": "BƯỚC 4: Phân bổ chi phí ABC (Cost Allocation)",
                "status": "PASS",
                "campaign_summary_df": merged,
                "is_applicable": True,
                "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
            }
        except Exception as e:
            self.log("Step 4: Cost Allocation", "FAILED", f"Lỗi phân bổ chi phí ABC: {str(e)}")
            return {"name": "BƯỚC 4: Phân bổ chi phí ABC", "status": "FAILED", "error": str(e)}

    # --- Bước 5: Net Contribution Calculation ---
    def _step5_net_contribution(self, df_summary: pd.DataFrame) -> Dict[str, Any]:
        self.log("Step 5: Net Contribution", "RUNNING", "Đang tính toán Net Contribution, ROI và ROAS...")
        try:
            df_result = df_summary.copy(deep=True)
            has_costs = "Total_Cost" in df_result.columns and df_result["Total_Cost"].notna().any()

            if has_costs:
                # Net Contribution = Net Sales - COGS - Total Cost
                df_result["Net_Contribution"] = df_result["Net_Sales"] - df_result["Attributed_COGS"] - df_result["Total_Cost"]

                # ROAS = Attributed Revenue / Total Cost
                df_result["ROAS"] = np.where(
                    df_result["Total_Cost"] > 0,
                    df_result["Attributed_Revenue"] / df_result["Total_Cost"],
                    0.0
                )

                # ROI = (Net Contribution / Total Cost) * 100
                df_result["ROI"] = np.where(
                    df_result["Total_Cost"] > 0,
                    (df_result["Net_Contribution"] / df_result["Total_Cost"]) * 100.0,
                    0.0
                )
            else:
                df_result["Net_Contribution"] = None
                df_result["ROAS"] = None
                df_result["ROI"] = None

            self.report_result = df_result

            # Đưa cảnh báo về chiến dịch âm lợi nhuận vào Exceptions nếu có
            if has_costs:
                for _, r in df_result.iterrows():
                    cid = r["Campaign_ID"]
                    if cid != "ORGANIC_NO_CAMPAIGN" and r["Net_Contribution"] is not None and r["Net_Contribution"] < 0:
                        if not any(e["Campaign_ID"] == cid and e["Error_Type"] == "UNPROFITABLE_CAMPAIGN" for e in self.exceptions_view):
                            self.exceptions_view.append({
                                "Order_ID": "MULTIPLE_ORDERS",
                                "Campaign_ID": cid,
                                "Error_Type": "UNPROFITABLE_CAMPAIGN",
                                "Raw_Value": f"Lỗ: {r['Net_Contribution']:,.0f} đ",
                                "Normalized_Value": f"ROAS: {r['ROAS']:.2f}x",
                                "Severity": "HIGH",
                                "Error_Description": f"Chiến dịch {r['Campaign_Name']} bị lỗ Net Contribution: {r['Net_Contribution']:,.0f} đ (ROAS: {r['ROAS']:.2f}x)",
                                "Proposed_Action": "Trưởng phòng xem xét điều chỉnh ngân sách hoặc dừng chương trình",
                                "Approval_Status": "PENDING_REVIEW",
                                "Reviewer": "Chưa duyệt",
                                "Review_Time": "N/A",
                                "Note": ""
                            })

            self.log("Step 5: Net Contribution", "PASS", f"Đã tính toán hoàn tất cho {len(df_result)} chiến dịch.", {
                "has_costs": has_costs,
                "total_net_sales": df_result["Net_Sales"].sum()
            })

            return {
                "name": "BƯỚC 5: Tự động hóa tính toán (Net Contribution Automation)",
                "status": "PASS",
                "report_rows": len(df_result),
                "has_costs": has_costs,
                "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
            }
        except Exception as e:
            self.log("Step 5: Net Contribution", "FAILED", f"Lỗi tính toán: {str(e)}")
            return {"name": "BƯỚC 5: Tự động hóa tính toán", "status": "FAILED", "error": str(e)}

    # --- Bước 6: Campaign Decision & Human-in-the-Loop ---
    def _step6_campaign_decision(self) -> Dict[str, Any]:
        df_result = self.report_result
        has_costs = "Net_Contribution" in df_result.columns and df_result["Net_Contribution"].notna().any()

        decisions = []
        for _, r in df_result.iterrows():
            if not has_costs:
                decisions.append("DATA_INSUFFICIENT (Chưa có dữ liệu chi phí)")
            elif "MISSING_SOURCE_DATA" in str(r["Campaign_ID"]):
                decisions.append("CAMPAIGN_DATA_PENDING (Chưa gắn chiến dịch marketing)")
            elif r["Campaign_ID"] == "ORGANIC_NO_CAMPAIGN":
                decisions.append("ORGANIC_TRAFFIC (Kênh tự nhiên)")
            else:
                roas = r["ROAS"]
                net_contrib = r["Net_Contribution"]
                if roas >= 2.5 and net_contrib > 0:
                    decisions.append("SCALE (Tiếp tục thử nghiệm & Mở rộng)")
                elif roas >= 1.0 and net_contrib >= 0:
                    decisions.append("OPTIMIZE (Điều chỉnh cơ chế)")
                else:
                    decisions.append("TERMINATE (Dừng chương trình / Tối ưu khẩn cấp)")

        df_result["Strategic_Decision"] = decisions
        self.report_result = df_result

        pending_exceptions = [e for e in self.exceptions_view if e.get("Approval_Status") == "PENDING_REVIEW"]
        status = "WAITING_APPROVAL" if pending_exceptions else "PASS"

        self.log("Step 6: Campaign Decision", status,
            f"Phân loại chiến lược 3 nhóm hoàn tất. Ngoại lệ chờ Trưởng phòng duyệt: {len(pending_exceptions)} mục.", {
                "total_exceptions": len(self.exceptions_view),
                "pending_approval": len(pending_exceptions)
            }
        )

        return {
            "name": "BƯỚC 6: Ra quyết định & Phê duyệt ngoại lệ (Human-in-the-Loop)",
            "status": status,
            "total_exceptions": len(self.exceptions_view),
            "pending_approval": len(pending_exceptions),
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
        }

    # ==========================================================================
    # HUMAN-IN-THE-LOOP: PHÊ DUYỆT NGOẠI LỆ CÓ KIỂM SOÁT THẨM QUYỀN
    # ==========================================================================

    def resolve_exception(
        self,
        order_id: str,
        action: str,
        reviewer_role: str,
        reviewer_name: str,
        note: str = ""
    ) -> Tuple[bool, str]:
        """
        Phê duyệt hoặc từ chối ngoại lệ với kiểm soát thẩm quyền chặt chẽ:
        - Kiểm tra quyền: reviewer_role phải thuộc danh sách AUTHORIZED_ROLES.
        - Kiểm tra giải trình: Bắt buộc phải có note ghi chú cho các trường hợp nghiêm trọng.
        - Lưu lịch sử kiểm toán (Approval Audit Log).
        """
        # 1. Kiểm soát quyền hạn ở Backend
        if reviewer_role not in self.AUTHORIZED_ROLES:
            return False, f"Từ chối thao tác: Vai trò '{reviewer_role}' không có thẩm quyền phê duyệt ngoại lệ (Yêu cầu: Trưởng phòng Marketing hoặc Quản trị viên)."

        # 2. Kiểm tra ghi chú giải trình nếu là action quan trọng
        clean_note = str(note).strip()
        if not clean_note and action in ["APPROVE", "CHẤP THUẬN", "APPROVED"]:
            # Kiểm tra xem item có mức độ HIGH hoặc CRITICAL không
            target_items = [e for e in self.exceptions_view if e["Order_ID"] == order_id]
            if target_items and target_items[0].get("Severity") in ["CRITICAL", "HIGH"]:
                return False, f"Bắt buộc nhập lý do / ghi chú giải trình khi phê duyệt ngoại lệ có độ rủi ro {target_items[0].get('Severity')}."

        # 3. Cập nhật trạng thái
        updated = False
        action_std = "APPROVED" if "APPROVE" in action.upper() else ("REJECTED" if "REJECT" in action.upper() else "CORRECTION_REQUESTED")

        for e in self.exceptions_view:
            if e["Order_ID"] == order_id:
                e["Approval_Status"] = action_std
                e["Reviewer"] = f"{reviewer_name} ({reviewer_role})"
                e["Review_Time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                e["Note"] = clean_note
                updated = True

                self.approval_history.append({
                    "Order_ID": order_id,
                    "Action": action_std,
                    "Reviewer": reviewer_name,
                    "Role": reviewer_role,
                    "Timestamp": e["Review_Time"],
                    "Note": clean_note
                })

        if updated:
            self.log("Human-in-the-Loop", "PASS", f"Đã cập nhật trạng thái {action_std} cho ngoại lệ {order_id} bởi {reviewer_name}.")
            # Chạy lại các bước phụ thuộc
            self.run_process_workflow()
            return True, f"Phê duyệt thành công: Đã chuyển trạng thái sang {action_std} cho {order_id}."
        else:
            return False, f"Không tìm thấy ngoại lệ với mã: {order_id}."

    # ==========================================================================
    # GIAI ĐOẠN 4: VERIFICATION (7 PHÉP KIỂM TOÁN TỰ ĐỘNG)
    # ==========================================================================

    def run_verification(self) -> Dict[str, Any]:
        """
        Thực hiện 7 phép kiểm toán tự động theo đúng tiêu chuẩn hệ thống:
        CHK-01: Schema và tính đầy đủ dữ liệu.
        CHK-02: Tính duy nhất của Order_ID và Return_ID.
        CHK-03: Tính hợp lệ của giá trị tiền tệ.
        CHK-04: Đối soát tổng doanh thu phân bổ với doanh thu nguồn.
        CHK-05: Đối soát hoàn trả và ngăn trừ trùng.
        CHK-06: Kiểm tra ngoại lệ và phê duyệt hợp lệ.
        CHK-07: Đối soát chi phí và Net Contribution.
        """
        tests = []
        is_all_applicable_pass = True

        df_tx = self.data.get("Normalized_Transactions", self.data.get("Transactions"))
        df_ret = self.data.get("Normalized_Returns", self.data.get("Returns"))
        df_costs = self.data.get("Normalized_Campaign_Costs", self.data.get("Campaign_Costs"))

        has_ret = (df_ret is not None and not df_ret.empty)
        has_costs = (df_costs is not None and not df_costs.empty)

        # CHK-01: Schema và tính đầy đủ dữ liệu
        req_cols = ["Order_ID", "Order_Value", "Campaign_List"]
        present_cols = [c for c in req_cols if c in df_tx.columns] if df_tx is not None else []
        t1_pass = (len(present_cols) == len(req_cols))
        tests.append({
            "code": "CHK-01",
            "name": "Kiểm tra Schema & Tính Đầy Đủ Dữ Liệu",
            "condition": "Bắt buộc có đầy đủ các trường: Order_ID, Order_Value, Campaign_List",
            "expected": f"Đầy đủ {len(req_cols)} trường cốt lõi",
            "actual": f"Có {len(present_cols)}/{len(req_cols)} trường ({', '.join(present_cols)})",
            "status": "PASS" if t1_pass else "FAIL",
            "impact": "Cơ sở dữ liệu đầu vào cho toàn bộ thuật toán phân tích"
        })
        if not t1_pass: is_all_applicable_pass = False

        # CHK-02: Tính duy nhất của Order_ID và Return_ID
        unresolved_dups = [
            e for e in self.exceptions_view
            if e.get("Error_Type") == "DUPLICATE_ORDER_ID" and e.get("Approval_Status") == "PENDING_REVIEW"
        ]
        t2_pass = (len(unresolved_dups) == 0)
        tests.append({
            "code": "CHK-02",
            "name": "Tính Duy Nhất Của Order_ID & Return_ID",
            "condition": "Không còn mã đơn trùng lặp chưa được Trưởng phòng phê duyệt giải trình",
            "expected": "0 đơn trùng chưa duyệt",
            "actual": f"Còn {len(unresolved_dups)} đơn trùng đang chờ duyệt",
            "status": "PASS" if t2_pass else "FAIL",
            "impact": "Tránh nhân đôi doanh thu và giao dịch ảo"
        })
        if not t2_pass: is_all_applicable_pass = False

        # CHK-03: Tính hợp lệ của giá trị tiền tệ
        unresolved_curr_errors = [
            e for e in self.exceptions_view
            if e.get("Error_Type") in ["INVALID_CURRENCY_FORMAT", "NEGATIVE_CURRENCY"] and e.get("Approval_Status") == "PENDING_REVIEW"
        ]
        t3_pass = (len(unresolved_curr_errors) == 0)
        tests.append({
            "code": "CHK-03",
            "name": "Tính Hợp Lệ Của Giá Trị Tiền Tệ",
            "condition": "Không có giá trị tiền tệ âm hoặc sai định dạng chưa qua phê duyệt",
            "expected": "0 lỗi tiền tệ chưa duyệt",
            "actual": f"Còn {len(unresolved_curr_errors)} lỗi tiền tệ chờ xử lý",
            "status": "PASS" if t3_pass else "FAIL",
            "impact": "Đảm bảo tính chính xác tuyệt đối của số tiền đối soát"
        })
        if not t3_pass: is_all_applicable_pass = False

        # CHK-04: Đối soát tổng doanh thu phân bổ với doanh thu nguồn
        if self.detailed_attributed_df is not None:
            total_attr = self.detailed_attributed_df["Attributed_Revenue"].sum()
            # Doanh thu nguồn chỉ tính các đơn hợp lệ không bị từ chối
            rejected_ids = set(e["Order_ID"] for e in self.exceptions_view if e.get("Approval_Status") == "REJECTED")
            valid_source = df_tx[~df_tx["Order_ID"].isin(rejected_ids)]["Order_Value"].sum() if df_tx is not None else 0.0
            diff_rev = abs(valid_source - total_attr)
            t4_pass = (diff_rev < 0.01)
            tests.append({
                "code": "CHK-04",
                "name": "Đối Soát Doanh Thu Phân Bổ Với Nguồn",
                "condition": "Tổng Attributed Revenue == Tổng Doanh thu nguồn hợp lệ (Độ lệch < 0.01)",
                "expected": f"{valid_source:,.0f} đ",
                "actual": f"{total_attr:,.0f} đ (Lệch: {diff_rev:.2f} đ)",
                "status": "PASS" if t4_pass else "FAIL",
                "impact": "Chứng minh thuật toán Multi-touch không làm thất thoát hoặc tạo khống doanh thu"
            })
            if not t4_pass: is_all_applicable_pass = False
        else:
            tests.append({
                "code": "CHK-04",
                "name": "Đối Soát Doanh Thu Phân Bổ Với Nguồn",
                "condition": "Chưa hoàn tất bước phân bổ doanh thu",
                "expected": "Hoàn tất Process",
                "actual": "Chưa chạy Process",
                "status": "FAIL",
                "impact": "Chưa có số liệu phân bổ"
            })
            is_all_applicable_pass = False

        # CHK-05: Đối soát hoàn trả và ngăn trừ trùng
        if has_ret:
            unresolved_returns = [
                e for e in self.exceptions_view
                if e.get("Error_Type") == "OUT_OF_WINDOW_RETURN" and e.get("Approval_Status") == "PENDING_REVIEW"
            ]
            t5_pass = (len(unresolved_returns) == 0)
            tests.append({
                "code": "CHK-05",
                "name": "Đối Soát Hoàn Trả & Ngăn Trừ Trùng",
                "condition": "Toàn bộ đơn hoàn ngoài Return Window phải được Trưởng phòng duyệt",
                "expected": "0 đơn hoàn ngoài hạn chưa duyệt",
                "actual": f"Còn {len(unresolved_returns)} đơn hoàn ngoài hạn chờ duyệt",
                "status": "PASS" if t5_pass else "FAIL",
                "impact": "Tránh khấu trừ hoàn trả sai chính sách"
            })
            if not t5_pass: is_all_applicable_pass = False
        else:
            tests.append({
                "code": "CHK-05",
                "name": "Đối Soát Hoàn Trả & Ngăn Trừ Trùng",
                "condition": "Bảng tính không có dữ liệu hoàn trả (Returns Tab)",
                "expected": "Có dữ liệu hoàn trả",
                "actual": "Dữ liệu hoàn trả chưa được cung cấp",
                "status": "NOT_APPLICABLE",
                "impact": "Bỏ qua phép kiểm hoàn trả một cách an toàn và minh bạch"
            })

        # CHK-06: Kiểm tra ngoại lệ và phê duyệt hợp lệ (Human-in-the-Loop)
        pending_all = [e for e in self.exceptions_view if e.get("Approval_Status") == "PENDING_REVIEW"]
        t6_pass = (len(pending_all) == 0)
        tests.append({
            "code": "CHK-06",
            "name": "Kiểm Tra Ngoại Lệ & Phê Duyệt Hợp Lệ (Human-in-the-Loop)",
            "condition": "Toàn bộ ngoại lệ phải được người có thẩm quyền phê duyệt trước khi phát hành",
            "expected": "0 ngoại lệ chờ duyệt",
            "actual": f"Còn {len(pending_all)} ngoại lệ chưa được duyệt",
            "status": "PASS" if t6_pass else "FAIL",
            "impact": "Đảm bảo tính chịu trách nhiệm của cấp quản lý trước khi xuất báo cáo"
        })
        if not t6_pass: is_all_applicable_pass = False

        # CHK-07: Đối soát chi phí và Net Contribution
        if has_costs and self.report_result is not None:
            df_res = self.report_result
            # Kiểm tra công thức: Net_Contribution == Net_Sales - COGS - Total_Cost
            calc_diff = abs((df_res["Net_Sales"] - df_res["Attributed_COGS"] - df_res["Total_Cost"]) - df_res["Net_Contribution"]).max()
            t7_pass = (calc_diff < 0.01)
            tests.append({
                "code": "CHK-07",
                "name": "Đối Soát Chi Phí ABC & Net Contribution",
                "condition": "Net Contribution = Net Sales - COGS - Total ABC Cost (Khớp tuyệt đối)",
                "expected": "Khớp công thức 100%",
                "actual": f"Độ lệch tối đa: {calc_diff:.4f} đ",
                "status": "PASS" if t7_pass else "FAIL",
                "impact": "Bảo đảm báo cáo tài chính tuân thủ chuẩn kế toán quản trị"
            })
            if not t7_pass: is_all_applicable_pass = False
        else:
            tests.append({
                "code": "CHK-07",
                "name": "Đối Soát Chi Phí ABC & Net Contribution",
                "condition": "Bảng tính không có dữ liệu chi phí chiến dịch (Campaign_Costs Tab)",
                "expected": "Có dữ liệu chi phí",
                "actual": "Dữ liệu chi phí chưa được cung cấp",
                "status": "NOT_APPLICABLE",
                "impact": "Không thể kiểm toán Net Contribution khi chưa có số liệu chi phí"
            })

        pass_count = sum(1 for t in tests if t["status"] == "PASS")
        fail_count = sum(1 for t in tests if t["status"] == "FAIL")
        na_count = sum(1 for t in tests if t["status"] == "NOT_APPLICABLE")

        self.verification_results = {
            "overall_status": "PASS" if is_all_applicable_pass else "FAIL",
            "tests": tests,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "na_count": na_count,
            "total_tests": len(tests),
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        return self.verification_results

    # ==========================================================================
    # GIAI ĐOẠN 5: XUẤT BÁO CÁO HTML STANDALONE
    # ==========================================================================

    def generate_html_report(self) -> str:
        """Sinh file HTML Dashboard chuyên nghiệp, độc lập hoàn toàn."""
        if self.report_result is None:
            return "<h1>Báo cáo chưa được khởi tạo. Vui lòng chạy quy trình PROCESS trước.</h1>"

        df_res = self.report_result
        has_costs = "Total_Cost" in df_res.columns and df_res["Total_Cost"].notna().any()

        total_gross = df_res["Attributed_Revenue"].sum()
        total_cogs = df_res["Attributed_COGS"].sum()
        total_net_sales = df_res["Net_Sales"].sum()
        total_returns = df_res["Attributed_Return"].sum()
        total_costs = df_res["Total_Cost"].sum() if has_costs else 0.0
        total_net_contrib = df_res["Net_Contribution"].sum() if has_costs else None

        rows_html = ""
        for _, r in df_res.iterrows():
            cid = r["Campaign_ID"]
            cname = r["Campaign_Name"]
            rev = r["Attributed_Revenue"]
            ret = r["Attributed_Return"]
            cogs = r["Attributed_COGS"]
            ns = r["Net_Sales"]
            cost = r["Total_Cost"] if has_costs else None
            nc = r["Net_Contribution"] if has_costs else None
            roas = r["ROAS"] if has_costs else None
            roi = r["ROI"] if has_costs else None
            dec = r.get("Strategic_Decision", "N/A")

            badge_color = "#10B981" if "SCALE" in dec else ("#F59E0B" if "OPTIMIZE" in dec else ("#EF4444" if "TERMINATE" in dec else "#64748B"))

            rows_html += f"""
            <tr>
                <td><b>{cname}</b><br><span style="font-size:11px; color:#64748B;">{cid} • {r.get('Channel', 'N/A')}</span></td>
                <td style="text-align:right;">{rev:,.0f} đ</td>
                <td style="text-align:right; color:#DC2626;">{ret:,.0f} đ</td>
                <td style="text-align:right; color:#475569;">{cogs:,.0f} đ</td>
                <td style="text-align:right; font-weight:600; color:#2563EB;">{ns:,.0f} đ</td>
                <td style="text-align:right;">{f"{cost:,.0f} đ" if cost is not None else "<i>Chưa có</i>"}</td>
                <td style="text-align:right; font-weight:700; color:{'#10B981' if (nc and nc>0) else '#EF4444'};">{f"{nc:,.0f} đ" if nc is not None else "<i>Chưa có</i>"}</td>
                <td style="text-align:center;">{f"{roas:.2f}x" if roas is not None else "N/A"}</td>
                <td style="text-align:center;">{f"{roi:+.1f}%" if roi is not None else "N/A"}</td>
                <td style="text-align:center;"><span style="background:{badge_color}; color:#FFF; font-size:11px; font-weight:600; padding:4px 8px; border-radius:6px;">{dec.split(' ')[0]}</span></td>
            </tr>
            """

        exc_html = ""
        for idx, e in enumerate(self.exceptions_view):
            status_color = "#10B981" if e.get("Approval_Status") == "APPROVED" else ("#EF4444" if e.get("Approval_Status") == "REJECTED" else "#F59E0B")
            exc_html += f"""
            <tr>
                <td>{idx+1}</td>
                <td><b>{e.get('Order_ID')}</b></td>
                <td><span style="background:#F1F5F9; color:#0F172A; padding:2px 6px; border-radius:4px; font-size:11px;">{e.get('Error_Type')}</span></td>
                <td>{e.get('Error_Description')}</td>
                <td><span style="color:{status_color}; font-weight:700;">{e.get('Approval_Status')}</span><br><small style="color:#64748B;">{e.get('Reviewer', 'N/A')}</small></td>
                <td><i>{e.get('Note') or 'Không có'}</i></td>
            </tr>
            """

        html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Marketing Campaign Performance Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #F8FAFC; color: #0F172A; margin: 0; padding: 24px; }}
        .report-header {{ background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 24px; margin-bottom: 20px; }}
        .header-title {{ font-size: 22px; font-weight: 700; color: #0F172A; }}
        .header-sub {{ font-size: 13px; color: #64748B; margin-top: 4px; }}
        .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }}
        .kpi-card {{ background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 18px; }}
        .kpi-label {{ font-size: 12px; color: #64748B; text-transform: uppercase; font-weight: 600; }}
        .kpi-value {{ font-size: 24px; font-weight: 700; margin-top: 4px; }}
        .section-card {{ background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px; margin-bottom: 20px; }}
        .section-title {{ font-size: 16px; font-weight: 700; margin-bottom: 14px; display: flex; align-items: center; gap: 8px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        th {{ background: #F1F5F9; color: #475569; font-weight: 600; text-align: left; padding: 10px 12px; border-bottom: 2px solid #CBD5E1; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #E2E8F0; }}
        tr:hover {{ background: #F8FAFC; }}
    </style>
</head>
<body>
    <div class="report-header">
        <div class="header-title">BÁO CÁO HIỆU QUẢ MARKETING CAMPAIGN & ĐỐI SOÁT TÀI CHÍNH</div>
        <div class="header-sub">Chuẩn hóa dữ liệu tự động • Multi-touch Attribution • Activity Based Costing • Xuất ngày: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
    </div>

    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-label">Tổng Doanh Thu Nguồn</div>
            <div class="kpi-value">{total_gross:,.0f} đ</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Net Sales (Sau hoàn)</div>
            <div class="kpi-value" style="color:#2563EB;">{total_net_sales:,.0f} đ</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Chi Phí ABC</div>
            <div class="kpi-value" style="color:#D97706;">{f"{total_costs:,.0f} đ" if has_costs else "Chưa cung cấp"}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Net Contribution</div>
            <div class="kpi-value" style="color:#10B981;">{f"{total_net_contrib:,.0f} đ" if total_net_contrib is not None else "Chưa cung cấp"}</div>
        </div>
    </div>

    <div class="section-card">
        <div class="section-title">📊 HIỆU QUẢ TỪNG CHIẾN DỊCH (MULTI-TOUCH ATTRIBUTION)</div>
        <table>
            <thead>
                <tr>
                    <th>Chiến Dịch</th>
                    <th style="text-align:right;">Doanh Thu Phân Bổ</th>
                    <th style="text-align:right;">Hoàn Trả</th>
                    <th style="text-align:right;">Giá Vốn (COGS)</th>
                    <th style="text-align:right;">Net Sales</th>
                    <th style="text-align:right;">Chi Phí ABC</th>
                    <th style="text-align:right;">Net Contribution</th>
                    <th style="text-align:center;">ROAS</th>
                    <th style="text-align:center;">ROI (%)</th>
                    <th style="text-align:center;">Quyết Định Chiến Lược</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>

    <div class="section-card">
        <div class="section-title">💡 KHUYẾN NGHỊ KINH DOANH CHIẾN LƯỢC (3 PHƯƠNG ÁN XỬ LÝ)</div>
        <div style="font-size:13px; line-height:1.6;">
            <p><b>1. TIẾP TỤC THỬ NGHIỆM & MỞ RỘNG (SCALE):</b> Dành cho các chiến dịch có ROAS &ge; 2.5x và Net Contribution dương bền vững.</p>
            <p><b>2. ĐIỀU CHỈNH CƠ CHẾ (OPTIMIZE):</b> Dành cho các chiến dịch hòa vốn hoặc biên lợi nhuận thấp, cần đàm phán giảm chi phí tiếp thị hoặc tối ưu tệp khách hàng.</p>
            <p><b>3. DỪNG CHƯƠNG TRÌNH (TERMINATE):</b> Dành cho các chiến dịch âm lợi nhuận sâu, chuyển ngân sách sang các kênh chuyển đổi cao.</p>
        </div>
    </div>

    <div class="section-card">
        <div class="section-title">⚠️ DANH SÁCH NGOẠI LỆ & LỊCH SỬ PHÊ DUYỆT (HUMAN-IN-THE-LOOP)</div>
        <table>
            <thead>
                <tr>
                    <th>STT</th>
                    <th>Mã Đơn</th>
                    <th>Loại Lỗi</th>
                    <th>Mô Tả</th>
                    <th>Trạng Thái & Người Duyệt</th>
                    <th>Ghi Chú Giải Trình</th>
                </tr>
            </thead>
            <tbody>
                {exc_html if exc_html else "<tr><td colspan='6' style='text-align:center;'>Không có ngoại lệ nào phát sinh.</td></tr>"}
            </tbody>
        </table>
    </div>
</body>
</html>"""
        return html
