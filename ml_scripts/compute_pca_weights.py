import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.append(PROJECT_ROOT)

from ml_scripts.preprocess_and_save_scaler import merge_dataframes
from server.config.features_config import FEATURES_CONFIG, DB_COLUMN_NAMES


def main():
    """主執行函數：計算 PCA 權重並儲存為 JSON"""
    df = merge_dataframes()
    if df.empty: return

    for feature in FEATURES_CONFIG:
        if feature.apply_log:
            df[feature.db_col] = np.log1p(df[feature.db_col])

    X = df[DB_COLUMN_NAMES]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    df_scaled = pd.DataFrame(X_scaled, columns=DB_COLUMN_NAMES)

    for feature in FEATURES_CONFIG:
        if feature.invert_score:
            df_scaled[feature.db_col] *= -1

    pca = PCA(n_components=len(DB_COLUMN_NAMES))
    pca.fit(df_scaled)

    # # Check variance
    # for i, ratio in enumerate(pca.explained_variance_ratio_, 1):
    #     print(f"PC{i}: {ratio:.4f}")
    # # Examine the component loadings (eigenvectors)
    # loadings = pd.DataFrame(
    #     pca.components_.T,
    #     index=DB_COLUMN_NAMES,
    #     columns=[f"PC{i + 1}" for i in range(len(DB_COLUMN_NAMES))]
    # )
    # print(loadings.round(4))

    pc1_loadings = pca.components_[0]
    # print("PC1 Loadings:\n", dict(zip(DB_COLUMN_NAMES, pc1_loadings)))
    abs_loadings = np.abs(pc1_loadings)
    weights = abs_loadings / np.sum(abs_loadings)

    weights_dict = {f.api_name: round(w, 4) for f, w in zip(FEATURES_CONFIG, weights)}

    print("Computed Weights:\n", json.dumps(weights_dict, indent=2))

    output_path = os.path.join(PROJECT_ROOT, "server", "config", "default_weights.json")
    with open(output_path, 'w') as f:
        json.dump(weights_dict, f, indent=2)
    print(f"Default weights saved to: {output_path}")


if __name__ == "__main__":
    main()