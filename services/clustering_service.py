import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from services.data_service import DataService

class ClusteringService:
    @classmethod
    def run_clustering(cls, n_clusters=3, random_state=42, n_init=10):
        df = DataService.get_df().copy()
        
        # Select countries with available 2023 arrivals
        tourism_cluster = df[['country', 'MostVisited_NumOfArrivals_Millions_2023', 'MostVisited_NumOfArrivals_Millions_2022']].copy()
        tourism_cluster['MostVisited_NumOfArrivals_Millions_2023'] = pd.to_numeric(
            tourism_cluster['MostVisited_NumOfArrivals_Millions_2023'], errors='coerce'
        )
        tourism_cluster['MostVisited_NumOfArrivals_Millions_2022'] = pd.to_numeric(
            tourism_cluster['MostVisited_NumOfArrivals_Millions_2022'], errors='coerce'
        )
        
        # Primary clustering dataset: valid 2023 arrivals
        valid_cluster = tourism_cluster[tourism_cluster['MostVisited_NumOfArrivals_Millions_2023'].notna()].copy()
        
        # Feature standardization using StandardScaler
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(valid_cluster[['MostVisited_NumOfArrivals_Millions_2023']])
        
        # Apply K-Means
        kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=n_init)
        valid_cluster['Cluster'] = kmeans.fit_predict(X_scaled)
        
        # Summary statistics per cluster
        summary_df = valid_cluster.groupby('Cluster')['MostVisited_NumOfArrivals_Millions_2023'].agg(
            ['count', 'mean', 'min', 'max']
        ).round(2).reset_index()
        
        # Order clusters by mean arrival to provide clear semantic interpretation
        cluster_summaries = []
        for _, row in summary_df.iterrows():
            c_id = int(row['Cluster'])
            c_mean = float(row['mean'])
            if c_mean > 50:
                tier = "Tier 1: Global Mega-Hubs (High Volume)"
            elif c_mean >= 20:
                tier = "Tier 2: Major Tourism Destinations (Moderate Volume)"
            else:
                tier = "Tier 3: Developing / Niche Destinations (Emerging Volume)"
                
            cluster_summaries.append({
                "cluster_id": c_id,
                "label": f"Cluster {c_id}",
                "tier_description": tier,
                "count": int(row['count']),
                "mean": c_mean,
                "min": float(row['min']),
                "max": float(row['max'])
            })

        # Country assignments list
        countries_list = []
        for _, row in valid_cluster.sort_values(by=['Cluster', 'MostVisited_NumOfArrivals_Millions_2023'], ascending=[True, False]).iterrows():
            countries_list.append({
                "country": str(row['country']),
                "arrivals_2023": round(float(row['MostVisited_NumOfArrivals_Millions_2023']), 2),
                "arrivals_2022": round(float(row['MostVisited_NumOfArrivals_Millions_2022']), 2) if pd.notna(row['MostVisited_NumOfArrivals_Millions_2022']) else None,
                "cluster": int(row['Cluster']),
                "cluster_name": f"Cluster {int(row['Cluster'])}"
            })

        # Scatter plot coordinates
        # 1. 2D points for countries having both 2022 and 2023 arrivals
        scatter_both_years = []
        for item in countries_list:
            if item['arrivals_2022'] is not None:
                scatter_both_years.append({
                    "country": item['country'],
                    "x": item['arrivals_2022'],
                    "y": item['arrivals_2023'],
                    "cluster": item['cluster']
                })

        # 2. 1D spread for all 49 countries
        scatter_all_countries = []
        for idx, item in enumerate(valid_cluster.sort_values(by='MostVisited_NumOfArrivals_Millions_2023').iterrows()):
            row = item[1]
            scatter_all_countries.append({
                "country": str(row['country']),
                "x": idx + 1,
                "y": round(float(row['MostVisited_NumOfArrivals_Millions_2023']), 2),
                "cluster": int(row['Cluster'])
            })

        return {
            "algorithm": "K-Means Clustering",
            "hyperparameters": {
                "n_clusters": n_clusters,
                "random_state": random_state,
                "n_init": n_init,
                "scaler": "StandardScaler"
            },
            "total_countries": len(valid_cluster),
            "cluster_summaries": cluster_summaries,
            "countries": countries_list,
            "scatter_both_years": scatter_both_years,
            "scatter_all_countries": scatter_all_countries,
            "note": "Clustering is trained on 49 countries with valid 2023 arrivals as implemented in the project notebook."
        }
