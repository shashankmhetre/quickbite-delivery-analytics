import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.cm as cm
import os

CHART_DIR = "charts"
os.makedirs(CHART_DIR, exist_ok=True)

plt.rcParams.update({
    "figure.dpi":        120,
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "grid.alpha":        0.3,
    "font.family":       "DejaVu Sans",
})
COLORS = ["#E8472B", "#F47C3C", "#FFC300", "#4CAF50",
          "#2196F3", "#9C27B0", "#00BCD4", "#FF5722"]


print("Loading datasets...")
df_customers   = pd.read_csv("Datasets/customers.csv")
df_restaurants = pd.read_csv("Datasets/restaurants.csv")
df_partners    = pd.read_csv("Datasets/delivery_partners.csv")
df_orders      = pd.read_csv("Datasets/orders.csv")
df_deliveries  = pd.read_csv("Datasets/deliveries.csv")

df_orders["order_date"]     = pd.to_datetime(df_orders["order_date"])
df_customers["signup_date"] = pd.to_datetime(df_customers["signup_date"])

for name, df in [("Customers", df_customers), ("Restaurants", df_restaurants),
                 ("Partners",  df_partners),   ("Orders",      df_orders),
                 ("Deliveries",df_deliveries)]:
    print(f"  {name}: {df.shape[0]:,} rows x {df.shape[1]} cols")


for df, label in [(df_orders, "orders"), (df_deliveries, "deliveries")]:
    before = len(df)
    df.drop_duplicates(inplace=True)
    print(f"  {label}: removed {before - len(df)} duplicates")

# fill missing delivery times with median — only affects cancelled/failed orders
df_deliveries["delivery_time_minutes"] = (
    df_deliveries["delivery_time_minutes"]
    .fillna(df_deliveries["delivery_time_minutes"].median())
)

df_orders["order_hour"]      = pd.to_datetime(
                                    df_orders["order_time"], format="%H:%M:%S"
                                ).dt.hour
df_orders["order_month_str"] = df_orders["order_date"].dt.strftime("%Y-%m")
df_orders["day_of_week"]     = df_orders["order_date"].dt.day_name()

# filter to delivered orders only for revenue and time analysis
df_delivered = df_orders[df_orders["order_status"] == "Delivered"].copy()
df_delivered = df_delivered.merge(
    df_deliveries[["order_id", "delivery_time_minutes", "delivery_rating", "distance_km"]],
    on="order_id", how="left"
)

avg_del_time     = df_delivered["delivery_time_minutes"].mean()
total_orders     = len(df_orders)
total_revenue    = df_delivered["order_value"].sum()
cancel_rate      = (df_orders["order_status"] == "Cancelled").mean() * 100
active_customers = df_delivered["customer_id"].nunique()

print(f"\nTotal Orders:      {total_orders:,}")
print(f"Total Revenue:     Rs.{total_revenue:,.0f}")
print(f"Avg Delivery Time: {avg_del_time:.1f} min")
print(f"Cancellation Rate: {cancel_rate:.1f}%")
print(f"Active Customers:  {active_customers:,}")


# normalize by days in month to avoid shorter months looking like dips
monthly = (df_delivered
           .groupby("order_month_str")["order_value"]
           .sum()
           .reset_index()
           .sort_values("order_month_str"))

monthly["year"]  = monthly["order_month_str"].str[:4].astype(int)
monthly["month"] = monthly["order_month_str"].str[5:7].astype(int)
monthly["days_in_month"] = monthly.apply(
    lambda r: pd.Timestamp(r["year"], r["month"], 1).days_in_month, axis=1
)
monthly["revenue_normalized"] = monthly["order_value"] / monthly["days_in_month"] * 30

fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(monthly["order_month_str"], monthly["revenue_normalized"] / 1_00_000,
        marker="o", linewidth=2.5, color=COLORS[0], markersize=6)
ax.fill_between(monthly["order_month_str"], monthly["revenue_normalized"] / 1_00_000,
                alpha=0.15, color=COLORS[0])
ax.set_title("Monthly Revenue Trend (2023-2024)\n(normalized to 30-day equivalent)",
             fontsize=14, fontweight="bold", pad=15)
ax.set_xlabel("Month")
ax.set_ylabel("Revenue (Rs. Lakhs, 30-day normalized)")
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("Rs.%.0fL"))
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/01_monthly_revenue.png")
plt.close()
print("Chart 1 saved")


hourly     = df_orders.groupby("order_hour").size().reset_index(name="orders")
peak       = hourly["orders"].max()
# highlight bars that are within 80% of peak volume
bar_colors = [COLORS[0] if v >= peak * 0.8 else COLORS[5] for v in hourly["orders"]]

fig, ax = plt.subplots(figsize=(12, 5))
ax.bar(hourly["order_hour"], hourly["orders"], color=bar_colors, edgecolor="white")
ax.set_title("Order Volume by Hour of Day", fontsize=14, fontweight="bold", pad=15)
ax.set_xlabel("Hour of Day (24h)")
ax.set_ylabel("Number of Orders")
ax.set_xticks(range(0, 24))
ax.axvspan(11.5, 14.5, alpha=0.08, color="orange", label="Lunch Peak")
ax.axvspan(18.5, 22.5, alpha=0.08, color="red",    label="Dinner Peak")
ax.legend()
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/02_orders_by_hour.png")
plt.close()
print("Chart 2 saved")


# join on customer city since orders table doesn't have city directly
city_rev = (df_delivered
            .merge(df_customers[["customer_id", "city"]], on="customer_id", how="left")
            .groupby("city")["order_value"]
            .sum()
            .sort_values(ascending=True))

fig, ax = plt.subplots(figsize=(9, 6))
bars = ax.barh(city_rev.index, city_rev.values / 1_00_000,
               color=COLORS[:len(city_rev)], edgecolor="white")
ax.set_title("Total Revenue by City", fontsize=14, fontweight="bold", pad=15)
ax.set_xlabel("Revenue (Rs. Lakhs)")
for bar, val in zip(bars, city_rev.values / 1_00_000):
    ax.text(val + 0.5, bar.get_y() + bar.get_height() / 2,
            f"Rs.{val:.1f}L", va="center", fontsize=9)
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/03_revenue_by_city.png")
plt.close()
print("Chart 3 saved")


cuisine_orders = (df_delivered
                  .merge(df_restaurants[["restaurant_id", "cuisine"]],
                         on="restaurant_id", how="left")
                  .groupby("cuisine")
                  .size()
                  .sort_values(ascending=True))

cuisine_colors = [
    "#E8472B","#F47C3C","#FFC300","#4CAF50",
    "#2196F3","#9C27B0","#00BCD4","#FF5722",
    "#795548","#607D8B","#E91E63","#009688"
]

fig, ax = plt.subplots(figsize=(11, 7))
bars = ax.barh(cuisine_orders.index, cuisine_orders.values,
               color=cuisine_colors[:len(cuisine_orders)],
               edgecolor="white", height=0.65)
ax.set_title("Cuisine Popularity by Order Volume", fontsize=14, fontweight="bold", pad=15)
ax.set_xlabel("Number of Orders")
for bar, val in zip(bars, cuisine_orders.values):
    pct = val / cuisine_orders.sum() * 100
    ax.text(val + cuisine_orders.max() * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{val:,}  ({pct:.1f}%)", va="center", fontsize=9)
ax.set_xlim(0, cuisine_orders.max() * 1.18)
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/04_cuisine_popularity.png")
plt.close()
print("Chart 4 saved")


median_del = df_delivered["delivery_time_minutes"].median()

fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(df_delivered["delivery_time_minutes"].dropna(), bins=30,
        color=COLORS[1], edgecolor="white", alpha=0.85)
ax.axvline(avg_del_time, color=COLORS[0], linestyle="--", linewidth=2,
           label=f"Mean: {avg_del_time:.1f} min")
ax.axvline(median_del, color=COLORS[5], linestyle=":", linewidth=2,
           label=f"Median: {median_del:.1f} min")
ax.set_title("Delivery Time Distribution", fontsize=14, fontweight="bold", pad=15)
ax.set_xlabel("Delivery Time (minutes)")
ax.set_ylabel("Number of Orders")
ax.legend()
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/05_delivery_time_dist.png")
plt.close()
print("Chart 5 saved")


top_rests = (df_delivered
             .merge(df_restaurants[["restaurant_id", "restaurant_name", "cuisine"]],
                    on="restaurant_id", how="left")
             .groupby(["restaurant_id", "restaurant_name", "cuisine"])["order_value"]
             .sum()
             .sort_values(ascending=True)
             .tail(10)
             .reset_index())

# gold-to-red gradient so the top restaurant stands out
gradient_colors = [cm.YlOrRd(0.35 + 0.65 * i / (len(top_rests) - 1))
                   for i in range(len(top_rests))]
labels = top_rests["restaurant_name"] + "\n(" + top_rests["cuisine"] + ")"

fig, ax = plt.subplots(figsize=(12, 7))
bars = ax.barh(labels, top_rests["order_value"] / 1000,
               color=gradient_colors, edgecolor="white", height=0.65)
ax.set_title("Top 10 Restaurants by Revenue", fontsize=14, fontweight="bold", pad=15)
ax.set_xlabel("Revenue (Rs. Thousands)")
for bar, val in zip(bars, top_rests["order_value"] / 1000):
    ax.text(val + top_rests["order_value"].max() / 1000 * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"Rs.{val:.0f}K", va="center", fontsize=9, fontweight="bold")
ax.set_xlim(0, top_rests["order_value"].max() / 1000 * 1.15)
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/06_top_restaurants.png")
plt.close()
print("Chart 6 saved")


day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
weekly = df_orders.groupby("day_of_week").size().reindex(day_order)

fig, ax = plt.subplots(figsize=(9, 5))
ax.bar(weekly.index, weekly.values, color=COLORS[3], edgecolor="white")
ax.set_title("Orders by Day of Week", fontsize=14, fontweight="bold", pad=15)
ax.set_xlabel("Day")
ax.set_ylabel("Number of Orders")
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/07_orders_by_day.png")
plt.close()
print("Chart 7 saved")


# bubble size = number of deliveries, color = avg rating
partner_perf = (df_deliveries
                .merge(df_partners[["partner_id", "partner_name", "experience_years"]],
                       on="partner_id", how="left")
                .groupby(["partner_id", "partner_name", "experience_years"])
                .agg(
                    total_deliveries  = ("delivery_id",           "count"),
                    avg_delivery_time = ("delivery_time_minutes", "mean"),
                    avg_rating        = ("delivery_rating",       "mean"),
                )
                .reset_index())

fig, ax = plt.subplots(figsize=(9, 6))
scatter = ax.scatter(
    partner_perf["experience_years"],
    partner_perf["avg_delivery_time"],
    c=partner_perf["avg_rating"],
    cmap="RdYlGn",
    s=partner_perf["total_deliveries"] * 3,
    alpha=0.75,
    edgecolors="grey",
    linewidths=0.5,
)
cbar = plt.colorbar(scatter, ax=ax)
cbar.set_label("Avg Delivery Rating", fontsize=9)
ax.set_title("Delivery Partner Efficiency\n(size = deliveries, color = rating)",
             fontsize=13, fontweight="bold", pad=12)
ax.set_xlabel("Experience (Years)")
ax.set_ylabel("Avg Delivery Time (min)")
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/08_partner_efficiency.png")
plt.close()
print("Chart 8 saved")


plot_del = df_deliveries[["distance_km", "delivery_time_minutes"]].dropna()

fig, ax = plt.subplots(figsize=(9, 6))
ax.scatter(plot_del["distance_km"], plot_del["delivery_time_minutes"],
           alpha=0.3, color=COLORS[4], edgecolors="none", s=15)
# fit a simple trend line
z = np.polyfit(plot_del["distance_km"], plot_del["delivery_time_minutes"], 1)
p = np.poly1d(z)
x_line = np.linspace(plot_del["distance_km"].min(), plot_del["distance_km"].max(), 100)
ax.plot(x_line, p(x_line), color=COLORS[0], linewidth=2, label="Trend")
ax.set_title("Distance vs Delivery Time", fontsize=14, fontweight="bold", pad=15)
ax.set_xlabel("Distance (km)")
ax.set_ylabel("Delivery Time (min)")
ax.legend()
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/09_distance_vs_time.png")
plt.close()
print("Chart 9 saved")


pay_dist = df_orders["payment_method"].value_counts()

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(pay_dist.index, pay_dist.values,
              color=COLORS[:len(pay_dist)], edgecolor="white")
ax.set_title("Orders by Payment Method", fontsize=14, fontweight="bold", pad=15)
ax.set_xlabel("Payment Method")
ax.set_ylabel("Number of Orders")
for bar, val in zip(bars, pay_dist.values):
    ax.text(bar.get_x() + bar.get_width() / 2, val + 10,
            f"{val:,}", ha="center", fontsize=10)
plt.tight_layout()
plt.savefig(f"{CHART_DIR}/10_payment_methods.png")
plt.close()
print("Chart 10 saved")

print(f"\nAll charts saved to {CHART_DIR}/")
