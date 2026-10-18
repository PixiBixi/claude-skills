ROOT_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
SCRIPT   := $(ROOT_DIR)skills/.update-skills.py

.DEFAULT_GOAL := help

.PHONY: help update-skills check validate

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

update-skills: ## Fetch latest SKILL.md from upstream sources (one commit per updated skill)
	@python3 $(SCRIPT) --commit

check: ## Show skills diffs without modifying files (dry-run)
	@python3 $(SCRIPT) --check

validate: ## Validate the plugin and marketplace manifests
	@claude plugin validate $(ROOT_DIR)
