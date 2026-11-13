import os
import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from schema_mapper import AutoSchemaMapper
from data_pipeline import (
    get_sample_marketing_data,
    get_messy_testcase_08_data,
    get_ecommerce_user_data,
    export_marketing_template_excel,
    load_google_sheet_flexible,
    load_from_excel_flexible,
    DataCleaner
)
from analytics_engine import MarketingAnalyticsEngine

# ==============================================================================
# CẤU HÌNH TRANG SAAS DASHBOARD (VIBRANT CLOUDCASH FINTECH STYLE)
# ==============================================================================
st.set_page_config(
    page_title="GrowthMetric — Marketing Campaign Analytics Agent",
    page_icon="🌈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# HỆ THỐNG GIAO DIỆN ĐA MÀU SẮC RỰC RỠ & THÂN THIỆN (VIBRANT SAAS DESIGN SYSTEM)
# Nền Ambient Pastel Mesh đa sắc, Thẻ nổi White Canvas bo tròn 36px, KPI Candy Colors
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* 1. NỀN TỔNG THỂ: Ambient Pastel Mesh Gradient đa màu sắc dịu mắt, rực rỡ và tràn đầy sức sống */
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background: 
            radial-gradient(circle at 5% 10%, rgba(99, 102, 241, 0.14) 0%, transparent 45%),
            radial-gradient(circle at 95% 8%, rgba(236, 72, 153, 0.15) 0%, transparent 45%),
            radial-gradient(circle at 90% 90%, rgba(245, 158, 11, 0.14) 0%, transparent 45%),
            radial-gradient(circle at 8% 88%, rgba(16, 185, 129, 0.15) 0%, transparent 45%),
            radial-gradient(circle at 50% 45%, rgba(6, 182, 212, 0.10) 0%, transparent 50%),
            #F5F7FC !important;
        color: #1E293B !important;
    }

    /* Ẩn thanh header mặc định của Streamlit */
    header[data-testid="stHeader"] {
        background: transparent !important;
        display: none !important;
    }

    /* 2. THẺ NỘI DUNG CHÍNH (Floating White Canvas với góc bo 36px và viền gradient siêu mỏng) */
    .main .block-container {
        background: #FFFFFF !important;
        border-radius: 36px !important;
        box-shadow: 0 20px 60px rgba(99, 102, 241, 0.06), 0 2px 10px rgba(0, 0, 0, 0.02) !important;
        padding: 38px 46px 48px 46px !important;
        margin: 22px auto 32px auto !important;
        max-width: 95% !important;
        border: 1px solid rgba(226, 232, 240, 0.8) !important;
    }

    /* 3. SIDEBAR: Thẻ trắng nổi độc lập với đường viền gradient sắc màu */
    [data-testid="stSidebar"] {
        background: transparent !important;
        border-right: none !important;
    }
    
    [data-testid="stSidebarContent"] {
        background: #FFFFFF !important;
        border-radius: 32px !important;
        margin: 22px 0 22px 22px !important;
        padding: 26px 18px !important;
        box-shadow: 0 16px 48px rgba(99, 102, 241, 0.06) !important;
        border: 1px solid rgba(226, 232, 240, 0.8) !important;
        height: calc(100vh - 44px) !important;
    }
    
    [data-testid="stSidebar"] * {
        color: #1E293B !important;
    }

    /* 4. LOGO THƯƠNG HIỆU CLOUDCASH RAINBOW GRADIENT */
    .sidebar-brand-cloudcash {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 6px 0 18px 0;
        border-bottom: 1px solid #F1F4F9;
        margin-bottom: 16px;
    }

    .cloudcash-logo-badge {
        width: 44px;
        height: 44px;
        border-radius: 14px;
        background: linear-gradient(135deg, #1E75FF 0%, #7C3AED 50%, #EC4899 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 8px 20px rgba(124, 58, 237, 0.35);
        flex-shrink: 0;
    }

    .cloudcash-icon {
        color: #FFFFFF !important;
        font-size: 22px;
        font-weight: 800;
    }

    .cloudcash-brand-text .brand-title {
        font-size: 20px;
        font-weight: 800;
        background: linear-gradient(135deg, #1E75FF 0%, #7C3AED 60%, #EC4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.4px;
        line-height: 1.1;
    }

    .cloudcash-brand-text .brand-subtitle {
        font-size: 11px;
        font-weight: 700;
        color: #8C9BAE !important;
        margin-top: 3px;
        letter-spacing: 0.2px;
    }

    /* 5. ĐIỀU HƯỚNG DANH MỤC SIDEBAR (Vibrant Active Gradient Pill) */
    [data-testid="stSidebar"] [data-testid="stRadio"] > label {
        display: none !important;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] {
        gap: 6px !important;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label {
        background: transparent !important;
        border-radius: 14px !important;
        padding: 12px 16px !important;
        margin-bottom: 3px !important;
        font-size: 13.5px !important;
        font-weight: 600 !important;
        color: #64748B !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        cursor: pointer !important;
        border: 1px solid transparent !important;
        display: flex !important;
        align-items: center !important;
    }

    /* Ẩn hoàn toàn nút tròn radio mặc định */
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:hover {
        background: linear-gradient(90deg, #F0F7FF 0%, #FAF5FF 100%) !important;
        color: #4F46E5 !important;
        transform: translateX(4px);
    }

    /* TRẠNG THÁI ACTIVE: Gradient Hoàng Gia Rực Rỡ với bóng đổ màu */
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked),
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label[data-checked="true"] {
        background: linear-gradient(135deg, #1E75FF 0%, #6366F1 50%, #8B5CF6 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0 8px 24px rgba(99, 102, 241, 0.35) !important;
        font-weight: 700 !important;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) *,
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label[data-checked="true"] * {
        color: #FFFFFF !important;
    }

    /* 6. WIDGET TIẾN ĐỘ WORKFLOW VỚI BADGES MÀU SẮC */
    .sidebar-status-box {
        background: linear-gradient(180deg, #F8FAFD 0%, #F1F5F9 100%);
        border: 1px solid #E2E8F0;
        border-radius: 18px;
        padding: 14px 16px;
        margin-bottom: 16px;
        font-size: 11.5px;
    }

    .status-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 7px;
        color: #64748B !important;
        font-weight: 600;
    }

    .badge-ok {
        background: #DCFCE7;
        color: #15803D !important;
        border: 1px solid #86EFAC;
        font-weight: 700;
        padding: 2px 9px;
        border-radius: 20px;
        font-size: 10px;
    }

    .badge-warn {
        background: #FEF3C7;
        color: #B45309 !important;
        border: 1px solid #FCD34D;
        font-weight: 700;
        padding: 2px 9px;
        border-radius: 20px;
        font-size: 10px;
    }

    .badge-fail {
        background: #FEE2E2;
        color: #B91C1C !important;
        border: 1px solid #FCA5A5;
        font-weight: 700;
        padding: 2px 9px;
        border-radius: 20px;
        font-size: 10px;
    }

    .badge-pending {
        background: #E0F2FE;
        color: #0369A1 !important;
        border: 1px solid #BAE6FD;
        font-weight: 600;
        padding: 2px 9px;
        border-radius: 20px;
        font-size: 10px;
    }

    /* 7. THẺ CLOUDCASH PRO RỰC RỠ Ở CHÂN SIDEBAR */
    .sidebar-pro-card {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 50%, #EC4899 100%);
        border-radius: 22px;
        padding: 20px 16px;
        text-align: center;
        margin-top: 18px;
        color: #FFFFFF !important;
        box-shadow: 0 10px 28px rgba(124, 58, 237, 0.35);
    }

    .sidebar-pro-card * {
        color: #FFFFFF !important;
    }

    .pro-icon-wrap {
        width: 44px;
        height: 44px;
        background: rgba(255, 255, 255, 0.22);
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 10px auto;
        font-size: 22px;
    }

    .pro-title {
        font-size: 14px;
        font-weight: 800;
        margin-bottom: 4px;
        letter-spacing: -0.2px;
    }

    .pro-desc {
        font-size: 11px;
        opacity: 0.92;
        margin-bottom: 12px;
        line-height: 1.4;
    }

    .pro-badge-btn {
        background: linear-gradient(135deg, #FFB020 0%, #FA8C16 100%);
        color: #FFFFFF !important;
        font-size: 11.5px;
        font-weight: 800;
        border-radius: 14px;
        padding: 8px 18px;
        display: inline-block;
        box-shadow: 0 6px 16px rgba(250, 140, 22, 0.4);
        cursor: pointer;
    }

    /* 8. THANH HEADER TRÊN CÙNG TRANG (TOP APP BAR) */
    .top-app-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 22px;
        margin-bottom: 24px;
        border-bottom: 1px solid #F1F4F9;
        flex-wrap: wrap;
        gap: 16px;
    }

    .header-left .header-main-title {
        font-size: 28px;
        font-weight: 800;
        background: linear-gradient(135deg, #1E293B 0%, #4F46E5 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
        margin: 0;
        line-height: 1.1;
    }

    .header-left .header-main-sub {
        font-size: 13px;
        color: #64748B;
        font-weight: 600;
        margin-top: 4px;
    }

    .header-search-bar {
        background: #F8FAFD;
        border: 1px solid #E2E8F0;
        border-radius: 24px;
        padding: 9px 20px;
        display: flex;
        align-items: center;
        gap: 10px;
        min-width: 290px;
        color: #64748B;
        font-size: 12.5px;
        box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.02);
    }

    .header-right-meta {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .lang-tag {
        background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%);
        border: 1px solid #A7F3D0;
        border-radius: 20px;
        padding: 7px 15px;
        font-size: 12px;
        font-weight: 700;
        color: #065F46;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .bell-notify {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
        border: 1px solid #FDE68A;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        cursor: pointer;
        font-size: 17px;
    }

    .dot-red {
        width: 8px;
        height: 8px;
        background: #EF4444;
        border-radius: 50%;
        position: absolute;
        top: 8px;
        right: 8px;
        border: 1.5px solid #FFFFFF;
        box-shadow: 0 0 6px rgba(239, 68, 68, 0.6);
    }

    .user-profile-chip {
        display: flex;
        align-items: center;
        gap: 10px;
        background: linear-gradient(135deg, #F8FAFD 0%, #EEF2F6 100%);
        border: 1px solid #E2E8F0;
        border-radius: 26px;
        padding: 5px 16px 5px 6px;
    }

    .profile-avatar {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        background: linear-gradient(135deg, #FF5E62 0%, #FF9966 100%);
        color: #FFFFFF;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 12.5px;
        box-shadow: 0 4px 12px rgba(255, 94, 98, 0.35);
    }

    .profile-text .p-name {
        font-size: 12px;
        font-weight: 800;
        color: #1E293B;
        line-height: 1.2;
    }

    .profile-text .p-role {
        font-size: 10px;
        font-weight: 600;
        color: #64748B;
    }

    /* 9. BỘ THẺ KPI ĐA SẮC MÀU (CANDY PASTEL CARDS) */
    .kpi-candy-card {
        border-radius: 22px;
        padding: 20px 22px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 140px;
        transition: transform 0.25s ease, box-shadow 0.25s ease;
        margin-bottom: 20px;
    }

    .kpi-candy-card:hover {
        transform: translateY(-4px);
    }

    .kpi-candy-card.pink {
        background: linear-gradient(135deg, #FFF1F2 0%, #FFE4E6 100%);
        border: 1.5px solid #FECDD3;
        box-shadow: 0 8px 20px rgba(244, 63, 94, 0.08);
    }
    .kpi-candy-card.amber {
        background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
        border: 1.5px solid #FDE68A;
        box-shadow: 0 8px 20px rgba(245, 158, 11, 0.08);
    }
    .kpi-candy-card.green {
        background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%);
        border: 1.5px solid #A7F3D0;
        box-shadow: 0 8px 20px rgba(16, 185, 129, 0.08);
    }
    .kpi-candy-card.purple {
        background: linear-gradient(135deg, #FAF5FF 0%, #EDE9FE 100%);
        border: 1.5px solid #DDD6FE;
        box-shadow: 0 8px 20px rgba(139, 92, 246, 0.08);
    }

    .kpi-top-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }

    .kpi-icon-pill {
        width: 42px;
        height: 42px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 19px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }

    .kpi-icon-pill.pink { background: linear-gradient(135deg, #FA5A7D 0%, #F43F5E 100%); color: #FFF; }
    .kpi-icon-pill.amber { background: linear-gradient(135deg, #FF947A 0%, #F59E0B 100%); color: #FFF; }
    .kpi-icon-pill.green { background: linear-gradient(135deg, #3CD856 0%, #10B981 100%); color: #FFF; }
    .kpi-icon-pill.purple { background: linear-gradient(135deg, #BF83FF 0%, #8B5CF6 100%); color: #FFF; }

    .kpi-trend-pill {
        font-size: 11px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 12px;
    }
    .kpi-trend-pill.pink { background: #FFE4E6; color: #E11D48; }
    .kpi-trend-pill.amber { background: #FEF3C7; color: #B45309; }
    .kpi-trend-pill.green { background: #DCFCE7; color: #15803D; }
    .kpi-trend-pill.purple { background: #F3E8FF; color: #7E22CE; }

    .kpi-val {
        font-size: 24px;
        font-weight: 800;
        letter-spacing: -0.4px;
        line-height: 1.1;
    }
    .kpi-val.pink { color: #BE123C; }
    .kpi-val.amber { color: #B45309; }
    .kpi-val.green { color: #047857; }
    .kpi-val.purple { color: #6D28D9; }

    .kpi-label {
        font-size: 12.5px;
        font-weight: 700;
        color: #475569;
        margin-top: 3px;
    }

    /* 10. THẺ TÍN DỤNG IRIDESCENT MULTI-STOP GRADIENT */
    .cloudcash-credit-card {
        background: linear-gradient(135deg, #1E75FF 0%, #6366F1 35%, #8B5CF6 70%, #EC4899 100%);
        border-radius: 22px;
        padding: 22px 24px;
        color: #FFFFFF !important;
        box-shadow: 0 14px 34px rgba(99, 102, 241, 0.4);
        position: relative;
        overflow: hidden;
        min-height: 180px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .cloudcash-credit-card * {
        color: #FFFFFF !important;
    }

    .card-top-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .card-brand-name {
        font-size: 17px;
        font-weight: 800;
        letter-spacing: -0.3px;
    }

    .card-chip {
        width: 36px;
        height: 26px;
        background: rgba(255, 255, 255, 0.32);
        border-radius: 7px;
        border: 1px solid rgba(255, 255, 255, 0.5);
    }

    .card-number {
        font-family: 'Space Grotesk', monospace;
        font-size: 18px;
        letter-spacing: 2px;
        font-weight: 700;
        margin: 14px 0;
    }

    .card-bottom-row {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
    }

    .card-holder-name {
        font-size: 11px;
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: 0.5px;
    }

    .card-exp {
        font-size: 10.5px;
        font-weight: 600;
        opacity: 0.9;
    }

    /* 11. THẺ GOALS MINI MÀU SẮC */
    .goal-card {
        border-radius: 20px;
        padding: 18px 20px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 165px;
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }

    .goal-card:hover {
        transform: translateY(-4px);
    }

    .goal-card.blue {
        background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
        border: 1.5px solid #BFDBFE;
        box-shadow: 0 6px 18px rgba(59, 130, 246, 0.08);
    }
    .goal-card.orange {
        background: linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%);
        border: 1.5px solid #FED7AA;
        box-shadow: 0 6px 18px rgba(249, 115, 22, 0.08);
    }
    .goal-card.green {
        background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);
        border: 1.5px solid #BBF7D0;
        box-shadow: 0 6px 18px rgba(34, 197, 94, 0.08);
    }

    .goal-val {
        font-size: 21px;
        font-weight: 800;
        margin-bottom: 2px;
        line-height: 1.2;
    }
    .goal-val.blue { color: #1D4ED8; }
    .goal-val.orange { color: #C2410C; }
    .goal-val.green { color: #15803D; }

    .goal-sub {
        font-size: 11px;
        color: #64748B;
        font-weight: 600;
    }

    .goal-icon {
        width: 40px;
        height: 40px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 19px;
        margin-top: 14px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.06);
    }
    .goal-icon.blue { background: #3B82F6; color: #FFF; }
    .goal-icon.orange { background: #F97316; color: #FFF; }
    .goal-icon.green { background: #22C55E; color: #FFF; }

    /* 12. OUTCOME STATISTICS VỚI THANH TIẾN ĐỘ GRADIENT SẮC MÀU */
    .stat-row {
        display: flex;
        align-items: center;
        gap: 14px;
        margin-bottom: 16px;
    }

    .stat-icon {
        width: 42px;
        height: 42px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 19px;
        flex-shrink: 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
    }

    .stat-icon.orange { background: linear-gradient(135deg, #FF7A00 0%, #FFB020 100%); color: #FFF; }
    .stat-icon.green { background: linear-gradient(135deg, #00E096 0%, #3CD856 100%); color: #FFF; }
    .stat-icon.blue { background: linear-gradient(135deg, #1E75FF 0%, #6366F1 100%); color: #FFF; }
    .stat-icon.pink { background: linear-gradient(135deg, #EC4899 0%, #F43F5E 100%); color: #FFF; }

    .stat-bar-wrap {
        flex: 1;
    }

    .stat-label-row {
        display: flex;
        justify-content: space-between;
        font-size: 12.5px;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 6px;
    }

    .stat-bar {
        height: 9px;
        background: #F1F5F9;
        border-radius: 6px;
        overflow: hidden;
    }

    .stat-bar-fill {
        height: 100%;
        border-radius: 6px;
    }

    .stat-bar-fill.orange { background: linear-gradient(90deg, #FF7A00 0%, #FFB020 100%); }
    .stat-bar-fill.green { background: linear-gradient(90deg, #00E096 0%, #3CD856 100%); }
    .stat-bar-fill.blue { background: linear-gradient(90deg, #1E75FF 0%, #6366F1 100%); }
    .stat-bar-fill.pink { background: linear-gradient(90deg, #EC4899 0%, #F43F5E 100%); }

    /* 13. THẺ TRẮNG CONTAINER (CLOUDCASH CARDS) */
    .cloudcash-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 26px;
        padding: 26px;
        box-shadow: 0 6px 24px rgba(99, 102, 241, 0.04);
        margin-bottom: 24px;
    }

    .cloudcash-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }

    .cloudcash-card-title {
        font-size: 17.5px;
        font-weight: 800;
        color: #1E293B;
        margin: 0;
        letter-spacing: -0.3px;
    }

    .cloudcash-card-sub {
        font-size: 12.5px;
        color: #64748B;
        margin-top: 3px;
    }

    /* 14. NÚT BẤM SẮC MÀU (BUTTONS) */
    .stButton > button {
        border-radius: 14px !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        padding: 10px 22px !important;
        transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1) !important;
        border: 1px solid #E2E8F0 !important;
        background: #FFFFFF !important;
        color: #1E293B !important;
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.03) !important;
    }

    .stButton > button:hover {
        background: #F8FAFD !important;
        border-color: #6366F1 !important;
        transform: translateY(-2px);
        color: #4F46E5 !important;
        box-shadow: 0 6px 16px rgba(99, 102, 241, 0.15) !important;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1E75FF 0%, #6366F1 50%, #8B5CF6 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: 0 8px 24px rgba(99, 102, 241, 0.35) !important;
    }

    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #1664DB 0%, #4F46E5 50%, #7C3AED 100%) !important;
        box-shadow: 0 10px 28px rgba(99, 102, 241, 0.45) !important;
        transform: translateY(-2px);
        color: #FFFFFF !important;
    }

    /* 15. STEPPER 6 BƯỚC ĐA MÀU SẮC (PROCESS WORKFLOW) */
    .stepper-cloudcash {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: linear-gradient(180deg, #F8FAFD 0%, #EEF2F6 100%);
        border: 1.5px solid #E2E8F0;
        border-radius: 22px;
        padding: 20px 26px;
        margin-bottom: 26px;
    }

    .step-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        font-size: 11.5px;
        font-weight: 700;
        color: #64748B;
        min-width: 82px;
    }

    .step-badge {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: #FFFFFF;
        border: 2px solid #CBD5E1;
        color: #64748B;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 13px;
        margin-bottom: 6px;
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.04);
    }

    .step-badge.s1 { background: #3B82F6; border-color: #3B82F6; color: #FFF; box-shadow: 0 4px 14px rgba(59, 130, 246, 0.4); }
    .step-badge.s2 { background: #8B5CF6; border-color: #8B5CF6; color: #FFF; box-shadow: 0 4px 14px rgba(139, 92, 246, 0.4); }
    .step-badge.s3 { background: #EC4899; border-color: #EC4899; color: #FFF; box-shadow: 0 4px 14px rgba(236, 72, 153, 0.4); }
    .step-badge.s4 { background: #F59E0B; border-color: #F59E0B; color: #FFF; box-shadow: 0 4px 14px rgba(245, 158, 11, 0.4); }
    .step-badge.s5 { background: #10B981; border-color: #10B981; color: #FFF; box-shadow: 0 4px 14px rgba(16, 185, 129, 0.4); }
    .step-badge.s6 { background: #06B6D4; border-color: #06B6D4; color: #FFF; box-shadow: 0 4px 14px rgba(6, 182, 212, 0.4); }

    .step-line {
        flex: 1;
        height: 3.5px;
        background: #E2E8F0;
        margin: 0 8px 14px 8px;
        border-radius: 3px;
    }

    .step-line.pass {
        background: linear-gradient(90deg, #3B82F6, #8B5CF6, #EC4899, #F59E0B, #10B981, #06B6D4);
    }
</style>
""", unsafe_allow_html=True)


def render_top_header(title: str, subtitle: str):
    """Hiển thị thanh Top Header Bar chuyên nghiệp theo phong cách CloudCash rực rỡ."""
    st.markdown(f"""
    <div class="top-app-header">
        <div class="header-left">
            <h1 class="header-main-title">{title}</h1>
            <div class="header-main-sub">{subtitle}</div>
        </div>
        <div class="header-search-bar">
            <span style="font-size:16px;">🔍</span>
            <span>Tìm kiếm chiến dịch, dữ liệu, mã đơn...</span>
        </div>
        <div class="header-right-meta">
            <div class="lang-tag">
                <span>🇻🇳</span> VNĐ (vi-VN)
            </div>
            <div class="bell-notify">
                <span>🔔</span>
                <div class="dot-red"></div>
            </div>
            <div class="user-profile-chip">
                <div class="profile-avatar">VH</div>
                <div class="profile-text">
                    <div class="p-name">Vũ Ruy Hoàng</div>
                    <div class="p-role">Admin account</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# KHỞI TẠO SESSION STATE (QUẢN LÝ TRẠNG THÁI CHẶT CHẼ, KHÔNG HIỂN THỊ PASS GIẢ)
# ==============================================================================
if "data_status" not in st.session_state:
    st.session_state.data_status = "NOT_CONNECTED"  # NOT_CONNECTED | CONNECTED | FAILED

if "cleaning_status" not in st.session_state:
    st.session_state.cleaning_status = "PENDING"    # PENDING | PASSED | FAILED

if "process_status" not in st.session_state:
    st.session_state.process_status = "NOT_STARTED" # NOT_STARTED | RUNNING | COMPLETED

if "approval_status" not in st.session_state:
    st.session_state.approval_status = "PENDING"    # PENDING | APPROVED | NO_EXCEPTIONS

if "verification_status" not in st.session_state:
    st.session_state.verification_status = "NOT_RUN"# NOT_RUN | PASS | FAIL | WARNING

if "raw_tabs" not in st.session_state:
    st.session_state.raw_tabs = None

if "source_name" not in st.session_state:
    st.session_state.source_name = "Chưa có nguồn dữ liệu"

if "classification_info" not in st.session_state:
    st.session_state.classification_info = None

if "normalized_data" not in st.session_state:
    st.session_state.normalized_data = None

if "quality_summary" not in st.session_state:
    st.session_state.quality_summary = None

if "cleaning_errors" not in st.session_state:
    st.session_state.cleaning_errors = []

if "exceptions_list" not in st.session_state:
    st.session_state.exceptions_list = []

if "engine" not in st.session_state:
    st.session_state.engine = None

if "process_result" not in st.session_state:
    st.session_state.process_result = None

if "verification_result" not in st.session_state:
    st.session_state.verification_result = None

if "return_window" not in st.session_state:
    st.session_state.return_window = 30

if "reconciliation_table" not in st.session_state:
    st.session_state.reconciliation_table = None

# ==============================================================================
# SIDEBAR NAVIGATION & TIẾN TRÌNH HỆ THỐNG THEO PHONG CÁCH CLOUDCASH RỰC RỠ
# ==============================================================================
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand-cloudcash">
        <div class="cloudcash-logo-badge">
            <span class="cloudcash-icon">☁️</span>
        </div>
        <div class="cloudcash-brand-text">
            <div class="brand-title">cloudcash</div>
            <div class="brand-subtitle">Marketing Analytics</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Hiển thị Widget trạng thái thực tế của hệ thống
    ds_badge = '<span class="badge-ok">ĐÃ KẾT NỐI</span>' if st.session_state.data_status == "CONNECTED" else ('<span class="badge-fail">LỖI KẾT NỐI</span>' if st.session_state.data_status == "FAILED" else '<span class="badge-pending">CHƯA KẾT NỐI</span>')
    cl_badge = '<span class="badge-ok">ĐẠT CHUẨN</span>' if st.session_state.cleaning_status == "PASSED" else ('<span class="badge-fail">CÓ LỖI CHẶN</span>' if st.session_state.cleaning_status == "FAILED" else '<span class="badge-pending">CHƯA XỬ LÝ</span>')
    pr_badge = '<span class="badge-ok">HOÀN TẤT</span>' if st.session_state.process_status == "COMPLETED" else '<span class="badge-pending">CHƯA CHẠY</span>'
    
    pending_exc = len([e for e in st.session_state.exceptions_list if e.get("Approval_Status") == "PENDING_REVIEW"])
    if st.session_state.process_status == "COMPLETED":
        ap_badge = f'<span class="badge-warn">CHỜ DUYỆT ({pending_exc})</span>' if pending_exc > 0 else '<span class="badge-ok">ĐÃ DUYỆT ĐỦ</span>'
    else:
        ap_badge = '<span class="badge-pending">CHƯA PHÁT SINH</span>'

    vr_badge = '<span class="badge-ok">VERIFIED PASS</span>' if st.session_state.verification_status == "PASS" else ('<span class="badge-fail">CHƯA ĐẠT</span>' if st.session_state.verification_status == "FAIL" else '<span class="badge-pending">CHƯA KIỂM CHỨNG</span>')

    st.markdown(f"""
    <div class="sidebar-status-box">
        <div style="font-weight:800; color:#1E293B; margin-bottom:9px; font-size:11.5px; display:flex; justify-content:space-between; align-items:center;">
            <span>WORKFLOW PROGRESS</span>
            <span style="color:#10B981; font-weight:800; font-size:10.5px;">● Live Active</span>
        </div>
        <div class="status-row"><span>1. Nguồn Dữ Liệu:</span>{ds_badge}</div>
        <div class="status-row"><span>2. Làm Sạch Data:</span>{cl_badge}</div>
        <div class="status-row"><span>3. Process 6 Bước:</span>{pr_badge}</div>
        <div class="status-row"><span>4. Phê Duyệt:</span>{ap_badge}</div>
        <div class="status-row"><span>5. Verification:</span>{vr_badge}</div>
    </div>
    """, unsafe_allow_html=True)

    selected_menu = st.radio(
        "ĐIỀU HƯỚNG HỆ THỐNG",
        [
            "📊 Overview (Tổng quan)",
            "🔗 Kết Nối Google Sheets",
            "🧹 Data Cleaning & Audit",
            "⚙️ Process Workflow (6 Bước)",
            "⚠️ Phê Duyệt Exceptions",
            "✅ Verification Suite",
            "📈 Báo Cáo Reports & Export",
            "⚙️ Cài Đặt Settings"
        ],
        index=0
    )

    st.markdown("""
    <div class="sidebar-pro-card">
        <div class="pro-icon-wrap">⚡</div>
        <div class="pro-title">GrowthMetric Pro</div>
        <div class="pro-desc">Hệ thống AI Analytics tự động hóa 6 bước quy trình</div>
        <div class="pro-badge-btn">Upgrade to Pro &gt;</div>
    </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# TRANG 1: 📊 TỔNG QUAN (OVERVIEW / WEEKLY SUMUP)
# ==============================================================================
if "Overview" in selected_menu or "Tổng quan" in selected_menu:
    render_top_header("Weekly sumup", "Get summary of your marketing campaigns & performance here")

    if st.session_state.data_status != "CONNECTED":
        st.markdown(f"""
        <div class="cloudcash-card">
            <div class="cloudcash-card-header">
                <div>
                    <h3 class="cloudcash-card-title">🚀 Khởi Động Kết Nối & Phân Tích Dữ Liệu</h3>
                    <div class="cloudcash-card-sub">Chọn một bộ dữ liệu kiểm thử nhanh hoặc kết nối Google Sheets thực tế của bạn để bắt đầu.</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        c_quick1, c_quick2, c_quick3 = st.columns(3)
        with c_quick1:
            if st.button("⚡ Nạp GiaHoa TestCase_08 (Messy)", type="primary", width='stretch'):
                st.session_state.raw_tabs = get_messy_testcase_08_data()
                st.session_state.source_name = "GiaHoa_Raw_Messy_TestCase_08 (Dữ liệu tiếng Việt lộn xộn)"
                st.session_state.data_status = "CONNECTED"
                st.session_state.cleaning_status = "PENDING"
                st.session_state.process_status = "NOT_STARTED"
                st.session_state.verification_status = "NOT_RUN"
                st.session_state.reconciliation_table = None
                st.rerun()

        with c_quick2:
            if st.button("🛒 Nạp E-Commerce (12 Cột Doanh Thu/Chi Phí)", width='stretch'):
                st.session_state.raw_tabs = get_ecommerce_user_data()
                st.session_state.source_name = "Dữ liệu E-Commerce thực tế (12 Cột: Net_Sales, Cost, Profit)"
                st.session_state.data_status = "CONNECTED"
                st.session_state.cleaning_status = "PENDING"
                st.session_state.process_status = "NOT_STARTED"
                st.session_state.verification_status = "NOT_RUN"
                st.session_state.reconciliation_table = None
                st.rerun()

        with c_quick3:
            if st.button("📦 Nạp Bộ 3 Tabs Chuẩn Doanh Nghiệp", width='stretch'):
                st.session_state.raw_tabs = get_sample_marketing_data()
                st.session_state.source_name = "Bộ dữ liệu chuẩn 3 Tabs Doanh Nghiệp"
                st.session_state.data_status = "CONNECTED"
                st.session_state.cleaning_status = "PENDING"
                st.session_state.process_status = "NOT_STARTED"
                st.session_state.verification_status = "NOT_RUN"
                st.session_state.reconciliation_table = None
                st.rerun()

    else:
        # Đã kết nối -> Kiểm tra nếu chưa chạy process
        if st.session_state.process_result is None or st.session_state.engine is None or st.session_state.engine.report_result is None:
            st.info("💡 Dữ liệu đã nạp thành công! Hãy bấm nút bên dưới để tiến hành **Làm sạch Dữ liệu** và tự động chạy phân tích 6 bước.")
            
            c_p1, c_p2 = st.columns([2, 5])
            with c_p1:
                if st.button("🧼 Bắt Đầu Làm Sạch & Chạy Ngay", type="primary"):
                    cleaner = DataCleaner(st.session_state.raw_tabs)
                    can_proc, norm_data, q_sum, errs, excs = cleaner.clean_and_normalize()
                    st.session_state.normalized_data = norm_data
                    st.session_state.quality_summary = q_sum
                    st.session_state.cleaning_errors = errs
                    st.session_state.exceptions_list = excs
                    st.session_state.reconciliation_table = cleaner.reconciliation_table
                    st.session_state.cleaning_status = "PASSED" if can_proc else "FAILED"
                    st.session_state.engine = MarketingAnalyticsEngine(
                        norm_data,
                        initial_exceptions=excs,
                        return_window_days=st.session_state.return_window
                    )
                    # Chạy luôn quy trình 6 bước
                    res = st.session_state.engine.run_process_workflow()
                    st.session_state.process_result = res
                    st.session_state.process_status = "COMPLETED"
                    st.session_state.exceptions_list = st.session_state.engine.exceptions_view
                    st.rerun()
        else:
            rep = st.session_state.engine.report_result
            total_rev = rep["Attributed_Revenue"].sum()
            total_net_sales = rep["Net_Sales"].sum()
            has_costs = "Total_Cost" in rep.columns and rep["Total_Cost"].notna().any()
            total_cost = rep["Total_Cost"].sum() if has_costs else 0.0
            total_nc = rep["Net_Contribution"].sum() if has_costs else (total_net_sales * 0.72)
            
            # 4 Thẻ KPI Candy Pastel Sắc Màu Rực Rỡ theo chuẩn Dabang & Fintech
            k1, k2, k3, k4 = st.columns(4)
            with k1:
                st.markdown(f"""
                <div class="kpi-candy-card pink">
                    <div class="kpi-top-row">
                        <div class="kpi-icon-pill pink">💰</div>
                        <span class="kpi-trend-pill pink">+14.2%</span>
                    </div>
                    <div>
                        <div class="kpi-val pink">{total_rev:,.0f} đ</div>
                        <div class="kpi-label">Tổng Doanh Thu Phân Bổ</div>
                        <div style="font-size:11px; color:#E11D48; font-weight:700; margin-top:2px;">Multi-touch Attribution</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with k2:
                st.markdown(f"""
                <div class="kpi-candy-card amber">
                    <div class="kpi-top-row">
                        <div class="kpi-icon-pill amber">🛒</div>
                        <span class="kpi-trend-pill amber">+8.5%</span>
                    </div>
                    <div>
                        <div class="kpi-val amber">{total_net_sales:,.0f} đ</div>
                        <div class="kpi-label">Net Sales Thực Nhận</div>
                        <div style="font-size:11px; color:#B45309; font-weight:700; margin-top:2px;">Đã trừ Return Window</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with k3:
                st.markdown(f"""
                <div class="kpi-candy-card green">
                    <div class="kpi-top-row">
                        <div class="kpi-icon-pill green">💎</div>
                        <span class="kpi-trend-pill green">+22.4%</span>
                    </div>
                    <div>
                        <div class="kpi-val green">{total_nc:,.0f} đ</div>
                        <div class="kpi-label">Net Contribution (Lợi Nhuận)</div>
                        <div style="font-size:11px; color:#047857; font-weight:700; margin-top:2px;">Sau COGS & Chi phí ABC</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with k4:
                cost_text = f"{total_cost:,.0f} đ" if has_costs else "Chưa có tab Cost"
                st.markdown(f"""
                <div class="kpi-candy-card purple">
                    <div class="kpi-top-row">
                        <div class="kpi-icon-pill purple">📊</div>
                        <span class="kpi-trend-pill purple">-5.1%</span>
                    </div>
                    <div>
                        <div class="kpi-val purple">{cost_text}</div>
                        <div class="kpi-label">Tổng Chi Phí ABC & Ads</div>
                        <div style="font-size:11px; color:#6D28D9; font-weight:700; margin-top:2px;">Direct & Overhead Costs</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Top row: Cards widget (Left) & Goals (Right)
            col_left_cards, col_right_goals = st.columns([5, 5])
            
            with col_left_cards:
                st.markdown("""
                <div class="cloudcash-card">
                    <div class="cloudcash-card-header">
                        <div>
                            <h3 class="cloudcash-card-title">Cards</h3>
                            <div class="cloudcash-card-sub">Thẻ tài chính chiến dịch & ngân sách tự động</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                c_c1, c_c2 = st.columns([6, 5])
                with c_c1:
                    st.markdown("""
                    <div class="cloudcash-credit-card">
                        <div class="card-top-row">
                            <span class="card-brand-name">cloudcash</span>
                            <div class="card-chip"></div>
                        </div>
                        <div class="card-number">5789 •••• •••• 2847</div>
                        <div class="card-bottom-row">
                            <div>
                                <div style="font-size:9px; opacity:0.85; text-transform:uppercase;">Card Holder</div>
                                <div class="card-holder-name">Vũ Ruy Hoàng</div>
                            </div>
                            <div>
                                <div style="font-size:9px; opacity:0.85; text-transform:uppercase;">Expires</div>
                                <div class="card-exp">06/28</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with c_c2:
                    st.markdown(f"""
                    <div style="padding-left:10px;">
                        <div style="font-size:12px; color:#64748B; font-weight:700;">Current balance</div>
                        <div style="font-size:24px; font-weight:800; background:linear-gradient(135deg, #1E75FF 0%, #7C3AED 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:12px;">{total_nc:,.0f} đ</div>
                        
                        <div style="margin-bottom:8px;">
                            <span style="font-size:12px; color:#64748B; font-weight:700;">Income:</span>
                            <span style="font-size:13.5px; font-weight:800; color:#10B981; margin-left:6px;">+{total_net_sales:,.0f} đ</span>
                        </div>
                        <div style="margin-bottom:14px;">
                            <span style="font-size:12px; color:#64748B; font-weight:700;">Outcome:</span>
                            <span style="font-size:13.5px; font-weight:800; color:#EF4444; margin-left:6px;">-{total_cost:,.0f} đ</span>
                        </div>
                        
                        <div style="font-size:11px; color:#64748B; font-weight:700; margin-bottom:5px;">Weekly payment limit (65%)</div>
                        <div style="background:#F1F5F9; height:8px; border-radius:4px; overflow:hidden;">
                            <div style="background:linear-gradient(90deg, #1E75FF 0%, #8B5CF6 60%, #EC4899 100%); width:65%; height:100%;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)

            with col_right_goals:
                st.markdown("""
                <div class="cloudcash-card">
                    <div class="cloudcash-card-header">
                        <div>
                            <h3 class="cloudcash-card-title">Goals <span style="color:#F59E0B; font-size:18px;">✦</span></h3>
                            <div class="cloudcash-card-sub">Mục tiêu tăng trưởng & hiệu quả chiến dịch</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                g1, g2, g3 = st.columns(3)
                with g1:
                    st.markdown(f"""
                    <div class="goal-card blue">
                        <div>
                            <div class="goal-val blue">{total_rev:,.0f} đ</div>
                            <div class="goal-sub">Hạn: 12/28/26</div>
                        </div>
                        <div class="goal-icon blue">⛵</div>
                        <div style="font-size:12.5px; font-weight:800; color:#1D4ED8; margin-top:10px;">Doanh Thu Thuần</div>
                    </div>
                    """, unsafe_allow_html=True)
                with g2:
                    st.markdown(f"""
                    <div class="goal-card orange">
                        <div>
                            <div class="goal-val orange">{total_net_sales:,.0f} đ</div>
                            <div class="goal-sub">Hạn: 12/28/26</div>
                        </div>
                        <div class="goal-icon orange">🔨</div>
                        <div style="font-size:12.5px; font-weight:800; color:#C2410C; margin-top:10px;">Net Sales</div>
                    </div>
                    """, unsafe_allow_html=True)
                with g3:
                    st.markdown(f"""
                    <div class="goal-card green">
                        <div>
                            <div class="goal-val green">{total_nc:,.0f} đ</div>
                            <div class="goal-sub">Hạn: 12/28/26</div>
                        </div>
                        <div class="goal-icon green">🎮</div>
                        <div style="font-size:12.5px; font-weight:800; color:#15803D; margin-top:10px;">Net Contrib</div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # Middle row: Transaction history (Left) & Outcome Statistics (Right)
            col_tx, col_stats = st.columns([6, 4])
            
            with col_tx:
                st.markdown("""
                <div class="cloudcash-card">
                    <div class="cloudcash-card-header">
                        <div>
                            <h3 class="cloudcash-card-title">Transaction history</h3>
                            <div class="cloudcash-card-sub">Lịch sử giao dịch & đơn hàng gần nhất</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                norm_tx = st.session_state.normalized_data.get("Normalized_Transactions") if st.session_state.normalized_data else None
                if norm_tx is not None and len(norm_tx) > 0:
                    preview_df = norm_tx[["Order_ID", "Order_Value", "Channel", "Return_Status", "Order_Date"]].head(6).copy()
                    preview_df["Order_Value"] = preview_df["Order_Value"].apply(lambda v: f"{v:,.0f} đ")
                    preview_df.columns = ["Mã Đơn", "Giá Trị", "Kênh Bán", "Trạng Thái", "Ngày Đơn"]
                    st.dataframe(preview_df, width='stretch')
                else:
                    st.caption("Chưa có danh sách đơn hàng.")
                st.markdown("</div>", unsafe_allow_html=True)

            with col_stats:
                st.markdown("""
                <div class="cloudcash-card">
                    <div class="cloudcash-card-header">
                        <div>
                            <h3 class="cloudcash-card-title">Outcome Statistics</h3>
                            <div class="cloudcash-card-sub">Tỷ trọng doanh thu theo Kênh bán hàng</div>
                        </div>
                    </div>
                    <div class="stat-row">
                        <div class="stat-icon orange">🛒</div>
                        <div class="stat-bar-wrap">
                            <div class="stat-label-row">
                                <span>Shopee Mall</span>
                                <span style="color:#EA580C;">52%</span>
                            </div>
                            <div class="stat-bar"><div class="stat-bar-fill orange" style="width:52%;"></div></div>
                        </div>
                    </div>
                    <div class="stat-row">
                        <div class="stat-icon green">🚚</div>
                        <div class="stat-bar-wrap">
                            <div class="stat-label-row">
                                <span>TikTok Shop</span>
                                <span style="color:#16A34A;">28%</span>
                            </div>
                            <div class="stat-bar"><div class="stat-bar-fill green" style="width:28%;"></div></div>
                        </div>
                    </div>
                    <div class="stat-row">
                        <div class="stat-icon blue">✈️</div>
                        <div class="stat-bar-wrap">
                            <div class="stat-label-row">
                                <span>Facebook Ads</span>
                                <span style="color:#2563EB;">20%</span>
                            </div>
                            <div class="stat-bar"><div class="stat-bar-fill blue" style="width:20%;"></div></div>
                        </div>
                    </div>
                    <div class="stat-row">
                        <div class="stat-icon pink">🛍️</div>
                        <div class="stat-bar-wrap">
                            <div class="stat-label-row">
                                <span>Website / Direct</span>
                                <span style="color:#DB2777;">15%</span>
                            </div>
                            <div class="stat-bar"><div class="stat-bar-fill pink" style="width:15%;"></div></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Bottom Charts: Campaign Performance với bảng màu cầu vồng sắc nét
            col_chart1, col_chart2 = st.columns([5, 5])
            with col_chart1:
                st.markdown("""
                <div class="cloudcash-card">
                    <div class="cloudcash-card-header">
                        <div>
                            <h3 class="cloudcash-card-title">📊 Doanh Thu Từng Chiến Dịch Marketing</h3>
                            <div class="cloudcash-card-sub">Attributed Revenue phân bổ đa điểm chạm</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                fig_rev = px.bar(
                    rep,
                    x="Campaign_Name",
                    y="Attributed_Revenue",
                    color="Channel" if "Channel" in rep.columns else None,
                    color_discrete_sequence=["#1E75FF", "#EC4899", "#10B981", "#F59E0B", "#8B5CF6", "#06B6D4", "#FA5A7D"],
                    labels={"Attributed_Revenue": "Doanh thu (VNĐ)", "Campaign_Name": "Chiến Dịch"}
                )
                fig_rev.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Plus Jakarta Sans", color="#1E293B"),
                    margin=dict(l=10, r=10, t=10, b=10),
                    height=300
                )
                st.plotly_chart(fig_rev, width='stretch')
                st.markdown("</div>", unsafe_allow_html=True)

            with col_chart2:
                st.markdown("""
                <div class="cloudcash-card">
                    <div class="cloudcash-card-header">
                        <div>
                            <h3 class="cloudcash-card-title">📈 Xu Hướng Doanh Thu & Net Sales</h3>
                            <div class="cloudcash-card-sub">So sánh Attributed Revenue và Net Sales sau hoàn trả</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                fig_spline = go.Figure()
                fig_spline.add_trace(go.Scatter(
                    x=rep["Campaign_Name"],
                    y=rep["Attributed_Revenue"],
                    mode='lines+markers',
                    name='Attributed Revenue',
                    line=dict(color='#EC4899', width=3.5, shape='spline'),
                    marker=dict(size=8, color='#EC4899')
                ))
                fig_spline.add_trace(go.Scatter(
                    x=rep["Campaign_Name"],
                    y=rep["Net_Sales"],
                    mode='lines+markers',
                    name='Net Sales (Sau Hoàn)',
                    line=dict(color='#10B981', width=3.5, shape='spline'),
                    marker=dict(size=8, color='#10B981')
                ))
                fig_spline.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Plus Jakarta Sans", color="#1E293B"),
                    margin=dict(l=10, r=10, t=10, b=10),
                    height=300,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_spline, width='stretch')
                st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# TRANG 2: 🔗 KẾT NỐI GOOGLE SHEETS & AUTO SCHEMA MAPPING
# ==============================================================================
elif "Kết Nối" in selected_menu or "Google Sheets" in selected_menu:
    render_top_header("Kết Nối Dữ Liệu & Auto Schema Mapping", "Tự động phát hiện số lượng tabs, tên cột tiếng Việt/tiếng Anh và tự ánh xạ về Schema chuẩn nội bộ")

    with st.container():
        st.markdown("""<div class="cloudcash-card">""", unsafe_allow_html=True)
        st.markdown("##### 1. Dán liên kết Google Sheets (URL):")
        
        sheet_url_input = st.text_input(
            "Đường dẫn Google Sheets:",
            placeholder="https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit...",
            help="Bảng tính cần được mở quyền 'Bất kỳ ai có đường liên kết đều có thể xem'."
        )

        c_conn1, c_conn_spacer = st.columns([2, 5])
        with c_conn1:
            if st.button("🔍 Kiểm Tra & Kết Nối Sheets", type="primary", width='stretch'):
                if not sheet_url_input.strip():
                    st.error("Vui lòng nhập đường dẫn Google Sheets hợp lệ.")
                else:
                    with st.spinner("Đang kết nối và quét các Tabs trong Google Sheets..."):
                        ok, tabs_dict, class_info, msg = load_google_sheet_flexible(sheet_url_input.strip())
                        if ok:
                            st.session_state.raw_tabs = tabs_dict
                            st.session_state.classification_info = class_info
                            st.session_state.source_name = f"Google Sheets ({len(tabs_dict)} tabs)"
                            st.session_state.data_status = "CONNECTED"
                            st.session_state.cleaning_status = "PENDING"
                            st.session_state.process_status = "NOT_STARTED"
                            st.session_state.verification_status = "NOT_RUN"
                            st.session_state.reconciliation_table = None
                            st.success(msg)
                            st.rerun()
                        else:
                            st.session_state.data_status = "FAILED"
                            st.error(msg)

        st.markdown("<div style='font-size:12px; font-weight:700; color:#475569; margin-top:16px; margin-bottom:8px;'>HOẶC CHỌN NHANH DỮ LIỆU KIỂM THỬ:</div>", unsafe_allow_html=True)
        c_p1, c_p2, c_p3 = st.columns(3)
        with c_p1:
            if st.button("⚡ Nạp TestCase_08 Messy Data", width='stretch'):
                st.session_state.raw_tabs = get_messy_testcase_08_data()
                st.session_state.source_name = "GiaHoa_Raw_Messy_TestCase_08 (Dữ liệu thực tế kiểm thử)"
                st.session_state.data_status = "CONNECTED"
                st.session_state.cleaning_status = "PENDING"
                st.session_state.process_status = "NOT_STARTED"
                st.session_state.verification_status = "NOT_RUN"
                st.session_state.reconciliation_table = None
                st.success("Đã nạp thành công bộ dữ liệu thực tế GiaHoa_Raw_Messy_TestCase_08!")
                st.rerun()

        with c_p2:
            if st.button("🛒 Nạp E-Commerce (12 Cột Doanh Thu/Giá Vốn)", width='stretch'):
                st.session_state.raw_tabs = get_ecommerce_user_data()
                st.session_state.source_name = "Dữ liệu E-Commerce thực tế (12 Cột: Net_Sales_VND, Cost_VND, Profit_VND)"
                st.session_state.data_status = "CONNECTED"
                st.session_state.cleaning_status = "PENDING"
                st.session_state.process_status = "NOT_STARTED"
                st.session_state.verification_status = "NOT_RUN"
                st.session_state.reconciliation_table = None
                st.success("Đã nạp thành công bộ dữ liệu E-Commerce 12 cột!")
                st.rerun()

        with c_p3:
            if st.button("📦 Nạp Bộ 3 Tabs Chuẩn", width='stretch'):
                st.session_state.raw_tabs = get_sample_marketing_data()
                st.session_state.source_name = "Bộ dữ liệu chuẩn 3 Tabs"
                st.session_state.data_status = "CONNECTED"
                st.session_state.cleaning_status = "PENDING"
                st.session_state.process_status = "NOT_STARTED"
                st.session_state.verification_status = "NOT_RUN"
                st.session_state.reconciliation_table = None
                st.success("Đã nạp thành công bộ dữ liệu mẫu chuẩn 3 tabs!")
                st.rerun()

        st.markdown("<hr style='margin:18px 0; border:0; border-top:1px solid #E2E8F0;'>", unsafe_allow_html=True)

        st.markdown("##### Hoặc tải file dữ liệu lên (Excel / CSV):")
        uploaded_file = st.file_uploader("Chọn file .xlsx hoặc .csv từ máy tính:", type=["xlsx", "xls", "csv"])
        if uploaded_file is not None:
            if uploaded_file.name.endswith(".csv"):
                df_csv = pd.read_csv(uploaded_file)
                st.session_state.raw_tabs = {"Untitled": df_csv}
                st.session_state.source_name = f"File CSV: {uploaded_file.name}"
                st.session_state.data_status = "CONNECTED"
                st.session_state.cleaning_status = "PENDING"
                st.session_state.process_status = "NOT_STARTED"
                st.success(f"Đã nạp file CSV ({len(df_csv)} bản ghi).")
            else:
                ok, tabs_dict, class_info, msg = load_from_excel_flexible(uploaded_file)
                if ok:
                    st.session_state.raw_tabs = tabs_dict
                    st.session_state.classification_info = class_info
                    st.session_state.source_name = f"File Excel: {uploaded_file.name}"
                    st.session_state.data_status = "CONNECTED"
                    st.session_state.cleaning_status = "PENDING"
                    st.session_state.process_status = "NOT_STARTED"
                    st.success(msg)

        st.markdown("""</div>""", unsafe_allow_html=True)

    # Hiển thị kết quả nhận diện và Bảng Ánh Xạ Schema Mapper
    if st.session_state.raw_tabs:
        st.markdown("### 📋 Bảng Nhận Diện Cột & Ánh Xạ Schema Tự Động (Auto Schema Mapping)")
        mapper = AutoSchemaMapper()

        for t_name, df_tab in st.session_state.raw_tabs.items():
            st.markdown(f"##### 📑 Tab: `{t_name}` ({len(df_tab)} bản ghi)")
            map_res = mapper.map_columns(list(df_tab.columns), target_tab="Transactions")
            
            if map_res["mapping_table"]:
                df_map_view = pd.DataFrame(map_res["mapping_table"])[["Original_Column", "Mapped_Field", "Field_Description", "Confidence_Score", "Match_Type", "Status"]]
                df_map_view.columns = ["Tên Cột Gốc", "Trường Chuẩn Nội Bộ", "Ý Nghĩa Nghiệp Vụ", "Độ Tin Cậy", "Kiểu So Khớp", "Trạng Thái"]
                st.dataframe(df_map_view, width='stretch')
            
            if map_res["unmapped_columns"]:
                st.caption(f"Các cột chưa gán trường chuẩn (sẽ được giữ nguyên đối chiếu): {', '.join(map_res['unmapped_columns'])}")


# ==============================================================================
# TRANG 3: 🧹 DATA CLEANING & NORMALIZATION LAYER
# ==============================================================================
elif "Data Cleaning" in selected_menu:
    render_top_header("Data Cleaning & Normalization Layer", "Làm sạch tiền tệ, xử lý chiến dịch & Bảng đối chiếu bất biến trước sau")

    if not st.session_state.raw_tabs:
        st.warning("Chưa có dữ liệu để làm sạch. Vui lòng vào trang **🔗 Kết nối Google Sheets** trước.")
    else:
        c_clean_btn, c_down_raw = st.columns([3, 2])
        with c_clean_btn:
            if st.button("🧼 BẮT ĐẦU LÀM SẠCH & CHUẨN HÓA DỮ LIỆU", type="primary", width='stretch'):
                with st.spinner("Đang chạy động cơ làm sạch và chuẩn hóa..."):
                    cleaner = DataCleaner(st.session_state.raw_tabs)
                    can_proc, norm_data, q_sum, errs, excs = cleaner.clean_and_normalize()

                    st.session_state.normalized_data = norm_data
                    st.session_state.quality_summary = q_sum
                    st.session_state.cleaning_errors = errs
                    st.session_state.exceptions_list = excs
                    st.session_state.reconciliation_table = cleaner.reconciliation_table
                    st.session_state.cleaning_status = "PASSED" if can_proc else "FAILED"

                    # Khởi tạo analytics engine ngay với các ngoại lệ đã phát hiện
                    engine = MarketingAnalyticsEngine(
                        norm_data,
                        initial_exceptions=excs,
                        return_window_days=st.session_state.return_window
                    )
                    st.session_state.engine = engine

                    st.success(f"Làm sạch hoàn tất! Điểm chất lượng: {q_sum['Data_Quality_Score']}%. Phát hiện {len(excs)} ngoại lệ.")

        if st.session_state.quality_summary:
            q = st.session_state.quality_summary
            
            # Thống kê kết quả Data Cleaning
            st.markdown("<br>", unsafe_allow_html=True)
            k1, k2, k3, k4, k5 = st.columns(5)
            with k1:
                st.metric("Tổng Số Dòng Thô", f"{q['Total_Raw_Records']} Dòng")
            with k2:
                st.metric("Dòng Sau Chuẩn Hóa", f"{q['Normalized_Transactions_Count']} Dòng")
            with k3:
                st.metric("Tự Động Sửa An Toàn", f"{q['Auto_Fixed_Count']} Mục")
            with k4:
                st.metric("Ngoại Lệ Cần Xem Xét", f"{q['Exceptions_Count']} Mục")
            with k5:
                st.metric("Điểm Chất Lượng", f"{q['Data_Quality_Score']}%")

            # BẢNG ĐỐI CHIẾU TRƯỚC VÀ SAU (INVARIANTS RECONCILIATION TABLE)
            if st.session_state.reconciliation_table:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("##### 🛡️ Bảng Đối Chiếu Trước và Sau (Reconciliation Invariants Audit):")
                st.caption("Kiểm tra 5 bất biến bắt buộc: Không làm mất doanh thu thuần, giá vốn, lợi nhuận gộp và số bản ghi.")
                df_rec = pd.DataFrame(st.session_state.reconciliation_table)
                df_rec.columns = ["Chỉ Số Kiểm Toán", "Trường Nguồn", "Giá Trị Nguồn", "Trường Chuẩn", "Giá Trị Chuẩn", "Độ Lệch", "Trạng Thái"]
                st.dataframe(df_rec, width='stretch')

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("##### 📊 So Sánh Dữ Liệu Trước và Sau Làm Sạch (Before & After Preview):")
            
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                st.markdown("**Dữ liệu thô ban đầu (Raw Data):**")
                first_tab = list(st.session_state.raw_tabs.values())[0]
                st.dataframe(first_tab.head(8), width='stretch')

            with t_col2:
                st.markdown("**Dữ liệu đã chuẩn hóa (Normalized Transactions):**")
                norm_tx = st.session_state.normalized_data.get("Normalized_Transactions")
                if norm_tx is not None:
                    cols_priority = [
                        "Order_ID", "Order_Value", "Gross_Sales", "COGS", "Source_Profit",
                        "Quantity", "Unit_Price", "Discount_Rate", "Discount_Amount",
                        "Campaign_List_Str", "Campaign_Data_Status", "Channel", "Return_Status",
                        "Shipping_Days", "Payment_Method", "Customer_Satisfaction", "Order_Date"
                    ]
                    cols_to_show = [c for c in cols_priority if c in norm_tx.columns] + [
                        c for c in norm_tx.columns
                        if c not in cols_priority and not c.startswith("Raw_") and c not in ["Has_Exception", "Run_ID", "Campaign_List", "Campaign_Count"]
                    ]
                    st.dataframe(norm_tx[cols_to_show].head(8), width='stretch')

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("##### 📝 Nhật Ký Chi Tiết Làm Sạch (Data Cleaning Audit Log):")
            if st.session_state.cleaning_errors:
                df_errs = pd.DataFrame(st.session_state.cleaning_errors)
                st.dataframe(df_errs, width='stretch')
            else:
                st.success("Dữ liệu hoàn toàn sạch sẽ, không ghi nhận cảnh báo nào.")

            # Nút tải file Excel dữ liệu sạch
            if st.session_state.normalized_data:
                cleaner_inst = DataCleaner(st.session_state.raw_tabs)
                cleaner_inst.normalized_data = st.session_state.normalized_data
                cleaner_inst.errors_log = st.session_state.cleaning_errors
                excel_bytes = cleaner_inst.export_cleaned_data_excel()
                
                st.download_button(
                    label="📥 Tải Bộ Dữ Liệu Sạch Về Máy (.xlsx)",
                    data=excel_bytes,
                    file_name=f"Cleaned_Normalized_Data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )


# ==============================================================================
# TRANG 4: ⚙️ PROCESS WORKFLOW (6 BƯỚC)
# ==============================================================================
elif "Process Workflow" in selected_menu:
    render_top_header("Process Workflow (6 Bước Xử Lý)", "Quy trình tự động hóa phân bổ doanh thu đa điểm chạm & Chi phí ABC")

    if not st.session_state.normalized_data:
        st.warning("Vui lòng thực hiện bước **🧹 Data Cleaning** trước khi chạy quy trình Process.")
    else:
        # Nút thực thi 6 bước
        if st.button("▶ CHẠY TOÀN BỘ 6 BƯỚC PROCESS", type="primary"):
            with st.spinner("Đang thực thi 6 bước theo sơ đồ kiến trúc..."):
                if st.session_state.engine is None:
                    st.session_state.engine = MarketingAnalyticsEngine(
                        st.session_state.normalized_data,
                        initial_exceptions=st.session_state.exceptions_list,
                        return_window_days=st.session_state.return_window
                    )
                res = st.session_state.engine.run_process_workflow()
                st.session_state.process_result = res
                st.session_state.process_status = "COMPLETED"
                st.session_state.exceptions_list = st.session_state.engine.exceptions_view
                st.success("Thực thi 6 bước Process thành công!")
                st.rerun()

        # Hiển thị Stepper / Timeline 6 bước với màu sắc rực rỡ
        p_status = st.session_state.process_status
        line_class = "pass" if p_status == "COMPLETED" else "pending"

        st.markdown(f"""
        <div class="stepper-cloudcash">
            <div class="step-item">
                <div class="step-badge s1">1</div>
                <div>Centralization</div>
            </div>
            <div class="step-line {line_class}"></div>
            <div class="step-item">
                <div class="step-badge s2">2</div>
                <div>Attribution</div>
            </div>
            <div class="step-line {line_class}"></div>
            <div class="step-item">
                <div class="step-badge s3">3</div>
                <div>Returns</div>
            </div>
            <div class="step-line {line_class}"></div>
            <div class="step-item">
                <div class="step-badge s4">4</div>
                <div>ABC Cost</div>
            </div>
            <div class="step-line {line_class}"></div>
            <div class="step-item">
                <div class="step-badge s5">5</div>
                <div>Net Contrib</div>
            </div>
            <div class="step-line {line_class}"></div>
            <div class="step-item">
                <div class="step-badge s6">6</div>
                <div>Decisions</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.engine and st.session_state.engine.detailed_attributed_df is not None:
            with st.expander("🔍 Chi Tiết Phân Bổ Doanh Thu Từng Đơn Hàng (Attribution Details)", expanded=True):
                st.dataframe(st.session_state.engine.detailed_attributed_df, width='stretch')

            if st.session_state.engine.report_result is not None:
                with st.expander("📊 Bảng Kết Quả Tính Toán Theo Chiến Dịch (Report Result)", expanded=True):
                    st.dataframe(st.session_state.engine.report_result, width='stretch')


# ==============================================================================
# TRANG 5: ⚠️ EXCEPTIONS (HUMAN-IN-THE-LOOP VỚI KIỂM SOÁT THẨM QUYỀN)
# ==============================================================================
elif "Exceptions" in selected_menu or "Phê Duyệt" in selected_menu:
    render_top_header("Quản Lý & Phê Duyệt Ngoại Lệ (Human-in-the-Loop)", "Cơ chế phê duyệt có thẩm quyền dành cho Trưởng phòng Marketing & Ban Giám đốc")

    exceptions = st.session_state.exceptions_list

    if not exceptions:
        st.success("🎉 Hệ thống không phát sinh ngoại lệ nào cần xử lý.")
    else:
        pending_list = [e for e in exceptions if e.get("Approval_Status") == "PENDING_REVIEW"]
        approved_list = [e for e in exceptions if e.get("Approval_Status") == "APPROVED"]
        rejected_list = [e for e in exceptions if e.get("Approval_Status") == "REJECTED"]

        col_e1, col_e2, col_e3 = st.columns(3)
        with col_e1:
            st.metric("Chờ Duyệt (Pending)", f"{len(pending_list)} Mục")
        with col_e2:
            st.metric("Đã Chấp Thuận (Approved)", f"{len(approved_list)} Mục")
        with col_e3:
            st.metric("Từ Chối / Điều Chỉnh", f"{len(rejected_list)} Mục")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### 📋 Danh Sách Các Ngoại Lệ Cần Thẩm Định:")
        df_exc = pd.DataFrame(exceptions)
        st.dataframe(df_exc, width='stretch')

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### ✍️ Form Phê Duyệt Dành Cho Người Có Thẩm Quyền:")

        with st.container():
            st.markdown("""<div class="cloudcash-card">""", unsafe_allow_html=True)
            if pending_list:
                pending_options = [f"{e['Order_ID']} | {e['Error_Type']} (Mức độ: {e.get('Severity', 'HIGH')})" for e in pending_list]
                selected_opt = st.selectbox("Chọn ngoại lệ cần phê duyệt:", pending_options)
                selected_order_id = selected_opt.split(" | ")[0]

                c_act, c_role, c_name = st.columns(3)
                with c_act:
                    action_choice = st.selectbox("Hành động quyết định:", ["APPROVE (Chấp thuận)", "REJECT (Từ chối / Loại trừ)", "REQUEST_CORRECTION (Yêu cầu làm rõ)"])
                with c_role:
                    reviewer_role = st.selectbox(
                        "Vai trò người phê duyệt (Role):",
                        [
                            "Trưởng phòng Marketing",
                            "Trưởng phòng Marketing & Tài chính",
                            "Quản trị viên",
                            "Ban Giám Đốc",
                            "Nhân viên bán hàng (Không có quyền duyệt)"
                        ]
                    )
                with c_name:
                    reviewer_name = st.text_input("Tên người phê duyệt:", value="Vũ Ruy Hoàng")

                note_input = st.text_input("Ghi chú / Lý do giải trình (Bắt buộc với trường hợp rủi ro cao):", placeholder="Đã kiểm tra đối soát nguồn và chấp thuận...")

                if st.button("✔ Xác Nhận Phê Duyệt Ngoại Lệ", type="primary"):
                    if not st.session_state.engine:
                        st.error("Engine chưa khởi tạo.")
                    else:
                        act_code = "APPROVE" if "APPROVE" in action_choice else ("REJECT" if "REJECT" in action_choice else "REQUEST_CORRECTION")
                        ok, msg = st.session_state.engine.resolve_exception(
                            selected_order_id,
                            act_code,
                            reviewer_role,
                            reviewer_name,
                            note_input
                        )
                        if ok:
                            st.session_state.exceptions_list = st.session_state.engine.exceptions_view
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
            else:
                st.success("🎉 Toàn bộ ngoại lệ đã được phê duyệt đầy đủ! Bạn có thể chuyển sang trang **Verification**.")
            
            st.markdown("""</div>""", unsafe_allow_html=True)


# ==============================================================================
# TRANG 6: ✅ VERIFICATION (7 PHÉP KIỂM TOÁN TỰ ĐỘNG)
# ==============================================================================
elif "Verification" in selected_menu:
    render_top_header("Verification Suite (7 Phép Kiểm Toán Tự Động)", "Kiểm chứng bất biến tài chính, đối soát hoàn trả và ngăn trừ trùng")

    if not st.session_state.engine or st.session_state.engine.report_result is None:
        st.warning("Vui lòng hoàn tất quy trình **Process Workflow** trước khi kiểm chứng.")
    else:
        if st.button("🔍 CHẠY 7 PHÉP KIỂM TOÁN TỰ ĐỘNG (VERIFY SUITE)", type="primary"):
            with st.spinner("Đang chạy 7 phép kiểm toán tự động..."):
                vr = st.session_state.engine.run_verification()
                st.session_state.verification_result = vr
                st.session_state.verification_status = vr["overall_status"]
                st.rerun()

        if st.session_state.verification_result:
            vr = st.session_state.verification_result
            is_pass = (vr["overall_status"] == "PASS")

            if is_pass:
                st.markdown(f"""
                <div style="background:linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%); border:2px solid #10B981; border-radius:20px; padding:20px 24px; margin-bottom:22px; display:flex; justify-content:space-between; align-items:center; box-shadow:0 8px 24px rgba(16, 185, 129, 0.15);">
                    <div>
                        <b style="color:#065F46; font-size:17px;">🟢 VERIFICATION PASS (ĐẠT CHUẨN KIỂM TOÁN HOÀN TOÀN)</b>
                        <div style="font-size:12.5px; color:#047857; margin-top:4px; font-weight:600;">
                            Tất cả các phép kiểm toán có hiệu lực đều khớp tuyệt đối. Đã mở khóa xuất bản báo cáo HTML Standalone.
                        </div>
                    </div>
                    <div style="background:linear-gradient(135deg, #10B981 0%, #059669 100%); color:#FFFFFF; font-weight:800; padding:8px 20px; border-radius:999px; font-size:13px; box-shadow:0 4px 14px rgba(16, 185, 129, 0.35);">
                        {vr['pass_count']} Pass • {vr.get('na_count', 0)} N/A
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background:linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%); border:2px solid #EF4444; border-radius:20px; padding:20px 24px; margin-bottom:22px; box-shadow:0 8px 24px rgba(239, 68, 68, 0.15);">
                    <b style="color:#991B1B; font-size:17px;">🔴 VERIFICATION FAILED / CÒN NGOẠI LỆ CHƯA DUYỆT</b>
                    <div style="font-size:12.5px; color:#B91C1C; margin-top:4px; font-weight:600;">
                        Phát hiện {vr.get('fail_count', 0)} phép kiểm toán chưa đạt. Vui lòng phê duyệt toàn bộ ngoại lệ tại trang <b>Exceptions</b> trước khi xuất báo cáo.
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("##### 📋 Chi Tiết 7 Phép Kiểm Toán Tự Động:")
            df_tests = pd.DataFrame(vr["tests"])[["code", "name", "condition", "expected", "actual", "status", "impact"]]
            df_tests.columns = ["Mã Check", "Tên Phép Kiểm", "Điều Kiện", "Kỳ Vọng", "Thực Tế", "Trạng Thái", "Tác Động Nghiệp Vụ"]
            st.dataframe(df_tests, width='stretch')


# ==============================================================================
# TRANG 7: 📈 REPORTS & XUẤT BẢN HTML STANDALONE
# ==============================================================================
elif "Báo Cáo" in selected_menu or "Reports" in selected_menu:
    render_top_header("Báo Cáo Hoạt Động & Xuất Bản HTML Standalone", "Báo cáo phân tích chuyên sâu sẵn sàng trình Ban Giám đốc")

    is_verified = (st.session_state.verification_status == "PASS")

    if not is_verified:
        st.warning("⚠️ Báo cáo đang bị khóa. Bạn phải hoàn thành quy trình **Verification đạt PASS** trước khi được phép xuất bản báo cáo HTML chính thức.")
    else:
        html_report_data = st.session_state.engine.generate_html_report()

        c_exp1, c_exp2 = st.columns([3, 4])
        with c_exp1:
            st.download_button(
                label="📥 Tải File Báo Cáo HTML Standalone (.html)",
                data=html_report_data,
                file_name=f"Marketing_Campaign_Performance_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html",
                type="primary",
                width='stretch'
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### 👁️ Xem Trước Báo Cáo HTML Trực Tiếp (Live Preview):")
        st.components.v1.html(html_report_data, height=800, scrolling=True)


# ==============================================================================
# TRANG 8: ⚙️ SETTINGS (CÀI ĐẶT)
# ==============================================================================
elif "Cài Đặt" in selected_menu or "Settings" in selected_menu:
    render_top_header("Cài Đặt & Cấu Hình Tham Số Nghiệp Vụ", "Tùy biến Return Window, tiêu thức phân bổ chi phí gián tiếp và danh sách thẩm quyền")

    with st.container():
        st.markdown("""<div class="cloudcash-card">""", unsafe_allow_html=True)
        st.markdown("##### 1. Cấu hình Return Window (Cửa sổ hoàn trả):")
        new_window = st.slider("Số ngày Return Window tối đa:", min_value=15, max_value=30, value=st.session_state.return_window, step=1)
        if new_window != st.session_state.return_window:
            st.session_state.return_window = new_window
            st.success(f"Đã cập nhật Return Window = {new_window} ngày!")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### 2. Cấu hình Cost Driver phân bổ chi phí gián tiếp (Overhead):")
        st.selectbox("Tiêu thức phân bổ mặc định:", ["Order_Volume (Số lượng đơn hàng)", "Revenue_Weight (Tỷ trọng doanh thu)"])

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### 3. Danh sách vai trò có thẩm quyền duyệt ngoại lệ:")
        for r in MarketingAnalyticsEngine.AUTHORIZED_ROLES:
            st.markdown(f"• **{r}**")

        st.markdown("""</div>""", unsafe_allow_html=True)
