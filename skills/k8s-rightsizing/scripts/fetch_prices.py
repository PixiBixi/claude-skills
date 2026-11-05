#!/usr/bin/env python3
"""GCE list price per node-hour for every instance type in a nodes snapshot.

Uses the Cloud Billing Catalog API (list price, USD, no CUD or negotiated
discount) and `gcloud compute machine-types describe` for vCPU and memory.
Spot nodes get the Spot SKU. GKE only: elsewhere, write prices.json by hand.

Usage: python3 fetch_prices.py nodes.json > prices.json
"""
import json
import subprocess
import sys
import urllib.parse
import urllib.request

COMPUTE_SERVICE = "6F81-5844-456A"


def gcloud(*args):
    return subprocess.run(["gcloud", *args], check=True, capture_output=True, text=True).stdout.strip()


def skus(region, token):
    out, page = [], ""
    while True:
        q = urllib.parse.urlencode({"pageSize": 5000, "pageToken": page})
        req = urllib.request.Request(f"https://cloudbilling.googleapis.com/v1/services/{COMPUTE_SERVICE}/skus?{q}",
                                     headers={"Authorization": f"Bearer {token}"})
        body = json.load(urllib.request.urlopen(req))
        out += [s for s in body["skus"] if region in s.get("serviceRegions", [])]
        page = body.get("nextPageToken")
        if not page:
            return out


def rate(skus_, family, part, spot):
    """Hourly USD for one vCPU ("Core") or one GiB ("Ram") of a machine family."""
    for s in skus_:
        d = s["description"]
        if not d.upper().startswith(("SPOT PREEMPTIBLE " if spot else "") + family.upper() + " "):
            continue
        if f"Instance {part}" not in d or any(x in d for x in ("Commit", "Custom", "Sole", "Reserved", "DWS")):
            continue
        unit = s["pricingInfo"][0]["pricingExpression"]["tieredRates"][-1]["unitPrice"]
        return int(unit["units"]) + unit["nanos"] / 1e9
    raise SystemExit(f"no {'spot ' if spot else ''}{family} {part} SKU found")


def main():
    nodes = json.load(open(sys.argv[1]))["items"]
    labels = [n["metadata"]["labels"] for n in nodes]
    region = labels[0]["topology.kubernetes.io/region"]
    catalog = skus(region, gcloud("auth", "print-access-token"))
    prices = {}
    for lab in labels:
        mtype = lab["node.kubernetes.io/instance-type"]
        spot = lab.get("cloud.google.com/gke-spot") == "true"
        key = mtype + (":spot" if spot else "")
        if key in prices:
            continue
        spec = json.loads(gcloud("compute", "machine-types", "describe", mtype,
                                 "--zone", lab["topology.kubernetes.io/zone"], "--format=json"))
        family = mtype.split("-")[0]
        prices[key] = round(spec["guestCpus"] * rate(catalog, family, "Core", spot)
                            + spec["memoryMb"] / 1024 * rate(catalog, family, "Ram", spot), 5)
    json.dump(prices, sys.stdout, indent=1, sort_keys=True)


if __name__ == "__main__":
    main()
