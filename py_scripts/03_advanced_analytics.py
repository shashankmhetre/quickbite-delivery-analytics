import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler

os.chdir(os.path.dirname(os.path.abspath(__file__)))

CHART_DIR  = "../charts"
OUTPUT_DIR = "../Datasets"
os.makedirs(CHART_DIR,  exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

plt.rcParams.update({
    "figure.dpi":        120,
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "grid.alpha":        0.3,
})
COLORS = ["#E8472B", "#F47C3C", "#FFC300", "#4CAF50",
          "#2196F3", "#9C27B0", "#00BCD4", "#FF5722"]


print("Loading data...")
df_orders      = pd.read_csv("../Datasets/orders.csv")
df_restaurants = pd.read_csv("../Datasets/restaurants.csv")
df_customers   = pd.read_csv("../Datasets/customers.csv")
df_deliveries  = pd.read_csv("../Datasets/deliveries.csv")
df_partners    = pd.read_csv("../Datasets/delivery_partners.csv")

df_orders["order_date"]      = pd.to_datetime(df_orders["order_date"])
df_orders["order_hour"]      = pd.to_datetime(
                                    df_orders["order_time"], format="%H:%M:%S"
                                ).dt.hour
df_orders["month"]           = df_orders["order_date"].dt.month
df_orders["day_of_week"]     = df_orders["order_date"].dt.day_name()
df_orders["order_month_str"] = df_orders["order_date"].dt.strftime("%Y-%m")

df_delivered = df_orders[df_orders["order_status"] == "Delivered"].copy()
df_delivered = df_delivered.merge(
    df_deliveries[["order_id", "delivery_time_minutes", "delivery_rating", "distance_km"]],
    on="order_id", how="left"
)

print(f"  Total orders  : {len(df_orders):,}")
print(f"  Delivered     : {len(df_delivered):,}")


print("\nModule 1: Restaurant Performance Score")

rest_orders = (df_delivered
               .groupby("restaurant_id")
               .agg(
                   total_orders      = ("order_id",              "count"),
                   total_revenue     = ("order_value",           "sum"),
                   avg_delivery_time = ("delivery_time_minutes", "mean"),
               )
               .reset_index())

rest_perf = rest_orders.merge(
    df_restaurants[["restaurant_id", "restaurant_name", "cuisine", "city", "rating"]],
    on="restaurant_id"
)

# normalize all inputs to 0-1 before applying weights
scaler = MinMaxScaler()
rest_perf[["rating_n", "orders_n", "revenue_n", "speed_n"]] = (
    scaler.fit_transform(
        rest_perf[["rating", "total_orders", "total_revenue", "avg_delivery_time"]]
    )
)
# invert speed so lower delivery time = higher score
rest_perf["speed_n"] = 1 - rest_perf["speed_n"]

rest_perf["performance_score"] = (
    0.4 * rest_perf["rating_n"]  +
    0.3 * rest_perf["orders_n"]  +
    0.2 * rest_perf["revenue_n"] +
    0.1 * rest_perf["speed_n"]
).round(4)

rest_perf.sort_values("performance_score", ascending=False, inplace=True)
rest_perf["rank"] = range(1, len(rest_perf) + 1)
rest_perf.to_csv(f"{OUTPUT_DIR}/restaurant_scores.csv", index=False)

top15 = rest_perf.head(15).iloc[::-1]
fig, ax = plt.subplots(figsize=(11, 7))
bars = ax.barh(
    top15["restaurant_name"] + " (" + top15["city"] + ")",
    top15["performance_score"],
    color=COLORS[3], edgecolor="white"
)
ax.set_title("Top 15 Restaurants - Performance Score\n(0.4xRating + 0.3xOrders + 0.2xRevenue + 0.1xSpeed)",
             fontsize=12, fontweight="bold", pad=12)
ax.set_xlabel("Composite Performance Score (0-1)")
for bar, val in zip(bars, top15["performance_score"]):
    ax.text(val + 0.002, bar.get_y() + bar.get_height() / 2,
            f"{val:.3f}", va="center", fontsize=8)
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/11_restaurant_performance_score.png")
plt.close()
print("  Chart 11 saved")


print("\nModule 2: Customer Segmentation")

SNAPSHOT_DATE = df_delivered["order_date"].max() + pd.Timedelta(days=1)

rfm = (df_delivered
       .groupby("customer_id")
       .agg(
           recency   = ("order_date",  lambda x: (SNAPSHOT_DATE - x.max()).days),
           frequency = ("order_id",    "count"),
           monetary  = ("order_value", "sum"),
       )
       .reset_index())

# simple rule-based segmentation on top of RFM values
def segment(row):
    if row["frequency"] >= 10 and row["monetary"] >= 3000:
        return "High Value"
    elif row["frequency"] >= 5 and row["monetary"] >= 1500:
        return "Regular"
    elif row["frequency"] >= 2:
        return "Occasional"
    else:
        return "At Risk"

rfm["segment"] = rfm.apply(segment, axis=1)
rfm = rfm.merge(df_customers[["customer_id", "customer_name", "city"]], on="customer_id")
rfm.to_csv(f"{OUTPUT_DIR}/customer_segments.csv", index=False)

seg_counts = rfm["segment"].value_counts()
seg_colors = {"High Value": "#4CAF50", "Regular": "#2196F3",
              "Occasional": "#FFC300", "At Risk": "#E8472B"}

fig, axes = plt.subplots(1, 2, figsize=(13, 6))
axes[0].pie(seg_counts.values, labels=seg_counts.index,
            colors=[seg_colors[s] for s in seg_counts.index],
            autopct="%1.1f%%", startangle=90)
axes[0].set_title("Customer Segment Distribution", fontsize=13, fontweight="bold")

for seg, grp in rfm.groupby("segment"):
    axes[1].scatter(grp["frequency"], grp["monetary"],
                    label=seg, alpha=0.5, s=20, color=seg_colors[seg])
axes[1].set_title("Frequency vs Spend by Segment", fontsize=13, fontweight="bold")
axes[1].set_xlabel("Order Frequency")
axes[1].set_ylabel("Total Spend (Rs.)")
axes[1].legend()

plt.tight_layout()
plt.savefig(f"{CHART_DIR}/12_customer_segmentation.png")
plt.close()
print("  Chart 12 saved")


print("\nModule 3: Peak Demand Analysis")

day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
pivot = (df_orders
         .groupby(["day_of_week", "order_hour"])
         .size()
         .unstack(fill_value=0)
         .reindex(day_order))

fig, ax = plt.subplots(figsize=(14, 5))
im = ax.imshow(pivot.values, aspect="auto", cmap="YlOrRd")
ax.set_xticks(range(24))
ax.set_xticklabels([f"{h:02d}:00" for h in range(24)],
                   rotation=45, ha="right", fontsize=7)
ax.set_yticks(range(7))
ax.set_yticklabels(day_order)
plt.colorbar(im, ax=ax, label="Number of Orders")
ax.set_title("Order Demand Heatmap - Hour x Day of Week",
             fontsize=13, fontweight="bold", pad=12)
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/13_demand_heatmap.png")
plt.close()
print("  Chart 13 saved")

monthly = df_orders.groupby(df_orders["order_date"].dt.to_period("M")).size()

fig, ax = plt.subplots(figsize=(14, 4))
ax.bar(monthly.index.astype(str), monthly.values, color=COLORS[4], edgecolor="white")
ax.set_title("Monthly Order Volume (2023-2024)", fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Month")
ax.set_ylabel("Orders")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/14_monthly_order_volume.png")
plt.close()
print("  Chart 14 saved")


print("\nModule 4: Delivery Partner Efficiency")

partner_stats = (df_deliveries
                 .merge(df_partners[["partner_id", "partner_name",
                                     "experience_years", "vehicle_type"]],
                        on="partner_id")
                 .groupby(["partner_id", "partner_name", "experience_years", "vehicle_type"])
                 .agg(
                     deliveries     = ("delivery_id",           "count"),
                     avg_time       = ("delivery_time_minutes", "mean"),
                     avg_distance   = ("distance_km",           "mean"),
                     total_distance = ("distance_km",           "sum"),
                     avg_rating     = ("delivery_rating",       "mean"),
                 )
                 .reset_index())

partner_stats["del_per_hour"] = (60 / partner_stats["avg_time"]).round(2)
partner_stats["tier"] = pd.cut(
    partner_stats["avg_rating"],
    bins=[0, 3.0, 3.7, 4.3, 5.0],
    labels=["Poor","Average","Good","Excellent"]
)
partner_stats.sort_values("avg_rating", ascending=False, inplace=True)
partner_stats.to_csv(f"{OUTPUT_DIR}/partner_efficiency.csv", index=False)

tier_colors = {"Excellent": "#4CAF50", "Good": "#2196F3",
               "Average":   "#FFC300", "Poor": "#E8472B"}

fig, ax = plt.subplots(figsize=(9, 5))
for tier, grp in partner_stats.groupby("tier", observed=True):
    ax.scatter(
        grp["experience_years"] + np.random.uniform(-0.2, 0.2, len(grp)),
        grp["avg_rating"],
        label=str(tier),
        color=tier_colors[str(tier)],
        alpha=0.7,
        s=grp["deliveries"] * 1.5,
        edgecolors="grey", linewidths=0.4
    )
ax.set_title("Experience vs Avg Rating (size = deliveries)",
             fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Years of Experience")
ax.set_ylabel("Average Delivery Rating")
ax.legend(title="Tier")
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/15_partner_experience_vs_rating.png")
plt.close()
print("  Chart 15 saved")


print("\nModule 5: Geographic Hotspot Analysis")

city_stats = (df_delivered
              .merge(df_customers[["customer_id", "city"]], on="customer_id", how="left")
              .groupby("city")
              .agg(
                  total_orders    = ("order_id",    "count"),
                  total_revenue   = ("order_value", "sum"),
                  avg_order_value = ("order_value", "mean"),
              )
              .reset_index())

city_del = (df_deliveries
            .merge(df_orders[["order_id", "customer_id"]], on="order_id")
            .merge(df_customers[["customer_id", "city"]],  on="customer_id")
            .groupby("city")
            .agg(avg_del_time=("delivery_time_minutes", "mean"))
            .reset_index())

city_stats = city_stats.merge(city_del, on="city")
city_stats["demand_score"] = MinMaxScaler().fit_transform(city_stats[["total_orders"]])
city_stats.sort_values("total_orders", ascending=False, inplace=True)
city_stats.to_csv(f"{OUTPUT_DIR}/city_hotspots.csv", index=False)

# dual axis: bars for order volume, line for avg delivery time
fig, ax1 = plt.subplots(figsize=(10, 5))
x = range(len(city_stats))
ax1.bar(x, city_stats["total_orders"], color=COLORS[0], edgecolor="white", label="Orders")
ax1.set_xticks(x)
ax1.set_xticklabels(city_stats["city"], rotation=30, ha="right")
ax1.set_ylabel("Total Orders", color=COLORS[0])

ax2 = ax1.twinx()
ax2.plot(x, city_stats["avg_del_time"], color=COLORS[5],
         marker="o", linewidth=2, label="Avg Del. Time")
ax2.set_ylabel("Avg Delivery Time (min)", color=COLORS[5])

ax1.set_title("City Demand vs Average Delivery Time",
              fontsize=13, fontweight="bold", pad=12)
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/16_city_hotspots.png")
plt.close()
print("  Chart 16 saved")

print("\nDone. All outputs saved.")
