REGISTRY ?= docker.local.fyre.org

SERVICES := agent-gateway rag-loader rag-cli tools chromadb
SERVICE ?=
SERVICE_DIR := $(subst -,_,$(SERVICE))

.PHONY: build push release list-services check-service build-chromadb push-chromadb

build:
	@$(MAKE) check-service
	@if [ "$(SERVICE)" = "chromadb" ]; then \
		$(MAKE) -C docker/chromadb build REGISTRY=$(REGISTRY); \
	else \
		$(MAKE) -C services/$(SERVICE_DIR) build REGISTRY=$(REGISTRY); \
	fi

push:
	@$(MAKE) check-service
	@if [ "$(SERVICE)" = "chromadb" ]; then \
		$(MAKE) -C docker/chromadb push REGISTRY=$(REGISTRY); \
	else \
		$(MAKE) -C services/$(SERVICE_DIR) push REGISTRY=$(REGISTRY); \
	fi

release: build push

list-services:
	@echo "Available SERVICE values:"
	@for service in $(SERVICES); do \
		echo "  - $$service"; \
	done

check-service:
	@if [ -z "$(SERVICE)" ]; then \
		echo "SERVICE is required."; \
		echo "Example: make build SERVICE=agent-gateway"; \
		$(MAKE) list-services; \
		exit 1; \
	fi
	@if [ "$(SERVICE)" = "chromadb" ]; then \
		if [ ! -f "docker/chromadb/Makefile" ]; then \
			echo "Missing docker/chromadb/Makefile for SERVICE='chromadb'."; \
			exit 1; \
		fi; \
	else \
		if [ ! -f "services/$(SERVICE_DIR)/Makefile" ]; then \
			echo "Unknown SERVICE='$(SERVICE)'."; \
			$(MAKE) list-services; \
			exit 1; \
		fi; \
	fi

build-chromadb:
	@$(MAKE) -C docker/chromadb build REGISTRY=$(REGISTRY)

push-chromadb:
	@$(MAKE) -C docker/chromadb push REGISTRY=$(REGISTRY)
