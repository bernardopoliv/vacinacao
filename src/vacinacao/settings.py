import os

NAME_LOOKUPS = ["FULANO DA SILVA"]
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
# VAC_PUBLIC_LIST_URL = 'https://coronavirus.fortaleza.ce.gov.br/lista-vacinacao-d1.html'
VAC_PUBLIC_LIST_URL = 'https://spreadsheets.google.com/feeds/list/1IJBDu8dRGLkBgX72sRWKY6R9GfefsaDCXBd3Dz9PZNs/14/public/values'

FILES_DIR = f'{ROOT_DIR}/files'


# Cloud settings
S3_FILES_BUCKET = 'vacinacao-covid-ceara-2'

PULL_RESULTS_ASYNC = False


USE_INDEX = True
