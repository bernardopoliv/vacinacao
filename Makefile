check-version:
# Checks if VERSION is a defined variable.
# Must not be indented!
ifndef VERSION
	$(error VERSION is undefined.)
endif

up:
	docker-compose up -d --build

build-and-push: check-version ecr-login
	docker-compose build
	docker tag vacinacao-img:latest 244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:${VERSION}
	docker push 244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:${VERSION}

ecr-login:
	aws ecr get-login --no-include-email | sh

deploy-beta: check-version
	sam deploy --no-confirm-changeset --image-repositories VacinacaoFunction=244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:${VERSION} --image-repositories VacinacaoFunctionIndexer=244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:${VERSION} --config-env beta --parameter-overrides STAGE=beta URL="https://beta.meunomesaiunalista.com.br/" IMAGEURI="244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:${VERSION}"

deploy-prod: check-version
	sam deploy --no-confirm-changeset --image-repositories VacinacaoFunction=244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:${VERSION} --image-repositories VacinacaoFunctionIndexer=244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:${VERSION} --config-env prod --parameter-overrides STAGE=prod URL="https://meunomesaiunalista.com.br/" IMAGEURI="244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:${VERSION}"

webapp:
	python src/vacinacao/entrypoints.py
	# TODO
	# docker-compose run --rm --no-deps --entrypoint=python vacinacao "/src/vacinacao/entrypoints.py"

reindex:
	python src/vacinacao/service_layer/indexer.py

unit-tests: up
	docker-compose run --rm --no-deps --entrypoint=pytest vacinacao /tests/test_unit.py -vv

e2e-tests: up
	docker-compose run --rm --no-deps --entrypoint=pytest vacinacao /tests/test_e2e.py -vv

test: up e2e-tests unit-tests

lint: up
	docker-compose run --rm --no-deps --entrypoint=flake8 vacinacao "/src" "/tests"
	docker-compose run --rm --no-deps --entrypoint=black vacinacao --check "/src" "/tests"

snapshot: up
	docker-compose run --rm --no-deps --entrypoint=pytest vacinacao /tests/test_e2e.py -vv --snapshot-update