import os
import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text
from config import Config

class WarehouseService:
    _engine = None
    _active_db_type = 'sqlite'

    @classmethod
    def get_engine(cls):
        if cls._engine is None:
            # Try MySQL if configured
            if Config.DB_TYPE == 'mysql':
                try:
                    uri = Config.get_sqlalchemy_database_uri()
                    engine = create_engine(uri, pool_pre_ping=True)
                    # Test connection
                    with engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    cls._engine = engine
                    cls._active_db_type = 'mysql'
                except Exception as e:
                    # Fallback cleanly to SQLite
                    print(f"[WarehouseService] MySQL connection failed ({e}). Falling back to SQLite.")
                    cls._engine = create_engine(f"sqlite:///{Config.SQLITE_DB_PATH}")
                    cls._active_db_type = 'sqlite'
            else:
                cls._engine = create_engine(f"sqlite:///{Config.SQLITE_DB_PATH}")
                cls._active_db_type = 'sqlite'
                
            cls.ensure_warehouse_initialized()
        return cls._engine

    @classmethod
    def get_active_db_type(cls):
        if cls._engine is None:
            cls.get_engine()
        return cls._active_db_type

    @classmethod
    def ensure_warehouse_initialized(cls):
        """Builds star schema tables and runs ETL if fact_tourism table has no rows."""
        engine = cls.get_engine()
        needs_etl = False
        try:
            with engine.connect() as conn:
                res = conn.execute(text("SELECT COUNT(*) FROM fact_tourism")).scalar()
                if res == 0:
                    needs_etl = True
        except Exception:
            needs_etl = True

        if needs_etl:
            cls.run_etl()

    @classmethod
    def run_etl(cls):
        """Runs the ETL transformation matching the student project notebook."""
        engine = cls.get_engine()
        is_sqlite = (cls._active_db_type == 'sqlite')
        
        # Load CSV
        csv_path = Config.DATA_CSV_PATH
        if not os.path.exists(csv_path):
            csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'tourism_dataset.csv')
        df = pd.read_csv(csv_path)

        with engine.begin() as conn:
            # Drop existing if needed
            if is_sqlite:
                conn.execute(text("DROP TABLE IF EXISTS fact_tourism"))
                conn.execute(text("DROP TABLE IF EXISTS dim_country"))
                conn.execute(text("DROP TABLE IF EXISTS dim_time"))
                conn.execute(text("DROP TABLE IF EXISTS dim_tourism_type"))
                conn.execute(text("DROP TABLE IF EXISTS dim_worldbank"))

                # Create SQLite Tables
                conn.execute(text("""
                CREATE TABLE dim_country(
                    country_key INTEGER PRIMARY KEY,
                    country_name TEXT NOT NULL
                );
                """))
                conn.execute(text("""
                CREATE TABLE dim_time(
                    time_key INTEGER PRIMARY KEY,
                    year_num INTEGER NOT NULL,
                    year_category TEXT NOT NULL
                );
                """))
                conn.execute(text("""
                CREATE TABLE dim_tourism_type(
                    tourism_type_key INTEGER PRIMARY KEY,
                    data_type TEXT NOT NULL,
                    actual_or_predicted TEXT NOT NULL,
                    data_source TEXT NOT NULL
                );
                """))
                conn.execute(text("""
                CREATE TABLE dim_worldbank(
                    worldbank_key INTEGER PRIMARY KEY,
                    worldbank_data_year INTEGER NOT NULL,
                    source_name TEXT NOT NULL
                );
                """))
                conn.execute(text("""
                CREATE TABLE fact_tourism(
                    tourism_key INTEGER PRIMARY KEY,
                    country_key INTEGER,
                    time_key INTEGER,
                    tourism_type_key INTEGER,
                    worldbank_key INTEGER,
                    tourist_arrivals_millions REAL,
                    FOREIGN KEY (country_key) REFERENCES dim_country(country_key),
                    FOREIGN KEY (time_key) REFERENCES dim_time(time_key),
                    FOREIGN KEY (tourism_type_key) REFERENCES dim_tourism_type(tourism_type_key),
                    FOREIGN KEY (worldbank_key) REFERENCES dim_worldbank(worldbank_key)
                );
                """))
            else:
                # MySQL DDL
                conn.execute(text("DROP TABLE IF EXISTS fact_tourism"))
                conn.execute(text("DROP TABLE IF EXISTS dim_country"))
                conn.execute(text("DROP TABLE IF EXISTS dim_time"))
                conn.execute(text("DROP TABLE IF EXISTS dim_tourism_type"))
                conn.execute(text("DROP TABLE IF EXISTS dim_worldbank"))

                conn.execute(text("""
                CREATE TABLE dim_country(
                    country_key INT PRIMARY KEY,
                    country_name VARCHAR(100) NOT NULL
                ) ENGINE=InnoDB;
                """))
                conn.execute(text("""
                CREATE TABLE dim_time(
                    time_key INT PRIMARY KEY,
                    year_num INT NOT NULL,
                    year_category VARCHAR(30) NOT NULL
                ) ENGINE=InnoDB;
                """))
                conn.execute(text("""
                CREATE TABLE dim_tourism_type(
                    tourism_type_key INT PRIMARY KEY,
                    data_type VARCHAR(50) NOT NULL,
                    actual_or_predicted VARCHAR(20) NOT NULL,
                    data_source VARCHAR(100) NOT NULL
                ) ENGINE=InnoDB;
                """))
                conn.execute(text("""
                CREATE TABLE dim_worldbank(
                    worldbank_key INT PRIMARY KEY,
                    worldbank_data_year INT NOT NULL,
                    source_name VARCHAR(100) NOT NULL
                ) ENGINE=InnoDB;
                """))
                conn.execute(text("""
                CREATE TABLE fact_tourism(
                    tourism_key INT PRIMARY KEY,
                    country_key INT,
                    time_key INT,
                    tourism_type_key INT,
                    worldbank_key INT,
                    tourist_arrivals_millions DECIMAL(12,3),
                    FOREIGN KEY (country_key) REFERENCES dim_country(country_key),
                    FOREIGN KEY (time_key) REFERENCES dim_time(time_key),
                    FOREIGN KEY (tourism_type_key) REFERENCES dim_tourism_type(tourism_type_key),
                    FOREIGN KEY (worldbank_key) REFERENCES dim_worldbank(worldbank_key)
                ) ENGINE=InnoDB;
                """))

        # Populate tables using pandas
        # 1. DIM_COUNTRY
        dim_country = df[['country']].drop_duplicates().sort_values('country').reset_index(drop=True)
        dim_country['country_key'] = range(1, len(dim_country) + 1)
        dim_country.rename(columns={'country': 'country_name'}, inplace=True)
        dim_country = dim_country[['country_key', 'country_name']]
        dim_country.to_sql('dim_country', engine, if_exists='append', index=False)

        # 2. DIM_TIME
        years = [2022, 2023, 2024]
        wb_years = df['MostVisited_DataYear_WorldBank'].dropna().astype(int).unique().tolist()
        all_years = sorted(list(set(years + wb_years)))
        dim_time = pd.DataFrame({'year_num': all_years})
        dim_time['time_key'] = range(1, len(dim_time) + 1)
        dim_time['year_category'] = dim_time['year_num'].apply(lambda y: 'Predicted' if y == 2024 else 'Actual')
        dim_time = dim_time[['time_key', 'year_num', 'year_category']]
        dim_time.to_sql('dim_time', engine, if_exists='append', index=False)

        # 3. DIM_TOURISMTYPE
        dim_tourism_type = pd.DataFrame([
            {'tourism_type_key': 1, 'data_type': 'Tourist Arrivals', 'actual_or_predicted': 'Actual', 'data_source': 'Kaggle'},
            {'tourism_type_key': 2, 'data_type': 'Tourist Arrivals', 'actual_or_predicted': 'Predicted', 'data_source': 'Kaggle'},
            {'tourism_type_key': 3, 'data_type': 'Tourist Arrivals', 'actual_or_predicted': 'Actual', 'data_source': 'World Bank'}
        ])
        dim_tourism_type.to_sql('dim_tourism_type', engine, if_exists='append', index=False)

        # 4. DIM_WORLDBANK
        wb_data = df[df['MostVisited_DataYear_WorldBank'].notna()].copy()
        dim_wb = wb_data[['MostVisited_DataYear_WorldBank']].drop_duplicates().sort_values('MostVisited_DataYear_WorldBank').reset_index(drop=True)
        dim_wb['worldbank_key'] = range(1, len(dim_wb) + 1)
        dim_wb.rename(columns={'MostVisited_DataYear_WorldBank': 'worldbank_data_year'}, inplace=True)
        dim_wb['source_name'] = 'World Bank'
        dim_wb = dim_wb[['worldbank_key', 'worldbank_data_year', 'source_name']]
        dim_wb.to_sql('dim_worldbank', engine, if_exists='append', index=False)

        # 5. FACT_TOURISM
        year_cols = {
            2022: 'MostVisited_NumOfArrivals_Millions_2022',
            2023: 'MostVisited_NumOfArrivals_Millions_2023',
            2024: 'MostVisited_NumOfArrivalsPredictive_Millions_2024'
        }
        fact_parts = []
        for yr, col in year_cols.items():
            temp = df[['country', col]].copy()
            temp.rename(columns={col: 'tourist_arrivals_millions'}, inplace=True)
            temp['year_num'] = yr
            temp['tourism_type_key'] = 2 if yr == 2024 else 1
            temp['worldbank_key'] = None
            fact_parts.append(temp)

        fact_kaggle = pd.concat(fact_parts, ignore_index=True)
        fact_kaggle = fact_kaggle.dropna(subset=['tourist_arrivals_millions'])

        wb_fact = df[df['MostVisited_NumOfArrivals_WorldBank'].notna() & df['MostVisited_DataYear_WorldBank'].notna()].copy()
        wb_fact = wb_fact.rename(columns={
            'MostVisited_NumOfArrivals_WorldBank': 'tourist_arrivals_millions',
            'MostVisited_DataYear_WorldBank': 'year_num'
        })
        wb_fact['year_num'] = wb_fact['year_num'].astype(int)
        wb_fact['tourism_type_key'] = 3
        wb_key_map = dim_wb.set_index('worldbank_data_year')['worldbank_key']
        wb_fact['worldbank_key'] = wb_fact['year_num'].map(wb_key_map)
        wb_fact = wb_fact[['country', 'year_num', 'tourism_type_key', 'worldbank_key', 'tourist_arrivals_millions']]

        fact_tourism = pd.concat([fact_kaggle, wb_fact], ignore_index=True)
        fact_tourism = fact_tourism.merge(dim_country, left_on='country', right_on='country_name', how='left')
        fact_tourism = fact_tourism.merge(dim_time[['time_key', 'year_num']], on='year_num', how='left')
        fact_tourism = fact_tourism[['country_key', 'time_key', 'tourism_type_key', 'worldbank_key', 'tourist_arrivals_millions']].copy()
        fact_tourism.insert(0, 'tourism_key', range(1, len(fact_tourism) + 1))
        fact_tourism.to_sql('fact_tourism', engine, if_exists='append', index=False)

    @classmethod
    def execute_query(cls, sql_text, params=None):
        engine = cls.get_engine()
        with engine.connect() as conn:
            result = conn.execute(text(sql_text), params or {})
            cols = list(result.keys())
            rows = [dict(zip(cols, row)) for row in result.fetchall()]
            return {"columns": cols, "rows": rows, "count": len(rows)}

    @classmethod
    def get_schema_info(cls):
        return {
            "warehouse_name": "TourismVista Multidimensional Warehouse",
            "schema_type": "Star Schema",
            "active_database": cls.get_active_db_type().upper(),
            "grain": "One row per country, observation year, and tourism data type",
            "fact_table": {
                "name": "fact_tourism",
                "primary_key": "tourism_key",
                "foreign_keys": [
                    {"column": "country_key", "references": "dim_country(country_key)"},
                    {"column": "time_key", "references": "dim_time(time_key)"},
                    {"column": "tourism_type_key", "references": "dim_tourism_type(tourism_type_key)"},
                    {"column": "worldbank_key", "references": "dim_worldbank(worldbank_key)"}
                ],
                "measures": [
                    {"column": "tourist_arrivals_millions", "type": "DECIMAL(12,3) / REAL", "additive": "Yes, across countries for comparable years"}
                ]
            },
            "dimensions": [
                {
                    "name": "dim_country",
                    "primary_key": "country_key",
                    "attributes": ["country_name"]
                },
                {
                    "name": "dim_time",
                    "primary_key": "time_key",
                    "attributes": ["year_num", "year_category"]
                },
                {
                    "name": "dim_tourism_type",
                    "primary_key": "tourism_type_key",
                    "attributes": ["data_type", "actual_or_predicted", "data_source"]
                },
                {
                    "name": "dim_worldbank",
                    "primary_key": "worldbank_key",
                    "attributes": ["worldbank_data_year", "source_name"]
                }
            ],
            "etl_pipeline": [
                {"step": 1, "title": "Extract", "description": "Extract raw data from Kaggle CSV containing 203 countries and 6 columns."},
                {"step": 2, "title": "Transform & Clean", "description": "Parse numeric arrival figures, separate annual and World Bank records, generate surrogate keys for dimensions."},
                {"step": 3, "title": "Dimension Loading", "description": "Populate dim_country, dim_time, dim_tourism_type, and dim_worldbank with unique keys and attributes."},
                {"step": 4, "title": "Fact Assembly", "description": "Map natural keys to dimension foreign keys and compile unified fact_tourism table with 321 records."},
                {"step": 5, "title": "OLAP & Mining", "description": "Execute Roll-Up, Drill-Down, Slice, Dice, and Pivot queries and train Decision Tree, K-Means, and Apriori models."}
            ]
        }
