from data_pipeline import get_messy_testcase_08_data, DataCleaner
from analytics_engine import MarketingAnalyticsEngine

print("--- 1. NẠP DỮ LIỆU THỰC TẾ GIA HOA RAW MESSY ---")
raw_data = get_messy_testcase_08_data()
cleaner = DataCleaner(raw_data)
can_proceed, norm_data, quality_sum, errors, exceptions = cleaner.clean_and_normalize()

print(f"Chất lượng dữ liệu: {quality_sum['Data_Quality_Score']}% | Ngoại lệ phát hiện: {len(exceptions)}")

print("\n--- 2. KHỞI TẠO ĐỘNG CƠ PHÂN TÍCH (ANALYTICS ENGINE) ---")
engine = MarketingAnalyticsEngine(norm_data, initial_exceptions=exceptions, return_window_days=30)
res = engine.run_process_workflow()
print(f"Trạng thái Process: {res['status']}")
print(f"Số lượng bản ghi phân bổ chi tiết: {len(engine.detailed_attributed_df)}")
print(f"Số chiến dịch trong kết quả: {len(engine.report_result)}")

print("\n--- 3. KIỂM THỬ THẨM QUYỀN DUYỆT (ROLE-BASED APPROVAL) ---")
# Test TC14: Người không có thẩm quyền duyệt phải bị từ chối!
ok, msg = engine.resolve_exception("ORD-2003", "APPROVE", "Nhân viên thực tập", "Nguyen Van A", "Em xin duyệt đơn này")
print(f"Duyệt không có quyền: OK={ok} | Message: {msg}")
assert not ok, "Bảo mật thất bại: Người không có quyền vẫn duyệt được!"

# Test TC13: Phê duyệt hợp lệ bởi Trưởng phòng Marketing (có ghi chú)
for e in list(engine.exceptions_view):
    order_id = e["Order_ID"]
    sev = e.get("Severity")
    ok, msg = engine.resolve_exception(
        order_id,
        "APPROVE",
        "Trưởng phòng Marketing",
        "Trần Văn Trưởng",
        f"Đã thẩm định và chấp thuận ngoại lệ mức độ {sev} theo chính sách kinh doanh."
    )
    print(f"Duyệt {order_id} ({e['Error_Type']}): OK={ok}")

print(f"Ngoại lệ còn chờ duyệt: {len([e for e in engine.exceptions_view if e['Approval_Status'] == 'PENDING_REVIEW'])}")

print("\n--- 4. CHẠY 7 PHÉP KIỂM TOÁN TỰ ĐỘNG (VERIFICATION SUITE) ---")
ver = engine.run_verification()
print(f"Tổng kết Verification: {ver['overall_status']} (Pass: {ver['pass_count']}, Not Applicable: {ver['na_count']}, Fail: {ver['fail_count']})")
for t in ver["tests"]:
    print(f" - [{t['status']}] {t['code']}: {t['name']} | Actual: {t['actual']}")

assert ver["overall_status"] == "PASS", "Verification phải PASS sau khi toàn bộ ngoại lệ được duyệt!"

print("\n--- 5. XUẤT BÁO CÁO HTML STANDALONE ---")
html_out = engine.generate_html_report()
print(f"Độ dài file HTML: {len(html_out)} ký tự")
assert "BÁO CÁO HIỆU QUẢ MARKETING" in html_out
assert "Net Sales" in html_out
assert "SCALE" in html_out or "ORGANIC" in html_out

print("\n>>> KIỂM THỬ TOÀN DIỆN VỚI FILE GIA HOA MESSY TESTCASE 08 THÀNH CÔNG RỰC RỠ! <<<")

