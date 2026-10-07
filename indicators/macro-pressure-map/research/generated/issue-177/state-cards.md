# Issue #177 — State allocation cards (deterministic; see policy-matrix.csv)

Tiers are qualitative exposure tiers (0 / Low / Neutral / High), never portfolio weights.
`(limited)` = documented source limitation; `(policy-sensitive)` = tier changes under the full-common-sample panel.

## G_Low/I_Low — Deflationary bust — contracting activity with falling prices.

- High: treasury2y, treasury10y, longtreasury
- Neutral: sp500 (limited), nasdaq (limited), russell (limited), gold
- Low: —
- Zero: oil (limited)
- Cash: residual, bias low (opportunity score 9)
- Policy-sensitive sleeves: none
- Caveats: sp500: S&P TR reconstruction (^GSPC month-ends + Shiller dividends); ends 2023-06; nasdaq: price-only; dividends excluded (~0.96%/yr wedge); official TR only 2003+; russell: price-only; dividends excluded (~1.34%/yr wedge); official TR only 1995+; oil: investable = CL=F excess + TB3MS collateral from 2000-09; spot kept separately

## G_Low/I_Neutral — Disinflationary slowdown — weak growth, stable prices.

- High: —
- Neutral: sp500 (limited), nasdaq (limited) (policy-sensitive), russell (limited), treasury2y (policy-sensitive), treasury10y (policy-sensitive), longtreasury, oil (limited)
- Low: gold (policy-sensitive)
- Zero: —
- Cash: residual, bias neutral (opportunity score 7)
- Policy-sensitive sleeves: nasdaq, treasury2y, treasury10y, gold
- Caveats: sp500: S&P TR reconstruction (^GSPC month-ends + Shiller dividends); ends 2023-06; nasdaq: price-only; dividends excluded (~0.96%/yr wedge); official TR only 2003+; russell: price-only; dividends excluded (~1.34%/yr wedge); official TR only 1995+; oil: investable = CL=F excess + TB3MS collateral from 2000-09; spot kept separately [low confidence: insufficient sample]

## G_Low/I_High — Stagflationary slump — weak growth with high inflation.

- High: —
- Neutral: treasury2y (policy-sensitive), gold, oil (limited)
- Low: sp500 (limited), nasdaq (limited), russell (limited), treasury10y (policy-sensitive), longtreasury
- Zero: —
- Cash: residual, bias high (opportunity score 3)
- Policy-sensitive sleeves: treasury2y, treasury10y
- Caveats: sp500: S&P TR reconstruction (^GSPC month-ends + Shiller dividends); ends 2023-06; nasdaq: price-only; dividends excluded (~0.96%/yr wedge); official TR only 2003+; russell: price-only; dividends excluded (~1.34%/yr wedge); official TR only 1995+; oil: investable = CL=F excess + TB3MS collateral from 2000-09; spot kept separately [low confidence: insufficient sample]

## G_Neutral/I_Low — Healthy disinflation — steady growth, low inflation.

- High: sp500 (limited), treasury2y (policy-sensitive), longtreasury (policy-sensitive)
- Neutral: nasdaq (limited), russell (limited), treasury10y, gold, oil (limited)
- Low: —
- Zero: —
- Cash: residual, bias low (opportunity score 11)
- Policy-sensitive sleeves: treasury2y, longtreasury
- Caveats: sp500: S&P TR reconstruction (^GSPC month-ends + Shiller dividends); ends 2023-06; nasdaq: price-only; dividends excluded (~0.96%/yr wedge); official TR only 2003+; russell: price-only; dividends excluded (~1.34%/yr wedge); official TR only 1995+; oil: investable = CL=F excess + TB3MS collateral from 2000-09; spot kept separately

## G_Neutral/I_Neutral — Balanced expansion — steady growth, neutral inflation.

- High: —
- Neutral: sp500 (limited), nasdaq (limited), russell (limited), treasury2y, treasury10y, longtreasury, oil (limited)
- Low: gold
- Zero: —
- Cash: residual, bias neutral (opportunity score 7)
- Policy-sensitive sleeves: none
- Caveats: sp500: S&P TR reconstruction (^GSPC month-ends + Shiller dividends); ends 2023-06; nasdaq: price-only; dividends excluded (~0.96%/yr wedge); official TR only 2003+; russell: price-only; dividends excluded (~1.34%/yr wedge); official TR only 1995+; oil: investable = CL=F excess + TB3MS collateral from 2000-09; spot kept separately

## G_Neutral/I_High — Late-cycle heat — steady growth with elevated inflation.

- High: —
- Neutral: sp500 (limited), nasdaq (limited), gold, oil (limited)
- Low: treasury2y, treasury10y (policy-sensitive), longtreasury (policy-sensitive)
- Zero: russell (limited)
- Cash: residual, bias high (opportunity score 3)
- Policy-sensitive sleeves: treasury10y, longtreasury
- Caveats: sp500: S&P TR reconstruction (^GSPC month-ends + Shiller dividends); ends 2023-06; nasdaq: price-only; dividends excluded (~0.96%/yr wedge); official TR only 2003+; russell: price-only; dividends excluded (~1.34%/yr wedge); official TR only 1995+; oil: investable = CL=F excess + TB3MS collateral from 2000-09; spot kept separately

## G_High/I_Low — Productivity boom — strong growth, low inflation.

- High: longtreasury
- Neutral: sp500 (limited), nasdaq (limited) (policy-sensitive), treasury2y, treasury10y (policy-sensitive), oil (limited)
- Low: russell (limited)
- Zero: gold
- Cash: residual, bias neutral (opportunity score 6)
- Policy-sensitive sleeves: nasdaq, treasury10y
- Caveats: sp500: S&P TR reconstruction (^GSPC month-ends + Shiller dividends); ends 2023-06; nasdaq: price-only; dividends excluded (~0.96%/yr wedge); official TR only 2003+; russell: price-only; dividends excluded (~1.34%/yr wedge); official TR only 1995+; oil: investable = CL=F excess + TB3MS collateral from 2000-09; spot kept separately [low confidence: insufficient sample]

## G_High/I_Neutral — Broad boom — strong growth, neutral inflation.

- High: sp500 (limited), nasdaq (limited), russell (limited)
- Neutral: gold, oil (limited)
- Low: treasury2y, treasury10y (policy-sensitive), longtreasury
- Zero: —
- Cash: residual, bias neutral (opportunity score 8)
- Policy-sensitive sleeves: treasury10y
- Caveats: sp500: S&P TR reconstruction (^GSPC month-ends + Shiller dividends); ends 2023-06; nasdaq: price-only; dividends excluded (~0.96%/yr wedge); official TR only 2003+; russell: price-only; dividends excluded (~1.34%/yr wedge); official TR only 1995+; oil: investable = CL=F excess + TB3MS collateral from 2000-09; spot kept separately

## G_High/I_High — Overheating — strong growth with high inflation.

- High: —
- Neutral: sp500 (limited), nasdaq (limited), russell (limited), gold (policy-sensitive), oil (limited)
- Low: treasury2y, treasury10y, longtreasury
- Zero: —
- Cash: residual, bias neutral (opportunity score 5)
- Policy-sensitive sleeves: gold
- Caveats: sp500: S&P TR reconstruction (^GSPC month-ends + Shiller dividends); ends 2023-06; nasdaq: price-only; dividends excluded (~0.96%/yr wedge); official TR only 2003+; russell: price-only; dividends excluded (~1.34%/yr wedge); official TR only 1995+; oil: investable = CL=F excess + TB3MS collateral from 2000-09; spot kept separately

