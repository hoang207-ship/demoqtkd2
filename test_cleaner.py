from data_pipeline import get_messy_testcase_08_data, DataCleaner

data = get_messy_testcase_08_data()
cleaner = DataCleaner(data)
can_proceed, norm_data, summary, errors, exceptions = cleaner.clean_and_normalize()

print("Can proceed:", can_proceed)
print("Quality score:", summary["Data_Quality_Score"])
print("Auto fixed count:", summary["Auto_Fixed_Count"])
print("Exceptions count:", summary["Exceptions_Count"])
print("Errors logged:", len(errors))
print("Normalized Transactions shape:", norm_data["Normalized_Transactions"].shape)

print("\nExceptions summary:")
for e in exceptions:
    print(f" - [{e['Severity']}] {e['Order_ID']}: {e['Error_Type']} -> {e['Error_Description']}")

print("\nSample Normalized Data:")
print(norm_data["Normalized_Transactions"][["Order_ID", "Order_Value", "Campaign_List_Str", "Campaign_Count", "COGS"]].head(8))

