"""
IRISCC utility functions for IAGOS flight search, download and CO analysis.

All functions use fixed IRISCC parameters:
    - type = "profiles" (vertical measurements during ascent/descent)
    - originCO = "fire" (CO from biomass burning)
"""

import io
import re
import zipfile
from datetime import datetime
from pathlib import Path

import numpy as np
import requests
import xarray as xr


def search_flights(base_url, auth_headers, start, end, bbox, level="L1", region=None, airport=None, l4_type=None):
    """
    Search for IAGOS flights with CO fire contribution (profiles).

    Parameters:
        base_url (str): API base URL (e.g. "https://services.iagos-data.fr/prod/v2.0/downloads")
        auth_headers (dict): Authentication headers
        start (str): Start date in ISO 8601 format (yyyy-MM-ddTHH:mm:ss)
        end (str): End date in ISO 8601 format (yyyy-MM-ddTHH:mm:ss)
        bbox (str): Bounding box as "minLon,minLat,maxLon,maxLat"
        level (str): Data level ("L1", "L2" or "L4")
        region (list, optional): List of region codes (e.g., ["BONA", "EURO"])
        airport (list, optional): List of 3-letter airport codes (e.g., ["FRA", "CDG"])
        l4_type (list, optional): L4 file types (e.g., ["ECMWF", "CO_CONTRIBUTIONS"])

    Returns:
        dict: Search result with 'count' and 'totalSize', or None if error
    """
    params = {
        "start": start,
        "end": end,
        "bbox": bbox,
        "level": level,
        "type": "profiles",
        "originCO": "fire"
    }
    if region:
        params["region"] = region
    if airport:
        params["airport"] = airport
    if l4_type:
        params["l4Type"] = l4_type

    response = requests.get(f"{base_url}/search", params=params, headers=auth_headers)

    if response.status_code != 200:
        print(f"Error during search: {response.text}")
        return None

    result = response.json()
    print(f"Found {result['count']} flights")
    print(f"Total size: {result['totalSize']}")

    return result


def download_flights(base_url, auth_headers, start, end, bbox, level="L1", region=None, airport=None, l4_type=None, output_dir="../downloads"):
    """
    Search and download IAGOS flights with CO fire contribution (profiles).

    If the file already exists in the output directory, the download is skipped.

    Parameters:
        base_url (str): API base URL (e.g. "https://services.iagos-data.fr/prod/v2.0/downloads")
        auth_headers (dict): Authentication headers
        start (str): Start date in ISO 8601 format (yyyy-MM-ddTHH:mm:ss)
        end (str): End date in ISO 8601 format (yyyy-MM-ddTHH:mm:ss)
        bbox (str): Bounding box as "minLon,minLat,maxLon,maxLat"
        level (str): Data level ("L1", "L2" or "L4")
        region (list, optional): List of region codes (e.g., ["BONA", "EURO"])
        airport (list, optional): List of 3-letter airport codes (e.g., ["FRA", "CDG"])
        l4_type (list, optional): L4 file types (e.g., ["ECMWF", "CO_CONTRIBUTIONS"])
        output_dir (str): Directory where ZIP file will be saved

    Returns:
        Path: Path to downloaded ZIP file, or None if error
    """
    params = {
        "start": start,
        "end": end,
        "bbox": bbox,
        "level": level,
        "type": "profiles",
        "originCO": "fire"
    }
    if region:
        params["region"] = region
    if airport:
        params["airport"] = airport
    if l4_type:
        params["l4Type"] = l4_type

    # Check if file already exists (predict filename to avoid unnecessary download)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    start_date = start[:10]
    end_date = end[:10]
    expected_filename = f"iagos_{level}_profiles_{start_date}_to_{end_date}_fire"
    if l4_type:
        expected_filename += "_" + "_".join(l4_type)
    expected_filename += ".zip"

    zip_path = output_path / expected_filename
    if zip_path.exists():
        print(f"File already exists, skipping download: {zip_path}")
        return zip_path

    # Search to validate the request
    print("Searching...")
    search_response = requests.get(f"{base_url}/search", params=params, headers=auth_headers)

    if search_response.status_code != 200:
        print(f"Error during search: {search_response.text}")
        return None

    search_result = search_response.json()
    print(f"Found {search_result['count']} flights")
    print(f"Total size: {search_result['totalSize']}")

    if search_result['count'] == 0:
        print("No flights found")
        return None

    # Download the files
    print("\nDownloading...")
    download_response = requests.get(f"{base_url}/download-flights", params=params, headers=auth_headers)

    if download_response.status_code != 200:
        print(f"Error during download: {download_response.text}")
        return None

    # Determine the filename from Content-Disposition header
    content_disposition = download_response.headers.get('Content-Disposition', '')
    if 'filename=' in content_disposition:
        filename = content_disposition.split('filename=')[1].strip('"')
    else:
        filename = expected_filename

    zip_path = output_path / filename

    # Save the file
    content = download_response.content

    with open(zip_path, 'wb') as f:
        f.write(content)

    print(f"Download complete: {zip_path}")
    print(f"File size: {len(content) / 1024 / 1024:.2f} MB")

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        print(f"Number of files in ZIP: {len(zip_ref.namelist())}")

    return zip_path


def parse_size_to_bytes(size_str):
    """
    Convert a size string (e.g., "500.5MB", "1.2GB") to bytes.

    Parameters:
        size_str (str): Size string with unit (e.g., "500MB", "1.2GB")

    Returns:
        int: Size in bytes
    """
    try:
        size_str = size_str.strip().upper()

        if size_str.endswith("B") and not any(size_str.endswith(unit) for unit in ["KB", "MB", "GB", "TB"]):
            return int(float(size_str[:-1].replace(',', '.')))

        if size_str.endswith("KB"):
            value = float(size_str[:-2].replace(',', '.'))
            return int(value * 1024)
        elif size_str.endswith("MB"):
            value = float(size_str[:-2].replace(',', '.'))
            return int(value * 1024 * 1024)
        elif size_str.endswith("GB"):
            value = float(size_str[:-2].replace(',', '.'))
            return int(value * 1024 * 1024 * 1024)
        elif size_str.endswith("TB"):
            value = float(size_str[:-2].replace(',', '.'))
            return int(value * 1024 * 1024 * 1024 * 1024)
        else:
            return int(float(size_str.replace(',', '.')))
    except (ValueError, IndexError) as e:
        print(f"Warning: Could not parse size string '{size_str}': {e}")
        return 0


def split_large_dataset(base_url, auth_headers, start, end, bbox, level, region=None, airport=None, l4_type=None, max_size_bytes=1_000_000_000):
    """
    Recursively split a date range into periods under the size limit (default 1GB).

    Parameters:
        base_url (str): API base URL
        auth_headers (dict): Authentication headers
        start (str): Start date in ISO 8601 format
        end (str): End date in ISO 8601 format
        bbox (str): Bounding box as "minLon,minLat,maxLon,maxLat"
        level (str): Data level ("L1", "L2" or "L4")
        region (list, optional): List of region codes
        airport (list, optional): List of 3-letter airport codes (e.g., ["FRA", "CDG"])
        l4_type (list, optional): L4 file types (e.g., ["ECMWF", "CO_CONTRIBUTIONS"])
        max_size_bytes (int): Maximum size in bytes (default: 1GB)

    Returns:
        list: List of period dictionaries with "start", "end", "count", "size"
    """
    params = {
        "start": start,
        "end": end,
        "bbox": bbox,
        "level": level,
        "type": "profiles",
        "originCO": "fire"
    }
    if region:
        params["region"] = region
    if airport:
        params["airport"] = airport
    if l4_type:
        params["l4Type"] = l4_type

    response = requests.get(f"{base_url}/search", params=params, headers=auth_headers)

    if response.status_code != 200:
        print(f"Error searching period {start} to {end}: {response.text}")
        return []

    result = response.json()
    count = result.get('count', 0)
    total_size = result.get('totalSize', '0B')
    size_bytes = parse_size_to_bytes(total_size)

    if count == 0:
        return []

    if size_bytes <= max_size_bytes:
        return [{"start": start, "end": end, "count": count, "size": total_size}]

    # Split the period in half
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)
    duration = end_dt - start_dt
    mid_dt = start_dt + duration / 2
    mid_str = mid_dt.strftime('%Y-%m-%dT%H:%M:%S')

    left_periods = split_large_dataset(base_url, auth_headers, start, mid_str, bbox, level, region, airport, l4_type, max_size_bytes)
    right_periods = split_large_dataset(base_url, auth_headers, mid_str, end, bbox, level, region, airport, l4_type, max_size_bytes)

    return left_periods + right_periods


def _build_l2_index(zip_l2_path):
    """Index L2 files by (flight_id, phase) for O(1) lookup."""
    index = {}
    with zipfile.ZipFile(zip_l2_path, 'r') as z2:
        for fname in z2.namelist():
            m = re.search(r'IAGOS_(?:profile|timeseries)_(\d+)_L2_[\d.]+-?(ascent|descent)?\.nc4', fname)
            if m:
                index[(m.group(1), m.group(2))] = fname
    return index


def _detect_species(ds):
    """Return a set of chemical species names present in a dataset."""
    species = set()
    for var in ds.data_vars:
        if var.startswith('O3_') or var == 'O3':
            species.add('O3')
        elif var.startswith('CO2_') or var == 'CO2':
            species.add('CO2')
        elif var.startswith('CH4_') or var == 'CH4':
            species.add('CH4')
        elif re.match(r'^NO[A-Za-z0-9]*(_|$)', var):
            m = re.match(r'^(NO[A-Za-z0-9]*?)(_|$)', var)
            if m:
                species.add(m.group(1))
    return species


def _extract_co_stats(ds, co_avail):
    """
    Compute CO statistics from a dataset.
    Returns (stats_dict, has_valid) where stats_dict contains max/mean/median/p25/p75/alt_max.
    """
    co_data = ds['CO_P1'].values.astype(float)
    valid = co_data[~np.isnan(co_data)]
    if len(valid) == 0:
        return None, False

    alt_max_co = 0.0
    if 'baro_alt_AC' in ds:
        alt_data = ds['baro_alt_AC'].values.astype(float)
        alt_max_co = float(alt_data[np.nanargmax(co_data)])

    return {
        'co_availability': co_avail,
        'max_co': float(np.max(valid)),
        'mean_co': float(np.mean(valid)),
        'median_co': float(np.median(valid)),
        'p25_co': float(np.percentile(valid, 25)),
        'p75_co': float(np.percentile(valid, 75)),
        'alt_max_co': alt_max_co,
    }, True


def _read_co_from_l2(z2, l2_fname, flight_id):
    """Try to extract CO stats from L2. Returns (stats, has_valid)."""
    try:
        with z2.open(l2_fname) as f:
            ds = xr.open_dataset(io.BytesIO(f.read()))
        try:
            if 'CO_P1' not in ds:
                return None, False
            co_avail = ds['CO_P1'].attrs.get('availability', None)
            if not co_avail:
                return None, False
            return _extract_co_stats(ds, co_avail)
        finally:
            ds.close()
    except Exception as e:
        print(f"  Error reading L2 for {flight_id}: {e}")
        return None, False


def _read_co_from_l1(ds_l1, l1_co_avail, l1_fname):
    """Extract CO stats from an already-open L1 dataset. Returns (stats, has_valid)."""
    try:
        return _extract_co_stats(ds_l1, l1_co_avail)
    except Exception as e:
        print(f"  Error reading CO from L1 {l1_fname}: {e}")
        return None, False


def _process_flight(z2, z1, l1_fname, flight_id, phase, l2_index):
    """
    Process a single L1 file and return a flight result dict, or None if no valid CO.
    Also returns the source label ("L1", "L2") and whether CO was found.
    Returns (result_dict_or_None, source_or_None).
    """
    try:
        with z1.open(l1_fname) as f:
            ds_l1 = xr.open_dataset(io.BytesIO(f.read()))
    except Exception as e:
        print(f"  Error opening L1 {l1_fname}: {e}")
        return None, None

    try:
        l1_co_avail = ds_l1['CO_P1'].attrs.get('availability', None) if 'CO_P1' in ds_l1 else None
        if not l1_co_avail:
            return None, None

        flight_key = (flight_id, phase)
        stats, source = None, None

        if flight_key in l2_index:
            stats, has_valid = _read_co_from_l2(z2, l2_index[flight_key], flight_id)
            if has_valid:
                source = "L2"

        if source is None:
            stats, has_valid = _read_co_from_l1(ds_l1, l1_co_avail, l1_fname)
            if has_valid:
                source = "L1"

        if source is None:
            return None, None

        return {
            'flight_id': flight_id,
            'phase': phase or 'N/A',
            'airport': ds_l1.attrs.get('airport', 'N/A'),
            **stats,
            'source': source,
            'l1_filename': l1_fname,
            'l2_filename': l2_index.get(flight_key),
            'other_species': ', '.join(sorted(_detect_species(ds_l1))),
        }, source
    finally:
        ds_l1.close()


def rank_flights_by_co(zip_l2_path, zip_l1_path):
    """
    Analyze flights for valid CO_P1 data. Iterates over L1 files (the complete set).
    For each flight, checks L2 first (preferred), falls back to L1.
    Also detects other available chemical species (O3, CO2, CH4, NO-family).
    Returns flights sorted by max CO (descending).

    All file reading is done in memory (no disk extraction).

    Parameters:
        zip_l2_path (Path): Path to the L2 ZIP file
        zip_l1_path (Path): Path to the L1 ZIP file

    Returns:
        list: List of dicts sorted by max_co descending, each containing:
              flight_id, phase, max_co, mean_co, median_co, p25_co, p75_co,
              airport, source ("L1" or "L2"), l1_filename, other_species
    """
    l2_index = _build_l2_index(zip_l2_path)
    print(f"L2 index built: {len(l2_index)} files indexed")

    results = []
    l2_with_co = l1_with_co = no_co = 0
    l1_pattern = re.compile(r'IAGOS_(?:profile|timeseries)_(\d+)_L1_[\d.]+-?(ascent|descent)?\.nc4')

    with zipfile.ZipFile(zip_l2_path, 'r') as z2, zipfile.ZipFile(zip_l1_path, 'r') as z1:
        l1_files = z1.namelist()
        total = len(l1_files)
        print(f"Analyzing {total} L1 files for CO data...\n")

        for idx, l1_fname in enumerate(l1_files):
            m = l1_pattern.search(l1_fname)
            if not m:
                continue

            result, source = _process_flight(z2, z1, l1_fname, m.group(1), m.group(2), l2_index)

            if result is None:
                no_co += 1
            elif source == "L2":
                results.append(result)
                l2_with_co += 1
            else:
                results.append(result)
                l1_with_co += 1

            if (idx + 1) % 100 == 0:
                print(f"  Processed {idx + 1}/{total} files...")

    results.sort(key=lambda x: x['max_co'], reverse=True)

    print("\nAnalysis complete:")
    print(f"  CO from L2 (validated): {l2_with_co}")
    print(f"  CO from L1 (raw): {l1_with_co}")
    print(f"  No CO data: {no_co}")
    print(f"  Total flights with CO: {len(results)}")

    return results
