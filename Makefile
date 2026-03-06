REGISTRY ?= docker.local.fyre.org

SERVICES := agent-gateway rag-loader rag-cli tools
SERVICE ?=
SERVICE_DIR := $(subst -,_,$(SERVICE))

.PHONY: build push release list-services check-service

build:
	@$(MAKE) check-service
	@$(MAKE) -C services/$(SERVICE_DIR) build REGISTRY=$(REGISTRY)

push:
	@$(MAKE) check-service
	@$(MAKE) -C services/$(SERVICE_DIR) push REGISTRY=$(REGISTRY)

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
	@if [ ! -f "services/$(SERVICE_DIR)/Makefile" ]; then \
		echo "Unknown SERVICE='$(SERVICE)'."; \
		$(MAKE) list-services; \
		exit 1; \
	fi
