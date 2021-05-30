up:
	docker-compose up -d --build

build-and-push:
	docker-compose build
	docker tag vacinacao-img:latest 244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:0.11.2
	docker push 244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:0.11.2

ecr-login:
	aws ecr get-login --no-include-email | sh

deploy:
	sam deploy --no-confirm-changeset --image-repositories VacinacaoFunction=244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:0.10.3 --image-repositories VacinacaoFunctionIndexer=244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:0.11.2

webapp:
	python src/vacinacao/entrypoints.py

reindex:
	python src/vacinacao/service_layer/indexer.py

e2e-tests: up
	docker-compose run --rm --no-deps --entrypoint=pytest vacinacao /tests/test_e2e.py -vv

test: up e2e-tests

lint: up
	docker-compose run --rm --no-deps --entrypoint=flake8 vacinacao
	docker-compose run --rm --no-deps --entrypoint=black vacinacao --check .
