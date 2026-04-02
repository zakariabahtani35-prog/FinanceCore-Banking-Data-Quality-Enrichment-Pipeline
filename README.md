# 🏦 FinanceCore SA — Banking Transaction Data Pipeline

> **End-to-end data cleaning, validation, anomaly detection, and feature engineering pipeline for raw banking transaction data.**

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![Pandas](https://img.shields.io/badge/Pandas-2.x-150458?style=flat-square&logo=pandas)
![NumPy](https://img.shields.io/badge/NumPy-1.26-013243?style=flat-square&logo=numpy)
![Status](https://img.shields.io/badge/Status-Production--Ready-brightgreen?style=flat-square)
![Domain](https://img.shields.io/badge/Domain-Financial%20Analytics-navy?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square)

---

## 📌 Project Overview

This project delivers a **production-grade data pipeline** that transforms a raw, uncleaned banking transactions dataset into a structured, validated, and analytically enriched dataset — ready for downstream business intelligence, credit risk modeling, or data warehousing workflows.

Developed in the context of **FinanceCore SA**, a fictional mid-sized financial institution, this pipeline addresses the full spectrum of data quality challenges encountered in real financial data environments: structural inconsistencies, missing values, type coercion errors, normalization gaps, outlier detection, and KPI construction.

The result — `financecore_clean.csv` — is a clean, enriched, audit-ready analytical asset.

---

## 🧭 Business Problem

Raw banking transaction data arrives in inconsistent, fragmented formats. Analysts and data engineers in financial institutions regularly face:

- **Duplicate transaction records** that distort reporting and inflate volumes
- **Malformed numeric fields** (comma-decimal separators, trailing currency strings) that break aggregations
- **Inconsistent categorical labels** that prevent segmentation and group-by analytics
- **Missing critical dimensions** (credit score, balance, segment) that undermine risk assessment
- **Undetected outliers** in transaction amounts that may indicate fraud, errors, or edge cases
- **Absent business KPIs** such as rejection rates, net balance, and risk tiers

Without a rigorous cleaning and enrichment pipeline, downstream analytics produce misleading results. This project solves that problem systematically.

---

## 🎯 Objectives

### Technical Objectives
- Detect and resolve all structural and quality issues in the raw dataset
- Implement a reproducible, step-by-step cleaning pipeline in Python
- Apply statistical anomaly detection using the IQR method
- Engineer business-relevant features from transaction timestamps and financial fields
- Compute client-level and agency-level KPIs
- Export a final clean dataset ready for BI, ML, or database ingestion

### Business Objectives
- Provide FinanceCore SA's analytics team with a reliable, analysis-ready dataset
- Enable downstream credit risk scoring, client segmentation, and performance reporting
- Establish a foundation for an automated, repeatable data quality workflow

---

## 📂 Dataset Overview

**Input file:** `bank_transactions.csv`  
**Output file:** `financecore_clean.csv`

The raw dataset contains individual banking transaction records with the following fields:

| Column | Type | Description |
|---|---|---|
| `transaction_id` | String | Unique transaction identifier |
| `client_id` | String | Client identifier |
| `date_transaction` | String → DateTime | Transaction date (requires parsing) |
| `montant` | Float | Transaction amount (mixed formats) |
| `devise` | String | Currency code (requires normalization) |
| `taux_change_eur` | Float | Exchange rate to EUR |
| `montant_eur` | Float | Amount converted to EUR |
| `categorie` | String | Transaction category |
| `produit` | String | Financial product |
| `agence` | String | Branch/agency |
| `type_operation` | String | Operation type (debit/credit) |
| `statut` | String | Transaction status |
| `score_credit_client` | Float | Client credit score |
| `segment_client` | String | Client segment (requires harmonization) |
| `solde_avant` | Float | Balance before transaction (dirty format) |
| `taux_interet` | Float | Interest rate |

---

## 🔭 Project Scope

### In Scope
- Full data quality audit of the raw CSV
- Python-based cleaning and transformation pipeline
- Anomaly detection via IQR on transaction amounts
- Feature engineering from date and financial fields
- Client-level aggregated KPIs
- Agency-level rejection rate computation
- Export of a clean, enriched output dataset
- Documentation of all cleaning decisions in `DECISIONS.md`

### Out of Scope
- Database loading or ETL orchestration (planned as future improvement)
- Real-time streaming or incremental loading
- Machine learning model training
- Dashboard or visualization layer

---

## 🔍 Data Quality Issues Identified

The following issues were detected in the raw dataset during the initial inspection phase:

| Issue Type | Affected Column(s) | Resolution |
|---|---|---|
| **Duplicate rows** | `transaction_id` | Removed on primary key |
| **Incorrect date format** | `date_transaction` | Parsed with `pd.to_datetime` |
| **Comma as decimal separator** | `montant` | String replacement + numeric cast |
| **Trailing currency strings** | `solde_avant` | Stripped `" EUR"` suffix + cast |
| **Mixed case / extra whitespace** | `devise`, `agence`, `segment_client`, `categorie` | `.str.upper()`, `.str.capitalize()`, `.str.strip()` |
| **Missing credit scores** | `score_credit_client` | Imputed with column median |
| **Missing client segments** | `segment_client` | Imputed with column mode |
| **Missing agency values** | `agence` | Imputed with column mode |
| **Missing balances** | `solde_avant` | Imputed with column median |
| **Statistical outliers** | `montant` | Flagged via IQR method |

---

## 🔧 Data Cleaning Pipeline

The pipeline is implemented sequentially in `main.py` and follows this logic:

### Step 1 — Load & Inspect
```python
df = pd.read_csv("bank_transactions.csv")
print("Shape:", df.shape)
print(df.dtypes)
```
Initial structure inspection: dimensions, column types, null distribution.

### Step 2 — Remove Duplicates
```python
df = df.drop_duplicates(subset="transaction_id", keep="first")
```
Deduplicate on the primary business key, retaining the first occurrence.

### Step 3 — Parse Dates
```python
df["date_transaction"] = pd.to_datetime(df["date_transaction"], errors="coerce")
```
Coerce invalid dates to `NaT` rather than raising exceptions.

### Step 4 — Clean Numeric Fields
```python
df["montant"] = df["montant"].astype(str).str.replace(",", ".").pipe(pd.to_numeric, errors="coerce")
df["solde_avant"] = df["solde_avant"].astype(str).str.replace(" EUR", "").pipe(pd.to_numeric, errors="coerce")
```
Handles European decimal formatting and removes embedded currency labels.

### Step 5 — Normalize Text Columns
```python
df["devise"] = df["devise"].str.upper().str.strip()
df["segment_client"] = df["segment_client"].str.capitalize().str.strip()
df["agence"] = df["agence"].str.strip()
```
Standardizes categorical values for consistent grouping and joins.

### Step 6 — Impute Missing Values
```python
df["score_credit_client"] = df["score_credit_client"].fillna(df["score_credit_client"].median())
df["segment_client"] = df["segment_client"].fillna(df["segment_client"].mode()[0])
df["agence"] = df["agence"].fillna(df["agence"].mode()[0])
df["solde_avant"] = df["solde_avant"].fillna(df["solde_avant"].median())
```
Strategy: median for continuous fields (robust to outliers), mode for categorical fields.

---

## 🚨 Anomaly Detection

Statistical outlier detection is performed on `montant` using the **Interquartile Range (IQR)** method:

```python
Q1 = df["montant"].quantile(0.25)
Q3 = df["montant"].quantile(0.75)
IQR = Q3 - Q1

lower = Q1 - 1.5 * IQR
upper = Q3 + 1.5 * IQR

df["is_anomaly"] = (df["montant"] < lower) | (df["montant"] > upper)
```

**Design decision:** Anomalous records are **flagged, not deleted**. This preserves data integrity and gives downstream consumers full control over how to treat edge cases — whether for fraud investigation, manual review, or model exclusion. Removing outliers without business validation is considered bad practice in financial data pipelines.

Additionally, `score_credit_client` values outside the valid range `[300, 850]` can be identified as logically inconsistent and escalated for source-system investigation.

---

## ⚙️ Feature Engineering

### Date-Derived Features

| Feature | Source | Logic |
|---|---|---|
| `year` | `date_transaction` | `.dt.year` |
| `month` | `date_transaction` | `.dt.month` |
| `weekday` | `date_transaction` | `.dt.day_name()` |

These enable time-series segmentation, seasonality analysis, and weekday-level behavioral patterns.

### Risk Categorization

```python
def risk(score):
    if score >= 700:
        return "Low"
    elif score >= 580:
        return "Medium"
    else:
        return "High"

df["categorie_risque"] = df["score_credit_client"].apply(risk)
```

Translates the numeric credit score into a business-intelligible risk tier aligned with standard credit risk frameworks.

### Net Balance per Client

```python
df["credit"] = df["montant"].apply(lambda x: x if x > 0 else 0)
df["debit"] = df["montant"].apply(lambda x: x if x < 0 else 0)

net = df.groupby("client_id").agg({"credit": "sum", "debit": "sum"}).reset_index()
net["solde_net"] = net["credit"] + net["debit"]

df = df.merge(net[["client_id", "solde_net"]], on="client_id", how="left")
```

Provides the net financial position per client across all transactions in the dataset.

### Agency Rejection Rate (KPI)

```python
rejet = df[df["statut"] == "Rejected"].groupby("agence").size()
total = df.groupby("agence").size()
taux_rejet = (rejet / total).fillna(0).reset_index()
```

A key operational metric for branch performance monitoring and compliance reporting.

---

## 🔄 Project Workflow

```
bank_transactions.csv (raw)
         │
         ▼
   [1] Load & Inspect
         │
         ▼
   [2] Remove Duplicates (transaction_id)
         │
         ▼
   [3] Parse & Fix Data Types
     - date_transaction → datetime
     - montant → float (comma fix)
     - solde_avant → float (strip EUR)
         │
         ▼
   [4] Normalize Text Columns
     - devise, agence, segment_client, categorie
         │
         ▼
   [5] Impute Missing Values
     - median for numeric
     - mode for categorical
         │
         ▼
   [6] Anomaly Detection (IQR on montant)
     → is_anomaly flag
         │
         ▼
   [7] Feature Engineering
     - Date features (year, month, weekday)
     - categorie_risque
     - credit / debit split
     - solde_net per client
     - taux_rejet per agency
         │
         ▼
financecore_clean.csv (enriched, validated)
```

---

## 🛠️ Technologies Used

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Core language |
| pandas | 2.x | Data manipulation & transformation |
| NumPy | 1.26+ | Numerical operations, quantile computation |
| CSV (stdlib) | — | Input/output format |

---

## 🗂️ Repository Structure

```
financecore-transaction-pipeline/
│
├── bank_transactions.csv          # Raw input dataset
├── financecore_clean.csv          # Final clean, enriched output
├── main.py                        # Full cleaning & feature engineering pipeline
├── DECISIONS.md                   # Documented data cleaning decisions & rationale
└── README.md                      # This file
```

---

## 📤 Key Outputs

| Output | Description |
|---|---|
| `financecore_clean.csv` | Cleaned, validated, enriched transaction dataset |
| `is_anomaly` column | Boolean flag for statistical outliers in `montant` |
| `categorie_risque` column | Categorical credit risk tier per transaction |
| `solde_net` column | Net balance per client across all transactions |
| `taux_rejet` column | Agency-level transaction rejection rate |
| `year`, `month`, `weekday` | Time dimension features for analytics |
| `DECISIONS.md` | Audit trail of all transformation choices |

---

## 💡 Why This Project Matters

In financial services, data quality is not optional — it is a **regulatory and operational imperative**. Inaccurate or uncleaned transaction data leads to:

- Incorrect risk assessments and miscalibrated credit models
- Flawed regulatory reporting (e.g., AML/KYC compliance)
- Distorted business KPIs that mislead decision-makers
- Pipeline failures in downstream ETL or ML workflows

This project demonstrates the ability to **systematically diagnose and resolve data quality issues** at a professional level, applying industry-standard patterns (IQR for outliers, median/mode imputation, primary-key deduplication) with full transparency and documentation.

---

## 🧠 Skills Demonstrated

- **Data Quality Management** — systematic audit and resolution of structural issues
- **Exploratory Data Analysis (EDA)** — schema inspection, null profiling, type validation
- **Data Cleaning & Wrangling** — pandas transformation pipeline, type coercion, string normalization
- **Statistical Anomaly Detection** — IQR-based outlier flagging
- **Feature Engineering** — time decomposition, risk categorization, financial KPIs
- **Business KPI Construction** — rejection rates, net balance, client aggregations
- **Data Documentation** — `DECISIONS.md` audit trail, inline comments, README
- **Pipeline Design** — sequential, reproducible, audit-friendly processing logic

---

## 💻 Example Code Snippet

```python
# Anomaly detection using IQR on transaction amounts
Q1 = df["montant"].quantile(0.25)
Q3 = df["montant"].quantile(0.75)
IQR = Q3 - Q1

lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

df["is_anomaly"] = (df["montant"] < lower_bound) | (df["montant"] > upper_bound)

print(f"Anomalies detected: {df['is_anomaly'].sum()} "
      f"({df['is_anomaly'].mean():.1%} of total transactions)")
```

---

## 🚀 Future Improvements

| Priority | Improvement |
|---|---|
| High | Load `financecore_clean.csv` into a **PostgreSQL** database for persistent storage |
| High | Add **data validation tests** using `Great Expectations` or `pandera` |
| Medium | Build a **Power BI / Tableau dashboard** on top of the clean dataset |
| Medium | Automate the pipeline with **Apache Airflow** or **Prefect** |
| Medium | Extend anomaly detection with **Isolation Forest** for multivariate outliers |
| Low | Add **unit tests** for each transformation function using `pytest` |
| Low | Containerize the pipeline using **Docker** for portability |

---

## 📝 Conclusion

This project is a **realistic, end-to-end data engineering case study** built around the challenges that data teams face daily in financial services environments. It goes beyond surface-level data cleaning by combining rigorous validation, statistical anomaly detection, and business-driven feature engineering into a coherent, documented, and reproducible pipeline.

The `financecore_clean.csv` output is not just a "cleaned file" — it is a validated analytical asset enriched with risk classifications, client KPIs, and time dimensions that directly support credit risk analysis, agency performance monitoring, and segment-level reporting.

---

## 🏷️ GitHub Repository Metadata

### ✅ Recommended Repository Name
```
financecore-transaction-pipeline
```

### 📝 Repository Description
```
End-to-end data cleaning, anomaly detection, and feature engineering pipeline for raw banking transaction data. Built with Python and pandas for FinanceCore SA.
```

### 📌 About Section (GitHub)
```
Production-grade data pipeline that transforms raw banking transactions into a clean, validated, and analytically enriched dataset — including IQR-based anomaly detection, credit risk categorization, client KPIs, and agency-level rejection rates.
```

### 🔖 Suggested GitHub Topics / Tags
```
data-engineering  data-cleaning  pandas  python  banking  financial-analytics
feature-engineering  anomaly-detection  etl  data-quality  credit-risk  kpi
```

---

### 🔤 Alternative Project Titles

1. `FinanceCore SA — Banking Data Quality & Enrichment Pipeline`
2. `Transaction Intelligence Pipeline — Data Cleaning & Feature Engineering for Financial Analytics`
3. `Raw-to-Ready: Banking Transaction Cleaning Pipeline with Anomaly Detection`

### 📋 Alternative Repository Descriptions

1. `A rigorous, production-style Python pipeline for cleaning, validating, and enriching raw banking transaction data — including outlier flagging, risk scoring, and client KPI computation.`
2. `Data engineering pipeline for financial transaction data: deduplication, type normalization, IQR anomaly detection, feature engineering, and KPI aggregation using pandas.`
3. `From messy CSV to analytics-ready dataset: a documented, step-by-step data cleaning and enrichment pipeline for banking transactions at FinanceCore SA.`

---

<div align="center">

*Built with precision for portfolio-grade data engineering. Designed for analysts, engineers, and decision-makers who demand clean data.*

</div>
