# Issue #78 — Daily × Weekly Sizing Research Status

Status: **evidence collection gate**.

Completed before viewing any Daily × Weekly outcome comparison:

- preregistered `Daily Trigger × Weekly Sizing Context × Daily Health` hypothesis;
- froze three policy families: Daily-only benchmark, Weekly-direction cap, Weekly-direction + Weekly-Trendability cap;
- froze native-weekly classifier provenance: unchanged Issue #68 RC evaluated on 1W bars;
- froze Weekly Trendability at ER13 / ER26 / ER52 with 156-week percentile normalization;
- froze causal as-of rule `week_close_time <= daily_event_time`;
- built frozen-source weekly context Pine logger generator;
- generated `wyckoff-issue78-weekly-context-logger.pine`;
- built reusable daily-weekly sizing analyzer with the existing economic-value / temporal / tail / friction summaries;
- CI syntax/static-contract run passed;
- documented nine-market TradingView smoke/export checklist.

No Daily × Weekly performance result has been viewed yet.

Next evidence required: one native-1W Pine Logs CSV for each of the nine frozen markets. Existing accepted Issue #76 daily logs are reused and do not need re-export.