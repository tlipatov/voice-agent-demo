REGISTRY ?= docker.local.fyre.org
IMAGE_NAME ?= agent-gateway
IMAGE_TAG ?= latest
IMAGE := $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
COMPOSE ?= $(shell if docker compose version >/dev/null 2>&1; then echo "docker compose"; else echo "docker-compose"; fi)

.PHONY: build push release test e2e-up e2e-down e2e-test

build:
	docker build -f Dockerfile -t $(IMAGE) ../..

push:
	docker push $(IMAGE)

release: build push

test: e2e-test

e2e-up:
	$(COMPOSE) up -d

e2e-down:
	$(COMPOSE) down

e2e-test:
	@set -e; \
	$(COMPOSE) up -d; \
	trap '$(COMPOSE) down' EXIT; \
	PYTHONPATH=../.. python3 -m unittest discover -s tests -p "test_*.py"
