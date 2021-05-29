build-and-push:
	docker-compose build
	docker tag vacinacao-img:latest 244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:${GIT_COMMIT_REF}
	docker push 244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:${GIT_COMMIT_REF}

deploy:
	sam deploy --no-confirm-changeset --image-repositories VacinacaoFunction=244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:${GIT_COMMIT_REF} --image-repositories VacinacaoFunctionIndexer=244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:${GIT_COMMIT_REF}

webapp:
	python src/vacinacao/entrypoints.py

reindex:
	python src/vacinacao/indexer.py
