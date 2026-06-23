# IRISCC - IAGOS CO Fire Contributions

Notebooks for searching and downloading IAGOS flight data focused on **CO (Carbon Monoxide) from fire sources** using profile data (vertical measurements during ascent/descent).

## IRISCC Parameters

Fixed parameters for all notebooks in this project:
- `originCO = "fire"` (CO from biomass burning)
- `type = "profiles"` (vertical measurements during ascent/descent)

Variable parameters: `start`, `end`, `bbox`, `level`, `region`

## Notebook

| Notebook | Description |
|----------|-------------|
| `flight_search_download_demo_IRISCC_v2.ipynb` | Dual L1+L2 download, CO ranking, species detection and top flight plotting |

## Prerequisites

- Conda or Mamba
- IAGOS/AERIS SSO credentials ([create here](https://iagos.aeris-data.fr/))

## Setup

### 1. Clone the repository and create the environment

```bash
conda env create -f environment.yml
conda activate iagos-iriscc
```

### 2. Set up authentication (first-time only)

IAGOS services require authentication via AERIS SSO.

```bash
python src/fr/aeris/auth/generate_credentials.py
```

This will:
1. Prompt for your IAGOS/AERIS email and password
2. Prompt for a master password (used to encrypt/decrypt)
3. Generate encrypted values to copy into your `.env` file

Optionally, set the master password as an environment variable to avoid being prompted each time:

```bash
export IAGOS_MASTER_PASSWORD="your_master_password"
# Add to ~/.bashrc or ~/.zshrc for persistence
```

### 3. Start Jupyter

```bash
jupyter notebook
```

Then open the notebook from `notebooks/`.

## Project Structure

```
iagos_vre/
├── environment.yml
├── pyproject.toml
├── README.md
├── images/
│   └── GFED-regions.png
├── src/fr/aeris/
│   ├── auth/                            # SSO authentication
│   │   └── generate_credentials.py      # Credential encryption helper
│   └── iriscc.py                        # Search, download & analysis functions
├── notebooks/
│   └── flight_search_download_demo_IRISCC_v2.ipynb
└── downloads/           # Downloaded data (git-ignored)
```

## Environment

The `environment.yml` creates a conda environment `iagos-iriscc` with:
- Data processing: xarray, netcdf4, pandas, numpy, pyarrow
- Visualization: matplotlib
- Authentication: python-keycloak, cryptography
- Shared code: `fr.aeris` package (installed via `pip -e .`)

## API Reference

**Production server**: `https://services.iagos-data.fr/prod/v2.0/downloads`

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/search` | GET | Required | Search for flights (returns count and total size) |
| `/download-flights` | GET | Required | Download flight data as ZIP (max 1 GB) |

### Parameters (IRISCC)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| start | string | Yes | Start date (ISO 8601) |
| end | string | Yes | End date (ISO 8601) |
| bbox | string | Yes | Bounding box: minLon,minLat,maxLon,maxLat |
| level | string | Yes | `L1`, `L2`, or `L4` |
| region | list | No | GFED region codes (e.g., `["BONA", "EURO"]`) |
| l4Type | list | No | `ECMWF`, `CO_CONTRIBUTIONS`, `PV` (L4 only) |

**Fixed**: `type = "profiles"`, `originCO = "fire"`

### GFED Regions

| Code | Region | Code | Region |
|------|--------|------|--------|
| AUST | Australia | MIDE | Middle East |
| BOAS | Boreal Asia | NHAF | N. Hemisphere Africa |
| BONA | Boreal North America | NHSA | N. Hemisphere South America |
| CEAM | Central America | SEAS | Southeast Asia |
| CEAS | Central Asia | SHAF | S. Hemisphere Africa |
| EQAS | Equatorial Asia | SHSA | S. Hemisphere South America |
| EURO | Europe | TENA | Temperate North America |

## Downloads

Downloaded data (ZIP/NC4 files) is stored in `downloads/` and ignored by git.

## Troubleshooting

### "No module named 'fr.aeris'"

```bash
pip install -e .  # From the repository root
```

### "Invalid master password" or decryption error

- Ensure the master password matches the one used during encryption
- Check: `echo $IAGOS_MASTER_PASSWORD`

### "401 Unauthorized" from API

- Tokens expire after 5 minutes - re-run the authentication cell
- Verify your AERIS credentials are valid

### TripleDES deprecation warning

Expected behavior due to Jasypt compatibility. The encryption still works correctly.
