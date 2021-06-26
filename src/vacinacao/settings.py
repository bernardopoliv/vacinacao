import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

VAC_PUBLIC_LIST_URL = "https://spreadsheets.google.com/feeds/list/1IJBDu8dRGLkBgX72sRWKY6R9GfefsaDCXBd3Dz9PZNs/14/public/values"  # noqa

BASE_URL = os.getenv("VACINACAO_URL", "http://localhost:5000/")

# Cloud settings
S3_FILES_BUCKET = "vacinacao-covid-ceara-3"

PULL_RESULTS_ASYNC = False
