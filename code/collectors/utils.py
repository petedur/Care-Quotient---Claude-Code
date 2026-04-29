"""
Shared utilities for Census API collectors.
"""

import time
import requests


def census_get(url: str, params: dict, max_retries: int = 3) -> list:
    """
    GET a Census API endpoint with retries and exponential backoff.

    Retries on:
      - requests.Timeout
      - requests.ConnectionError
      - HTTP 5xx responses

    Raises the last exception if all retries are exhausted.
    """
    last_exc = None
    for attempt in range(max_retries):
        try:
            r = requests.get(url, params=params, timeout=45)
            if r.status_code >= 500:
                raise requests.HTTPError(f"Server error {r.status_code}", response=r)
            r.raise_for_status()
            return r.json()
        except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as exc:
            last_exc = exc
            if attempt < max_retries - 1:
                wait = 2 ** attempt  # 1s, 2s, 4s ...
                print(f"    Retry {attempt + 1}/{max_retries - 1} after {wait}s ({exc})")
                time.sleep(wait)
    raise last_exc


def census_get_zctas(
    url: str,
    variables: list,
    state_fips: str,
    city_zctas: set,
    api_key: str,
) -> list:
    """
    Query Census ACS for specific ZCTAs; return rows as a list of dicts
    {variable_code: int, "zcta": str}.

    Queries the city's ZCTAs directly by ID — the Census API does not support
    the `for=zcta:*&in=state:XX` pattern (returns 400 for most states). Querying
    by explicit ZCTA list is reliable and avoids that limitation.

    ZCTAs are batched in groups of 50 to stay within Census API URL length limits.

    Census suppression codes (negative integers like -666666666) are treated
    as 0 so they don't corrupt aggregated totals.

    Args:
        url:        Census ACS base URL
        variables:  List of variable codes, e.g. ["B07003_004E", "B01003_001E"]
        state_fips: 2-digit state FIPS string (unused; retained for API compatibility)
        city_zctas: Set of 5-digit ZIP strings defining the city
        api_key:    Census API key

    Returns:
        List of dicts, one per matching ZCTA. Each dict has "zcta" plus one key
        per variable with its integer value.
    """
    zcta_list = sorted(city_zctas)
    batch_size = 50
    zcta_col = "zip code tabulation area"
    results = []

    for i in range(0, len(zcta_list), batch_size):
        batch = zcta_list[i:i + batch_size]
        params = {
            "key": api_key,
            "get": ",".join(variables),
            "for": f"zip code tabulation area:{','.join(batch)}",
        }
        data = census_get(url, params)
        headers = data[0]
        if zcta_col not in headers:
            raise RuntimeError(
                f"Census API response missing '{zcta_col}' column. "
                f"Headers returned: {headers}"
            )
        zcta_idx = headers.index(zcta_col)

        for values in data[1:]:
            zcta = str(values[zcta_idx]).zfill(5)
            row = {"zcta": zcta}
            for h, v in zip(headers, values):
                if h in ("state", zcta_col):
                    continue
                try:
                    int_val = int(v) if v is not None else 0
                    row[h] = max(int_val, 0)   # treat Census suppression codes as 0
                except (ValueError, TypeError):
                    row[h] = 0
            results.append(row)

    return results
