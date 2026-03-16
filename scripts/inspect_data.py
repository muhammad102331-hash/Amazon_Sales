import pandas as pd
df = pd.read_excel('amazon_sales.xlsx')
print('Shape:', df.shape)
print('\nColumns:', df.columns.tolist())
print('\nDtypes:\n', df.dtypes)
print('\nFirst 3 rows:\n', df.head(3).to_string())
print('\nMissing:\n', df.isnull().sum())
print('\nDescribe:\n', df.describe().to_string())
