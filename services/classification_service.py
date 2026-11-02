import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from services.data_service import DataService

class ClassificationService:
    @staticmethod
    def classify_tourism(arrivals):
        if arrivals < 20:
            return "Low Tourism"
        elif arrivals <= 50:
            return "Medium Tourism"
        else:
            return "High Tourism"

    @classmethod
    def run_model(cls, max_depth=3, test_size=0.2, random_state=42):
        df = DataService.get_df().copy()
        
        # 1. Preprocess: select countries with both 2022 and 2023 arrival figures
        data = df[['country', 'MostVisited_NumOfArrivals_Millions_2022', 'MostVisited_NumOfArrivals_Millions_2023']].copy()
        data['MostVisited_NumOfArrivals_Millions_2022'] = pd.to_numeric(data['MostVisited_NumOfArrivals_Millions_2022'], errors='coerce')
        data['MostVisited_NumOfArrivals_Millions_2023'] = pd.to_numeric(data['MostVisited_NumOfArrivals_Millions_2023'], errors='coerce')
        data = data.dropna().reset_index(drop=True)

        valid_records_count = len(data)
        if valid_records_count < 5:
            raise ValueError(f"Insufficient valid records ({valid_records_count}) for classification.")

        # 2. Derive target category from 2023 arrivals
        data['tourism_category'] = data['MostVisited_NumOfArrivals_Millions_2023'].apply(cls.classify_tourism)
        category_counts = data['tourism_category'].value_counts().to_dict()

        # 3. Features (X: 2022 arrivals) and Target (y: 2023 category)
        X = data[['MostVisited_NumOfArrivals_Millions_2022']]
        y = data['tourism_category']

        # 4. Train-Test Split (preserving stratify if possible)
        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state, stratify=y
            )
        except Exception:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state
            )

        # 5. Train Decision Tree
        model = DecisionTreeClassifier(max_depth=max_depth, random_state=random_state)
        model.fit(X_train, y_train)

        # 6. Predict on Test Set
        y_pred = model.predict(X_test)
        accuracy = float(accuracy_score(y_test, y_pred))

        # 7. Confusion Matrix
        labels = ["Low Tourism", "Medium Tourism", "High Tourism"]
        cm = confusion_matrix(y_test, y_pred, labels=labels).tolist()

        # 8. Classification Report
        report_dict = classification_report(y_test, y_pred, labels=labels, output_dict=True, zero_division=0)
        formatted_report = []
        for label in labels:
            metrics = report_dict.get(label, {})
            formatted_report.append({
                "category": label,
                "precision": round(metrics.get("precision", 0.0), 2),
                "recall": round(metrics.get("recall", 0.0), 2),
                "f1_score": round(metrics.get("f1-score", 0.0), 2),
                "support": int(metrics.get("support", 0))
            })

        # 9. Test records breakdown
        test_results = []
        test_indices = X_test.index
        for idx in test_indices:
            row_data = data.loc[idx]
            actual = str(y_test.loc[idx])
            pred = str(model.predict(pd.DataFrame([[row_data['MostVisited_NumOfArrivals_Millions_2022']]], columns=['MostVisited_NumOfArrivals_Millions_2022']))[0])
            test_results.append({
                "country": str(row_data['country']),
                "arrivals_2022": round(float(row_data['MostVisited_NumOfArrivals_Millions_2022']), 2),
                "arrivals_2023": round(float(row_data['MostVisited_NumOfArrivals_Millions_2023']), 2),
                "actual_category": actual,
                "predicted_category": pred,
                "is_correct": bool(actual == pred)
            })

        correct_count = sum(1 for r in test_results if r['is_correct'])
        total_test = len(test_results)

        # Decision Tree rules text
        tree_rules = export_text(model, feature_names=['2022_Arrivals_Millions'])

        return {
            "model_name": "Decision Tree Classifier (CART)",
            "hyperparameters": {
                "max_depth": max_depth,
                "test_size": test_size,
                "random_state": random_state,
                "criterion": "gini"
            },
            "valid_records_count": valid_records_count,
            "train_count": len(X_train),
            "test_count": len(X_test),
            "accuracy": round(accuracy * 100, 2),
            "accuracy_ratio": f"{correct_count} out of {total_test}",
            "confusion_matrix": {
                "labels": labels,
                "matrix": cm
            },
            "classification_report": formatted_report,
            "category_distribution": category_counts,
            "test_results": test_results,
            "tree_rules": tree_rules,
            "thresholds": {
                "Low Tourism": "< 20 Million",
                "Medium Tourism": "20 to 50 Million",
                "High Tourism": "> 50 Million"
            },
            "limitation_notice": "The evaluation uses only four test records. Results are preliminary and may not generalize to a larger set of countries."
        }
