import os
import json
import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.preprocessing import StandardScaler

try:
    from xgboost import XGBRegressor
except ImportError:
    XGBRegressor = None

def preprocess_dataframe(df):
    data = df.copy()
    
    # 1. Clean Brand Name from CarName
    data['brand'] = data['CarName'].apply(lambda x: str(x).split(' ')[0].lower().strip())
    brand_map = {
        'maxda': 'mazda',
        'porcshz': 'porsche',
        'toyouta': 'toyota',
        'vokswagen': 'volkswagen',
        'vw': 'volkswagen',
        'alfa-romero': 'alfa-romeo'
    }
    data['brand'] = data['brand'].replace(brand_map)

    # 2. Feature Engineering
    data['power_to_weight'] = data['horsepower'] / data['curbweight']
    data['avg_mpg'] = (data['citympg'] + data['highwaympg']) / 2.0

    # 3. Cap numerical outliers based on IQR (same as notebook)
    numeric_cols = [
        'wheelbase', 'carlength', 'carwidth', 'carheight', 'curbweight', 
        'enginesize', 'boreratio', 'stroke', 'compressionratio', 'horsepower', 
        'peakrpm', 'citympg', 'highwaympg'
    ]
    for col in numeric_cols:
        Q1 = data[col].quantile(0.25)
        Q3 = data[col].quantile(0.75)
        IQR = Q3 - Q1
        data[col] = np.clip(data[col], Q1 - 1.5 * IQR, Q3 + 1.5 * IQR)

    return data

def main():
    csv_path = 'CarPrice_Assignment (1).csv'
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset {csv_path} not found.")

    df_raw = pd.read_csv(csv_path)
    df = preprocess_dataframe(df_raw)

    categorical_cols = [
        'fueltype', 'aspiration', 'doornumber', 'carbody', 
        'drivewheel', 'enginelocation', 'enginetype', 'cylindernumber', 
        'fuelsystem', 'brand'
    ]

    # Target and Features
    y = df['price'].values
    X_df = df.drop(columns=['car_ID', 'CarName', 'price'])

    # Categorical One-Hot Encoding
    X_encoded = pd.get_dummies(X_df, columns=categorical_cols, drop_first=True)
    feature_names = X_encoded.columns.tolist()

    # Train / Test split
    X_train, X_test, y_train, y_test = train_test_split(
        X_encoded, y, test_size=0.2, random_state=42
    )

    # Scaling for linear models
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    models = {
        "Linear Regression": LinearRegression(),
        "Ridge Regression": Ridge(alpha=1.0),
        "Lasso Regression": Lasso(alpha=1.0, max_iter=5000),
        "Random Forest": RandomForestRegressor(n_estimators=300, random_state=42),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=200, random_state=42)
    }

    if XGBRegressor is not None:
        models["XGBoost"] = XGBRegressor(n_estimators=300, random_state=42, verbosity=0)

    model_results = []
    trained_models = {}

    for name, model in models.items():
        is_linear = "Regression" in name and name != "Random Forest"
        X_tr = X_train_scaled if is_linear else X_train
        X_te = X_test_scaled if is_linear else X_test

        model.fit(X_tr, y_train)
        pred_tr = model.predict(X_tr)
        pred_te = model.predict(X_te)

        tr_r2 = float(r2_score(y_train, pred_tr))
        te_r2 = float(r2_score(y_test, pred_te))
        mae = float(mean_absolute_error(y_test, pred_te))
        rmse = float(np.sqrt(mean_squared_error(y_test, pred_te)))

        trained_models[name] = model

        model_results.append({
            "name": name,
            "train_r2": round(tr_r2, 4),
            "test_r2": round(te_r2, 4),
            "mae": round(mae, 2),
            "rmse": round(rmse, 2)
        })

        print(f"Model: {name:20s} | Test R2: {te_r2:.4f} | MAE: ${mae:,.2f} | RMSE: ${rmse:,.2f}")

    # Best model selection (Random Forest / XGBoost based on Test R2)
    best_model_info = sorted(model_results, key=lambda x: x['test_r2'], reverse=True)[0]
    best_name = best_model_info['name']
    best_model = trained_models[best_name]

    print(f"\nBest Model: {best_name} with Test R2 = {best_model_info['test_r2']}")

    # Feature Importance for tree model
    feature_importances = []
    if hasattr(best_model, 'feature_importances_'):
        importances = best_model.feature_importances_
        sorted_indices = np.argsort(importances)[::-1]
        for idx in sorted_indices[:20]:
            feature_importances.append({
                "feature": feature_names[idx],
                "importance": round(float(importances[idx]), 4)
            })

    # Prepare actual vs predicted for best model
    pred_best = best_model.predict(X_test)
    actual_vs_predicted = []
    for act, pred in zip(y_test[:40], pred_best[:40]):
        actual_vs_predicted.append({
            "actual": round(float(act), 2),
            "predicted": round(float(pred), 2)
        })

    # Collect metadata & schema defaults
    categorical_options = {}
    for col in categorical_cols:
        categorical_options[col] = sorted(df[col].dropna().unique().tolist())

    numerical_stats = {}
    num_cols = [
        'symboling', 'wheelbase', 'carlength', 'carwidth', 'carheight',
        'curbweight', 'enginesize', 'boreratio', 'stroke', 'compressionratio',
        'horsepower', 'peakrpm', 'citympg', 'highwaympg'
    ]
    for col in num_cols:
        numerical_stats[col] = {
            "min": float(df[col].min()),
            "max": float(df[col].max()),
            "mean": float(df[col].mean()),
            "median": float(df[col].median()),
            "default": float(df[col].median())
        }

    metadata = {
        "best_model_name": best_name,
        "model_results": model_results,
        "feature_names": feature_names,
        "feature_importances": feature_importances,
        "actual_vs_predicted": actual_vs_predicted,
        "categorical_options": categorical_options,
        "numerical_stats": numerical_stats,
        "total_records": len(df),
        "target_stats": {
            "min": float(df['price'].min()),
            "max": float(df['price'].max()),
            "mean": float(df['price'].mean()),
            "median": float(df['price'].median())
        }
    }

    # Save model pipeline artifact
    pipeline_artifact = {
        "best_model": best_model,
        "best_model_name": best_name,
        "feature_names": feature_names,
        "categorical_cols": categorical_cols,
        "scaler": scaler,
        "X_encoded_columns": feature_names
    }

    joblib.dump(pipeline_artifact, 'car_price_pipeline.joblib')
    with open('model_metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    print("Successfully saved car_price_pipeline.joblib and model_metadata.json!")

if __name__ == "__main__":
    main()
