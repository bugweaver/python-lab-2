"""Sample events and broken records used by the tests."""

VALID_CSV = (
    "timestamp,level,source,message\n"
    "2026-10-20T10:00:00Z,INFO,api,Started\n"
    "2026-10-20T10:01:00Z,ERROR,database,Failed\n"
)

INVALID_CSV = (
    "timestamp,level,source,message\n"
    "2026-10-20T10:00:00Z,FATAL,api,Failed\n"
)

MIXED_CSV = (
    "timestamp,level,source,message\n"
    "2026-10-20T10:00:00Z,INFO,api,Started\n"
    "2026-10-20T10:01:00Z,FATAL,api,Failed\n"
    "2026-10-20T10:02:00Z,WARNING,auth,Retry\n"
)

BAD_TIMESTAMP_CSV = (
    "timestamp,level,source,message\n"
    "not-a-timestamp,INFO,api,Started\n"
)

UNICODE_CSV = (
    "timestamp,level,source,message\n"
    "2026-10-20T12:00:00+03:00,INFO,сервис,Привет\n"
)

VALID_JSONL = (
    '{"timestamp":"2026-10-20T10:00:00Z",'
    '"level":"INFO","source":"api","message":"Started"}\n'
)

INVALID_JSONL = (
    '{"timestamp":"2026-10-20T10:00:00Z",'
    '"level":"FATAL","source":"api","message":"Failed"}\n'
)

MIXED_JSONL = (
    '{"timestamp":"2026-10-20T10:00:00Z","level":"INFO",'
    '"source":"api","message":"Started"}\n'
    '{"timestamp":"2026-10-20T10:01:00Z","level":"FATAL",'
    '"source":"api","message":"Failed"}\n'
    '{"timestamp":"2026-10-20T10:02:00Z","level":"ERROR",'
    '"source":"database","message":"Down"}\n'
)

BAD_TIMESTAMP_JSONL = (
    '{"timestamp":"yesterday","level":"INFO","source":"api","message":"Started"}\n'
)

UNICODE_JSONL = (
    '{"timestamp":"2026-10-20T12:00:00+03:00","level":"WARNING",'
    '"source":"сервис","message":"Привет"}\n'
)

EMPTY_FILE = ""
