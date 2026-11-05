#!/usr/bin/env python3
"""GCE list price and spec per machine type, for node_impact.py.

Covers every instance type in a nodes snapshot plus --shapes candidates (each
priced on-demand and spot). Uses the Cloud Billing Catalog API (list price,
USD, no CUD or negotiated discount) and `gcloud compute machine-types describe`.
GKE only: elsewhere, write prices.json by hand in the same shape.

Usage: python3 fetch_prices.py nodes.json [--shapes c4d-highmem-8,c4a-highmem-8] > prices.json
Output: {"<type>[:spot]": {"usd_h": 0.25, "vcpu": 4, "mem_gib": 31.0, "arch": "amd64"}}
"""
import argparse
import json
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

COMPUTE_SERVICE = "6F81-5844-456A"
ARM_FAMILIES = ("c4a", "t2a", "n4a", "a4x")


def gcloud(*args):
    return subprocess.run(["gcloud", *args], check=True, capture_output=True, text=True).stdout.strip()


def skus(region, token):
    out, page = [], ""
    while True:
        q = urllib.parse.urlencode({"pageSize": 5000, "pageToken": page})
        req = urllib.request.Request(f"https://cloudbilling.googleapis.com/v1/services/{COMPUTE_SERVICE}/skus?{q}",
                                     headers={"Authorization": f"Bearer {token}"})
        for attempt in range(6):
            try:
                body = json.load(urllib.request.urlopen(req))
                break
            except urllib.error.HTTPError as e:
                if e.code != 429 or attempt == 5:
                    raise
                time.sleep(2 ** attempt * 5)  # catalog API quota is per minute
        out += [s for s in body["skus"] if region in s.get("serviceRegions", [])]
        page = body.get("nextPageToken")
        if not page:
            return out


def rate(catalog, family, part, spot):
    """Hourly USD for one vCPU ("Core") or one GiB ("Ram") of a machine family."""
    for s in catalog:
        d = s["description"]
        if not d.upper().startswith(("SPOT PREEMPTIBLE " if spot else "") + family.upper() + " "):
            continue
        if f"Instance {part}" not in d or any(x in d for x in ("Commit", "Custom", "Sole", "Reserved", "DWS")):
            continue
        unit = s["pricingInfo"][0]["pricingExpression"]["tieredRates"][-1]["unitPrice"]
        return int(unit["units"]) + unit["nanos"] / 1e9
    raise SystemExit(f"no {'spot ' if spot else ''}{family} {part} SKU found")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nodes")
    ap.add_argument("--shapes", default="")
    a = ap.parse_args()

    labels = [n["metadata"]["labels"] for n in json.load(open(a.nodes))["items"]]
    region = labels[0]["topology.kubernetes.io/region"]
    zone = labels[0]["topology.kubernetes.io/zone"]
    wanted = {(lab["node.kubernetes.io/instance-type"], lab.get("cloud.google.com/gke-spot") == "true") for lab in labels}
    wanted |= {(s, spot) for s in a.shapes.split(",") if s for spot in (False, True)}

    catalog = skus(region, gcloud("auth", "print-access-token"))
    out = {}
    for mtype, spot in sorted(wanted):
        spec = json.loads(gcloud("compute", "machine-types", "describe", mtype, "--zone", zone, "--format=json"))
        family = mtype.split("-")[0]
        mem_gib = spec["memoryMb"] / 1024
        try:
            usd_h = spec["guestCpus"] * rate(catalog, family, "Core", spot) + mem_gib * rate(catalog, family, "Ram", spot)
        except SystemExit:
            continue
        out[mtype + (":spot" if spot else "")] = {
            "usd_h": round(usd_h, 5), "vcpu": spec["guestCpus"], "mem_gib": round(mem_gib, 2),
            "arch": "arm64" if family in ARM_FAMILIES else "amd64"}
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
