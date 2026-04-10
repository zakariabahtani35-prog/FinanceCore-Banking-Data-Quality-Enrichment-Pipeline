# FinanceCore SA — Banking Transaction Data Pipeline

> **Transforming raw, unreliable transactional data into a clean, enriched, analysis-ready asset through a production-grade Python pipeline.**

---

## Executive Summary

In the banking sector, data quality is not a technical convenience — it is a regulatory and operational imperative. Raw transaction data collected from heterogeneous sources routinely contains structural inconsistencies, missing values, malformed fields, and anomalous records that render it unfit for direct analysis.

This project implements a rigorous end-to-end data engineering pipeline for **FinanceCore SA**, a regional bank, processing the raw dataset `bank_transactions.csv` through a sequence of validated cleaning operations, statistical anomaly detection, and domain-driven feature engineering. The output — `financecore_clean.csv` — is a standardized, imputed, and semantically enriched dataset ready for downstream risk modeling, client segmentation, and operational reporting.

The pipeline is designed to be reproducible, documented, and audit-compliant, reflecting real-world data engineering standards applied in financial institutions.

---

## Project Objectives

- Identify and resolve data quality issues present in raw banking transaction records
- Normalize structural inconsistencies across numeric, temporal, and categorical fields
- Apply statistically sound imputation strategies to eliminate residual missingness
- Detect and flag transactional anomalies without altering or deleting underlying records
- Engineer analytical features covering temporal patterns, financial validation, client risk profiling, and agency performance
- Deliver a clean, enriched dataset suitable for immediate consumption by analysts and data scientists

---

## Dataset Overview

| Attribute | Detail |
|---|---|
| Source file | `bank_transactions.csv` |
| Rows | 2,060 |
| Columns | 16 |
| Domain | Retail banking transactions |

**Key fields:**

| Field | Description |
|---|---|
| `transaction_id` | Unique transaction identifier (primary key) |
| `client_id` | Client reference |
| `date_transaction` | Transaction date (raw string format) |
| `montant` | Transaction amount (raw, may contain formatting artifacts) |
| `devise` | Currency code (ISO 4217) |
| `taux_change_eur` | Exchange rate to EUR |
| `montant_eur` | Recorded EUR equivalent |
| `categorie` | Transaction category |
| `produit` | Banking product type |
| `agence` | Branch identifier |
| `type_operation` | Operation type (Virement, Retrait, Dépôt, Paiement) |
| `statut` | Transaction status (Approuvé, Rejeté, En attente) |
| `score_credit_client` | Client credit score |
| `segment_client` | Client segment (Premium, Standard, etc.) |
| `solde_avant` | Pre-transaction account balance |

---

## Data Quality Issues Identified

The following issues were systematically identified during the initial data quality assessment:

| Issue | Affected Field(s) | Impact |
|---|---|---|
| Duplicate transaction records | `transaction_id` | Inflated KPIs, broken referential integrity |
| Missing values | Multiple numeric and categorical columns | Downstream computation failures |
| Malformed date strings | `date_transaction` | Temporal features inaccessible |
| Comma decimal separators | `montant` | Silent type coercion failures |
| Embedded currency strings | `solde_avant` (e.g., `"12500 EUR"`) | Numeric casting errors |
| Mixed-case categorical labels | `devise`, `segment_client`, `statut` | False cardinality inflation |
| Extraneous whitespace | All object columns | Join mismatches, erroneous groupings |
| Out-of-range credit scores | `score_credit_client` | Invalid risk classifications |
| Statistical outliers in amounts | `montant` | Distorted aggregations and model bias |
| Zero exchange rates | `taux_change_eur` | Division errors in FX validation |

---

## Data Cleaning Pipeline

### 1. Structural Audit
Initial inspection via `df.shape`, `df.dtypes`, `df.head()`, and `df.describe()` establishes the data contract. Missing value percentages are computed across all columns to prioritize remediation.

### 2. Duplicate Removal
Duplicate rows identified by `transaction_id` are removed, retaining the first occurrence. In banking systems, duplicate transaction IDs indicate ETL failures or retry events and must be eliminated to maintain primary key integrity.

### 3. Date Normalization
`date_transaction` is converted to `datetime` using `pd.to_datetime(..., errors='coerce')`. Unparseable entries are replaced with `NaT`, preserving record continuity while surfacing temporal data gaps for review.

### 4. Amount Cleaning — `montant`
Comma decimal separators are replaced with standard dots before numeric coercion. This is a common artifact of European locale formats and must be resolved before any arithmetic or statistical operation.

### 5. Balance Cleaning — `solde_avant`
The string suffix `" EUR"` is stripped from balance values, followed by numeric conversion. This pattern arises when balance fields are exported with embedded unit labels from legacy banking systems.

### 6. Text Normalization
All object-type columns undergo `.str.strip()` to remove leading and trailing whitespace. Targeted normalizations are then applied:
- `devise` → uppercased to ISO 4217 standard
- `segment_client` → title-cased for canonical label form
- `agence`, `categorie`, `produit`, `type_operation`, `statut` → stripped and standardized

### 7. Missing Value Imputation

| Column | Strategy | Rationale |
|---|---|---|
| `score_credit_client` | Median | Robust to outliers in skewed credit score distributions |
| `solde_avant` | Median | Prevents inflation from extreme balance values |
| `segment_client` | Mode | Most probable segment for records with unknown classification |
| `agence` | Mode | Assigns the highest-volume branch as the default for unresolved records |

---

## Anomaly Detection Strategy

Anomaly detection is implemented as a **non-destructive flagging mechanism**. No records are deleted. Each anomaly is marked with a binary indicator, preserving full audit trail compliance.

### IQR-Based Amount Outlier Detection
The Interquartile Range method identifies statistical outliers in `montant`:

```
IQR = Q3 − Q1
Lower bound = Q1 − 1.5 × IQR
Upper bound = Q3 + 1.5 × IQR
```

Transactions outside these bounds receive `is_anomaly_montant = 1`. The IQR method is selected over z-score alternatives because transaction amounts are right-skewed — a distribution where mean-based methods produce systematically biased thresholds.

### Invalid Credit Score Detection
Credit scores outside the valid FICO range `[0, 850]` are flagged as `is_anomaly_score = 1`. Values in this range are definitionally invalid and indicate upstream data entry or system errors.

### Global Anomaly Flag
`is_anomaly = 1` if either `is_anomaly_montant` or `is_anomaly_score` is positive. This composite indicator serves as the master filter for compliance review workflows and anomaly reporting dashboards.

---

## Feature Engineering

### Temporal Features
Extracted from `date_transaction`:

| Feature | Business Use |
|---|---|
| `year` | Year-over-year trend analysis |
| `month` | Seasonal liquidity and volume patterns |
| `quarter` | Alignment with financial reporting periods |
| `weekday` | Day-of-week behavioral analysis (fraud signal) |

### Financial Validation Features

| Feature | Description |
|---|---|
| `taux_change_eur` (cleaned) | Zero rates replaced with `NaN` — a zero exchange rate is a sentinel value, not a valid conversion |
| `montant_eur_verifie` | Independently recomputed as `montant / taux_change_eur` |
| `ecart_montant_eur` | Absolute difference between recorded and recomputed EUR amount — non-zero values flag FX recording inconsistencies |

### Risk Classification — `categorie_risque`

| Credit Score | Category | Interpretation |
|---|---|---|
| ≥ 700 | Low Risk | Prime borrower — standard product access |
| ≥ 580 | Medium Risk | Standard client — enhanced monitoring |
| < 580 | High Risk | Sub-prime — restricted products, risk provisioning |

### Transaction Direction

- `credit = 1` for inflow operations: `Virement`, `Dépôt`
- `debit = 1` for outflow operations: `Retrait`, `Paiement`

### Client-Level KPIs
Aggregated per `client_id` and merged back to the transaction level:

| Feature | Description |
|---|---|
| `nb_transactions` | Total transaction count — activity level proxy |
| `montant_moyen` | Average transaction amount — value segment indicator |
| `nb_produits_distincts` | Distinct product count — wallet-share breadth |
| `total_credit` | Sum of inflows — liquidity assessment |
| `total_debit` | Sum of outflows — spending behavior analysis |
| `solde_net` | `total_credit − total_debit` — pipeline-derived net balance |

### Agency-Level KPI

| Feature | Description |
|---|---|
| `taux_rejet` | Rejection rate per agency: proportion of transactions with `statut = 'Rejeté'` — operational quality indicator |

---

## Output Deliverables

The pipeline produces `financecore_clean.csv`, a fully normalized, imputed, and feature-enriched dataset with the following guarantees:

- Zero residual missingness in all analytically critical columns
- Primary key integrity verified (no duplicate `transaction_id`)
- Standardized categorical vocabularies across all text fields
- Eighteen engineered features covering temporal, financial, risk, directional, client, and agency dimensions
- Non-destructive anomaly flags enabling filtered analysis without record loss
- Directly consumable by risk analysts, data scientists, and BI tools without further preprocessing

---

## Tech Stack

| Tool | Role |
|---|---|
| **Python 3.x** | Core pipeline language |
| **Pandas** | Data loading, transformation, aggregation |
| **NumPy** | Numerical operations and statistical computations |

---

## Project Workflow

```
bank_transactions.csv
        │
        ▼
┌─────────────────────┐
│  Data Exploration   │  shape, dtypes, missing values, duplicates
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   Data Cleaning     │  dates, amounts, balances, text normalization
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   Imputation        │  median (numeric) / mode (categorical)
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Anomaly Detection   │  IQR on montant, credit score range check
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Feature Engineering │  temporal, financial, risk, KPIs
└─────────┬───────────┘
          │
          ▼
  financecore_clean.csv
```

---

## Key Business Value

| Dimension | Value Delivered |
|---|---|
| **Risk Monitoring** | Anomaly flags and risk categories enable real-time screening of suspicious transactions |
| **Client Intelligence** | Aggregated KPIs support segmentation, churn modeling, and product targeting |
| **Operational Quality** | Agency rejection rates expose branch-level processing failures |
| **Regulatory Compliance** | Full audit trail preserved — no records deleted, all decisions documented |
| **Analytics Readiness** | Clean, typed, enriched dataset eliminates preprocessing overhead for downstream teams |

---

## Repository Structure

```
.
├── bank_transactions.csv       # Raw input dataset
├── financecore_clean.csv       # Cleaned and enriched output dataset
├── financecore_pipeline.py     # End-to-end data pipeline script
└── README.md                   # Project documentation
```

---

## How to Run the Project

**1. Clone the repository**
```bash
git clone https://github.com/your-username/financecore-data-pipeline.git
cd financecore-data-pipeline
```

**2. Install dependencies**
```bash
pip install pandas numpy
```

**3. Run the pipeline**
```bash
python financecore_pipeline.py
```

The cleaned dataset will be generated as `financecore_clean.csv` in the project root directory.

---

## Future Improvements

- **Interactive Dashboard** — Integrate Plotly or Streamlit to visualize transaction distributions, anomaly rates, and client KPIs in real time
- **ML-Based Anomaly Detection** — Replace rule-based flagging with Isolation Forest or Autoencoder models for contextual anomaly identification
- **Database Integration** — Replace CSV I/O with a PostgreSQL or BigQuery backend for scalable, production-grade data storage
- **Automated Data Validation** — Implement Great Expectations or Pandera to enforce schema contracts and raise alerts on upstream data drift
- **Pipeline Orchestration** — Migrate the pipeline to Apache Airflow or Prefect for scheduled, monitored execution in a production environment
- **Multi-Currency FX Validation** — Integrate a live exchange rate API (e.g., ECB Data Portal) to validate `taux_change_eur` against official benchmark rates

---

## Conclusion

This project demonstrates a complete, production-oriented approach to banking transaction data engineering. From raw ingestion through structured cleaning, statistical anomaly detection, and domain-driven feature engineering, every decision in the pipeline is grounded in both technical rigor and financial business logic.

The resulting dataset is not merely "cleaner" — it is analytically enriched, audit-compliant, and immediately actionable. This pipeline reflects the standards expected of data engineering work in regulated financial environments, where data quality is inseparable from institutional trust.

---

*FinanceCore SA Data Engineering Project — produced as a portfolio deliverable demonstrating applied data engineering in the banking domain.*
