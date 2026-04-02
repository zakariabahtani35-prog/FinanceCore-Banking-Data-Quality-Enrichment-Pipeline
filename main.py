import pandas as pd
import numpy as np

# 1. LOAD
df = pd.read_csv("bank_transactions.csv")

print("Shape:", df.shape)
print(df.dtypes)

# 2. CLEANING

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
df["devise"] = df["devise"].str.upper().str.strip()
df["agence"] = df["agence"].str.strip()
df["segment_client"] = df["segment_client"].str.capitalize().str.strip()
df["categorie"] = df["categorie"].str.capitalize().str.strip()
df["produit"] = df["produit"].str.strip()
df["type_operation"] = df["type_operation"].str.strip()
df["statut"] = df["statut"].str.strip()

# 3. MISSING VALUES

df["score_credit_client"] = df["score_credit_client"].fillna(df["score_credit_client"].median())
df["segment_client"] = df["segment_client"].fillna(df["segment_client"].mode()[0])
df["agence"] = df["agence"].fillna(df["agence"].mode()[0])
df["solde_avant"] = df["solde_avant"].fillna(df["solde_avant"].median())

# 4. ANOMALY DETECTION (IQR)


Q1 = df["montant"].quantile(0.25)
Q3 = df["montant"].quantile(0.75)
IQR = Q3 - Q1

lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR

df["is_anomaly"] = (df["montant"] < lower) | (df["montant"] > upper)

# 5. FEATURE ENGINEERING

# Date features
df["year"] = df["date_transaction"].dt.year
df["month"] = df["date_transaction"].dt.month
df["weekday"] = df["date_transaction"].dt.day_name()

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

# Net balance per client
net = df.groupby("client_id").agg({
    "credit": "sum",
    "debit": "sum"
}).reset_index()

net["solde_net"] = net["credit"] + net["debit"]

df = df.merge(net[["client_id", "solde_net"]], on="client_id", how="left")

# 6. SIMPLE KPI

rejet = df[df["statut"] == "Rejected"].groupby("agence").size()
total = df.groupby("agence").size()

taux_rejet = (rejet / total).fillna(0).reset_index()
taux_rejet.columns = ["agence", "taux_rejet"]

df = df.merge(taux_rejet, on="agence", how="left")

# 7. EXPORT

df.to_csv("financecore_clean.csv", index=False)

print("DONE")