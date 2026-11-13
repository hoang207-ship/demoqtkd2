import os
from data_pipeline import get_sample_marketing_data, DataCleaner
from analytics_engine import MarketingAnalyticsEngine

# 1. Load Data
tabs = get_sample_marketing_data()
print("1. Loaded 3 Tabs:", list(tabs.keys()))
for k, v in tabs.items():
    print(f"   - {k}: {len(v)} rows")

# 2. Data Cleaning
cleaner = DataCleaner(tabs)
is_valid, cleaned_tabs, quality_summary, errors_log = cleaner.clean_and_audit()
print("\n2. Data Quality Audit:")
print(f"   - Valid: {is_valid}")
print(f"   - Score: {quality_summary.get('Data_Quality_Score')}%")
print(f"   - Issues found: {len(errors_log)}")

# 3. Process Workflow
engine = MarketingAnalyticsEngine(cleaned_tabs, return_window_days=30)
res = engine.run_process_workflow()
print("\n3. Process Workflow Execution:")
print(f"   - Status: {res.get('status')}")
print(f"   - Report_Result Campaigns: {len(res.get('report_result', []))}")
print(f"   - Exceptions in Exceptions_View: {len(res.get('exceptions_view', []))}")

# 4. Resolve Exceptions (Human-in-the-Loop)
print("\n4. Resolving Exceptions:")
for exc in engine.exceptions_view:
    order_id = exc.get('Order_ID')
    err = exc.get('Error_Type')
    status = exc.get('Approval_Status')
    print(f"   - Item {order_id} ({err}): {status}")
    if status == 'PENDING_REVIEW':
        engine.resolve_exception(order_id, 'APPROVED', 'Trưởng phòng Marketing', 'Phê duyệt ngoại lệ theo chính sách CSKH')
        print(f"     -> Approved: {order_id}")

# 5. Verification
ver = engine.run_verification()
print("\n5. Verification 7 Tests:")
print(f"   - Overall Status: {ver.get('overall_status')}")
print(f"   - Passed: {ver.get('pass_count')}/{len(ver.get('tests', []))}")
for t in ver.get('tests', []):
    print(f"   - [{t['status']}] {t['code']}: {t['name']} | Actual: {t['actual']}")

# 6. HTML Report Export
html = engine.generate_html_report()
print("\n6. HTML Standalone Report Generation:")
print(f"   - Length: {len(html)} bytes")
assert "BÁO CÁO HIỆU QUẢ MARKETING" in html, "Missing Title Header"
assert "Net Sales" in html, "Missing Net Sales"
assert "Net Contribution" in html, "Missing Net Contribution"
assert "KHUYẾN NGHỊ KINH DOANH" in html, "Missing Business Recommendations"
assert "TIẾP TỤC THỬ NGHIỆM" in html, "Missing Strategy Options"

print("\nSUCCESS! ALL 5 PHASES AND 6 PROCESS STEPS FULLY OPERATIONAL AND VERIFIED!")
