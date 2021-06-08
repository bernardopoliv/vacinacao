up:
	docker-compose up -d --build

build-and-push: ecr-login
	docker-compose build
	docker tag vacinacao-img:latest 244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:0.14.5
	docker push 244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:0.14.5

ecr-login:
	aws ecr get-login --no-include-email | sh

deploy:
	sam deploy --no-confirm-changeset --image-repositories VacinacaoFunction=244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:0.14.5 --image-repositories VacinacaoFunctionIndexer=244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:0.14.0

webapp:
	python src/vacinacao/entrypoints.py
	# TODO
	# docker-compose run --rm --no-deps --entrypoint=python vacinacao "/src/vacinacao/entrypoints.py"

reindex:
	python src/vacinacao/service_layer/indexer.py

e2e-tests: up
	docker-compose run --rm --no-deps --entrypoint=pytest vacinacao /tests/test_e2e.py -vv

test: up e2e-tests

lint: up
	docker-compose run --rm --no-deps --entrypoint=flake8 vacinacao "/src" "/tests"
	docker-compose run --rm --no-deps --entrypoint=black vacinacao --check "/src" "/tests"

snapshot:
	docker-compose run --rm --no-deps --entrypoint=pytest vacinacao /tests/test_e2e.py -vv --snapshot-update