from streamlit.testing.v1 import AppTest

PAGES = [
    "Overview (Tổng quan)", "Kết Nối Google Sheets", "Data Cleaning & Audit",
    "Process Workflow (6 Bước)", "Phê Duyệt Exceptions", "Verification Suite",
    "Báo Cáo Reports & Export", "Cài Đặt Settings",
]


def check(at, step):
    if at.exception:
        print(f"[FAIL] {step}:", [e.message for e in at.exception])
        raise SystemExit(1)
    print(f"[OK] {step}")


def nav(at, p):
    at.radio(key="nav_page").set_value(p).run()


def btn(at, key):
    return [b for b in at.button if b.key == key][0]


for dataset in ["messy", "ecom", "std"]:
    print(f"\n===== Dataset: {dataset} =====")
    at = AppTest.from_file("../app.py", default_timeout=120)
    at.run(); check(at, "Initial load")

    for p in PAGES:
        nav(at, p); check(at, f"Empty page: {p}")

    nav(at, PAGES[0])
    btn(at, f"qs_{dataset}").click().run(); check(at, "Quick load")
    assert at.session_state["data_status"] == "CONNECTED"

    btn(at, "ov_run_all").click().run(); check(at, "Clean + 6 steps")
    print("   cleaning:", at.session_state["cleaning_status"], "| process:", at.session_state["process_status"])

    for p in PAGES:
        nav(at, p); check(at, f"Page after process: {p}")

    nav(at, PAGES[4])
    for _ in range(60):
        pend = [e for e in at.session_state["exceptions_list"] if e.get("Approval_Status") == "PENDING_REVIEW"]
        if not pend:
            break
        at.text_area[0].input("Đã đối soát chứng từ gốc và chấp thuận")
        submit = [b for b in at.button if "Xác nhận" in str(b.label)][0]
        submit.click().run(); check(at, f"Approve (pending before: {len(pend)})")
    left = len([e for e in at.session_state["exceptions_list"] if e.get("Approval_Status") == "PENDING_REVIEW"])
    print("   pending left:", left)

    if at.session_state["process_status"] == "COMPLETED":
        nav(at, PAGES[5])
        btn(at, "btn_verify").click().run(); check(at, "Verification")
        print("   verification:", at.session_state["verification_status"])

        nav(at, PAGES[6]); check(at, "Report page")
        nav(at, PAGES[0]); check(at, "Dashboard final")
    else:
        assert at.session_state["cleaning_status"] == "FAILED"
        nav(at, PAGES[3]); check(at, "Process blocked on critical cleaning errors")
        assert btn(at, "btn_empty_proc_fail") is not None

    # Next-step button navigation works
    nav(at, PAGES[7])
    btn(at, "btn_reset").click().run(); check(at, "Reset session")
    assert at.session_state["data_status"] == "NOT_CONNECTED"

print("\nALL SMOKE TESTS PASSED")
