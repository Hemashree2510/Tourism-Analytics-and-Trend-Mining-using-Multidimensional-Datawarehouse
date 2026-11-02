import os
from flask import Flask, render_template, jsonify, request
from config import Config
from services.data_service import DataService
from services.warehouse_service import WarehouseService
from services.classification_service import ClassificationService
from services.clustering_service import ClusteringService
from services.association_service import AssociationService
from services.olap_service import OlapService

app = Flask(__name__)
app.config.from_object(Config)

# Ensure warehouse is initialized on start
with app.app_context():
    try:
        WarehouseService.ensure_warehouse_initialized()
    except Exception as e:
        print(f"Warning: Warehouse auto-init message: {e}")

# ============================================================
# TEMPLATE PAGE ROUTES
# ============================================================

@app.route('/')
@app.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html', active_page='dashboard')

@app.route('/country-analysis')
def country_analysis_page():
    country = request.args.get('country', 'France')
    return render_template('country_analysis.html', active_page='country_analysis', selected_country=country)

@app.route('/trends')
def trends_page():
    return render_template('trends.html', active_page='trends')

@app.route('/classification')
def classification_page():
    return render_template('classification.html', active_page='classification')

@app.route('/clustering')
def clustering_page():
    return render_template('clustering.html', active_page='clustering')

@app.route('/association-rules')
def association_rules_page():
    return render_template('association_rules.html', active_page='association_rules')

@app.route('/olap')
def olap_page():
    return render_template('olap.html', active_page='olap')

@app.route('/warehouse')
def warehouse_page():
    return render_template('warehouse.html', active_page='warehouse')

@app.route('/data-dictionary')
def data_dictionary_page():
    return render_template('data_dictionary.html', active_page='data_dictionary')

@app.route('/about')
def about_page():
    return render_template('about.html', active_page='about')


# ============================================================
# REST API ENDPOINTS
# ============================================================

@app.route('/api/summary', methods=['GET'])
def api_summary():
    filters = {
        'year': request.args.get('year', 'All'),
        'country': request.args.get('country', 'All'),
        'data_type': request.args.get('data_type', 'All'),
        'category': request.args.get('category', 'All')
    }
    kpis = DataService.get_kpis(filters)
    return jsonify(kpis)

@app.route('/api/countries', methods=['GET'])
def api_countries():
    countries = DataService.get_all_countries()
    return jsonify({"count": len(countries), "countries": countries})

@app.route('/api/years', methods=['GET'])
def api_years():
    years = DataService.get_available_years()
    return jsonify(years)

@app.route('/api/tourism/trends', methods=['GET'])
def api_trends():
    trends = DataService.get_tourism_trends()
    return jsonify(trends)

@app.route('/api/tourism/top-countries', methods=['GET'])
def api_top_countries():
    year = int(request.args.get('year', 2023))
    limit = request.args.get('limit', type=int)
    search = request.args.get('search', '').strip()
    category = request.args.get('category', 'All')
    res = DataService.get_top_countries(year=year, limit=limit, search=search, category=category)
    return jsonify(res)

@app.route('/api/country/<country_name>', methods=['GET'])
def api_country_details(country_name):
    details = DataService.get_country_details(country_name)
    if not details:
        return jsonify({"error": f"Country '{country_name}' not found."}), 404
        
    # Also attach cluster and classification if applicable
    try:
        clf_result = ClassificationService.run_model()
        test_matches = [t for t in clf_result['test_results'] if t['country'].lower() == country_name.lower()]
        if test_matches:
            details['classification_test_record'] = test_matches[0]
            
        cluster_res = ClusteringService.run_clustering()
        c_matches = [c for c in cluster_res['countries'] if c['country'].lower() == country_name.lower()]
        if c_matches:
            details['cluster'] = c_matches[0]['cluster']
            details['cluster_name'] = c_matches[0]['cluster_name']
    except Exception as e:
        print("Note attaching ML details:", e)

    return jsonify(details)

@app.route('/api/classification/results', methods=['GET'])
def api_classification_results():
    try:
        res = ClassificationService.run_model()
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/classification/run', methods=['POST'])
def api_classification_run():
    data = request.get_json() or {}
    max_depth = int(data.get('max_depth', 3))
    test_size = float(data.get('test_size', 0.2))
    random_state = int(data.get('random_state', 42))
    try:
        res = ClassificationService.run_model(max_depth=max_depth, test_size=test_size, random_state=random_state)
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/clustering/results', methods=['GET'])
def api_clustering_results():
    try:
        res = ClusteringService.run_clustering()
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/clustering/run', methods=['POST'])
def api_clustering_run():
    data = request.get_json() or {}
    n_clusters = int(data.get('n_clusters', 3))
    random_state = int(data.get('random_state', 42))
    try:
        res = ClusteringService.run_clustering(n_clusters=n_clusters, random_state=random_state)
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/association-rules', methods=['GET'])
def api_association_rules():
    try:
        res = AssociationService.run_association()
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/association-rules/run', methods=['POST'])
def api_association_rules_run():
    data = request.get_json() or {}
    min_support = float(data.get('min_support', 0.1))
    min_confidence = float(data.get('min_confidence', 0.5))
    try:
        res = AssociationService.run_association(min_support=min_support, min_confidence=min_confidence)
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/olap/rollup', methods=['GET'])
def api_olap_rollup():
    try:
        res = OlapService.execute_rollup()
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/olap/drilldown', methods=['GET'])
def api_olap_drilldown():
    year = int(request.args.get('year', 2023))
    try:
        res = OlapService.execute_drilldown(year=year)
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/olap/slice', methods=['GET'])
def api_olap_slice():
    year = int(request.args.get('year', 2023))
    try:
        res = OlapService.execute_slice(year=year)
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/olap/dice', methods=['GET', 'POST'])
def api_olap_dice():
    if request.method == 'POST':
        data = request.get_json() or {}
        countries = data.get('countries', ['India', 'China', 'United States', 'France', 'Spain'])
        years = data.get('years', [2022, 2023, 2024])
    else:
        c_param = request.args.get('countries')
        y_param = request.args.get('years')
        countries = [c.strip() for c in c_param.split(',')] if c_param else ['India', 'China', 'United States', 'France', 'Spain']
        years = [int(y.strip()) for y in y_param.split(',')] if y_param else [2022, 2023, 2024]

    try:
        res = OlapService.execute_dice(countries=countries, years=years)
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/olap/pivot', methods=['GET'])
def api_olap_pivot():
    try:
        res = OlapService.execute_pivot()
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/data-dictionary', methods=['GET'])
def api_data_dictionary():
    return jsonify(DataService.get_data_dictionary())

@app.route('/api/warehouse/schema', methods=['GET'])
def api_warehouse_schema():
    return jsonify(WarehouseService.get_schema_info())

@app.route('/api/warehouse/etl/run', methods=['POST'])
def api_warehouse_etl_run():
    try:
        WarehouseService.run_etl()
        return jsonify({"status": "success", "message": "ETL completed successfully into multidimensional warehouse."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', port=port, debug=Config.DEBUG)
