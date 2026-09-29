# Issue #121 commodity source gate — final Phase 1 status

Status: **BLOCKED / PENDING REPRODUCIBLE LONG-HISTORY TOTAL-RETURN TRANSPORT**

Target:
- Broad Commodities minus Cash
- >=50 years preferred
- investable futures total-return semantics required

Institutional benchmark audited:
- S&P GSCI Total Return

Documented official semantics:
- S&P GSCI first value date: 1969-12-31
- launch date: 1991-04-11
- pre-launch history is hypothetical / back-tested under the index methodology
- spot return is not total return
- excess return includes futures price + roll mechanics
- total return additionally includes collateral yield

Official benchmark pages expose current index information and interactive data/export surfaces, but this Phase 1 audit did not establish a stable, machine-retrievable, legally reusable historical total-return transport that can be hash-frozen inside GitHub Actions for the full >=50-year window.

Therefore:

- do not use spot commodity prices as a substitute;
- do not use GSG or another modern ETF as the ultra-long primary source;
- do not infer Commodity-Cash payoff from modern #109 evidence;
- do not block Equity-Treasury / Treasury-Cash / Gold-Cash rematch.

Phase 1 commodity verdict:

`blocked_pending_reproducible_total_return_transport`

No Commodity-Cash HMRA payoff was computed.

This is a source-access limitation, not a negative commodity research verdict.
