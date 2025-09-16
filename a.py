#!/usr/bin/python3
import sys
import os
import time
import json
import argparse
import requests

# Cache settings for the bgp.tools file
BGPT_CACHE_FILE = "bgp_tools_cache.jsonl"
BGPT_CACHE_EXPIRATION = 86400  # seconds (24 hours)

def get_bgptools_lines():
    """
    Returns the lines from the cached bgp.tools JSONL file.
    If the file does not exist or is older than BGPT_CACHE_EXPIRATION,
    it is re-downloaded.
    """
    url = "https://bgp.tools/table.jsonl"
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/100 Safari/537.36")
    }
    # If cache exists and is fresh, use it.
    if os.path.exists(BGPT_CACHE_FILE):
        mod_time = os.path.getmtime(BGPT_CACHE_FILE)
        if time.time() - mod_time < BGPT_CACHE_EXPIRATION:
            try:
                with open(BGPT_CACHE_FILE, "r", encoding="utf-8") as f:
                    return f.readlines()
            except Exception as e:
                print(f"Error reading cache file: {e}")
    # Otherwise, download a fresh copy.
    try:
        print("Downloading fresh bgp.tools data (this may take a moment)...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        content = response.text
        with open(BGPT_CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        return content.splitlines()
    except Exception as e:
        if os.path.exists(BGPT_CACHE_FILE):
            try:
                with open(BGPT_CACHE_FILE, "r", encoding="utf-8") as f:
                    return f.readlines()
            except Exception as e:
                print(f"Error reading fallback cache file: {e}")
        print(f"Error fetching bgp.tools data: {e}")
        return []

def normalize_asn(asn):
    """
    Ensures the ASN is in the proper format (e.g. "AS62419").
    """
    asn = asn.strip().upper()
    if not asn.startswith("AS"):
        asn = "AS" + asn
    return asn

def fetch_prefixes_bgpview(asn):
    """
    Fetch IP prefixes for the given ASN from the BGPView API.
    """
    url = f"https://api.bgpview.io/asn/{asn}/prefixes"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching data from BGPView for {asn}: {e}")
        return []
    
    data = response.json()
    if data.get("status") != "ok":
        print(f"BGPView API error for {asn}: {data}")
        return []
    
    prefixes = []
    for entry in data.get("data", {}).get("ipv4_prefixes", []):
        if "prefix" in entry:
            prefixes.append(entry["prefix"])
    for entry in data.get("data", {}).get("ipv6_prefixes", []):
        if "prefix" in entry:
            prefixes.append(entry["prefix"])
    return prefixes

def fetch_prefixes_ripe(asn):
    """
    Fetch IP prefixes for the given ASN from the RIPEstat API.
    """
    url = f"https://stat.ripe.net/data/announced-prefixes/data.json?resource={asn}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching data from RIPEstat for {asn}: {e}")
        return []
    
    data = response.json()
    if data.get("status") != "ok":
        print(f"RIPEstat API error for {asn}: {data}")
        return []
    
    prefixes = []
    for entry in data.get("data", {}).get("prefixes", []):
        if "prefix" in entry:
            prefixes.append(entry["prefix"])
    return prefixes

def fetch_prefixes_bgptools(asn):
    """
    Fetch IP prefixes for the given ASN from the bgp.tools JSONL data.
    """
    try:
        numeric_asn = int(asn[2:]) if asn.startswith("AS") else int(asn)
    except ValueError:
        print(f"Invalid ASN format: {asn}")
        return []
    
    lines = get_bgptools_lines()
    prefixes = []
    for line in lines:
        if line:
            try:
                entry = json.loads(line)
                if entry.get("ASN") == numeric_asn:
                    cidr = entry.get("CIDR")
                    if cidr:
                        prefixes.append(cidr)
            except Exception:
                continue
    return prefixes

def process_asn(asn):
    """
    Process a single ASN: fetch prefixes from all sources and return the
    combined unique prefixes as a sorted list.
    """
    combined_prefixes = set()
    
    print(f"Fetching from BGPView for {asn}...")
    prefixes_bgpview = fetch_prefixes_bgpview(asn)
    if prefixes_bgpview:
        print("BGPView results:")
        for prefix in prefixes_bgpview:
            print("  " + prefix)
            combined_prefixes.add(prefix)
    else:
        print("No results from BGPView.")

    print(f"\nFetching from RIPEstat for {asn}...")
    prefixes_ripe = fetch_prefixes_ripe(asn)
    if prefixes_ripe:
        print("RIPEstat results:")
        for prefix in prefixes_ripe:
            print("  " + prefix)
            combined_prefixes.add(prefix)
    else:
        print("No results from RIPEstat.")

    print(f"\nFetching from bgp.tools for {asn} (using cached data if available)...")
    prefixes_bgptools = fetch_prefixes_bgptools(asn)
    if prefixes_bgptools:
        print("bgp.tools results:")
        for prefix in prefixes_bgptools:
            print("  " + prefix)
            combined_prefixes.add(prefix)
    else:
        print("No results from bgp.tools.")

    sorted_prefixes = sorted(combined_prefixes)
    print(f"\nCombined unique IP ranges for {asn}:")
    for prefix in sorted_prefixes:
        print("  " + prefix)
    return sorted_prefixes

def main():
    parser = argparse.ArgumentParser(
        description="Fetch IP ranges for given ASNs from multiple sources and output combined results."
    )
    parser.add_argument("asns", nargs="+", help="List of ASNs (e.g. AS62419)")
    parser.add_argument("-d", "--dest", default=".", help="Destination folder for output TXT files (default: current directory)")
    args = parser.parse_args()

    # Ensure destination folder exists; if not, create it.
    dest_folder = args.dest
    if not os.path.isdir(dest_folder):
        try:
            os.makedirs(dest_folder)
            print(f"Created destination folder: {dest_folder}")
        except Exception as e:
            print(f"Error creating destination folder '{dest_folder}': {e}")
            sys.exit(1)

    # Process each ASN
    for asn_input in args.asns:
        asn = normalize_asn(asn_input)
        print(f"\nProcessing {asn}...")
        combined_prefixes = process_asn(asn)

        # Write only the combined unique prefixes (one per line) to the output file.
        output_filename = os.path.join(dest_folder, f"{asn}.txt")
        try:
            with open(output_filename, "w", encoding="utf-8") as f:
                for prefix in combined_prefixes:
                    f.write(prefix + "\n")
            print(f"Output written to {output_filename}\n")
        except Exception as e:
            print(f"Error writing {asn} to file: {e}")

if __name__ == "__main__":
    main()

