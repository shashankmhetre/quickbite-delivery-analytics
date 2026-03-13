# QuickBite Delivery Analytics

A data analytics project built on a simulated food delivery platform. I created this to practice building an end-to-end pipeline — from generating data to running analysis and storing it in a database.

**Tools used:** Python, pandas, MySQL, scikit-learn, matplotlib

---

## What this project covers

I built a synthetic dataset that mimics an Indian food delivery platform across 8 cities over 2 years (2023–2024). The data includes customers, restaurants, delivery partners, orders, and deliveries — around 50,000 order records in total.

The analysis is split across three scripts:

- **01_generate_dataset.py** — generates all the data with realistic patterns (peak hours, seasonal spikes, city-wise distribution)
- **02_eda_and_visualization.py** — exploratory analysis and charts
- **03_advanced_analytics.py** — customer segmentation, cohort analysis, delivery performance, and revenue trends

The final datasets are also loaded into a MySQL database with a proper relational schema.

---

## Some findings worth mentioning

- April 2024 was the highest revenue month (₹14.2L), likely reflecting the IPL season pattern built into the data
- Average delivery partner rating (3.66) is noticeably lower than restaurant rating (4.35) — the delivery experience drags down overall satisfaction
- Loyalty tier had almost no impact on order value — Platinum customers averaged ₹541 vs Bronze at ₹519
- UPI was the dominant payment method at 52%; Cash on Delivery was under 10%
- Mumbai and Delhi together made up 43% of total revenue
- Peak ordering was between 7–9 PM, with a smaller lunch spike around noon

---

## Dataset overview

| Table | Rows |
|-------|------|
| customers | 5,000 |
| restaurants | 500 |
| delivery_partners | 1,000 |
| orders | 50,000 |
| deliveries | 50,000 |

Total revenue across the dataset: ₹2.75 crore | Avg order value: ₹549.94

---

## Folder structure

```
├── scripts/
│   ├── 01_generate_dataset.py
│   ├── 02_eda_and_visualization.py
│   └── 03_advanced_analytics.py
├── data/
│   └── sample/          # 500-row samples of each table
├── sql/
│   └── schema.sql
├── charts/              # output visualizations
└── requirements.txt
```

---

## How to run

```bash
git clone https://github.com/shashankmhetre/quickbite-delivery-analytics.git
cd quickbite-delivery-analytics
pip install -r requirements.txt

python scripts/01_generate_dataset.py   # generates CSVs
python scripts/02_eda_and_visualization.py
python scripts/03_advanced_analytics.py
```

For MySQL, update your credentials in the script and run `schema.sql` in Workbench first.

---

## Requirements

```
pandas
matplotlib
scikit-learn
sqlalchemy
pymysql
numpy
```

---

*Dataset is synthetically generated. Does not represent any real company's data.*
