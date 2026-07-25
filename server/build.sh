#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="${ROOT_DIR}/infra"
TFVARS_FILE="${TFVARS_FILE:-${INFRA_DIR}/terraform.tfvars}"

usage() {
  cat <<'EOF'
Usage: ./build.sh [options]

Build workflow for Void Loop Lambda backend:
1. Build and push Docker image to ECR
2. Update lambda_image_tag in infra/terraform.tfvars (advisory; CI owns image_uri)
3. Run default Django management commands (migrate)
4. Update Lambda function code to the new image

Options:
  --tag <tag>                  Image tag to use (default: v<version> from pyproject.toml)
  --ecr-url <url>              ECR repository URL (skip terraform output lookup)
  --project-name <name>        Project name for SSM path (default: from terraform.tfvars)
  --environment <name>         Environment for SSM path (default: from terraform.tfvars)
  --region <region>            AWS region (default: from terraform.tfvars)
  --skip-push                  Skip Docker build/push
  --skip-tfvars-update         Do not update lambda_image_tag in terraform.tfvars
  --skip-default-commands      Skip management commands run
  --skip-lambda-update         Do not call lambda update-function-code
  --cmd "<manage.py args>"     Extra manage.py command (repeatable)
  -h, --help                   Show help

Notes:
- Image tag defaults to v + version from pyproject.toml.
- Infra bootstrap (API Gateway, domain, SSM) is via infra/deploy.sh.
- Database URL and Django secret key are read from SSM:
  /<project-name>/<environment>/database_url
  /<project-name>/<environment>/django_secret_key
EOF
}

log() {
  echo "[build] $*"
}

warn() {
  echo "[build][warn] $*" >&2
}

die() {
  echo "[build][error] $*" >&2
  exit 1
}

require_cmd() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || die "Missing required command: $cmd"
}

get_tfvars_string() {
  local key="$1"
  local file="$2"

  if [[ ! -f "$file" ]]; then
    return 0
  fi

  local line
  line="$(grep -E "^${key}[[:space:]]*=" "$file" | tail -n 1 || true)"
  if [[ -z "$line" ]]; then
    return 0
  fi

  echo "$line" | sed -E 's/^[^=]*=[[:space:]]*"(.*)"[[:space:]]*$/\1/'
}

set_tfvars_string() {
  local key="$1"
  local value="$2"
  local file="$3"
  local tmp_file

  tmp_file="$(mktemp)"

  if grep -qE "^${key}[[:space:]]*=" "$file"; then
    sed -E "s|^(${key}[[:space:]]*=[[:space:]]*\").*(\"[[:space:]]*)$|\\1${value}\\2|" "$file" > "$tmp_file"
  else
    cat "$file" > "$tmp_file"
    printf "\n%s = \"%s\"\n" "$key" "$value" >> "$tmp_file"
  fi

  mv "$tmp_file" "$file"
}

get_project_version() {
  local file="${ROOT_DIR}/pyproject.toml"
  [[ -f "$file" ]] || die "Missing pyproject.toml at $file"

  local version
  version="$(grep -E '^version[[:space:]]*=' "$file" | head -n 1 | sed -E 's/^version[[:space:]]*=[[:space:]]*"([^"]+)".*/\1/')"
  [[ -n "$version" ]] || die "Could not read version from $file"
  echo "$version"
}

SKIP_PUSH=false
SKIP_TFVARS_UPDATE=false
SKIP_DEFAULT_COMMANDS=false
SKIP_LAMBDA_UPDATE=false

TAG=""
ECR_URL="${ECR_URL:-}"
PROJECT_NAME="${PROJECT_NAME:-}"
ENVIRONMENT="${ENVIRONMENT:-}"
AWS_REGION="${AWS_REGION:-}"
MANAGE_COMMANDS=()
DEFAULT_MANAGE_COMMANDS=(
  "migrate --noinput"
)
DB_DNS_RETRY_ATTEMPTS="${DB_DNS_RETRY_ATTEMPTS:-4}"
DB_DNS_RETRY_DELAY_SECONDS="${DB_DNS_RETRY_DELAY_SECONDS:-5}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tag)
      TAG="${2:-}"
      [[ -n "$TAG" ]] || die "--tag requires a value"
      shift
      ;;
    --ecr-url)
      ECR_URL="${2:-}"
      [[ -n "$ECR_URL" ]] || die "--ecr-url requires a value"
      shift
      ;;
    --project-name)
      PROJECT_NAME="${2:-}"
      [[ -n "$PROJECT_NAME" ]] || die "--project-name requires a value"
      shift
      ;;
    --environment)
      ENVIRONMENT="${2:-}"
      [[ -n "$ENVIRONMENT" ]] || die "--environment requires a value"
      shift
      ;;
    --region)
      AWS_REGION="${2:-}"
      [[ -n "$AWS_REGION" ]] || die "--region requires a value"
      shift
      ;;
    --skip-push)
      SKIP_PUSH=true
      ;;
    --skip-tfvars-update)
      SKIP_TFVARS_UPDATE=true
      ;;
    --skip-default-commands)
      SKIP_DEFAULT_COMMANDS=true
      ;;
    --skip-lambda-update)
      SKIP_LAMBDA_UPDATE=true
      ;;
    --cmd)
      [[ -n "${2:-}" ]] || die "--cmd requires a value"
      MANAGE_COMMANDS+=("$2")
      shift
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
require_cmd docker
require_cmd grep
require_cmd sed
require_cmd openssl

[[ -f "$TFVARS_FILE" ]] || die "Missing terraform.tfvars at $TFVARS_FILE"

if [[ -z "$PROJECT_NAME" ]]; then
  PROJECT_NAME="$(get_tfvars_string "project_name" "$TFVARS_FILE")"
fi
if [[ -z "$ENVIRONMENT" ]]; then
  ENVIRONMENT="$(get_tfvars_string "environment" "$TFVARS_FILE")"
fi
if [[ -z "$AWS_REGION" ]]; then
  AWS_REGION="$(get_tfvars_string "aws_region" "$TFVARS_FILE")"
fi

PROJECT_NAME="${PROJECT_NAME:-voidloop}"
ENVIRONMENT="${ENVIRONMENT:-prod}"
AWS_REGION="${AWS_REGION:-ap-south-2}"

if [[ -z "$TAG" ]]; then
  TAG="v$(get_project_version)"
fi

log "Project: ${PROJECT_NAME}"
log "Environment: ${ENVIRONMENT}"
log "Region: ${AWS_REGION}"
log "Image tag: ${TAG}"

log "Validating AWS credentials"
aws sts get-caller-identity >/dev/null

if [[ -z "$ECR_URL" ]]; then
  require_cmd terraform
  log "Initializing Terraform to read ECR output"
  terraform -chdir="$INFRA_DIR" init -reconfigure -input=false >/dev/null
  ECR_URL="$(terraform -chdir="$INFRA_DIR" output -raw ecr_repository_url)"
fi

IMAGE_URI="${ECR_URL}:${TAG}"

if [[ "$SKIP_PUSH" != "true" ]]; then
  ECR_REGISTRY="${ECR_URL%%/*}"

  log "Logging into ECR: ${ECR_REGISTRY}"
  aws ecr get-login-password --region "$AWS_REGION" \
    | docker login --username AWS --password-stdin "$ECR_REGISTRY" >/dev/null

  log "Building and pushing image: ${IMAGE_URI}"
  docker buildx build \
    --platform linux/amd64 \
    --provenance=false \
    --sbom=false \
    -f "$ROOT_DIR/Dockerfile.lambda" \
    -t "$IMAGE_URI" \
    --push \
    "$ROOT_DIR"
else
  warn "Skipping Docker build/push"
fi

if [[ "$SKIP_TFVARS_UPDATE" != "true" ]]; then
  set_tfvars_string "lambda_image_tag" "$TAG" "$TFVARS_FILE"
  log "Updated lambda_image_tag in ${TFVARS_FILE}"
else
  warn "Skipping terraform.tfvars tag update"
fi

if [[ "$SKIP_DEFAULT_COMMANDS" != "true" ]]; then
  PARAM_PREFIX="/${PROJECT_NAME}/${ENVIRONMENT}"

  log "Reading runtime DB settings from SSM"
  DATABASE_URL="$(aws ssm get-parameter \
    --name "${PARAM_PREFIX}/database_url" \
    --with-decryption \
    --region "$AWS_REGION" \
    --query 'Parameter.Value' \
    --output text 2>/dev/null || true)"

  SECRET_KEY="$(aws ssm get-parameter \
    --name "${PARAM_PREFIX}/django_secret_key" \
    --with-decryption \
    --region "$AWS_REGION" \
    --query 'Parameter.Value' \
    --output text 2>/dev/null || true)"

  [[ -n "$DATABASE_URL" ]] || die "Missing SSM parameter: ${PARAM_PREFIX}/database_url"

  if [[ -z "$SECRET_KEY" ]]; then
    SECRET_KEY="$(openssl rand -hex 32)"
    warn "Missing ${PARAM_PREFIX}/django_secret_key in SSM; using generated value for migration run"
  fi

  log "Pulling image for migration run: ${IMAGE_URI}"
  docker pull "$IMAGE_URI" >/dev/null

  DOCKER_ENV_ARGS=(
    -e DJANGO_ENV=production
    -e DEBUG=False
    -e DATABASE_URL="$DATABASE_URL"
    -e SECRET_KEY="$SECRET_KEY"
  )

  run_manage_command() {
    local cmd="$1"
    local attempt=1
    local output
    local status

    while (( attempt <= DB_DNS_RETRY_ATTEMPTS )); do
      log "Running manage.py ${cmd} (attempt ${attempt}/${DB_DNS_RETRY_ATTEMPTS})"

      set +e
      output="$(docker run --rm \
        --network host \
        --entrypoint sh \
        "${DOCKER_ENV_ARGS[@]}" \
        "$IMAGE_URI" \
        -lc "python manage.py ${cmd}" 2>&1)"
      status=$?
      set -e

      if [[ $status -eq 0 ]]; then
        echo "$output"
        return 0
      fi

      echo "$output" >&2

      if echo "$output" | grep -q "failed to resolve host" && (( attempt < DB_DNS_RETRY_ATTEMPTS )); then
        warn "Transient DNS resolution failure while running '${cmd}'. Retrying in ${DB_DNS_RETRY_DELAY_SECONDS}s..."
        sleep "$DB_DNS_RETRY_DELAY_SECONDS"
        ((attempt++))
        continue
      fi

      return $status
    done
  }

  if [[ ${#MANAGE_COMMANDS[@]} -eq 0 ]]; then
    MANAGE_COMMANDS=("${DEFAULT_MANAGE_COMMANDS[@]}")
  fi

  for cmd in "${MANAGE_COMMANDS[@]}"; do
    run_manage_command "$cmd"
  done
else
  warn "Skipping default management commands"
fi

LAMBDA_FUNCTION_NAME="${PROJECT_NAME}-${ENVIRONMENT}"

if [[ "$SKIP_LAMBDA_UPDATE" != "true" ]]; then
  if aws lambda get-function \
    --function-name "$LAMBDA_FUNCTION_NAME" \
    --region "$AWS_REGION" >/dev/null 2>&1; then
    log "Updating Lambda function code: ${LAMBDA_FUNCTION_NAME} -> ${IMAGE_URI}"
    aws lambda update-function-code \
      --function-name "$LAMBDA_FUNCTION_NAME" \
      --image-uri "$IMAGE_URI" \
      --region "$AWS_REGION" >/dev/null

    log "Waiting for Lambda update to succeed"
    aws lambda wait function-updated \
      --function-name "$LAMBDA_FUNCTION_NAME" \
      --region "$AWS_REGION"
    log "Lambda updated"
  else
    warn "Lambda ${LAMBDA_FUNCTION_NAME} does not exist yet (bootstrap)."
    warn "Image is in ECR. Create the function with: cd infra && terraform apply"
    warn "Then re-run: ./build.sh --skip-push --skip-default-commands"
  fi
else
  warn "Skipping Lambda function code update"
fi

cat <<EOF

Done.
Image: ${IMAGE_URI}
Lambda: ${LAMBDA_FUNCTION_NAME}

Useful examples:
- Build and push only: ./build.sh --skip-default-commands --skip-lambda-update
- Build, push, migrate, update Lambda: ./build.sh
- Build, push, and run custom commands:
  ./build.sh --cmd "migrate --noinput"
EOF
