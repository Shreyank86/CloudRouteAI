import pandas as pd
import pickle
import numpy as np
import os
import warnings
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

# Ignore minor sklearn warnings for clean output
warnings.filterwarnings("ignore")

def minmax_normalize(df, feature_cols):
    """
    Apply min-max normalization (0 to 1) to all feature columns.
    This MUST match the cross-scenario normalization used in predict.py
    so training and prediction are on the same scale.
    Returns normalized dataframe and the scaler bounds.
    """
    df_norm = df.copy()
    scaler_bounds = {}
    for col in feature_cols:
        col_min = df[col].min()
        col_max = df[col].max()
        col_range = col_max - col_min
        if col_range > 0:
            df_norm[col] = (df[col] - col_min) / col_range
        else:
            df_norm[col] = 0.5
        scaler_bounds[col] = {'min': col_min, 'max': col_max}
    return df_norm, scaler_bounds

def train_model():
    # Paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "ns3_network_flows.csv")
    model_path = os.path.join(current_dir, "model.pkl")

    print(f"Loading dataset from {csv_path}...")
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: Could not find the CSV file at {csv_path}")
        return

    # The 7 features matching M2 processed JSON format
    feature_cols = ['latency_ms', 'throughput_mbps', 'packet_loss_rate',
                    'tx_packets', 'rx_packets', 'jitter_ms', 'queue_delay_ms']

    print("Applying min-max normalization to training features (0-1 scale)...")
    df_norm, scaler_bounds = minmax_normalize(df, feature_cols)

    X = df_norm[feature_cols]
    y = df['target_cost']

    # Print training data range summary
    print("\nTraining data feature ranges (raw):")
    for col in feature_cols:
        b = scaler_bounds[col]
        print(f"  {col:<22}: min={b['min']:.4f}, max={b['max']:.4f}")

    # Split the dataset: 80% train, 20% test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Train the Random Forest model
    print(f"\nTraining Random Forest Regressor (100 trees)...")
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    # Evaluate
    predictions = model.predict(X_test)
    mse = mean_squared_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)
    print(f"Model trained successfully!")
    print(f"  Mean Squared Error (MSE) : {mse:.4f}")
    print(f"  R2 Score (accuracy proxy): {r2:.4f}  (1.0 = perfect)")

    # Feature importances
    print("\nFeature Importances:")
    importances = model.feature_importances_
    for i in np.argsort(importances)[::-1]:
        bar = '#' * int(importances[i] * 40)
        print(f"  {feature_cols[i]:<22}: {importances[i]:.4f}  {bar}")

    # Save model
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"\nModel saved to {model_path}")

if __name__ == "__main__":
    train_model()
