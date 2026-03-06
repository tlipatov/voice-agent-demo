REGISTRY ?= docker.local.fyre.org
IMAGE_NAME ?= rag-cli
IMAGE_TAG ?= latest
IMAGE := $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: build push release

build:
	docker build -f Dockerfile -t $(IMAGE) ../..

push:
	docker push $(IMAGE)

release: build push
