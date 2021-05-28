build-and-push:
	docker-compose build
	docker tag vacinacao-img:latest 244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:0.8.5
	docker push 244978745220.dkr.ecr.us-east-1.amazonaws.com/vacinacao-app:0.8.5

deploy:
	sam deploy --no-confirm-changeset

webapp:
	python src/vacinacao/entrypoints.py

reindex:
	python src/vacinacao/indexer.py
