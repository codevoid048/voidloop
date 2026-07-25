#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

usage() {
  cat <<'EOF'
Usage: ./deploy.sh [options]

Deployment flow for Void Loop API infra:
1. Bootstrap remote Terraform state (S3 + lockfile)
2. Run terraform init/plan/apply

Options:
  --auto-approve         Apply terraform plan without prompt
  --non-interactive      Fail instead of prompting for apply
  --skip-state-bootstrap Skip S3 backend bootstrap
  --skip-terraform       Skip terraform init/plan/apply
  -h, --help             Show this help

EOF
}

log() {
  echo "[deploy] $*"
}

die() {
  echo "[deploy][error] $*" >&2
  exit 1
}

require_cmd() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || die "Missing required command: $cmd"
}

create_state_bucket() {
  if aws s3api head-bucket --bucket "$STATE_BUCKET" >/dev/null 2>&1; then
    log "State bucket already exists: $STATE_BUCKET"
  else
    log "Creating state bucket: $STATE_BUCKET"
    if [[ "$AWS_REGION" == "us-east-1" ]]; then
      aws s3api create-bucket --bucket "$STATE_BUCKET" --region "$AWS_REGION" >/dev/null
    else
      aws s3api create-bucket \
        --bucket "$STATE_BUCKET" \
        --region "$AWS_REGION" \
        --create-bucket-configuration "LocationConstraint=$AWS_REGION" >/dev/null
    fi
  fi

  aws s3api put-bucket-versioning \
    --bucket "$STATE_BUCKET" \
    --versioning-configuration Status=Enabled >/dev/null

  aws s3api put-bucket-encryption \
    --bucket "$STATE_BUCKET" \
    --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}' >/dev/null

  aws s3api put-public-access-block \
    --bucket "$STATE_BUCKET" \
    --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" >/dev/null

  log "State bucket configured (versioning + encryption + public block)"
}

AUTO_APPROVE=false
NON_INTERACTIVE=false
SKIP_STATE_BOOTSTRAP=false
SKIP_TERRAFORM=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --auto-approve)
      AUTO_APPROVE=true
      ;;
    --non-interactive)
      NON_INTERACTIVE=true
      ;;
    --skip-state-bootstrap)
      SKIP_STATE_BOOTSTRAP=true
      ;;
    --skip-terraform)
      SKIP_TERRAFORM=true
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "Unknown option: $1"
      ;;
  esac
  shift
done

require_cmd aws
require_cmd terraform

if [[ -f .deploy.env ]]; then
  log "Loading values from .deploy.env"
  # shellcheck source=/dev/null
  source .deploy.env
fi

PROJECT_NAME="${PROJECT_NAME:-voidloop}"
ENVIRONMENT="${ENVIRONMENT:-prod}"
AWS_REGION="${AWS_REGION:-ap-south-2}"
STATE_BUCKET="${STATE_BUCKET:-${PROJECT_NAME}-terraform-state-${ENVIRONMENT}-aps2}"
TFVARS_FILE="${TFVARS_FILE:-terraform.tfvars}"

log "Validating AWS credentials"
aws sts get-caller-identity >/dev/null

if [[ ! -f "$TFVARS_FILE" ]]; then
  if [[ -f terraform.tfvars.example ]]; then
    cp terraform.tfvars.example "$TFVARS_FILE"
    log "Created $TFVARS_FILE from terraform.tfvars.example"
  else
    die "Missing terraform.tfvars.example"
  fi
fi

if [[ "$SKIP_STATE_BOOTSTRAP" != "true" ]]; then
  create_state_bucket
else
  log "Skipping state bootstrap"
fi

if [[ "$SKIP_TERRAFORM" != "true" ]]; then
  log "Running terraform init"
  terraform init -reconfigure

  log "Running terraform plan"
  terraform plan -out=tfplan

  if [[ "$AUTO_APPROVE" == "true" ]]; then
    log "Applying terraform plan"
    terraform apply tfplan
  else
    if [[ "$NON_INTERACTIVE" == "true" ]]; then
      die "Terraform apply confirmation required. Re-run with --auto-approve"
    fi

    read -r -p "Apply terraform plan now? (y/N): " confirm_apply
    if [[ "$confirm_apply" =~ ^[Yy]$ ]]; then
      terraform apply tfplan
    else
      log "Skipping terraform apply by user choice"
      exit 0
    fi
  fi
else
  log "Skipping terraform init/plan/apply"
  exit 0
fi

API_TARGET="$(terraform output -raw api_domain_target 2>/dev/null || true)"
GHA_ROLE="$(terraform output -raw github_actions_role_arn 2>/dev/null || true)"
ECR_URL="$(terraform output -raw ecr_repository_url 2>/dev/null || true)"

cat <<EOF

Deployment flow completed.

What was handled:
- S3 state bucket + encryption + public block + lockfile
- Terraform init/plan/apply (including SSM secrets from terraform.tfvars)

Next steps:
1. Cloudflare DNS: CNAME api.voidloop -> ${API_TARGET:-<api_domain_target>}
2. Push first image: ../build.sh  (or wait for GitHub Actions)
3. Set GitHub secret AWS_ROLE_ARN=${GHA_ROLE:-<github_actions_role_arn>}
4. ECR repo: ${ECR_URL:-<ecr_repository_url>}

Checks:
- aws lambda get-function-configuration --function-name ${PROJECT_NAME}-${ENVIRONMENT} --region ${AWS_REGION}
- aws logs tail /aws/lambda/${PROJECT_NAME}-${ENVIRONMENT} --region ${AWS_REGION} --follow
EOF
