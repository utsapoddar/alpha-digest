"""Bounded market-wide Form 4 discovery; aggregators are reference links only."""
from datetime import datetime
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

import requests
import time

from digest.fetchers.base import edgar_get, edgar_get_xml
from digest.fetchers.sec_edgar import _parse_form4_xml

ATOM = '{http://www.w3.org/2005/Atom}'
CURRENT_URL = 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4&owner=only&count=100&output=atom&start={start}'
MIN_VALUE_USD = 1000000


def trade_key(trade):
    return (trade.get('owner_cik') or trade['entity'], trade.get('ticker', ''),
            trade.get('transaction_date') or trade['date'], trade['action'],
            trade.get('shares'), trade.get('price_per_share'), trade.get('transaction_index', 0))


def merge_large_trades(existing, discovered, min_value_usd=MIN_VALUE_USD):
    unique = {}
    for trade in [*existing, *discovered]:
        if trade.get('value_usd', 0) >= min_value_usd:
            unique.setdefault(trade_key(trade), trade)
    return sorted(unique.values(), key=lambda trade: trade['value_usd'], reverse=True)


def parse_ownership(xml, filing_date, source_url, min_value_usd=MIN_VALUE_USD):
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return []
    if root.tag != 'ownershipDocument':
        return []
    owner = root.findtext('.//rptOwnerName') or root.findtext('issuer/issuerName') or 'Unknown reporting owner'
    trades = _parse_form4_xml(xml, owner, filing_date)
    results = []
    for trade in trades:
        if trade['value_usd'] < min_value_usd:
            continue
        ticker = trade.get('ticker', '')
        trade['source_url'] = source_url
        trade['openinsider_url'] = f'http://openinsider.com/{ticker}' if ticker else 'http://openinsider.com/'
        trade['finviz_url'] = f'https://finviz.com/quote.ashx?t={ticker}' if ticker else 'https://finviz.com/insidertrading.ashx'
        results.append(trade)
    return results


def fetch_large_insiders(session, since: datetime, until: datetime,
                         min_value_usd=MIN_VALUE_USD, max_filings=200):
    """Inspect a bounded newest-first feed; always disclose the coverage limit."""
    trades, seen, failed = [], set(), 0
    reached_since, scanned = False, 0
    deadline = time.monotonic() + 180
    for start in range(0, max_filings, 100):
        if time.monotonic() >= deadline:
            break
        try:
            raw = edgar_get_xml(CURRENT_URL.format(start=start), session)
            if not raw:
                failed += 1
                break
            entries = ET.fromstring(raw).findall(f'{ATOM}entry')
        except (requests.RequestException, ET.ParseError):
            failed += 1
            break
        if not entries:
            reached_since = True
            break
        for entry in entries:
            if time.monotonic() >= deadline:
                break
            updated = entry.findtext(f'{ATOM}updated', '')[:10]
            filed = datetime.fromisoformat(updated)
            if filed < since:
                reached_since = True
                break
            if filed >= until:
                continue
            link = entry.find(f'{ATOM}link')
            url = link.get('href', '') if link is not None else ''
            parsed = urlsplit(url)
            if parsed.scheme != 'https' or parsed.hostname != 'www.sec.gov' or '/Archives/edgar/data/' not in parsed.path:
                continue
            directory = url.rsplit('/', 1)[0] + '/'
            if directory in seen:
                continue
            seen.add(directory)
            if scanned >= max_filings:
                break
            scanned += 1
            try:
                index = edgar_get(directory + 'index.json', session)
                items = (index or {}).get('directory', {}).get('item', [])
                found = False
                for item in items:
                    if time.monotonic() >= deadline:
                        break
                    name = item.get('name', '')
                    if not name.endswith('.xml') or '/' in name:
                        continue
                    xml = edgar_get_xml(directory + name, session)
                    if not xml:
                        continue
                    root = ET.fromstring(xml)
                    if root.tag == 'ownershipDocument':
                        trades.extend(parse_ownership(xml, updated, directory + name, min_value_usd))
                        found = True
                        break
                if not found:
                    failed += 1
            except (requests.RequestException, ET.ParseError, ValueError):
                failed += 1
        if reached_since or scanned >= max_filings:
            break
    coverage = (f'SEC discovery inspected {scanned} filings within the filing-date window; '
                f'inspection cap {max_filings}, discovery limited to the newest {((max_filings + 99) // 100) * 100} feed entries. '
                f'{failed} filing/feed retrieval failures; 180-second source budget. '
                'This is not an exhaustive market-wide screen. Trade dates may precede filing dates.')
    return {'trades': merge_large_trades([], trades, min_value_usd), 'coverage': coverage}
