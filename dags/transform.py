import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from xgboost import XGBRegressor

def preprocess_data(df):
    # === Clean and convert numeric columns ===
    df['top'] = df['top'].str.replace('#', '').astype(int)
    df['rating_count'] = df['rating_count'].str.replace(',', '').astype(int)
    df['price'] = df['price'].str.replace('$', '').astype(float)
    df['bought_info'] = df['bought_info'].astype(str).str.extract(r'(\d+)K\+')[0]
    df['bought_info'] = pd.to_numeric(df['bought_info'], errors='coerce') * 1000
    df['brand'] = df['brand'].fillna("unknown")
    return df


def train_and_predict(df):
    data = df
    # === Encoder ===
    df = df.drop(columns=['id', 'link'])
    label_cols = ['category', 'brand', 'skin_type']
    for col in label_cols:
        df[col] = LabelEncoder().fit_transform(df[col].astype(str))

    # === Split data === 
    df_train = df[df['bought_info'].notna()]
    df_test = df[df['bought_info'].isna()]
    
    X = df_train.drop(columns=['bought_info'])
    y = df_train['bought_info']
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.1, random_state=42)
    
    # === Scale data ===
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    
    # === Random Forest ===
    rf_params = {
        'n_estimators': [100, 200],
        'max_depth': [10, 20, None],
        'min_samples_split': [2, 5],
        'min_samples_leaf': [1, 2]
    }
    rf = RandomizedSearchCV(
        RandomForestRegressor(random_state=42),
        rf_params, n_iter=5, cv=3,
        scoring='neg_mean_squared_error', n_jobs=-1, random_state=42
    )
    rf.fit(X_train_scaled, y_train)
    
    # === XGBoost === 
    xgb_params = {
        'n_estimators': [100, 200],
        'max_depth': [3, 6],
        'learning_rate': [0.01, 0.05],
        'subsample': [0.7, 0.8],
        'colsample_bytree': [0.7, 0.8],
        'reg_alpha': [0.1, 0.5],
        'reg_lambda': [0.5, 1.0]
    }
    xgb = RandomizedSearchCV(
        XGBRegressor(random_state=42, objective='reg:squarederror'),
        xgb_params, n_iter=5, cv=3,
        scoring='neg_mean_squared_error', n_jobs=-1, random_state=42
    )
    xgb.fit(X_train_scaled, y_train)
    
    # === Evaluate models === 
    rf_pred = rf.best_estimator_.predict(X_val_scaled)
    xgb_pred = xgb.best_estimator_.predict(X_val_scaled)
    # MSE
    rf_mse = mean_squared_error(y_val, rf_pred)
    xgb_mse = mean_squared_error(y_val, xgb_pred)
    # R2
    rf_r2 = r2_score(y_val, rf_pred)
    xgb_r2 = r2_score(y_val, xgb_pred)
    print(f"Random Forest MSE: {rf_mse} - R²: {rf_r2}")
    print(f"XGBoost MSE: {xgb_mse} - R²: {xgb_r2}")
    # === Select best model === 
    best_model = rf.best_estimator_ if rf_mse < xgb_mse else xgb.best_estimator_
    
    # === Predict missing values === 
    X_test_scaled = scaler.transform(df_test.drop(columns=['bought_info']))
    df_test['predicted_bought_info'] = np.round(best_model.predict(X_test_scaled)).astype(int)
    
    # === Update original DataFrame === 
    data.loc[data['bought_info'].isna(), 'bought_info'] = df_test['predicted_bought_info']
    
    return data

def process_dataframe(file_path):
    df = pd.read_csv(file_path)
    df = preprocess_data(df)
    df = train_and_predict(df)
    return df

if __name__ == "__main__":
    file_path = "C:\\Users\\trong\\OneDrive\\Documents\\Project\\amazon-ecommerce\\raw.csv"
    processed_df = process_dataframe(file_path)
    print(processed_df.head())
    print(processed_df.info())
    processed_df.to_csv("processed.csv", index=False)