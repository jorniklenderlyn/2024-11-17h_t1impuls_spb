import pandas as pd

# Example DataFrame
data = {
    "int_column": [1, 2, "a", 4],
    "float_column": [1.5, "b", 3.7, 4.1],
    "string_column": ["x", "y", "z", "w"]
}

df = pd.DataFrame(data)

# Replace non-numeric entries with None in columns of type int or float
for col in df.select_dtypes(include=["int", "float"]).columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Replace NaN (result of coercion) with None
df = df.where(pd.notnull(df), None)

print(df)
