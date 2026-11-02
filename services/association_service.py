import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules
from services.data_service import DataService

class AssociationService:
    @staticmethod
    def categorize_arrivals(val):
        if val < 20:
            return "Low"
        elif val <= 50:
            return "Medium"
        else:
            return "High"

    @classmethod
    def run_association(cls, min_support=0.1, min_confidence=0.5):
        df = DataService.get_df().copy()
        
        # 1. Select countries with valid 2022 and 2023 arrivals
        assoc_df = df[['country', 'MostVisited_NumOfArrivals_Millions_2022', 'MostVisited_NumOfArrivals_Millions_2023']].copy()
        assoc_df['MostVisited_NumOfArrivals_Millions_2022'] = pd.to_numeric(
            assoc_df['MostVisited_NumOfArrivals_Millions_2022'], errors='coerce'
        )
        assoc_df['MostVisited_NumOfArrivals_Millions_2023'] = pd.to_numeric(
            assoc_df['MostVisited_NumOfArrivals_Millions_2023'], errors='coerce'
        )
        assoc_df = assoc_df.dropna().reset_index(drop=True)

        if len(assoc_df) == 0:
            return {
                "error": "No valid records available for association mining.",
                "rules": [],
                "transactions_count": 0
            }

        # 2. Categorize arrivals
        assoc_df['2022_Category'] = assoc_df['MostVisited_NumOfArrivals_Millions_2022'].apply(cls.categorize_arrivals)
        assoc_df['2023_Category'] = assoc_df['MostVisited_NumOfArrivals_Millions_2023'].apply(cls.categorize_arrivals)

        # 3. Create transactions
        transactions = []
        country_transactions = []
        for _, row in assoc_df.iterrows():
            item_2022 = f"2022_{row['2022_Category']}"
            item_2023 = f"2023_{row['2023_Category']}"
            transactions.append([item_2022, item_2023])
            country_transactions.append({
                "country": str(row['country']),
                "arrivals_2022": round(float(row['MostVisited_NumOfArrivals_Millions_2022']), 2),
                "category_2022": row['2022_Category'],
                "arrivals_2023": round(float(row['MostVisited_NumOfArrivals_Millions_2023']), 2),
                "category_2023": row['2023_Category'],
                "items": [item_2022, item_2023]
            })

        # 4. Encode transactions using TransactionEncoder
        te = TransactionEncoder()
        te_ary = te.fit(transactions).transform(transactions)
        df_te = pd.DataFrame(te_ary, columns=te.columns_)

        # 5. Generate frequent itemsets using Apriori
        frequent_itemsets = apriori(df_te, min_support=min_support, use_colnames=True)
        
        rules_list = []
        if not frequent_itemsets.empty:
            # 6. Generate association rules
            rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)
            
            for _, r in rules.sort_values(by='confidence', ascending=False).iterrows():
                ant = list(r['antecedents'])
                con = list(r['consequents'])
                ant_str = ", ".join(ant)
                con_str = ", ".join(con)
                rules_list.append({
                    "antecedent": ant_str,
                    "consequent": con_str,
                    "rule_text": f"{ant_str} -> {con_str}",
                    "support": round(float(r['support']), 4),
                    "support_pct": round(float(r['support']) * 100, 1),
                    "confidence": round(float(r['confidence']), 4),
                    "confidence_pct": round(float(r['confidence']) * 100, 1),
                    "lift": round(float(r['lift']), 4)
                })

        return {
            "algorithm": "Apriori Association Rule Mining",
            "parameters": {
                "min_support": min_support,
                "min_confidence": min_confidence
            },
            "transactions_count": len(transactions),
            "transactions": country_transactions,
            "rules": rules_list,
            "frequent_itemsets_count": len(frequent_itemsets),
            "note": "Derived from 17 country transitions between 2022 and 2023 arrival categories."
        }
