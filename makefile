PWD = $(shell pwd)
PROJECTNAME = auctioneer
REPO = mdev.docker.lamoda.ru
VERSION = $(shell git rev-parse --short HEAD)
DATE = $(shell date +%Y-%m-%d)
DEFAULT_IMAGE_NAME = base
IMAGE_NAME = $(REPO)/$(PROJECTNAME)/$(DEFAULT_IMAGE_NAME)
IMAGE_ID = $(shell docker images -aqf "label=$(IMAGE_NAME)")
CONTAINER_NAME = auctioneer
ENV_FILE = local.env

.PHONY: build, shell, run, run_celery_beat, run_celery_worker, remove, docs

@build: build
@stub:
	echo "VERSION=$(DATE)-$(VERSION)" > .artifact
@push:
	docker push $(REPO)/$(PROJECTNAME)/base:$(DATE)-$(VERSION)



build:
	docker build -t $(IMAGE_NAME):$(DATE)-$(VERSION) -t $(IMAGE_NAME):latest --label $(IMAGE_NAME) --rm  .

shell:
	docker run -it --rm $(IMAGE_NAME) sh

run:
	docker run -it --rm --env-file=$(ENV_FILE) --name $(CONTAINER_NAME) -p 8000:8000 $(IMAGE_NAME) \
	python manage.py runserver 0.0.0.0:8000

run_celery_worker:
	docker exec -it $(shell docker ps -aqf "name=$(CONTAINER_NAME)") celery -A common worker -l info -Q keyword_bids

run_celery_beat:
	docker exec -it $(shell docker ps -aqf "name=$(CONTAINER_NAME)") celery -A common beat -l info

remove:
	docker rmi --force $(IMAGE_ID)

docs:
	pip install -U sphinx && pip install sphinx-rtd-theme && cd docs && make html && ln -s docs/build/html/index.html manual.html
