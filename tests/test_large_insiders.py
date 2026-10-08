from datetime import datetime
from digest.fetchers.large_insiders import parse_ownership, merge_large_trades
from digest.renderer import render_html, render_web_html

XML = b'''<ownershipDocument><issuer><issuerName>Acme</issuerName><issuerTradingSymbol>ACME</issuerTradingSymbol></issuer><reportingOwner><reportingOwnerId><rptOwnerCik>123</rptOwnerCik><rptOwnerName>Example Owner</rptOwnerName></reportingOwnerId></reportingOwner><nonDerivativeTable><nonDerivativeTransaction><transactionDate><value>2026-10-05</value></transactionDate><transactionCoding><transactionCode>P</transactionCode></transactionCoding><transactionAmounts><transactionShares><value>10000</value></transactionShares><transactionPricePerShare><value>100</value></transactionPricePerShare></transactionAmounts></nonDerivativeTransaction></nonDerivativeTable></ownershipDocument>'''


def test_threshold_buy_sale_and_metadata():
    trades = parse_ownership(XML, '2026-10-06', 'https://www.sec.gov/filing', 1000000)
    assert len(trades) == 1
    assert trades[0]['value_usd'] == 1000000
    assert trades[0]['date'] == '2026-10-06'
    assert trades[0]['transaction_date'] == '2026-10-05'
    assert trades[0]['ticker'] == 'ACME'
    assert trades[0]['action'] == 'BUY'
    assert parse_ownership(XML.replace(b'<transactionCode>P',b'<transactionCode>S'), '2026-10-06', 'url', 1000000)[0]['action'] == 'SELL'


def test_small_unknown_and_non_market_transactions_excluded():
    assert not parse_ownership(XML.replace(b'<value>100</value>', b'<value>99.99</value>'), '2026-10-06', 'url', 1000000)
    assert not parse_ownership(XML.replace(b'<value>100</value>', b'<value></value>'), '2026-10-06', 'url', 1000000)
    assert not parse_ownership(XML.replace(b'<transactionCode>P', b'<transactionCode>A'), '2026-10-06', 'url', 1000000)


def test_merge_deduplicates_and_filters_small_trades():
    trades = parse_ownership(XML, '2026-10-06', 'url', 1000000)
    assert len(merge_large_trades(trades, trades, 1000000)) == 1
    assert merge_large_trades([dict(trades[0],value_usd=999999)], [], 1000000) == []


def test_both_outputs_show_primary_and_reference_links():
    trades = parse_ownership(XML, '2026-10-06', 'https://www.sec.gov/filing', 1000000)
    summary = {'large_insider_trades': trades, 'insider_coverage': 'Bounded SEC discovery'}
    for render in (render_html,render_web_html):
        html = render(summary, {}, '2026-10-01','2026-10-08')
        assert 'Large insider trades' in html
        assert 'https://www.sec.gov/filing' in html
        assert 'https://www.google.com/finance/' in html
        assert 'http://openinsider.com/ACME' in html
        assert 'https://finviz.com/quote.ashx?t=ACME' in html
        assert 'Bounded SEC discovery' in html


def test_invalid_prices_do_not_become_large_trades():
    for value in (b'NaN', b'Infinity', b'not-a-number'):
        assert not parse_ownership(XML.replace(b'<value>100</value>', b'<value>'+value+b'</value>'), '2026-10-06','url',1000000)


def test_registry_enables_real_large_trade_fetcher():
    from digest.fetchers import FETCHER_REGISTRY
    from digest import config
    assert 'large_insiders' in FETCHER_REGISTRY
    assert config.load_sources_config()['fetchers']['large_insiders']['enabled'] is True


def test_identical_transaction_rows_are_not_collapsed_within_one_filing():
    row = XML.split(b'<nonDerivativeTransaction>')[1].split(b'</nonDerivativeTransaction>')[0]
    two = XML.replace(b'</nonDerivativeTable>', b'<nonDerivativeTransaction>'+row+b'</nonDerivativeTransaction></nonDerivativeTable>')
    trades = parse_ownership(two, '2026-10-06','url',1000000)
    assert len(merge_large_trades([],trades,1000000)) == 2


def test_main_dry_run_wires_fetcher_enrichment_and_rendering(tmp_path, monkeypatch):
    import main
    from digest.fetchers import FETCHER_REGISTRY
    trades = parse_ownership(XML, '2026-10-06','https://www.sec.gov/filing',1000000)
    monkeypatch.setattr(main.config,'load_sources_config',lambda: {'fetchers': {'large_insiders': {'enabled':True,'max_filings':2}}})
    monkeypatch.setattr(main.config,'DATA_DIR',tmp_path)
    monkeypatch.setattr(main,'load_watchlist',lambda _: [])
    monkeypatch.setattr(main,'load_date_range',lambda: (datetime(2026,10,1),datetime(2026,10,8)))
    calls = []
    def fetch(session,since,until,**kwargs):
        calls.append((since,until,kwargs))
        return {'trades':trades,'coverage':'Test SEC coverage'}
    monkeypatch.setitem(FETCHER_REGISTRY,'large_insiders',{'fn':fetch,'scope':'global'})
    def summarize(enriched,*args):
        assert enriched['trades'][0]['value_usd'] == 1000000
        return {}
    monkeypatch.setattr(main,'summarize',summarize)
    main.main(dry_run=True)
    assert calls[0][2] == {'min_value_usd':1000000,'max_filings':2}
    assert 'Test SEC coverage' in (tmp_path/'last_digest.html').read_text()
