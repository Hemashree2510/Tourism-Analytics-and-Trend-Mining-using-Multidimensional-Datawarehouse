import time
from services.warehouse_service import WarehouseService

class OlapService:
    @classmethod
    def execute_rollup(cls):
        sql = """SELECT
    t.year_num AS YEAR_NUM,
    SUM(f.tourist_arrivals_millions) AS TOTAL_ARRIVALS
FROM fact_tourism f
JOIN dim_time t ON f.time_key = t.time_key
GROUP BY t.year_num
ORDER BY t.year_num;"""
        
        t0 = time.time()
        res = WarehouseService.execute_query(sql)
        duration_ms = round((time.time() - t0) * 1000, 2)

        # Separate annual kaggle data from world bank historical data for clear display
        formatted_rows = []
        for r in res['rows']:
            yr = int(r['YEAR_NUM'])
            tot = float(r['TOTAL_ARRIVALS'])
            if yr in [2022, 2023, 2024]:
                note = "Annual Report (Millions)"
                tot_display = f"{tot:,.2f} M"
            else:
                note = "World Bank Historical (Raw count)"
                tot_display = f"{int(tot):,}"
            formatted_rows.append({
                "YEAR_NUM": yr,
                "TOTAL_ARRIVALS_DISPLAY": tot_display,
                "TOTAL_ARRIVALS": tot,
                "DATA_SCOPE": note
            })

        return {
            "operation": "ROLL-UP",
            "title": "Year-Wise Tourism Totals Roll-Up",
            "description": "Aggregates tourist arrivals from fine-grained country observations to higher-level yearly summaries.",
            "sql_query": sql,
            "duration_ms": duration_ms,
            "columns": ["YEAR_NUM", "TOTAL_ARRIVALS_DISPLAY", "DATA_SCOPE"],
            "rows": formatted_rows
        }

    @classmethod
    def execute_drilldown(cls, year=2023):
        year = int(year)
        sql = f"""SELECT
    t.year_num AS YEAR_NUM,
    c.country_name AS COUNTRY_NAME,
    SUM(f.tourist_arrivals_millions) AS TOURIST_ARRIVALS
FROM fact_tourism f
JOIN dim_time t ON f.time_key = t.time_key
JOIN dim_country c ON f.country_key = c.country_key
WHERE t.year_num = {year}
GROUP BY t.year_num, c.country_name
ORDER BY TOURIST_ARRIVALS DESC;"""

        t0 = time.time()
        res = WarehouseService.execute_query(sql)
        duration_ms = round((time.time() - t0) * 1000, 2)

        formatted_rows = []
        for r in res['rows']:
            val = float(r['TOURIST_ARRIVALS'])
            disp = f"{val:.2f} M" if year in [2022, 2023, 2024] else f"{int(val):,}"
            formatted_rows.append({
                "YEAR_NUM": r['YEAR_NUM'],
                "COUNTRY_NAME": r['COUNTRY_NAME'],
                "TOURIST_ARRIVALS": val,
                "TOURIST_ARRIVALS_DISPLAY": disp
            })

        return {
            "operation": "DRILL-DOWN",
            "title": f"Country-Level Drill-Down for Year {year}",
            "description": "Navigates down from yearly aggregate totals to country-level arrivals.",
            "selected_year": year,
            "sql_query": sql,
            "duration_ms": duration_ms,
            "columns": ["YEAR_NUM", "COUNTRY_NAME", "TOURIST_ARRIVALS_DISPLAY"],
            "rows": formatted_rows
        }

    @classmethod
    def execute_slice(cls, year=2023):
        year = int(year)
        sql = f"""SELECT
    c.country_name AS COUNTRY_NAME,
    f.tourist_arrivals_millions AS TOURIST_ARRIVALS_MILLIONS
FROM fact_tourism f
JOIN dim_country c ON f.country_key = c.country_key
JOIN dim_time t ON f.time_key = t.time_key
WHERE t.year_num = {year}
  AND f.tourism_type_key = 1
ORDER BY f.tourist_arrivals_millions DESC;"""

        t0 = time.time()
        res = WarehouseService.execute_query(sql)
        duration_ms = round((time.time() - t0) * 1000, 2)

        formatted_rows = []
        for r in res['rows']:
            val = float(r['TOURIST_ARRIVALS_MILLIONS'])
            formatted_rows.append({
                "COUNTRY_NAME": r['COUNTRY_NAME'],
                "TOURIST_ARRIVALS_MILLIONS": val,
                "TOURIST_ARRIVALS_DISPLAY": f"{val:.2f} M"
            })

        return {
            "operation": "SLICE",
            "title": f"Single-Dimension Slice: Year {year} (Actual Arrivals)",
            "description": "Extracts a 2D slice from the cube by fixing the Time dimension (year = " + str(year) + ") and Tourism Type (Actual = 1).",
            "selected_year": year,
            "sql_query": sql,
            "duration_ms": duration_ms,
            "columns": ["COUNTRY_NAME", "TOURIST_ARRIVALS_DISPLAY"],
            "rows": formatted_rows
        }

    @classmethod
    def execute_dice(cls, countries=None, years=None):
        if not countries:
            countries = ['India', 'China', 'United States', 'France', 'Spain']
        if not years:
            years = [2022, 2023, 2024]

        clean_countries = [c.replace("'", "''") for c in countries]
        c_str = ", ".join(f"'{c}'" for c in clean_countries)
        y_str = ", ".join(str(int(y)) for y in years)

        sql = f"""SELECT
    c.country_name AS COUNTRY_NAME,
    t.year_num AS YEAR_NUM,
    f.tourist_arrivals_millions AS TOURIST_ARRIVALS_MILLIONS
FROM fact_tourism f
JOIN dim_country c ON f.country_key = c.country_key
JOIN dim_time t ON f.time_key = t.time_key
WHERE c.country_name IN ({c_str})
  AND t.year_num IN ({y_str})
  AND f.tourism_type_key IN (1, 2)
ORDER BY c.country_name, t.year_num;"""

        t0 = time.time()
        res = WarehouseService.execute_query(sql)
        duration_ms = round((time.time() - t0) * 1000, 2)

        formatted_rows = []
        for r in res['rows']:
            val = float(r['TOURIST_ARRIVALS_MILLIONS'])
            formatted_rows.append({
                "COUNTRY_NAME": r['COUNTRY_NAME'],
                "YEAR_NUM": r['YEAR_NUM'],
                "TOURIST_ARRIVALS_MILLIONS": val,
                "TOURIST_ARRIVALS_DISPLAY": f"{val:.2f} M"
            })

        return {
            "operation": "DICE",
            "title": "Multi-Dimensional Dice Sub-Cube",
            "description": "Defines a sub-cube by applying multiple range/membership criteria across Country, Time, and Tourism Type dimensions.",
            "selected_countries": countries,
            "selected_years": years,
            "sql_query": sql,
            "duration_ms": duration_ms,
            "columns": ["COUNTRY_NAME", "YEAR_NUM", "TOURIST_ARRIVALS_DISPLAY"],
            "rows": formatted_rows
        }

    @classmethod
    def execute_pivot(cls):
        sql = """SELECT
    c.country_name AS COUNTRY_NAME,
    SUM(CASE WHEN t.year_num = 2022 THEN f.tourist_arrivals_millions END) AS ARRIVALS_2022,
    SUM(CASE WHEN t.year_num = 2023 THEN f.tourist_arrivals_millions END) AS ARRIVALS_2023,
    SUM(CASE WHEN t.year_num = 2024 THEN f.tourist_arrivals_millions END) AS ARRIVALS_2024
FROM fact_tourism f
JOIN dim_country c ON f.country_key = c.country_key
JOIN dim_time t ON f.time_key = t.time_key
WHERE f.tourism_type_key IN (1, 2)
GROUP BY c.country_name
ORDER BY c.country_name;"""

        t0 = time.time()
        res = WarehouseService.execute_query(sql)
        duration_ms = round((time.time() - t0) * 1000, 2)

        formatted_rows = []
        for r in res['rows']:
            v22 = r['ARRIVALS_2022']
            v23 = r['ARRIVALS_2023']
            v24 = r['ARRIVALS_2024']
            formatted_rows.append({
                "COUNTRY_NAME": r['COUNTRY_NAME'],
                "ARRIVALS_2022": f"{float(v22):.2f} M" if v22 is not None else "N/A",
                "ARRIVALS_2023": f"{float(v23):.2f} M" if v23 is not None else "N/A",
                "ARRIVALS_2024": f"{float(v24):.2f} M" if v24 is not None else "N/A",
            })

        return {
            "operation": "PIVOT",
            "title": "Cross-Tabular Pivot Grid",
            "description": "Rotates data axes to display countries on the rows and arrival years (2022, 2023, 2024 predicted) along the columns.",
            "sql_query": sql,
            "duration_ms": duration_ms,
            "columns": ["COUNTRY_NAME", "ARRIVALS_2022", "ARRIVALS_2023", "ARRIVALS_2024"],
            "rows": formatted_rows
        }
