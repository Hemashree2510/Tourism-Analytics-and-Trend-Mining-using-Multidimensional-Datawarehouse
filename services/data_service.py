import os
import pandas as pd
import numpy as np
from config import Config

class DataService:
    _instance = None
    _df = None

    @classmethod
    def get_df(cls):
        if cls._df is None:
            csv_path = Config.DATA_CSV_PATH
            if not os.path.exists(csv_path):
                # Fallback to local data dir
                csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'tourism_dataset.csv')
            
            df = pd.read_csv(csv_path)
            # Ensure proper numeric typing without altering NaNs
            num_cols = [
                'MostVisited_NumOfArrivalsPredictive_Millions_2024',
                'MostVisited_NumOfArrivals_Millions_2023',
                'MostVisited_NumOfArrivals_Millions_2022',
                'MostVisited_NumOfArrivals_WorldBank',
                'MostVisited_DataYear_WorldBank'
            ]
            for col in num_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            cls._df = df
        return cls._df

    @staticmethod
    def classify_arrival(value):
        if pd.isna(value):
            return "N/A"
        if value < 20:
            return "Low Tourism"
        elif value <= 50:
            return "Medium Tourism"
        else:
            return "High Tourism"

    @classmethod
    def get_all_countries(cls):
        df = cls.get_df()
        return sorted(df['country'].dropna().unique().tolist())

    @classmethod
    def get_available_years(cls):
        df = cls.get_df()
        wb_years = sorted(df['MostVisited_DataYear_WorldBank'].dropna().astype(int).unique().tolist())
        return {
            "standard_years": [2022, 2023, 2024],
            "worldbank_years": wb_years
        }

    @classmethod
    def get_kpis(cls, filters=None):
        df = cls.get_df()
        
        # Apply filters if provided
        filtered = df.copy()
        if filters:
            if filters.get('country') and filters['country'] != 'All':
                filtered = filtered[filtered['country'] == filters['country']]
            if filters.get('category') and filters['category'] != 'All':
                target_col = 'MostVisited_NumOfArrivals_Millions_2023'
                if filters.get('year') == '2022':
                    target_col = 'MostVisited_NumOfArrivals_Millions_2022'
                elif filters.get('year') == '2024':
                    target_col = 'MostVisited_NumOfArrivalsPredictive_Millions_2024'
                filtered = filtered[filtered[target_col].apply(cls.classify_arrival) == filters['category']]

        # Card 1: Countries in Dataset
        total_countries = int(filtered['country'].nunique())

        # Card 2: Countries with 2023 Data
        valid_2023 = filtered[filtered['MostVisited_NumOfArrivals_Millions_2023'].notna()]
        count_2023 = int(len(valid_2023))

        # Card 3: Highest Arrival Country in 2023
        if not valid_2023.empty:
            top_row = valid_2023.sort_values(by='MostVisited_NumOfArrivals_Millions_2023', ascending=False).iloc[0]
            highest_country = {
                "country": str(top_row['country']),
                "arrivals": round(float(top_row['MostVisited_NumOfArrivals_Millions_2023']), 2),
                "year": 2023
            }
        else:
            highest_country = {"country": "N/A", "arrivals": 0.0, "year": 2023}

        # Card 4: 2022-2023 Comparison (only records with both years valid)
        both_years = filtered[
            filtered['MostVisited_NumOfArrivals_Millions_2022'].notna() &
            filtered['MostVisited_NumOfArrivals_Millions_2023'].notna()
        ]
        if not both_years.empty:
            tot_2022 = float(both_years['MostVisited_NumOfArrivals_Millions_2022'].sum())
            tot_2023 = float(both_years['MostVisited_NumOfArrivals_Millions_2023'].sum())
            growth = round(((tot_2023 - tot_2022) / tot_2022) * 100, 1) if tot_2022 > 0 else 0.0
            yoy_comparison = {
                "available": True,
                "growth_pct": growth,
                "tot_2022": round(tot_2022, 2),
                "tot_2023": round(tot_2023, 2),
                "countries_count": int(len(both_years)),
                "note": f"Calculated on {len(both_years)} comparable countries with valid 2022 and 2023 records"
            }
        else:
            yoy_comparison = {
                "available": False,
                "growth_pct": 0.0,
                "tot_2022": 0.0,
                "tot_2023": 0.0,
                "countries_count": 0,
                "note": "No common countries with valid data for both 2022 and 2023"
            }

        # Card 5: 2024 Predicted Arrivals
        valid_2024 = filtered[filtered['MostVisited_NumOfArrivalsPredictive_Millions_2024'].notna()]
        count_2024 = int(len(valid_2024))
        tot_2024 = round(float(valid_2024['MostVisited_NumOfArrivalsPredictive_Millions_2024'].sum()), 2) if count_2024 > 0 else 0.0
        avg_2024 = round(float(valid_2024['MostVisited_NumOfArrivalsPredictive_Millions_2024'].mean()), 2) if count_2024 > 0 else 0.0

        return {
            "total_countries": total_countries,
            "countries_2023_data": count_2023,
            "highest_country": highest_country,
            "yoy_comparison": yoy_comparison,
            "predicted_2024": {
                "count": count_2024,
                "total_millions": tot_2024,
                "average_millions": avg_2024
            }
        }

    @classmethod
    def get_top_countries(cls, year=2023, limit=10, search="", category=""):
        df = cls.get_df().copy()
        
        # Column selection based on year
        if year == 2022:
            target_col = 'MostVisited_NumOfArrivals_Millions_2022'
        elif year == 2024:
            target_col = 'MostVisited_NumOfArrivalsPredictive_Millions_2024'
        else:
            target_col = 'MostVisited_NumOfArrivals_Millions_2023'
            year = 2023

        # Filter out rows where target_col is null
        valid = df[df[target_col].notna()].copy()

        if search:
            valid = valid[valid['country'].str.contains(search, case=False, na=False)]

        valid['Category'] = valid[target_col].apply(cls.classify_arrival)
        if category and category != 'All':
            valid = valid[valid['Category'] == category]

        valid = valid.sort_values(by=target_col, ascending=False)
        if limit:
            valid = valid.head(limit)

        records = []
        for rank, (_, row) in enumerate(valid.iterrows(), start=1):
            records.append({
                "rank": rank,
                "country": row['country'],
                "arrivals_2022": round(float(row['MostVisited_NumOfArrivals_Millions_2022']), 2) if pd.notna(row['MostVisited_NumOfArrivals_Millions_2022']) else None,
                "arrivals_2023": round(float(row['MostVisited_NumOfArrivals_Millions_2023']), 2) if pd.notna(row['MostVisited_NumOfArrivals_Millions_2023']) else None,
                "arrivals_2024_pred": round(float(row['MostVisited_NumOfArrivalsPredictive_Millions_2024']), 2) if pd.notna(row['MostVisited_NumOfArrivalsPredictive_Millions_2024']) else None,
                "selected_year_arrival": round(float(row[target_col]), 2),
                "category": row['Category']
            })
        return {
            "year": year,
            "total_available": len(valid),
            "records": records
        }

    @classmethod
    def get_tourism_trends(cls):
        df = cls.get_df()

        # 1. Yearly totals
        tot_2022 = df['MostVisited_NumOfArrivals_Millions_2022'].dropna()
        tot_2023 = df['MostVisited_NumOfArrivals_Millions_2023'].dropna()
        tot_2024 = df['MostVisited_NumOfArrivalsPredictive_Millions_2024'].dropna()

        # 2. Top 10 for 2023
        top_10_2023 = df[df['MostVisited_NumOfArrivals_Millions_2023'].notna()].sort_values(
            by='MostVisited_NumOfArrivals_Millions_2023', ascending=False
        ).head(10)
        
        top_countries_chart = {
            "labels": top_10_2023['country'].tolist(),
            "data": [round(val, 2) for val in top_10_2023['MostVisited_NumOfArrivals_Millions_2023'].tolist()]
        }

        # 3. 2022 vs 2023 comparison for common 17 countries
        common = df[
            df['MostVisited_NumOfArrivals_Millions_2022'].notna() &
            df['MostVisited_NumOfArrivals_Millions_2023'].notna()
        ].sort_values(by='MostVisited_NumOfArrivals_Millions_2023', ascending=False)

        comparison_chart = {
            "labels": common['country'].tolist(),
            "data_2022": [round(val, 2) for val in common['MostVisited_NumOfArrivals_Millions_2022'].tolist()],
            "data_2023": [round(val, 2) for val in common['MostVisited_NumOfArrivals_Millions_2023'].tolist()],
            "sample_size": len(common)
        }

        # 4. Classification categories distribution for 2023
        categories = df['MostVisited_NumOfArrivals_Millions_2023'].dropna().apply(cls.classify_arrival).value_counts().to_dict()

        # 5. World bank historical distribution
        wb_data = df[df['MostVisited_DataYear_WorldBank'].notna() & df['MostVisited_NumOfArrivals_WorldBank'].notna()]
        wb_summary = wb_data.groupby('MostVisited_DataYear_WorldBank')['MostVisited_NumOfArrivals_WorldBank'].agg(['count', 'sum']).reset_index()
        wb_summary = wb_summary.sort_values(by='MostVisited_DataYear_WorldBank')

        return {
            "yearly_aggregates": {
                "2022_actual": {"count": int(len(tot_2022)), "total_millions": round(float(tot_2022.sum()), 2), "mean": round(float(tot_2022.mean()), 2)},
                "2023_actual": {"count": int(len(tot_2023)), "total_millions": round(float(tot_2023.sum()), 2), "mean": round(float(tot_2023.mean()), 2)},
                "2024_pred": {"count": int(len(tot_2024)), "total_millions": round(float(tot_2024.sum()), 2), "mean": round(float(tot_2024.mean()), 2)},
                "note": "Units in Millions. Coverage varies (20 countries in 2022, 49 in 2023, 50 in 2024). Not interpolated."
            },
            "top_countries_2023": top_countries_chart,
            "comparison_2022_2023": comparison_chart,
            "category_distribution": categories,
            "world_bank_historical": {
                "years": [int(y) for y in wb_summary['MostVisited_DataYear_WorldBank'].tolist()],
                "counts": [int(c) for c in wb_summary['count'].tolist()],
                "totals_raw": [float(s) for s in wb_summary['sum'].tolist()],
                "totals_millions": [round(float(s) / 1e6, 2) for s in wb_summary['sum'].tolist()],
                "note": "World Bank observations are reported in raw numbers (converted to millions for comparison) across varying years."
            }
        }

    @classmethod
    def get_country_details(cls, country_name):
        df = cls.get_df()
        row = df[df['country'].str.lower() == country_name.strip().lower()]
        if row.empty:
            return None
        r = row.iloc[0]

        arr_2022 = round(float(r['MostVisited_NumOfArrivals_Millions_2022']), 2) if pd.notna(r['MostVisited_NumOfArrivals_Millions_2022']) else None
        arr_2023 = round(float(r['MostVisited_NumOfArrivals_Millions_2023']), 2) if pd.notna(r['MostVisited_NumOfArrivals_Millions_2023']) else None
        arr_2024 = round(float(r['MostVisited_NumOfArrivalsPredictive_Millions_2024']), 2) if pd.notna(r['MostVisited_NumOfArrivalsPredictive_Millions_2024']) else None
        wb_arr = float(r['MostVisited_NumOfArrivals_WorldBank']) if pd.notna(r['MostVisited_NumOfArrivals_WorldBank']) else None
        wb_year = int(r['MostVisited_DataYear_WorldBank']) if pd.notna(r['MostVisited_DataYear_WorldBank']) else None

        category = cls.classify_arrival(arr_2023) if arr_2023 is not None else "N/A"

        # YoY change if both exist
        yoy_change = None
        if arr_2022 is not None and arr_2023 is not None and arr_2022 > 0:
            yoy_change = round(((arr_2023 - arr_2022) / arr_2022) * 100, 2)

        return {
            "country": r['country'],
            "arrivals_2022": arr_2022,
            "arrivals_2023": arr_2023,
            "arrivals_2024_pred": arr_2024,
            "worldbank_arrivals": wb_arr,
            "worldbank_arrivals_millions": round(wb_arr / 1e6, 2) if wb_arr is not None else None,
            "worldbank_year": wb_year,
            "category": category,
            "yoy_change_pct": yoy_change
        }

    @classmethod
    def get_data_dictionary(cls):
        df = cls.get_df()
        attributes = [
            {
                "attribute_name": "country",
                "data_type": "String / Text",
                "description": "Name of the sovereign country or reporting territory",
                "role": "Dimension (DIM_Country)",
                "missing_count": int(df['country'].isna().sum()),
                "valid_count": int(df['country'].notna().sum()),
                "sample_value": "France, United States, Japan"
            },
            {
                "attribute_name": "MostVisited_NumOfArrivalsPredictive_Millions_2024",
                "data_type": "Decimal / Real",
                "description": "Predicted tourist arrivals in 2024 expressed in millions",
                "role": "Measure (FACT_Tourism - Predicted)",
                "missing_count": int(df['MostVisited_NumOfArrivalsPredictive_Millions_2024'].isna().sum()),
                "valid_count": int(df['MostVisited_NumOfArrivalsPredictive_Millions_2024'].notna().sum()),
                "sample_value": "89.4, 83.7, 79.3"
            },
            {
                "attribute_name": "MostVisited_NumOfArrivals_Millions_2023",
                "data_type": "Decimal / Real",
                "description": "Actual international tourist arrivals in 2023 expressed in millions",
                "role": "Measure (FACT_Tourism - Actual)",
                "missing_count": int(df['MostVisited_NumOfArrivals_Millions_2023'].isna().sum()),
                "valid_count": int(df['MostVisited_NumOfArrivals_Millions_2023'].notna().sum()),
                "sample_value": "100.0, 85.17, 66.48"
            },
            {
                "attribute_name": "MostVisited_NumOfArrivals_Millions_2022",
                "data_type": "Decimal / Real",
                "description": "Actual international tourist arrivals in 2022 expressed in millions",
                "role": "Measure (FACT_Tourism - Actual)",
                "missing_count": int(df['MostVisited_NumOfArrivals_Millions_2022'].isna().sum()),
                "valid_count": int(df['MostVisited_NumOfArrivals_Millions_2022'].notna().sum()),
                "sample_value": "79.4, 71.66, 50.87"
            },
            {
                "attribute_name": "MostVisited_NumOfArrivals_WorldBank",
                "data_type": "Numeric / Integer",
                "description": "Historical international tourist arrivals reported by the World Bank (raw count)",
                "role": "Measure (FACT_Tourism - World Bank)",
                "missing_count": int(df['MostVisited_NumOfArrivals_WorldBank'].isna().sum()),
                "valid_count": int(df['MostVisited_NumOfArrivals_WorldBank'].notna().sum()),
                "sample_value": "117,109,000; 45,037,000"
            },
            {
                "attribute_name": "MostVisited_DataYear_WorldBank",
                "data_type": "Integer",
                "description": "Reference year associated with the World Bank historical arrival figure",
                "role": "Dimension (DIM_WorldBank / DIM_Time)",
                "missing_count": int(df['MostVisited_DataYear_WorldBank'].isna().sum()),
                "valid_count": int(df['MostVisited_DataYear_WorldBank'].notna().sum()),
                "sample_value": "2019, 2020"
            }
        ]
        return {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "attributes": attributes
        }
