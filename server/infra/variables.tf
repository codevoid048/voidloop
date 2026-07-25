variable "project_name" {
  description = "Project slug used in resource names."
  type        = string
  default     = "voidloop"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "prod"
}

variable "aws_region" {
  description = "Primary AWS region for Lambda/API/ECR."
  type        = string
  default     = "ap-south-2"
}

variable "tags" {
  description = "Additional tags to apply to resources."
  type        = map(string)
  default     = {}
}

variable "lambda_image_tag" {
  description = "Initial container image tag in ECR for Lambda (CI updates image_uri afterwards)."
  type        = string
  default     = "v0.1.0"
}

variable "lambda_architecture" {
  description = "Lambda architecture."
  type        = string
  default     = "x86_64"

  validation {
    condition     = contains(["x86_64", "arm64"], var.lambda_architecture)
    error_message = "lambda_architecture must be one of: x86_64, arm64."
  }
}

variable "lambda_memory_size" {
  description = "Lambda memory size in MB."
  type        = number
  default     = 1024
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds."
  type        = number
  default     = 30
}

variable "lambda_ephemeral_storage_mb" {
  description = "Lambda ephemeral storage size in MB."
  type        = number
  default     = 512
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days."
  type        = number
  default     = 30
}

variable "api_stage_name" {
  description = "API Gateway stage name."
  type        = string
  default     = "prod"
}

variable "api_domain_name" {
  description = "Custom domain for API Gateway (for example api.voidloop.williamkeri.com)."
  type        = string
}

variable "api_acm_certificate_arn" {
  description = "ACM certificate ARN in the same region as API Gateway."
  type        = string
}

variable "django_secret_key" {
  description = "Django SECRET_KEY for production (stored in SSM by Terraform)."
  type        = string
  sensitive   = true

  validation {
    condition     = length(trimspace(var.django_secret_key)) > 0
    error_message = "django_secret_key must be set in terraform.tfvars."
  }
}

variable "allowed_hosts" {
  description = "Comma-separated ALLOWED_HOSTS value."
  type        = string
}

variable "cors_allowed_origins" {
  description = "Comma-separated CORS_ALLOWED_ORIGINS value."
  type        = string
}

variable "database_url" {
  description = "PostgreSQL connection URL (stored in SSM by Terraform)."
  type        = string
  sensitive   = true

  validation {
    condition     = length(trimspace(var.database_url)) > 0
    error_message = "database_url must be set in terraform.tfvars."
  }
}

variable "jwt_access_token_lifetime_minutes" {
  description = "JWT access token lifetime in minutes."
  type        = number
  default     = 60
}

variable "jwt_refresh_token_lifetime_days" {
  description = "JWT refresh token lifetime in days."
  type        = number
  default     = 7
}

variable "extra_lambda_env" {
  description = "Additional environment variables merged into Lambda env."
  type        = map(string)
  default     = {}
}

variable "github_repository" {
  description = "Monorepo GitHub repository (owner/name) allowed to assume the deploy role via OIDC."
  type        = string
}

variable "create_github_oidc_provider" {
  description = "Create the GitHub Actions OIDC provider in this account. Set false and pass github_oidc_provider_arn if one already exists."
  type        = bool
  default     = true
}

variable "github_oidc_provider_arn" {
  description = "Existing GitHub OIDC provider ARN when create_github_oidc_provider is false."
  type        = string
  default     = ""

  validation {
    condition     = var.create_github_oidc_provider || length(trimspace(var.github_oidc_provider_arn)) > 0
    error_message = "github_oidc_provider_arn is required when create_github_oidc_provider is false."
  }
}
