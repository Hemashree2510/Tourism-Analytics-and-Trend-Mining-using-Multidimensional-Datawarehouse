# TourismVista — Tourism Analytics and Trend Mining Using a Multidimensional Data Warehouse

An academic web application developed for the **Data Warehousing and Data Mining (CSI3010)** course.

- **Student Researcher:** HEMASHREE G (Register No: 23MID0092)
- **Faculty Mentor:** Prof. Devipriya
- **Lab Slot:** L19 + L20
- **Technology Stack:** Python Flask, Pandas, Scikit-learn, mlxtend, SQLAlchemy, Chart.js, Leaflet, HTML5/CSS3/JavaScript

---

## 🌟 Key Features

1. **Multidimensional Data Warehouse:**
   - Academic **Star Schema** with a central fact table (`fact_tourism`) referencing four dimensions: `dim_country`, `dim_time`, `dim_tourism_type`, and `dim_worldbank`.
   - Automatic ETL pipeline that extracts raw data from Kaggle, cleans missing values without fabricating zeroes, synthesizes surrogate keys, and populates the warehouse tables.
   - Dual-mode database connectivity: connects to MySQL via environment variables with a transparent, zero-configuration SQLite fallback.

2. **OLAP Cube Operations:**
   - **Roll-Up:** Aggregate international tourist arrivals to higher-level yearly summaries.
   - **Drill-Down:** Navigate from global totals down to individual country-level arrivals for a chosen year.
   - **Slice:** Extract single-dimension slices (e.g., year = 2023 for actual arrivals).
   - **Dice:** Query sub-cubes across multiple dimensions (e.g., specific subsets of countries and years).
   - **Pivot:** Transpose dimensional axes to cross-tabulate country arrival trends across 2022, 2023, and 2024.

3. **Data Mining & Analytics:**
   - **Decision Tree Classification (CART):** Classifies destinations into Low (<20M), Medium (20–50M), and High (>50M) arrival tiers. Achieves 75% test accuracy on unseen data with full confusion matrix and classification reports.
   - **K-Means Clustering:** Standardizes arrival figures using `StandardScaler` and partitions destinations into 3 empirical tiers (Mega-Hubs, Major Destinations, Emerging Hubs).
   - **Apriori Association Rule Mining:** Generates directional transition rules between consecutive arrival tiers evaluated using Support, Confidence, and Lift metrics.

4. **Academic Dashboard UI:**
   - Polished white aesthetic with navy headings, soft card shadows, and subtle accents.
   - Responsive layout with interactive Chart.js charts and Leaflet world map.
   - Real-time global filter controls (Year, Country, Data Type, Arrival Category).
   - Strict data validation rules: no fabricated monthly time series or extrapolated statistics.

---

## 🚀 Quick Start & Execution

### 1. Prerequisites
Ensure Python 3.10+ is installed on your system.

### 2. Installation
Navigate to the `tourismvista` directory and install the required dependencies:

```bash
cd tourismvista
python -m pip install -r requirements.txt
```

### 3. Environment Configuration (Optional)
The application works immediately out-of-the-box using the local SQLite warehouse. If you wish to connect to a MySQL instance:

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Set your MySQL credentials:
   ```env
   DB_TYPE=mysql
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=your_password
   DB_NAME=tourism_warehouse
   ```

### 4. Run the Web Application
Launch the Flask development server:

```bash
python app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 📁 Project Directory Structure

```
tourismvista/
├── app.py                      # Main Flask application and REST API endpoints
├── config.py                   # Configuration and database URI resolver
├── requirements.txt            # Python dependencies
├── .env.example                # Template for environment variables
├── README.md                   # Project documentation
│
├── data/
│   ├── tourism_dataset.csv     # Original Kaggle dataset (203 rows x 6 cols)
│   └── tourism_warehouse.db    # Relational Star Schema warehouse (SQLite fallback)
│
├── services/
|   |__ __init__.py             # Python package initializer
│   ├── data_service.py         # CSV loading, KPIs, data dictionary, and trends
│   ├── warehouse_service.py    # Star Schema DDL, ETL loader, and SQL executor
│   ├── classification_service.py# Decision Tree model training & evaluation
│   ├── clustering_service.py   # K-Means clustering with StandardScaler
│   ├── association_service.py  # Apriori frequent itemsets & rule mining
│   └── olap_service.py         # Roll-up, Drill-Down, Slice, Dice, Pivot queries
│
├── templates/
│   ├── base.html               # Master layout with sidebar and header
│   ├── dashboard.html          # Main analytics dashboard & Leaflet map
│   ├── country_analysis.html   # Country-level deep-dive scorecard
│   ├── trends.html             # Longitudinal trend and growth analysis
│   ├── classification.html     # Decision Tree methodology & live evaluation
│   ├── clustering.html         # K-Means scatter plot & cluster summaries
│   ├── association_rules.html  # Apriori rules table & confidence charts
│   ├── olap.html               # Live OLAP operations with formatted SQL
│   ├── warehouse.html          # Star Schema ER diagram and DDL scripts
│   ├── data_dictionary.html    # Searchable dataset metadata & missing counts
│   └── about.html              # Academic research background and team info
│
└── static/
    ├── css/
    │   └── style.css           # Premium academic stylesheet
    └── js/
        ├── dashboard.js        # Dashboard chart bindings and Leaflet map
        ├── country_analysis.js # Country scorecard interaction
        ├── trends.js           # Trends visualizer
        ├── classification.js   # Dynamic classification runner
        ├── clustering.js       # Dynamic clustering runner
        ├── association_rules.js# Dynamic association runner
        └── olap.js             # Interactive OLAP query execution
```

---

## 📊 Analytical Methodology Summary

| Component | Technical Implementation | Academic Result |
| :--- | :--- | :--- |
| **Warehouse Grain** | One row per country, observation year, and data type | 321 fact records |
| **Decision Tree** | Max depth = 3, random_state = 42, 80/20 train-test | 75% accuracy (3 of 4 correct) |
| **K-Means** | StandardScaler, k = 3, random_state = 42, n_init = 10 | 3 volume tiers (Mega, Major, Emerging) |
| **Apriori** | Min Support = 0.10, Min Confidence = 0.50 | 6 high-confidence transition rules |
| **OLAP Operations** | Roll-Up, Drill-Down, Slice, Dice, Pivot | Real-time parameterized SQL |
