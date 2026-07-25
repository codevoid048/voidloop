.PHONY: help plan apply

help:
	@echo "Available commands:"
	@echo "  make init           - Terraform init"
	@echo "  make plan           - Terraform plan"
	@echo "  make apply          - Terraform apply"
	@echo "  make destroy        - Terraform destroy"

init:
	terraform init -reconfigure

plan:
	terraform plan -out=tfplan

apply:
	terraform apply tfplan

destroy:
	terraform destroy