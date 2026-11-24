"""Tests for the ticker -> CIK lookup. No network: uses a small sample of SEC's JSON."""

import pytest

from app.ingestion.edgar import build_ticker_map, ticker_to_cik

# Same shape as https://www.sec.gov/files/company_tickers.json
SAMPLE_RAW = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
    "1": {"cik_str": 1318605, "ticker": "TSLA", "title": "Tesla, Inc."},
}


def test_build_ticker_map_pads_cik_to_10_digits() -> None:
    assert build_ticker_map(SAMPLE_RAW) == {"AAPL": "0000320193", "TSLA": "0001318605"}


def test_ticker_to_cik_is_case_insensitive() -> None:
    ticker_map = build_ticker_map(SAMPLE_RAW)
    assert ticker_to_cik("aapl", ticker_map) == "0000320193"
    assert ticker_to_cik("TSLA", ticker_map) == "0001318605"


def test_ticker_to_cik_unknown_ticker_raises() -> None:
    with pytest.raises(ValueError, match="Unknown ticker"):
        ticker_to_cik("NOPE", build_ticker_map(SAMPLE_RAW))
