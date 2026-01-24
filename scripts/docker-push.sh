#!/bin/bash

# Script to build and push Docker images to Docker Hub
# Usage: ./scripts/docker-push.sh <docker-username>

set -e

# Check if Docker username is provided
if [ -z "$1" ]; then
  echo "Error: Docker Hub username is required"
  echo "Usage: ./scripts/docker-push.sh <docker-username>"
  exit 1
fi

DOCKER_USERNAME=$1
IMAGE_NAME="fiscal-guard"
VERSION=${2:-latest}

echo "Building images with docker compose..."
docker compose build

# Tag and push API image
echo "Tagging and pushing API image..."
docker tag fiscal-guard-api ${DOCKER_USERNAME}/${IMAGE_NAME}-api:${VERSION}
docker push ${DOCKER_USERNAME}/${IMAGE_NAME}-api:${VERSION}

# Tag and push UI image
echo "Tagging and pushing UI image..."
docker tag fiscal-guard-ui ${DOCKER_USERNAME}/${IMAGE_NAME}-ui:${VERSION}
docker push ${DOCKER_USERNAME}/${IMAGE_NAME}-ui:${VERSION}

echo "Successfully pushed images:"
echo "  - ${DOCKER_USERNAME}/${IMAGE_NAME}-api:${VERSION}"
echo "  - ${DOCKER_USERNAME}/${IMAGE_NAME}-ui:${VERSION}"
