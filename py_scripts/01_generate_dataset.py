import pandas as pd
import numpy as np
import random
from faker import Faker
from datetime import datetime, timedelta

fake = Faker('en_IN')
np.random.seed(42)
random.seed(42)

START_DATE = datetime(2023, 1, 1)
END_DATE   = datetime(2024, 12, 31)
TOTAL_DAYS = (END_DATE - START_DATE).days + 1

N_CUSTOMERS         = 5000
N_RESTAURANTS       = 500
N_DELIVERY_PARTNERS = 1000
N_ORDERS            = 50000

CITIES       = ['Delhi','Mumbai','Bangalore','Hyderabad','Chennai','Pune','Kolkata','Ahmedabad']
CITY_WEIGHTS = [0.20, 0.22, 0.16, 0.12, 0.10, 0.08, 0.07, 0.05]

# date multipliers for festivals and IPL season
def get_spike_dates():
    spikes = {}
    for year in [2023, 2024]:
        spikes[datetime(year, 1, 1)]   = 1.30
        spikes[datetime(year, 12, 31)] = 1.35
        spikes[datetime(year, 1, 2)]   = 1.15
        spikes[datetime(year, 2, 14)]  = 1.20
        spikes[datetime(year, 2, 13)]  = 1.10

        # IPL — tapered across March-May instead of a flat spike
        for day in range(1, 32):
            spikes[datetime(year, 3, day)] = 1.08
        for day in range(1, 31):
            spikes[datetime(year, 4, day)] = 1.12
        for day in range(1, 32):
            spikes[datetime(year, 5, day)] = 1.10

        spikes[datetime(year, 8, 15)] = 1.20
        spikes[datetime(year, 8, 14)] = 1.10

        diwali = datetime(2023, 11, 12) if year == 2023 else datetime(2024, 11, 1)
        spikes[diwali - timedelta(days=2)] = 1.20
        spikes[diwali - timedelta(days=1)] = 1.30
        spikes[diwali]                     = 1.45
        spikes[diwali + timedelta(days=1)] = 1.35
        spikes[diwali + timedelta(days=2)] = 1.25
        spikes[diwali + timedelta(days=3)] = 1.15

        spikes[datetime(year, 12, 24)] = 1.20
        spikes[datetime(year, 12, 25)] = 1.30
        spikes[datetime(year, 12, 26)] = 1.15

    return spikes

SPIKE_DATES = get_spike_dates()
all_dates   = [START_DATE + timedelta(days=i) for i in range(TOTAL_DAYS)]
RAINY_DAYS  = set(random.sample(all_dates, int(TOTAL_DAYS * 0.15)))

CUISINE_NAMES = {
    'North Indian':  ['Punjabi Tadka','Royal Tandoor','Delhi Darbar','Spice of Punjab',
                      'Tandoori Nights','Maharaja Kitchen','Amritsar Express'],
    'South Indian':  ['Udupi Bhavan','Dosa Plaza','Madras Cafe','Sambar House',
                      'Idli Express','Coconut Grove','Chennai Tiffin'],
    'Chinese':       ['Dragon Wok','Golden Panda','Red Dragon','Wok Dynasty',
                      'Shanghai Bites','Lucky Dragon','Oriental Bowl'],
    'Italian':       ['Pizza Palace','Pasta Fresca','Little Italy','Roma Kitchen',
                      'Napoli Pizzeria','Bella Pasta','Tuscany Table'],
    'Fast Food':     ['Burger Hub','Crunchy Bites','Fry Nation','Quick Bites',
                      'Urban Burgers','Snack Shack','Bite Express'],
    'Biryani':       ['Nawabi Biryani','Biryani Junction','Hyderabadi Dum Biryani',
                      'Royal Biryani House','Dum Delight','Biryani Express','Spice Biryani Co.'],
    'Cafe':          ['Urban Brew','Bean Cafe','Coffee Corner','Brewed Awakening',
                      'The Coffee Spot','Daily Grind Cafe','Cafe Aroma'],
    'Bakery':        ['Sweet Crumbs','Oven Fresh','Daily Bread','Golden Crust Bakery',
                      'Sugar Oven',"Baker's Delight",'Crust & Crumbs'],
    'Desserts':      ['Dessert Haven','Sugar Bliss','Sweet Tooth','Frosted Delights',
                      'Heavenly Sweets','Creamy Treats','Velvet Desserts'],
    'Street Food':   ['Chaat Junction','Mumbai Tiffin','Delhi Street Bites','Spice Street',
                      'Tasty Chaat Corner','Desi Street Kitchen','Bazaar Bites'],
    'Healthy':       ['Green Bowl','Fit Kitchen','Fresh Fuel','Nutri Bites',
                      'Clean Plate Kitchen','Vital Greens','Wholesome Bowl'],
    'Continental':   ['Bistro Central','Urban Plate','The Continental Kitchen','Grand Bistro',
                      'Classic Table','The European Kitchen','Gourmet Avenue'],
}

CUISINE_DEMAND = {
    'Fast Food': 0.14, 'Biryani': 0.14, 'North Indian': 0.13, 'Street Food': 0.11,
    'Chinese': 0.10,   'South Indian': 0.09, 'Cafe': 0.07,  'Italian': 0.06,
    'Desserts': 0.05,  'Bakery': 0.04,  'Healthy': 0.04, 'Continental': 0.03,
}

CUISINE_PREP = {
    'Fast Food': (10,15), 'Cafe': (5,10), 'Bakery': (8,12), 'Desserts': (8,12),
    'Street Food': (10,18), 'South Indian': (12,20), 'Chinese': (15,22),
    'Italian': (15,25), 'North Indian': (15,25), 'Healthy': (12,20),
    'Biryani': (20,30), 'Continental': (18,28),
}

# customer behavioral segments drive ordering time and cuisine preference
SEGMENTS        = ['office_lunch','weekend_treat','late_night','family_dinner','occasional']
SEGMENT_WEIGHTS = [0.25, 0.20, 0.15, 0.25, 0.15]

SEGMENT_CUISINE_PREF = {
    'office_lunch':  ['Fast Food','Cafe','South Indian','Healthy','Street Food'],
    'weekend_treat': ['Biryani','North Indian','Chinese','Continental','Italian'],
    'late_night':    ['Fast Food','Desserts','Street Food','Biryani','Chinese'],
    'family_dinner': ['North Indian','Biryani','Chinese','South Indian','Italian'],
    'occasional':    list(CUISINE_NAMES.keys()),
}

def segment_order_value(segment):
    if segment == 'office_lunch':  return np.random.uniform(150, 400)
    if segment == 'weekend_treat': return np.random.uniform(400, 900)
    if segment == 'late_night':    return np.random.uniform(200, 500)
    if segment == 'family_dinner': return np.random.uniform(450, 1200)
    return np.random.uniform(200, 700)

def _hour_weights(segment, dow):
    is_weekend = dow >= 4

    if segment == 'office_lunch':
        if not is_weekend:
            w = [0.2] * 24
            for h in [9, 10]:    w[h] = 1.0
            for h in [12, 13]:   w[h] = 8.0
            w[14] = 4.0
            for h in [18,19,20]: w[h] = 1.0
        else:
            w = [0.3] * 24
            for h in [12,13,14]: w[h] = 3.0
            for h in [19, 20]:   w[h] = 2.0

    elif segment == 'weekend_treat':
        if is_weekend:
            w = [0.2] * 24
            for h in [13, 14]:      w[h] = 3.0
            for h in [19,20,21,22]: w[h] = 5.0
        else:
            w = [0.3] * 24
            for h in [19,20,21]: w[h] = 4.0
            for h in [12, 13]:   w[h] = 2.0

    elif segment == 'late_night':
        if dow in [4, 5]:
            w = [0.5] * 24
            for h in [22, 23]: w[h] = 8.0
            w[0] = 6.0; w[1] = 4.0
            for h in [20, 21]: w[h] = 3.0
        else:
            w = [0.4] * 24
            for h in [22, 23]: w[h] = 5.0
            w[0] = 3.0; w[1] = 2.0
            for h in [19,20,21]: w[h] = 2.0

    elif segment == 'family_dinner':
        w = [0.2] * 24
        for h in [19,20,21]: w[h] = 8.0
        w[18] = 3.0; w[22] = 2.0
        for h in [12, 13]:   w[h] = 1.5

    else:
        w = [0.3] * 24
        for h in range(2, 8):  w[h] = 0.1
        for h in [12, 13]:     w[h] = 2.0
        for h in [19,20,21]:   w[h] = 3.0

    return w

def segment_order_time(segment, date):
    dow     = date.weekday()
    weights = _hour_weights(segment, dow)
    total   = sum(weights)
    probs   = [ww / total for ww in weights]
    hour    = np.random.choice(range(24), p=probs)
    minute  = random.randint(0, 59)
    second  = random.randint(0, 59)
    return f"{hour:02d}:{minute:02d}:{second:02d}"

PAYMENT_METHODS = ['UPI','Debit Card','Credit Card','Cash on Delivery','Wallet']
PAYMENT_WEIGHTS = [0.53, 0.17, 0.13, 0.10, 0.07]

LOYALTY_TIERS   = ['Bronze','Silver','Gold','Platinum']
LOYALTY_WEIGHTS = [0.57, 0.21, 0.14, 0.08]

def orders_per_year(tier, segment):
    if segment == 'occasional':
        return random.randint(1, 4)
    base = {'Bronze': (3,12), 'Silver': (10,22), 'Gold': (22,45), 'Platinum': (40,90)}
    lo, hi = base[tier]
    return random.randint(lo, hi)

# weekend gets higher order volume
DOW_WEIGHTS = {0: 0.10, 1: 0.11, 2: 0.12, 3: 0.12, 4: 0.16, 5: 0.20, 6: 0.19}


print("Generating customers...")

def generate_signup_date(start, total_days):
    # most customers signed up before the analysis window starts
    roll = random.random()
    if roll < 0.70:
        days_before = random.randint(365, 365 * 3)
        return start - timedelta(days=days_before)
    elif roll < 0.90:
        days_before = random.randint(1, 180)
        return start - timedelta(days=days_before)
    else:
        return start + timedelta(days=random.randint(0, total_days - 30))

customers         = []
customer_segments = []

for i in range(N_CUSTOMERS):
    city    = random.choices(CITIES, weights=CITY_WEIGHTS)[0]
    signup  = generate_signup_date(START_DATE, TOTAL_DAYS)
    tier    = random.choices(LOYALTY_TIERS, weights=LOYALTY_WEIGHTS)[0]
    segment = random.choices(SEGMENTS, weights=SEGMENT_WEIGHTS)[0]
    payment = random.choices(PAYMENT_METHODS, weights=PAYMENT_WEIGHTS)[0]
    avg_val = segment_order_value(segment)

    customers.append({
        'customer_id':              f'CUST{i+1:05d}',
        'customer_name':            fake.name(),
        'city':                     city,
        'signup_date':              signup.date(),
        'loyalty_tier':             tier,
        'avg_order_value':          round(avg_val, 2),
        'preferred_payment_method': payment,
    })
    customer_segments.append(segment)

df_customers = pd.DataFrame(customers)
df_customers.to_csv('customers.csv', index=False)
print(f"  customers.csv -> {len(df_customers)} rows")


print("Generating restaurants...")

cuisines_pool = list(CUISINE_DEMAND.keys())
cuisine_w     = list(CUISINE_DEMAND.values())
price_cats    = ['Budget','Mid-range','Premium']
price_weights = [0.40, 0.40, 0.20]

used_names  = {c: [] for c in cuisines_pool}
restaurants = []

for i in range(N_RESTAURANTS):
    cuisine = random.choices(cuisines_pool, weights=cuisine_w)[0]
    city    = random.choices(CITIES, weights=CITY_WEIGHTS)[0]

    name_pool       = CUISINE_NAMES[cuisine]
    base_name       = random.choice(name_pool)
    count           = used_names[cuisine].count(base_name)
    # append city name if the restaurant name is already used
    restaurant_name = base_name if count == 0 else f"{base_name} {city}"
    used_names[cuisine].append(base_name)

    lo, hi    = CUISINE_PREP[cuisine]
    prep_time = random.randint(lo, hi)
    rating    = round(np.random.beta(7, 3) * 1.9 + 3.0, 1)
    rating    = min(4.9, max(3.0, rating))
    price_cat = random.choices(price_cats, weights=price_weights)[0]

    restaurants.append({
        'restaurant_id':         f'REST{i+1:04d}',
        'restaurant_name':       restaurant_name,
        'city':                  city,
        'cuisine':               cuisine,
        'avg_prep_time_minutes': prep_time,
        'rating':                rating,
        'price_category':        price_cat,
    })

df_restaurants = pd.DataFrame(restaurants)
df_restaurants.to_csv('restaurants.csv', index=False)
print(f"  restaurants.csv -> {len(df_restaurants)} rows")


print("Generating delivery partners...")

delivery_partners = []
for i in range(N_DELIVERY_PARTNERS):
    city      = random.choices(CITIES, weights=CITY_WEIGHTS)[0]
    vehicle   = random.choices(['Bike','Scooter'], weights=[0.88, 0.12])[0]
    exp_years = round(min(np.random.exponential(scale=1.8), 10.0), 1)
    # more experienced partners tend to have slightly higher ratings
    base_r    = 3.5 + (exp_years / 10) * 1.0
    rating    = round(min(5.0, max(2.5, np.random.normal(base_r, 0.3))), 1)
    join      = START_DATE + timedelta(days=random.randint(0, TOTAL_DAYS - 10))

    delivery_partners.append({
        'partner_id':       f'PART{i+1:05d}',
        'partner_name':     fake.name(),
        'city':             city,
        'experience_years': exp_years,
        'vehicle_type':     vehicle,
        'join_date':        join.date(),
        'avg_rating':       rating,
    })

df_partners = pd.DataFrame(delivery_partners)
df_partners.to_csv('delivery_partners.csv', index=False)
print(f"  delivery_partners.csv -> {len(df_partners)} rows")


def weighted_date():
    for _ in range(300):
        d   = START_DATE + timedelta(days=random.randint(0, TOTAL_DAYS - 1))
        dow = d.weekday()

        # linear growth factor: order volume increases ~40% from Jan 2023 to Dec 2024
        days_elapsed  = (d - START_DATE).days
        growth_factor = 1.0 + 0.40 * (days_elapsed / TOTAL_DAYS)

        w  = DOW_WEIGHTS[dow]
        w *= SPIKE_DATES.get(d, 1.0)
        w *= growth_factor
        if d in RAINY_DAYS:
            w *= 1.10

        if random.random() < w / 2.2:
            return d

    return START_DATE + timedelta(days=random.randint(0, TOTAL_DAYS - 1))

def is_peak_hour(time_str):
    hour = int(time_str.split(':')[0])
    return (12 <= hour <= 14) or (19 <= hour <= 22)


print("Generating orders...")

rest_by_city    = {}
partner_by_city = {}
for _, r in df_restaurants.iterrows():
    rest_by_city.setdefault(r['city'], []).append(r)
for _, p in df_partners.iterrows():
    partner_by_city.setdefault(p['city'], []).append(p)

# scale per-customer order counts to hit exactly N_ORDERS total
cust_order_counts = []
for idx, row in df_customers.iterrows():
    seg  = customer_segments[idx]
    tier = row['loyalty_tier']
    n    = orders_per_year(tier, seg) * 2
    cust_order_counts.append(n)

total_raw = sum(cust_order_counts)
scale     = N_ORDERS / total_raw
cust_order_counts = [max(1, round(c * scale)) for c in cust_order_counts]

diff = N_ORDERS - sum(cust_order_counts)
idxs = random.sample(range(N_CUSTOMERS), abs(diff))
for idx in idxs:
    cust_order_counts[idx] += 1 if diff > 0 else -1
    cust_order_counts[idx]  = max(0, cust_order_counts[idx])

STATUS_CHOICES = ['Delivered','Cancelled','Failed']
STATUS_WEIGHTS = [0.92, 0.06, 0.02]

orders       = []
order_meta   = []
order_id_ctr = 1

for cust_idx, row in df_customers.iterrows():
    cust_id       = row['customer_id']
    city          = row['city']
    segment       = customer_segments[cust_idx]
    pref_pay      = row['preferred_payment_method']
    n_orders      = cust_order_counts[cust_idx]
    city_rests    = rest_by_city.get(city, list(df_restaurants.sample(3).itertuples()))
    pref_cuisines = SEGMENT_CUISINE_PREF[segment]

    for _ in range(n_orders):
        order_date     = weighted_date()
        order_time_str = segment_order_time(segment, order_date)

        # 70% of the time customer picks from their preferred cuisine list
        if random.random() < 0.70:
            filtered = [r for r in city_rests if r['cuisine'] in pref_cuisines]
        else:
            filtered = city_rests
        if not filtered:
            filtered = city_rests

        # weight restaurant selection by rating
        ratings  = np.array([r['rating'] for r in filtered])
        weights  = ratings / ratings.sum()
        rest_row = random.choices(filtered, weights=weights)[0]

        rest_id   = rest_row['restaurant_id']
        cuisine   = rest_row['cuisine']
        prep_time = rest_row['avg_prep_time_minutes']
        price_cat = rest_row['price_category']

        base_val = segment_order_value(segment)
        if price_cat == 'Budget':
            base_val *= random.uniform(0.75, 0.95)
        elif price_cat == 'Premium':
            base_val *= random.uniform(1.10, 1.40)
        base_val *= SPIKE_DATES.get(order_date, 1.0) * random.uniform(0.97, 1.03)
        if order_date in RAINY_DAYS and cuisine in ['Biryani','Fast Food','North Indian']:
            base_val *= random.uniform(1.05, 1.15)
        order_val = round(max(150, min(1200, base_val)), 2)

        payment = pref_pay if random.random() < 0.70 else random.choices(
            PAYMENT_METHODS, weights=PAYMENT_WEIGHTS)[0]

        sw = list(STATUS_WEIGHTS)
        if order_date in RAINY_DAYS:
            sw[1] += 0.02; sw[0] -= 0.02
        status = random.choices(STATUS_CHOICES, weights=sw)[0]

        order_id_str = f'ORD{order_id_ctr:07d}'
        order_id_ctr += 1

        orders.append({
            'order_id':       order_id_str,
            'customer_id':    cust_id,
            'restaurant_id':  rest_id,
            'order_date':     order_date.date(),
            'order_time':     order_time_str,
            'order_value':    order_val,
            'payment_method': payment,
            'order_status':   status,
        })
        order_meta.append({
            'order_id':   order_id_str,
            'city':       city,
            'status':     status,
            'prep_time':  prep_time,
            'order_date': order_date,
            'order_time': order_time_str,
        })

orders     = orders[:N_ORDERS]
order_meta = order_meta[:N_ORDERS]

df_orders = pd.DataFrame(orders)
df_orders.to_csv('orders.csv', index=False)
print(f"  orders.csv -> {len(df_orders)} rows")


print("Generating deliveries...")

DIST_RANGES  = [(0.5,2),(2,5),(5,8),(8,12),(12,15)]
DIST_WEIGHTS = [0.37, 0.33, 0.18, 0.09, 0.03]

def sample_distance():
    bucket = random.choices(DIST_RANGES, weights=DIST_WEIGHTS)[0]
    return round(random.uniform(*bucket), 2)

partner_lookup = {}
for _, p in df_partners.iterrows():
    partner_lookup.setdefault(p['city'], []).append(p)

deliveries = []
for meta in order_meta:
    order_id   = meta['order_id']
    city       = meta['city']
    status     = meta['status']
    prep_time  = meta['prep_time']
    order_date = meta['order_date']
    time_str   = meta['order_time']

    city_parts = partner_lookup.get(city, list(df_partners.sample(1).to_dict('records')))
    partner    = random.choice(city_parts)
    partner_id = partner['partner_id'] if isinstance(partner, dict) else partner.partner_id
    vehicle    = partner['vehicle_type'] if isinstance(partner, dict) else partner.vehicle_type
    exp_years  = partner['experience_years'] if isinstance(partner, dict) else partner.experience_years

    distance   = sample_distance()
    base_speed = 25 if vehicle == 'Bike' else 28
    speed      = base_speed + exp_years * 0.3 + random.uniform(-2, 2)
    travel_min = (distance / speed) * 60

    # peak hours and rain both slow down delivery
    traffic_mult = random.uniform(1.20, 1.40) if is_peak_hour(time_str) else random.uniform(1.00, 1.10)
    if order_date in RAINY_DAYS:
        traffic_mult *= random.uniform(1.05, 1.15)

    prep_var      = prep_time * random.uniform(0.85, 1.25)
    delivery_time = round(prep_var + travel_min * traffic_mult + random.uniform(0, 5), 1)
    delivery_time = max(10, min(90, delivery_time))

    if status == 'Delivered':
        base_r = random.uniform(3.5, 5.0)
        # longer deliveries tend to get lower ratings
        if delivery_time > 45: base_r -= random.uniform(0.3, 0.8)
        if delivery_time > 60: base_r -= random.uniform(0.2, 0.5)
        delivery_rating   = round(max(1.0, min(5.0, base_r + random.uniform(-0.3, 0.3))), 1)
        restaurant_rating = round(max(1.0, min(5.0, random.uniform(3.2, 5.0) + random.uniform(-0.2, 0.2))), 1)
    else:
        delivery_rating   = None
        restaurant_rating = None

    deliveries.append({
        'delivery_id':           f'DEL{len(deliveries)+1:07d}',
        'order_id':              order_id,
        'partner_id':            partner_id,
        'distance_km':           distance,
        'delivery_time_minutes': delivery_time,
        'delivery_rating':       delivery_rating,
        'restaurant_rating':     restaurant_rating,
    })

df_deliveries = pd.DataFrame(deliveries)
df_deliveries.to_csv('deliveries.csv', index=False)
print(f"  deliveries.csv -> {len(df_deliveries)} rows")

print("\nDone.")
print(f"  customers.csv         : {len(df_customers):,} rows")
print(f"  restaurants.csv       : {len(df_restaurants):,} rows")
print(f"  delivery_partners.csv : {len(df_partners):,} rows")
print(f"  orders.csv            : {len(df_orders):,} rows")
print(f"  deliveries.csv        : {len(df_deliveries):,} rows")
