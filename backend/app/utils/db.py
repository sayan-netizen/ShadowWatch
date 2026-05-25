from pymongo import MongoClient
import os
import logging

try:
    import certifi
    _CA_FILE = certifi.where()
except ImportError:
    _CA_FILE = None

# We will initialize this lazily or let it run on import, but we'll use settings if possible.
# For now, keeping the same pattern to avoid breaking imports, but adding indexing.
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

_is_atlas = MONGO_URI.startswith("mongodb+srv")

try:
    _mongo_kwargs = {
        # Fail fast if Atlas is unreachable rather than hanging gunicorn workers.
        # serverSelectionTimeoutMS: how long to wait to find a usable server (5 s).
        # socketTimeoutMS: max time for a single DB operation (10 s).
        "serverSelectionTimeoutMS": 5000,
        "socketTimeoutMS":          10000,
    }
    if _is_atlas and _CA_FILE:
        client = MongoClient(MONGO_URI, tls=True, tlsCAFile=_CA_FILE, **_mongo_kwargs)
    elif _is_atlas:
        client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True, **_mongo_kwargs)
    else:
        client = MongoClient(MONGO_URI, **_mongo_kwargs)
except Exception as e:
    logging.error(f"Failed to create MongoDB client: {e}")
    raise

db = client['phishguard_db']

def get_db():
    return db

def init_db_indexes():
    """Create necessary database indexes for performance."""
    try:
        # Users collection
        db.users.create_index("username", unique=True)
        db.users.create_index("email", unique=True)
        
        # Scans collection
        db.scans.create_index("user_id")
        db.scans.create_index([("timestamp", -1)])
        
        # Alerts collection
        db.alerts.create_index("user_id")
        db.alerts.create_index([("timestamp", -1)])
        db.alerts.create_index("is_read")
        
        # Activity Logs collection
        db.activity_logs.create_index("user_id")
        db.activity_logs.create_index([("timestamp", -1)])

        # -----------------------------------------------------------------
        # Antigravity — Endpoint Module Collections
        # -----------------------------------------------------------------

        # monitored_hosts: look up a host by user + hostname, and by API key hash
        db.monitored_hosts.create_index("user_id")
        db.monitored_hosts.create_index("api_key_hash", unique=True)
        db.monitored_hosts.create_index([("user_id", 1), ("hostname", 1)])

        # endpoint_telemetry: time-series reads by host and user
        db.endpoint_telemetry.create_index("host_id")
        db.endpoint_telemetry.create_index("user_id")
        db.endpoint_telemetry.create_index([("timestamp", -1)])
        db.endpoint_telemetry.create_index([("host_id", 1), ("timestamp", -1)])

        # endpoint_alerts: dashboard reads — unread first, per user
        db.endpoint_alerts.create_index("user_id")
        db.endpoint_alerts.create_index("host_id")
        db.endpoint_alerts.create_index([("timestamp", -1)])
        db.endpoint_alerts.create_index([("user_id", 1), ("is_read", 1)])
        db.endpoint_alerts.create_index([("user_id", 1), ("threat_level", 1)])
        
        logging.info("Database indexes initialized successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize database indexes: {e}")
