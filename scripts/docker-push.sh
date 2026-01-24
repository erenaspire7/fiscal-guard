#!/bin/bash

# Script to build and push Docker images to Docker Hub using buildx
# Usage: ./scripts/docker-push.sh <docker-username> [version]

set -e

# Check if Docker username is provided
if [ -z "$1" ]; then
  echo "Error: Docker Hub username is required"
  echo "Usage: ./scripts/docker-push.sh <docker-username> [version]"
  echo "Example: ./scripts/docker-push.sh myuser latest"
  exit 1
fi

DOCKER_USERNAME=$1
IMAGE_NAME="fiscal-guard"
VERSION=${2:-latest}
PLATFORM="linux/amd64,linux/arm64"

echo "Setting up buildx builder..."
docker buildx create --name fiscal-guard-builder --use 2>/dev/null || docker buildx use fiscal-guard-builder

# Build and push API image
echo "Building and pushing API image for ${PLATFORM}..."
docker buildx build \
  --platform ${PLATFORM} \
  --file api/Dockerfile \
  --tag ${DOCKER_USERNAME}/${IMAGE_NAME}-api:${VERSION} \
  --push \
  .


echo "Successfully pushed multi-platform images:"
echo "  - ${DOCKER_USERNAME}/${IMAGE_NAME}-api:${VERSION}"
echo "  Platforms: ${PLATFORM}"
