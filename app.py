import os
import json
import numpy as np
import pandas as pd
import joblib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

app = FastAPI(
    title="AutoValuate Pro — Automotive Valuation Platform",
    description="Enterprise Car Valuation, Resale Analysis & Market Intelligence",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

USD_TO_INR = 83.5

# Load pipeline and metadata silently
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PIPELINE_PATH = os.path.join(BASE_DIR, "car_price_pipeline.joblib")
METADATA_PATH = os.path.join(BASE_DIR, "model_metadata.json")
CSV_PATH = os.path.join(BASE_DIR, "CarPrice_Assignment (1).csv")

if not os.path.exists(PIPELINE_PATH) or not os.path.exists(METADATA_PATH):
    raise FileNotFoundError("System initialization files missing. Please run train_model.py first.")

pipeline_data = joblib.load(PIPELINE_PATH)
best_model = pipeline_data["best_model"]
feature_names = pipeline_data["feature_names"]
categorical_cols = pipeline_data["categorical_cols"]

with open(METADATA_PATH, "r", encoding="utf-8") as f:
    raw_metadata = json.load(f)

df_raw = pd.read_csv(CSV_PATH)
df_raw['brand'] = df_raw['CarName'].apply(lambda x: str(x).split(' ')[0].lower().strip())
brand_map = {
    'maxda': 'mazda',
    'porcshz': 'porsche',
    'toyouta': 'toyota',
    'vokswagen': 'volkswagen',
    'vw': 'volkswagen',
    'alfa-romero': 'alfa-romeo'
}
df_raw['brand'] = df_raw['brand'].replace(brand_map)
df_raw['power_to_weight'] = df_raw['horsepower'] / df_raw['curbweight']
df_raw['avg_mpg'] = (df_raw['citympg'] + df_raw['highwaympg']) / 2.0


class CarInput(BaseModel):
    brand: str = Field(default="toyota")
    symboling: int = Field(default=0)
    fueltype: str = Field(default="gas")
    aspiration: str = Field(default="std")
    doornumber: str = Field(default="four")
    carbody: str = Field(default="sedan")
    drivewheel: str = Field(default="fwd")
    enginelocation: str = Field(default="front")
    wheelbase: float = Field(default=97.0)
    carlength: float = Field(default=172.0)
    carwidth: float = Field(default=65.5)
    carheight: float = Field(default=53.7)
    curbweight: float = Field(default=2330.0)
    enginetype: str = Field(default="ohc")
    cylindernumber: str = Field(default="four")
    enginesize: float = Field(default=120.0)
    fuelsystem: str = Field(default="mpfi")
    boreratio: float = Field(default=3.3)
    stroke: float = Field(default=3.25)
    compressionratio: float = Field(default=9.0)
    horsepower: float = Field(default=100.0)
    peakrpm: float = Field(default=5200.0)
    citympg: float = Field(default=25.0)
    highwaympg: float = Field(default=30.0)


class CompareInput(BaseModel):
    carA: CarInput
    carB: CarInput


def format_car_features(car_dict: dict) -> pd.DataFrame:
    df_single = pd.DataFrame([car_dict])
    df_single['power_to_weight'] = df_single['horsepower'] / df_single['curbweight']
    df_single['avg_mpg'] = (df_single['citympg'] + df_single['highwaympg']) / 2.0
    df_encoded = pd.get_dummies(df_single, columns=categorical_cols, drop_first=True)
    df_encoded = df_encoded.reindex(columns=feature_names, fill_value=0)
    return df_encoded


def format_inr(val_inr: float) -> str:
    if val_inr >= 10000000:
        return f"₹ {val_inr / 10000000:.2f} Cr"
    elif val_inr >= 100000:
        return f"₹ {val_inr / 100000:.2f} Lakh"
    else:
        return f"₹ {val_inr:,.0f}"


def get_car_image(body_style: str) -> str:
    body = body_style.lower()
    valid_types = ['sedan', 'hatchback', 'convertible', 'wagon', 'hardtop']
    if body in valid_types:
        return f"/static/images/{body}.png"
    return "/static/images/sedan.png"


@app.get("/api/metadata")
def get_metadata():
    """Sanitized metadata without ML training disclosures."""
    return {
        "categorical_options": raw_metadata["categorical_options"],
        "numerical_stats": raw_metadata["numerical_stats"]
    }


@app.get("/api/market-trends")
def get_market_trends():
    """Returns commercial market intelligence data."""
    brand_avg = df_raw.groupby('brand')['price'].agg(['mean', 'count']).reset_index()
    brand_avg = brand_avg.sort_values('mean', ascending=False)
    
    body_dist = df_raw['carbody'].value_counts().to_dict()
    fuel_dist = df_raw['fueltype'].value_counts().to_dict()

    scatter_data = []
    for _, row in df_raw.iterrows():
        price_usd = float(row["price"])
        price_inr = round(price_usd * USD_TO_INR, 2)
        scatter_data.append({
            "brand": row["brand"].upper(),
            "horsepower": float(row["horsepower"]),
            "price_usd": price_usd,
            "price_inr": price_inr,
            "price_lakhs": round(price_inr / 100000, 2),
            "carbody": row["carbody"].capitalize()
        })

    return {
        "brand_averages": {
            "brands": [b.upper() for b in brand_avg["brand"].tolist()],
            "avg_prices_usd": [round(x, 2) for x in brand_avg["mean"].tolist()],
            "avg_prices_inr_lakhs": [round((x * USD_TO_INR) / 100000, 2) for x in brand_avg["mean"].tolist()]
        },
        "body_distribution": {k.capitalize(): v for k, v in body_dist.items()},
        "fuel_distribution": {k.capitalize(): v for k, v in fuel_dist.items()},
        "scatter_data": scatter_data
    }


@app.post("/api/predict")
def predict_price(car: CarInput):
    car_dict = car.dict()
    df_features = format_car_features(car_dict)
    
    predicted_val_usd = float(best_model.predict(df_features)[0])
    predicted_val_usd = max(5000.0, round(predicted_val_usd, 2))

    margin_usd = 1200.0
    lower_bound_usd = max(4500.0, round(predicted_val_usd - margin_usd, 2))
    upper_bound_usd = round(predicted_val_usd + margin_usd, 2)

    predicted_val_inr = predicted_val_usd * USD_TO_INR
    lower_bound_inr = lower_bound_usd * USD_TO_INR
    upper_bound_inr = upper_bound_usd * USD_TO_INR

    inr_formatted = format_inr(predicted_val_inr)
    inr_lakhs = round(predicted_val_inr / 100000, 2)

    # Market Price Breakdown (Showroom / Trade-in / Private Resale)
    new_car_showroom_inr = predicted_val_inr * 1.25  # Ex-showroom premium
    trade_in_offer_inr = predicted_val_inr * 0.88     # Instant dealer cash offer

    # Depreciation projections over 5 years
    depreciation_schedule = [
        {"year": "Current Value", "price_inr": inr_formatted, "retain_pct": "100%"},
        {"year": "Year 1", "price_inr": format_inr(predicted_val_inr * 0.85), "retain_pct": "85%"},
        {"year": "Year 2", "price_inr": format_inr(predicted_val_inr * 0.74), "retain_pct": "74%"},
        {"year": "Year 3", "price_inr": format_inr(predicted_val_inr * 0.65), "retain_pct": "65%"},
        {"year": "Year 5", "price_inr": format_inr(predicted_val_inr * 0.50), "retain_pct": "50%"},
    ]

    # Market segment classification
    if predicted_val_inr < 1000000:
        segment = "Compact Economy"
        seg_color = "#34d399"
    elif predicted_val_inr < 2000000:
        segment = "Mid-Size Premium"
        seg_color = "#60a5fa"
    elif predicted_val_inr < 3500000:
        segment = "Executive Class"
        seg_color = "#a78bfa"
    else:
        segment = "Ultra Luxury / Sports"
        seg_color = "#f472b6"

    power_to_weight = round(car.horsepower / car.curbweight, 4)
    avg_mpg = round((car.citympg + car.highwaympg) / 2.0, 1)

    key_drivers = []
    if car.enginesize > 150:
        key_drivers.append("High Performance Engine Capacity")
    elif car.enginesize < 100:
        key_drivers.append("Optimized Fuel Efficient Powertrain")

    if car.horsepower > 140:
        key_drivers.append("High Horsepower Rating")

    if car.curbweight > 2800:
        key_drivers.append("Reinforced Chassis Structure")

    if car.brand in ['bmw', 'porsche', 'buick', 'jaguar']:
        key_drivers.append(f"Premium Brand Tier ({car.brand.upper()})")

    if not key_drivers:
        key_drivers.append("Standard Commuter Configuration")

    car_image = get_car_image(car.carbody)

    return {
        "predicted_price_usd": predicted_val_usd,
        "predicted_price_inr": round(predicted_val_inr, 2),
        "inr_formatted": inr_formatted,
        "inr_lakhs": inr_lakhs,
        "new_car_showroom_inr": format_inr(new_car_showroom_inr),
        "trade_in_offer_inr": format_inr(trade_in_offer_inr),
        "lower_bound_usd": lower_bound_usd,
        "upper_bound_usd": upper_bound_usd,
        "lower_bound_inr": format_inr(lower_bound_inr),
        "upper_bound_inr": format_inr(upper_bound_inr),
        "market_tier": segment,
        "tier_color": seg_color,
        "power_to_weight": power_to_weight,
        "avg_mpg": avg_mpg,
        "key_drivers": key_drivers,
        "car_image": car_image,
        "depreciation_schedule": depreciation_schedule,
        "inputs": car_dict
    }


@app.post("/api/compare")
def compare_cars(compare: CompareInput):
    """Compares two vehicle configurations side-by-side."""
    featA = format_car_features(compare.carA.dict())
    featB = format_car_features(compare.carB.dict())

    priceA_usd = max(5000.0, round(float(best_model.predict(featA)[0]), 2))
    priceB_usd = max(5000.0, round(float(best_model.predict(featB)[0]), 2))

    priceA_inr = priceA_usd * USD_TO_INR
    priceB_inr = priceB_usd * USD_TO_INR

    diff_inr = abs(priceA_inr - priceB_inr)

    return {
        "carA": {
            "brand": compare.carA.brand.upper(),
            "body": compare.carA.carbody.capitalize(),
            "price_inr": format_inr(priceA_inr),
            "price_usd": f"${priceA_usd:,.2f}",
            "horsepower": compare.carA.horsepower,
            "mpg": round((compare.carA.citympg + compare.carA.highwaympg) / 2, 1),
            "image": get_car_image(compare.carA.carbody)
        },
        "carB": {
            "brand": compare.carB.brand.upper(),
            "body": compare.carB.carbody.capitalize(),
            "price_inr": format_inr(priceB_inr),
            "price_usd": f"${priceB_usd:,.2f}",
            "horsepower": compare.carB.horsepower,
            "mpg": round((compare.carB.citympg + compare.carB.highwaympg) / 2, 1),
            "image": get_car_image(compare.carB.carbody)
        },
        "price_difference": format_inr(diff_inr),
        "higher_value_car": "Car A" if priceA_inr > priceB_inr else "Car B"
    }


STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def read_root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))
