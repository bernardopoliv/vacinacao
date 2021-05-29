build-and-push:
	docker-compose build
	docker tag vacinacao-img:latest 244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:0.10.3
	docker push 244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:0.10.3

ecr-login:
	aws ecr get-login --no-include-email | sh

deploy:
	sam deploy --no-confirm-changeset --image-repositories VacinacaoFunction=244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:0.10.3 --image-repositories VacinacaoFunctionIndexer=244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:0.10.3

webapp:
	python src/vacinacao/entrypoints.py

reindex:
	python src/vacinacao/indexer.py
