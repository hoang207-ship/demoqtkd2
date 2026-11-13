import pandas as pd
from data_pipeline import (
    DataCleaner,
    get_sample_marketing_data,
    get_messy_testcase_08_data,
    get_ecommerce_user_data,
)
from analytics_engine import MarketingAnalyticsEngine

print("=== BẮT ĐẦU 10 BÀI KIỂM THỬ DATA CLEANING & NORMALIZATION ===")

# ------------------------------------------------------------------
# TEST 1: Dữ liệu mô phỏng Google Sheets 9 tab
# ------------------------------------------------------------------
base = get_sample_marketing_data()
nine_tabs = {
    "Transactions": base["Transactions"],
    "Returns": base["Returns"],
    "Campaign_Costs": base["Campaign_Costs"],
    "Channels": pd.DataFrame({"Channel_Name": [" Facebook ", "Google  Ads"], "Status": ["Active", "Active"]}),
    "Customers": pd.DataFrame({"Customer_ID": ["C01", "C02"], "Join_Date": ["15/02/2026", "2026-02-16"]}),
    "Products": pd.DataFrame({"SKU": ["P1", "P2"], "Category": [" Beauty ", " Tech "]}),
    "Targets": pd.DataFrame({"Month": ["2026-01", "2026-02"], "Target_VND": [50000000, 60000000]}),
    "Summary": pd.DataFrame({"Metric": ["GMV"], "Value": [100000000]}),
    "Audit_Notes": pd.DataFrame({"Note_Date": ["01/03/2026"], "Reviewer": [" Vũ Ruy Hoàng "]}),
}
raw_snapshot = {k: v.copy(deep=True) for k, v in nine_tabs.items()}
cleaner1 = DataCleaner(nine_tabs)
can1, norm1, q1, err1, exc1 = cleaner1.clean_and_normalize()
assert q1["Total_Tabs_Count"] == 9 and q1["Tabs_Processed_Count"] == 9, f"Expected 9 tabs, got {q1}"
assert q1["Campaign_Data_Status"] in ("AVAILABLE", "MISSING_SOURCE_DATA")
print(f"[PASS] Test 1 (9-tab Google Sheets): Tabs={q1['Tabs_Processed_Count']}/{q1['Total_Tabs_Count']}, Status={q1['Status']}, Audit={q1['Audit_Log_Count']}")

# ------------------------------------------------------------------
# TEST 2: Một hoặc nhiều tab không có dữ liệu (rỗng)
# ------------------------------------------------------------------
empty_tabs = {
    "Transactions": base["Transactions"].copy(deep=True),
    "Returns": pd.DataFrame(columns=["Return_ID", "Order_ID", "Return_Amount"]),
    "Campaign_Costs": base["Campaign_Costs"].copy(deep=True),
    "Empty_Aux": pd.DataFrame(),
}
cleaner2 = DataCleaner(empty_tabs)
can2, norm2, q2, err2, exc2 = cleaner2.clean_and_normalize()
assert can2 is True
assert cleaner2.tab_statuses["Returns"]["Status"] == "WARNING"
assert cleaner2.tab_statuses["Empty_Aux"]["Status"] == "WARNING"
print(f"[PASS] Test 2 (Empty tabs): Returns={cleaner2.tab_statuses['Returns']['Status']}, Empty_Aux={cleaner2.tab_statuses['Empty_Aux']['Status']}, Overall={q2['Status']}")

# ------------------------------------------------------------------
# TEST 3: Thiếu cột quan trọng (không có Transactions / thiếu cột doanh thu)
# ------------------------------------------------------------------
missing_col_tabs = {
    "Channels": pd.DataFrame({"Channel_Name": ["Facebook", "TikTok"]}),
    "Notes": pd.DataFrame({"Note": ["Test không có tab Transactions"]}),
}
cleaner3 = DataCleaner(missing_col_tabs)
can3, norm3, q3, err3, exc3 = cleaner3.clean_and_normalize()
assert can3 is False
assert q3["Status"] == "FAILED"
assert q3["Campaign_Data_Status"] == "MISSING_SOURCE_DATA"
assert any(e["Error_Type"] == "MISSING_TRANSACTIONS_TAB" for e in err3)
print(f"[PASS] Test 3 (Missing Transactions/Revenue col - No UnboundLocalError): Status={q3['Status']}, Campaign_Data_Status={q3['Campaign_Data_Status']}")

# ------------------------------------------------------------------
# TEST 4: Ngày tháng & tiền tệ không đồng nhất
# ------------------------------------------------------------------
inconsistent_df = pd.DataFrame([
    {"Order_ID": "ORD-A1", "Order_Date": "2026-01-05", "Order_Value": "1.500.000 VNĐ", "Campaign_List": "PG01; PG02", "Campaign_Count": 2},
    {"Order_ID": "ORD-A2", "Order_Date": "06/01/2026", "Order_Value": "2.5 triệu", "Campaign_List": "PG01 / PG03", "Campaign_Count": 2},
    {"Order_ID": "ORD-A3", "Order_Date": "07-01-2026", "Order_Value": 800000, "Campaign_List": "PG01", "Campaign_Count": 1},
    {"Order_ID": "ORD-A4", "Order_Date": "bad-date", "Order_Value": "2.500 VNĐ", "Campaign_List": "PG02", "Campaign_Count": 1},
])
cleaner4 = DataCleaner({"Transactions": inconsistent_df})
can4, norm4, q4, err4, exc4 = cleaner4.clean_and_normalize()
tx4 = norm4["Normalized_Transactions"]
assert tx4["Order_Date"].iloc[:3].tolist() == ["2026-01-05", "2026-01-06", "2026-01-07"]
assert pd.isna(tx4["Order_Date"].iloc[3])
assert list(tx4["Order_Value"]) == [1500000.0, 2500000.0, 800000.0, 2500.0]
print(f"[PASS] Test 4 (Inconsistent dates & currencies): Dates={list(tx4['Order_Date'])}, Values={list(tx4['Order_Value'])}")

# ------------------------------------------------------------------
# TEST 5: Dữ liệu trùng lặp (không tự ý xóa)
# ------------------------------------------------------------------
dup_df = pd.DataFrame([
    {"Order_ID": "ORD-DUP", "Order_Date": "2026-01-10", "Order_Value": 500000, "Campaign_List": "PG01", "Campaign_Count": 1},
    {"Order_ID": "ORD-DUP", "Order_Date": "2026-01-10", "Order_Value": 500000, "Campaign_List": "PG01", "Campaign_Count": 1},
])
cleaner5 = DataCleaner({"Transactions": dup_df})
can5, norm5, q5, err5, exc5 = cleaner5.clean_and_normalize()
assert len(norm5["Normalized_Transactions"]) == 2, "Không được tự ý xóa bản ghi trùng"
assert q5["Duplicate_Rows_Count"] >= 2
assert any(e["Error_Type"] == "DUPLICATE_ORDER_ID" for e in exc5)
print(f"[PASS] Test 5 (Duplicates preserved & flagged): Rows={len(norm5['Normalized_Transactions'])}, Dups={q5['Duplicate_Rows_Count']}")

# ------------------------------------------------------------------
# TEST 6: Dữ liệu thiếu và ngoại lệ
# ------------------------------------------------------------------
messy_tabs = get_messy_testcase_08_data()
cleaner6 = DataCleaner(messy_tabs)
can6, norm6, q6, err6, exc6 = cleaner6.clean_and_normalize()
assert q6["Exceptions_Count"] > 0 and q6["Missing_Fields_Count"] > 0
assert q6["Status"] == "FAILED"
print(f"[PASS] Test 6 (Missing & Exceptions): Missing={q6['Missing_Fields_Count']}, Exceptions={q6['Exceptions_Count']}, Status={q6['Status']}")

# ------------------------------------------------------------------
# TEST 7: Một tab lỗi nhưng các tab khác vẫn xử lý được
# ------------------------------------------------------------------
faulty_tabs = {
    "Transactions": base["Transactions"].copy(deep=True),
    "Broken_Aux": pd.DataFrame({"Col": [1]}),
    "Good_Aux": pd.DataFrame({"Kenh": ["  Shopee  "], "Ngay": ["01/04/2026"]}),
}
cleaner7 = DataCleaner(faulty_tabs)
# Ghi đè raw_tabs để mô phỏng lỗi runtime ở 1 tab độc lập
cleaner7.raw_tabs["Broken_Aux"] = object()
cleaner7.classification["tab_roles"]["Broken_Aux"] = "Unknown"
can7, norm7, q7, err7, exc7 = cleaner7.clean_and_normalize()
assert norm7["Normalized_Transactions"] is not None and len(norm7["Normalized_Transactions"]) == 7
assert cleaner7.tab_statuses["Good_Aux"]["Status"] == "SUCCESS"
assert cleaner7.tab_statuses["Broken_Aux"]["Status"] == "FAILED"
assert q7["Status"] == "FAILED"  # Không báo SUCCESS khi còn tab lỗi
print(f"[PASS] Test 7 (Fault isolation across tabs): Tx={len(norm7['Normalized_Transactions'])}, Good_Aux={cleaner7.tab_statuses['Good_Aux']['Status']}, Broken_Aux={cleaner7.tab_statuses['Broken_Aux']['Status']}")

# ------------------------------------------------------------------
# TEST 8: Idempotency & Bảo toàn Raw Data
# ------------------------------------------------------------------
c8_a = DataCleaner(nine_tabs)
_, norm8_a, q8_a, _, _ = c8_a.clean_and_normalize()
_, norm8_b, q8_b, _, _ = c8_a.clean_and_normalize()
assert q8_a["Total_Net_Sales_VND"] == q8_b["Total_Net_Sales_VND"]
assert q8_a["Audit_Log_Count"] == q8_b["Audit_Log_Count"]
for k in nine_tabs:
    pd.testing.assert_frame_equal(nine_tabs[k], raw_snapshot[k])
print(f"[PASS] Test 8 (Idempotent & Raw Data preserved 100%): NetSales={q8_a['Total_Net_Sales_VND']:,.0f}")

# ------------------------------------------------------------------
# TEST 9 & TEST 10: Process 6 bước + Phê duyệt + Verification Suite + Audit Log
# ------------------------------------------------------------------
assert len(cleaner1.audit_log) > 0, "Audit Log phải ghi nhận các thay đổi"
required_audit_keys = {"Tab", "Column", "Row_Index", "Record_ID", "Raw_Value", "Cleaned_Value", "Reason", "Method", "Timestamp"}
assert required_audit_keys.issubset(set(cleaner1.audit_log[0].keys()))

engine9 = MarketingAnalyticsEngine(norm1, initial_exceptions=exc1, return_window_days=30)
res9 = engine9.run_process_workflow()
assert res9["status"] == "COMPLETED"
for e in list(engine9.exceptions_view):
    if e.get("Approval_Status") == "PENDING_REVIEW":
        ok, _ = engine9.resolve_exception(e["Order_ID"], "APPROVE", "Trưởng phòng Marketing", "Vũ Ruy Hoàng", "Đã đối soát")
        assert ok
ver10 = engine9.run_verification()
assert ver10["overall_status"] == "PASS"
print(f"[PASS] Test 9 & 10 (6-step Process + Verification + Audit Log): Process={res9['status']}, Verification={ver10['overall_status']}, AuditEntries={len(cleaner1.audit_log)}")
print("\n>>> TẤT CẢ 10/10 BÀI KIỂM THỬ ĐẠT 100% <<<")
