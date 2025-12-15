"""Realtime Alerts tools: detect, store, and query alerts."""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import json

from app.config import config
import app.sub_agents.data_orchestrator.tools as bq_tools

# convenience reference (bq_tools._bq_store may be None in test env)
_bq_store = getattr(bq_tools, "_bq_store", None)


def detect_high_volatility(tickers: List[str], vol_threshold: float = 0.6) -> Dict[str, Any]:
    """Detect tickers with realized volatility above a threshold.

    Args:
        tickers: list of ticker symbols
        vol_threshold: annualized volatility threshold (e.g., 0.6 = 60%)

    Returns:
        dict with list of alerts
    """
    alerts = []
    for t in tickers:
        try:
            res = bq_tools.get_baseline_metrics(t)
        except Exception:
            continue
        # fetch market/economic/index context via Data Orchestrator
        try:
            context = bq_tools.get_market_economic_data(t)
        except Exception:
            context = None
        if res.get("status") != "success":
            continue
        metrics = res.get("result", {})
        vol = metrics.get("HistVol_5D_Ann", 0.0)
        if vol is None:
            vol = 0.0
        if vol >= vol_threshold:
            alert = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "ticker": t.upper(),
                "alert_type": "high_volatility",
                "severity": "high" if vol >= vol_threshold * 1.5 else "medium",
                "metric": "HistVol_5D_Ann",
                "metric_value": float(vol),
                "details": {
                    "source": metrics.get("SourceTable"),
                    "sample_points": metrics.get("SamplePoints"),
                    "context": context if context else {}
                }
            }
            alerts.append(alert)
    return {"status": "success", "alerts": alerts}


def store_alerts_to_bq(alerts: List[Dict[str, Any]], table_name: str = "realtime_alerts") -> Dict[str, Any]:
    """Store alerts into a BigQuery table. Returns insertion status."""
    if not _bq_store or not _bq_store.client:
        return {"status": "error", "message": "BigQuery not available"}

    table_id = f"{_bq_store.project}.{_bq_store.dataset}.{table_name}"
    # transform alerts to rows
    rows = []
    for a in alerts:
        rows.append({
            "id": a.get("id"),
            "timestamp": a.get("timestamp"),
            "ticker": a.get("ticker"),
            "alert_type": a.get("alert_type"),
            "severity": a.get("severity"),
            "metric": a.get("metric"),
            "metric_value": a.get("metric_value"),
            "details": json.dumps(a.get("details", {})),
        })

    try:
        errors = _bq_store.client.insert_rows_json(table_id, rows)
        if errors:
            return {"status": "error", "message": errors}
        return {"status": "success", "inserted": len(rows)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def publish_alert_event(alert: Dict[str, Any]) -> Dict[str, Any]:
    """Raise an in-process event for an alert. Placeholder for Pub/Sub or webhook."""
    # Try Pub/Sub if configured
    events = []
    if config.ALERTS_PUBSUB_TOPIC:
        try:
            pub_res = publish_alert_pubsub(alert, topic=config.ALERTS_PUBSUB_TOPIC)
            events.append(pub_res)
        except Exception as e:
            print(f"⚠️  Pub/Sub publish failed: {e}")

    # Try webhook if configured
    if config.ALERTS_WEBHOOK_URL:
        try:
            web_res = publish_alert_webhook(alert, url=config.ALERTS_WEBHOOK_URL)
            events.append(web_res)
        except Exception as e:
            print(f"⚠️  Webhook publish failed: {e}")

    # Always emit an in-process event record
    event = {
        "type": "alert_raised",
        "timestamp": datetime.utcnow().isoformat(),
        "payload": alert,
        "outcomes": events,
    }
    print(f"🔔 Alert event: {event['type']} for {alert.get('ticker')} - {alert.get('alert_type')}")
    return event


def publish_alert_pubsub(alert: Dict[str, Any], topic: str) -> Dict[str, Any]:
    """Publish alert to Cloud Pub/Sub topic. topic should be full topic path or name.

    Returns dict with publish result metadata.
    """
    try:
        from google.cloud import pubsub_v1
    except Exception as e:
        raise RuntimeError("google-cloud-pubsub not available: %s" % e)

    publisher = pubsub_v1.PublisherClient()
    # Accept both short topics and full project/topic paths
    if topic.startswith("projects/"):
        topic_path = topic
    else:
        project = _bq_store.project if _bq_store else config.GOOGLE_CLOUD_PROJECT
        topic_path = publisher.topic_path(project, topic)

    data = json.dumps(alert).encode('utf-8')
    future = publisher.publish(topic_path, data)
    # Return immediate metadata (future may be pending)
    return {"status": "published", "topic": topic_path, "result": str(future)}


def publish_alert_webhook(alert: Dict[str, Any], url: str) -> Dict[str, Any]:
    """POST alert payload to a webhook URL. Returns response summary."""
    try:
        import requests
    except Exception as e:
        raise RuntimeError("requests not available: %s" % e)

    hdr = {"Content-Type": "application/json"}
    resp = requests.post(url, json=alert, headers=hdr, timeout=10)
    return {"status": "webhook_posted", "code": resp.status_code, "url": url}


def get_active_alerts(hours: int = 24, table_name: str = "realtime_alerts") -> Dict[str, Any]:
    """Query recent alerts from BigQuery table within the last `hours`.

    Returns:
        dict with list of alerts
    """
    if not _bq_store or not _bq_store.client:
        return {"status": "error", "message": "BigQuery not available"}

    end = datetime.utcnow()
    start = end - timedelta(hours=hours)
    table_id = f"{_bq_store.project}.{_bq_store.dataset}.{table_name}"
    sql = f"SELECT id, timestamp, ticker, alert_type, severity, metric, metric_value, details FROM `{table_id}` WHERE timestamp BETWEEN '{start.isoformat()}' AND '{end.isoformat()}' LIMIT 1000"
    try:
        df = _bq_store.query_to_df(sql)
        rows = df.to_dict(orient="records") if not df.empty else []
        # parse details JSON field
        for r in rows:
            if isinstance(r.get('details'), str):
                try:
                    r['details'] = json.loads(r['details'])
                except Exception:
                    pass
        return {"status": "success", "alerts": rows}
    except Exception as e:
        return {"status": "error", "message": str(e)}
