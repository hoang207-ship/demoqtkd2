import pandas as pd
from schema_mapper import AutoSchemaMapper

mapper = AutoSchemaMapper()

user_cols = [
    'Quantity',
    'Unit_Price_VND',
    'Discount',
    'Sales_VND',
    'Discount_Amount_VND',
    'Net_Sales_VND',
    'Cost_VND',
    'Profit_VND',
    'Shipping_Days',
    'Returned',
    'Customer_Satisfaction',
    'Payment_Method'
]

res = mapper.map_columns(user_cols, target_tab='Transactions')
print("Mapping Result:")
print("Mapped Dict:")
for k, v in res['mapped_dict'].items():
    print(f"  {k:25} -> {v}")

print("\nMissing Required:", res['missing_required'])
print("Is Valid:", res['is_valid'])
print("Has Revenue Col:", res['has_revenue_col'])
print("Has Campaign Col:", res['has_campaign_col'])
print("Unmapped:", res['unmapped_columns'])

assert res['mapped_dict']['Net_Sales_VND'] == 'Order_Value', "Net_Sales_VND must map to Order_Value!"
assert res['mapped_dict']['Sales_VND'] == 'Gross_Sales', "Sales_VND must map to Gross_Sales!"
assert res['mapped_dict']['Cost_VND'] == 'COGS', "Cost_VND must map to COGS!"
assert res['mapped_dict']['Profit_VND'] == 'Source_Profit', "Profit_VND must map to Source_Profit!"
assert res['mapped_dict']['Discount_Amount_VND'] == 'Discount_Amount', "Discount_Amount_VND must map to Discount_Amount!"
assert res['mapped_dict']['Discount'] == 'Discount_Rate', "Discount must map to Discount_Rate!"
assert res['mapped_dict']['Quantity'] == 'Quantity', "Quantity must map to Quantity!"
assert res['mapped_dict']['Unit_Price_VND'] == 'Unit_Price', "Unit_Price_VND must map to Unit_Price!"
assert res['mapped_dict']['Returned'] == 'Return_Status', "Returned must map to Return_Status!"
assert res['mapped_dict']['Shipping_Days'] == 'Shipping_Days', "Shipping_Days must map to Shipping_Days!"
assert res['mapped_dict']['Customer_Satisfaction'] == 'Customer_Satisfaction', "Customer_Satisfaction must map to Customer_Satisfaction!"
assert res['mapped_dict']['Payment_Method'] == 'Payment_Method', "Payment_Method must map to Payment_Method!"

print("\n>>> ALL 12 USER COLUMNS MAPPED WITH 100% PRECISION! <<<")

