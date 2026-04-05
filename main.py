import pandas as pd
import numpy as np

df = pd.read_csv("bank_transactions.csv")

print("Shape:", df.shape)
print(df.dtypes)
print(df.head())
print(df.describe())

# 2 EXPLORATION

# Missing values %
missing = df.isnull().mean() * 100
print("\nMissing values (%):\n", missing.sort_values(ascending=False))

# Duplicates analysis BEFORE removing
duplicates = df[df.duplicated(subset="transaction_id", keep=False)]
print("\nNumber of duplicate transactions:", duplicates.shape[0])

# 3. CLEANING

# Remove duplicates
df = df.drop_duplicates(subset="transaction_id", keep="first")

# Fix date
df["date_transaction"] = pd.to_datetime(df["date_transaction"], errors="coerce")

# Fix montant
df["montant"] = df["montant"].astype(str).str.replace(",", ".")
df["montant"] = pd.to_numeric(df["montant"], errors="coerce")

# Fix solde_avant
df["solde_avant"] = df["solde_avant"].astype(str).str.replace(" EUR", "")
df["solde_avant"] = pd.to_numeric(df["solde_avant"], errors="coerce")

# Clean text columns
text_cols = ["devise", "agence", "segment_client", "categorie",
             "produit", "type_operation", "statut"]

for col in text_cols:
    df[col] = df[col].astype(str).str.strip()

df["devise"] = df["devise"].str.upper()
df["segment_client"] = df["segment_client"].str.capitalize()

# 4. MISSING VALUES

df["score_credit_client"] = df["score_credit_client"].fillna(df["score_credit_client"].median())
df["solde_avant"] = df["solde_avant"].fillna(df["solde_avant"].median())

df["segment_client"] = df["segment_client"].fillna(df["segment_client"].mode()[0])
df["agence"] = df["agence"].fillna(df["agence"].mode()[0])


# 5. ANOMALY DETECTION
# IQR on montant
Q1 = df["montant"].quantile(0.25)
Q3 = df["montant"].quantile(0.75)
IQR = Q3 - Q1

lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR

df["is_anomaly_montant"] = (df["montant"] < lower) | (df["montant"] > upper)

# Credit score anomalies
df["is_anomaly_score"] = (df["score_credit_client"] < 0) | (df["score_credit_client"] > 850)

# Global anomaly flag
df["is_anomaly"] = df["is_anomaly_montant"] | df["is_anomaly_score"]

# 6.FEATURE ENGINEERING

# Date features
df["year"] = df["date_transaction"].dt.year
df["month"] = df["date_transaction"].dt.month
df["quarter"] = df["date_transaction"].dt.to_period("Q").astype(str)
df["weekday"] = df["date_transaction"].dt.day_name()

# Verify montant EUR
df["montant_eur_verifie"] = df["montant"] / df["taux_change_eur"]
df["ecart_montant_eur"] = df["montant_eur"] - df["montant_eur_verifie"]

# Risk category
def risk(score):
    if score >= 700:
        return "Low"
    elif score >= 580:
        return "Medium"
    else:
        return "High"

df["categorie_risque"] = df["score_credit_client"].apply(risk)

# Credit / Debit
df["credit"] = df["montant"].apply(lambda x: x if x > 0 else 0)
df["debit"] = df["montant"].apply(lambda x: x if x < 0 else 0)

# Aggregations per client
client_stats = df.groupby("client_id").agg({
    "transaction_id": "count",
    "montant": "mean",
    "produit": "nunique",
    "credit": "sum",
    "debit": "sum"
}).reset_index()

client_stats.columns = [
    "client_id",
    "nb_transactions",
    "montant_moyen",
    "nb_produits_distincts",
    "total_credit",
    "total_debit"
]

client_stats["solde_net"] = client_stats["total_credit"] + client_stats["total_debit"]

df = df.merge(client_stats, on="client_id", how="left")

# Rejection rate per agence
rejet = df[df["statut"] == "Rejected"].groupby("agence").size()
total = df.groupby("agence").size()

taux_rejet = (rejet / total).fillna(0).reset_index()
taux_rejet.columns = ["agence", "taux_rejet"]

df = df.merge(taux_rejet, on="agence", how="left")

# 7. FINAL CHECK

print("\nFinal shape:", df.shape)

# 8. EXPORT

df.to_csv("financecore_clean.csv", index=False)

print("DONE - Dataset cleaned & enriched")
