#!/usr/bin/env python3
"""Minimal Bloomberg Desktop API client for Issue #119.

blpapi is imported lazily so CI can test the pipeline without Bloomberg.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from issue119_bbg_common import HISTORICAL_FIELDS


class BloombergError(RuntimeError):
    pass


def _scalar(element: Any) -> Any:
    """Best-effort extraction of a scalar Bloomberg Element."""
    if element is None or element.isNull():
        return None
    try:
        return element.getValue()
    except Exception:
        try:
            return element.getValueAsString()
        except Exception:
            return None


def _sequence_to_dict(element: Any) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for i in range(element.numElements()):
        child = element.getElement(i)
        name = str(child.name())
        if child.isArray():
            out[name] = [
                _sequence_to_dict(child.getValueAsElement(j))
                for j in range(child.numValues())
            ]
        elif child.isComplexType():
            out[name] = _sequence_to_dict(child)
        else:
            out[name] = _scalar(child)
    return out


class BloombergDesktopClient:
    def __init__(
        self,
        *,
        host: str = "localhost",
        port: int = 8194,
        event_timeout_ms: int = 10000,
    ) -> None:
        try:
            import blpapi  # type: ignore
        except ImportError as exc:
            raise BloombergError(
                "blpapi is not installed; run this on the Bloomberg workstation Python environment"
            ) from exc

        self.blpapi = blpapi
        self.event_timeout_ms = int(event_timeout_ms)
        options = blpapi.SessionOptions()
        options.setServerHost(host)
        options.setServerPort(int(port))
        self.session = blpapi.Session(options)
        if not self.session.start():
            raise BloombergError("failed to start Bloomberg Desktop API session")
        if not self.session.openService("//blp/refdata"):
            self.session.stop()
            raise BloombergError("failed to open //blp/refdata")
        self.service = self.session.getService("//blp/refdata")

    def close(self) -> None:
        try:
            self.session.stop()
        except Exception:
            pass

    def __enter__(self) -> "BloombergDesktopClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _events(self):
        blpapi = self.blpapi
        while True:
            event = self.session.nextEvent(self.event_timeout_ms)
            et = event.eventType()
            if et == blpapi.Event.TIMEOUT:
                raise BloombergError("Bloomberg response timed out")
            yield event
            if et == blpapi.Event.RESPONSE:
                break

    @staticmethod
    def _raise_response_error(message: Any) -> None:
        if message.hasElement("responseError"):
            raise BloombergError(str(message.getElement("responseError")))

    def bulk_index_members(
        self,
        index_security: str,
        field: str = "INDX_MEMBERS",
    ) -> list[dict[str, Any]]:
        request = self.service.createRequest("ReferenceDataRequest")
        request.append("securities", index_security)
        request.append("fields", field)
        self.session.sendRequest(request)

        rows: list[dict[str, Any]] = []
        for event in self._events():
            for message in event:
                self._raise_response_error(message)
                if not message.hasElement("securityData"):
                    continue
                security_data = message.getElement("securityData")
                for i in range(security_data.numValues()):
                    sec = security_data.getValueAsElement(i)
                    if sec.hasElement("securityError"):
                        raise BloombergError(
                            f"{index_security}: {sec.getElement('securityError')}"
                        )
                    field_data = sec.getElement("fieldData")
                    if not field_data.hasElement(field):
                        continue
                    bulk = field_data.getElement(field)
                    for j in range(bulk.numValues()):
                        rows.append(
                            _sequence_to_dict(bulk.getValueAsElement(j))
                        )
        if not rows:
            raise BloombergError(f"{index_security}: {field} returned no rows")
        return rows

    def reference_data(
        self,
        securities: list[str],
        fields: list[str] | tuple[str, ...],
    ) -> dict[str, dict[str, Any]]:
        request = self.service.createRequest("ReferenceDataRequest")
        for security in securities:
            request.append("securities", security)
        for field in fields:
            request.append("fields", field)
        self.session.sendRequest(request)

        out: dict[str, dict[str, Any]] = {}
        for event in self._events():
            for message in event:
                self._raise_response_error(message)
                if not message.hasElement("securityData"):
                    continue
                security_data = message.getElement("securityData")
                for i in range(security_data.numValues()):
                    sec = security_data.getValueAsElement(i)
                    security = sec.getElementAsString("security")
                    row: dict[str, Any] = {"security": security}
                    if sec.hasElement("securityError"):
                        row["_error"] = str(sec.getElement("securityError"))
                        out[security] = row
                        continue
                    field_data = sec.getElement("fieldData")
                    for field in fields:
                        row[field] = (
                            _scalar(field_data.getElement(field))
                            if field_data.hasElement(field)
                            else None
                        )
                    out[security] = row
        return out

    def historical_data(
        self,
        securities: list[str],
        *,
        start_date: str,
        end_date: str,
        fields: tuple[str, ...] = HISTORICAL_FIELDS,
    ) -> dict[str, pd.DataFrame]:
        """Fetch split-adjusted, non-dividend-adjusted daily OHLCV."""
        request = self.service.createRequest("HistoricalDataRequest")
        for security in securities:
            request.append("securities", security)
        for field in fields:
            request.append("fields", field)

        request.set("startDate", start_date.replace("-", ""))
        request.set("endDate", end_date.replace("-", ""))
        request.set("periodicitySelection", "DAILY")
        request.set("adjustmentFollowDPDF", False)
        request.set("adjustmentNormal", False)
        request.set("adjustmentAbnormal", False)
        request.set("adjustmentSplit", True)

        self.session.sendRequest(request)
        rows: dict[str, list[dict[str, Any]]] = {
            security: [] for security in securities
        }
        errors: dict[str, str] = {}

        for event in self._events():
            for message in event:
                self._raise_response_error(message)
                if not message.hasElement("securityData"):
                    continue
                sec = message.getElement("securityData")
                security = sec.getElementAsString("security")
                if sec.hasElement("securityError"):
                    errors[security] = str(sec.getElement("securityError"))
                    continue
                field_data = sec.getElement("fieldData")
                for i in range(field_data.numValues()):
                    item = field_data.getValueAsElement(i)
                    row: dict[str, Any] = {
                        "DATE": _scalar(item.getElement("date"))
                    }
                    for field in fields:
                        row[field] = (
                            _scalar(item.getElement(field))
                            if item.hasElement(field)
                            else None
                        )
                    rows.setdefault(security, []).append(row)

        out: dict[str, pd.DataFrame] = {}
        for security, security_rows in rows.items():
            if security in errors:
                continue
            out[security] = pd.DataFrame(
                security_rows,
                columns=["DATE", *fields],
            )
        return out
