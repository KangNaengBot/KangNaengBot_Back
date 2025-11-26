#!/bin/bash

# ADK Web UI 실행 스크립트 (Secret Manager 사용)

set -e

PROJECT_ID="kangnam-backend"

echo "========================================="
echo "  ADK Web UI - Secret Manager 연동"
echo "========================================="
echo ""

# Secret Manager에서 환경 변수 로드
echo "[1/2] Secret Manager에서 환경 변수 로드 중..."

export GOOGLE_CLOUD_PROJECT=$(gcloud secrets versions access latest --secret=GOOGLE_CLOUD_PROJECT --project=$PROJECT_ID 2>/dev/null || echo "kangnam-backend")
export VERTEX_AI_LOCATION=$(gcloud secrets versions access latest --secret=VERTEX_AI_LOCATION --project=$PROJECT_ID 2>/dev/null || echo "us-east4")

echo "  ✓ GOOGLE_CLOUD_PROJECT: $GOOGLE_CLOUD_PROJECT"
echo "  ✓ VERTEX_AI_LOCATION: $VERTEX_AI_LOCATION"
echo ""

# ADK Web UI 실행
echo "[2/2] ADK Web UI 시작..."
echo ""

adk web
