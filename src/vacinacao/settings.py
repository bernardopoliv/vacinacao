import os

NAME_LOOKUPS = ["FULANO DA SILVA"]
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

VAC_PUBLIC_LIST_URL = 'https://spreadsheets.google.com/feeds/list/1IJBDu8dRGLkBgX72sRWKY6R9GfefsaDCXBd3Dz9PZNs/14/public/values'

BASE_URL = (
    "http://localhost:5000/"
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME") is None
    # TODO: make this dynamic per environment
    else "https://p47k7h5cd5.execute-api.us-east-1.amazonaws.com/Prod/"
)

# Cloud settings
S3_FILES_BUCKET = 'vacinacao-covid-ceara-3'

PULL_RESULTS_ASYNC = False
