#!/usr/bin/env python3
import requests
import pandas as pd

# ── CONFIG ────────────────────────────────────────────────────────────────
WP_DOMAIN    = "forcerentacar.com.tr"               # your site
WP_USER      = "yasem"                              # WordPress username
APP_PASSWORD = "EFXS VCoN g5oS yEgs PeDZ OvXr"      # application-password
OUTPUT_FILE  = "dispcost_export.xlsx"

def normalize_domain(d):
    return d.replace("https://", "").replace("http://", "").rstrip("/")

def get_cars():
    """GET /wp-json/vikrentcar/v1/cars → list of {idcar,name}"""
    base = normalize_domain(WP_DOMAIN)
    url  = f"https://{base}/wp-json/vikrentcar/v1/cars"
    resp = requests.get(url, auth=(WP_USER, APP_PASSWORD), timeout=10)
    resp.raise_for_status()
    return resp.json()

def get_tariffs(car_id):
    """GET /wp-json/vikrentcar/v1/tariffs?car_id={car_id} → list of {day,cost}"""
    base = normalize_domain(WP_DOMAIN)
    url  = f"https://{base}/wp-json/vikrentcar/v1/tariffs"
    resp = requests.get(url,
                        auth=(WP_USER, APP_PASSWORD),
                        params={"car_id": car_id},
                        timeout=10)
    resp.raise_for_status()
    return resp.json()

def main():
    all_rows = []
    for car in get_cars():
        cid  = int(car["idcar"])
        name = car["name"]
        for entry in get_tariffs(cid):
            # cast to proper types
            day  = int(entry["day"])
            cost = float(entry["cost"])
            all_rows.append({
                "car_id":   cid,
                "car_name": name,
                "day":      day,
                "cost":     cost,
            })

    # build DataFrame and export to Excel
    df = pd.DataFrame(all_rows)
    # optional: sort by car_id, day
    df = df.sort_values(["car_id", "day"])
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"Exported {len(df)} rows to {OUTPUT_FILE!r}")

if __name__ == "__main__":
    main()
