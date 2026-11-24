"""SEC EDGAR client: ticker -> CIK lookup, filing listing and raw filing download."""

import os
import time
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession}/{doc}"

# <repo>/data/raw, anchored to this file so it works from any working directory.
RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"

MIN_INTERVAL = 0.15  # seconds between requests: ~6.7 req/sec, under SEC's limit of 10
MAX_RETRIES = 3
TIMEOUT = 30  # seconds
RETRY_STATUSES = {429, 500, 502, 503, 504}  # rate-limited or server-side: worth retrying

_session = requests.Session()  # reuses one TCP connection across requests
_last_request_at = 0.0


@dataclass(frozen=True)
class Filing:
    """One filing from a company's EDGAR submission history."""

    form: str
    accession: str
    primary_doc: str
    filed_at: date
    url: str


def _user_agent() -> str:
    """Read the SEC User-Agent from the environment; SEC blocks requests without one."""
    user_agent = os.getenv("SEC_USER_AGENT", "")
    if not user_agent or "YOUR_EMAIL" in user_agent:
        raise RuntimeError("Set SEC_USER_AGENT in .env to 'Your Name your@email'.")
    return user_agent


def _get(url: str) -> requests.Response:
    """GET a URL with the SEC User-Agent, rate limiting and retries.

    Every request in this module goes through here, so none can skip the rules.
    """
    global _last_request_at
    headers = {"User-Agent": _user_agent()}
    error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        # Rate limit: wait until MIN_INTERVAL has passed since the previous request.
        wait = MIN_INTERVAL - (time.monotonic() - _last_request_at)
        if wait > 0:
            time.sleep(wait)
        _last_request_at = time.monotonic()

        try:
            response = _session.get(url, headers=headers, timeout=TIMEOUT)
        except (requests.ConnectionError, requests.Timeout) as exc:
            error = exc
        else:
            if response.status_code not in RETRY_STATUSES:
                response.raise_for_status()  # e.g. 403/404: retrying will not help
                return response
            error = requests.HTTPError(f"HTTP {response.status_code}")

        if attempt < MAX_RETRIES:
            time.sleep(2**attempt)  # exponential backoff: 2s, then 4s

    raise RuntimeError(f"GET {url} failed after {MAX_RETRIES} attempts") from error


def build_ticker_map(raw: dict[str, dict]) -> dict[str, str]:
    """Turn SEC's company_tickers.json into {"AAPL": "0000320193", ...}.

    SEC's JSON looks like {"0": {"cik_str": 320193, "ticker": "AAPL", "title": ...}}.
    CIKs are zero-padded to 10 digits because the submissions API requires that.
    """
    return {row["ticker"].upper(): str(row["cik_str"]).zfill(10) for row in raw.values()}


@lru_cache(maxsize=1)
def fetch_ticker_map() -> dict[str, str]:
    """Download the ticker -> CIK map once per process."""
    return build_ticker_map(_get(TICKERS_URL).json())


def ticker_to_cik(ticker: str, ticker_map: dict[str, str] | None = None) -> str:
    """Return the 10-digit CIK for a ticker. Pass ticker_map to avoid the network."""
    if ticker_map is None:
        ticker_map = fetch_ticker_map()
    try:
        return ticker_map[ticker.upper()]
    except KeyError:
        raise ValueError(f"Unknown ticker: {ticker}") from None


def list_filings(cik: str, form: str) -> list[Filing]:
    """List a company's recent filings of one form type (e.g. "10-K"), newest first."""
    recent = _get(SUBMISSIONS_URL.format(cik=cik)).json()["filings"]["recent"]

    # "recent" is column-oriented (one list per field), so zip the columns into rows.
    rows = zip(
        recent["form"],
        recent["accessionNumber"],
        recent["primaryDocument"],
        recent["filingDate"],
    )
    return [
        Filing(
            form=row_form,
            accession=accession,
            primary_doc=primary_doc,
            filed_at=date.fromisoformat(filing_date),
            url=ARCHIVE_URL.format(
                cik_int=int(cik),  # archive paths use the CIK without leading zeros
                accession=accession.replace("-", ""),  # and the accession without dashes
                doc=primary_doc,
            ),
        )
        for row_form, accession, primary_doc, filing_date in rows
        if row_form == form
    ]


def download_latest(ticker: str, form: str) -> Path:
    """Download a company's latest filing of a form type; return the saved path."""
    filings = list_filings(ticker_to_cik(ticker), form)
    if not filings:
        raise ValueError(f"No {form} filings found for {ticker}")
    latest = filings[0]  # EDGAR returns newest first

    filename = f"{form}_{latest.filed_at}_{latest.accession}.html".replace("/", "-")
    path = RAW_DIR / ticker.upper() / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_get(latest.url).content)
    return path


if __name__ == "__main__":
    saved = download_latest("AAPL", "10-K")
    print(f"Saved {saved} ({saved.stat().st_size / 1_000_000:.1f} MB)")
