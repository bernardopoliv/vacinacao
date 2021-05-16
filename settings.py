import os

import geckodriver_autoinstaller


NAME_LOOKUPS = ["FULANO DA SILVA"]
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
VAC_PUBLIC_LIST_URL = 'https://coronavirus.fortaleza.ce.gov.br/lista-vacinacao-d1.html'

INITIAL_DATE = '14/05/2021'
FILES_DIR = f'{ROOT_DIR}/files'
DAYS_AHEAD = 1


# Cloud settings
S3_FILES_BUCKET = 'vacinacao-covid-ceara-2'

# Downloads geckodriver and puts it in $PATH
geckodriver_autoinstaller.install()
