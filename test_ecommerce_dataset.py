import pandas as pd
from schema_mapper import AutoSchemaMapper

# 1. Dataset mô phỏng chính xác 100% dữ liệu nguồn trong 2 ảnh của user
USER_ECOMMERCE_DATA = [
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
    }
]

df_raw = pd.DataFrame(USER_ECOMMERCE_DATA)
mapper = AutoSchemaMapper()
map_res = mapper.map_columns(list(df_raw.columns), target_tab="Transactions")

print("Mapped columns:")
for k, v in map_res["mapped_dict"].items():
    print(f"  {k:25} -> {v}")

print("Has revenue:", map_res["has_revenue_col"])
print("Has campaign:", map_res["has_campaign_col"])

