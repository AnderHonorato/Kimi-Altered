#!/usr/bin/env bash
# Prepara e testa o motor oficial sem baixar os pesos (1,56 TB).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENGINE="$ROOT/engine/kimi-k3-in-c"
URL="https://github.com/FareedKhan-dev/kimi-k3-in-c.git"
REF="v1.0.0"

for cmd in git make gcc; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    printf 'ERRO: comando ausente: %s\n' "$cmd" >&2
    exit 1
  fi
done

if [ -n "${MSYSTEM:-}" ]; then
  if [ "$MSYSTEM" != "MINGW64" ]; then
    echo "AVISO: no Windows utilize o terminal MSYS2 MinGW x64 (MINGW64)." >&2
    exit 1
  fi
fi

mkdir -p "$ROOT/engine"
if [ -d "$ENGINE/.git" ]; then
  echo "Motor existente detectado. Sem atualizacao automatica."
elif [ -e "$ENGINE" ]; then
  echo "ERRO: pasta do motor ja existe, mas nao e um clone Git." >&2
  exit 1
else
  echo "Clonando versao oficial marcada como $REF..."
  git clone --depth 1 --branch "$REF" "$URL" "$ENGINE"
fi

echo "Compilando o motor..."
make -C "$ENGINE" -j2
echo "Executando testes do motor sem checkpoint..."
make -C "$ENGINE" test

echo "Preparacao concluida. Nenhum modelo gigante foi baixado."
echo "Proximo passo: verificar requisitos de RAM, CPU e SSD antes do checkpoint."
