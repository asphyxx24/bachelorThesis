#!/bin/bash
set -e
cd ~/thesis
source .venv/bin/activate
source .env

OUTDIR=data/layer2
DATE=20260504_1323

declare -A PROVIDERS
PROVIDERS=(
  [deepgram_stt]="api.deepgram.com"
  [revai_stt]="api.rev.ai"
  [azure_stt]="italynorth.stt.speech.microsoft.com"
  [openai_llm]="api.openai.com"
  [groq_llm]="api.groq.com"
  [mistral_llm]="api.mistral.ai"
  [deepgram_tts]="api.deepgram.com"
  [openai_tts]="api.openai.com"
  [azure_tts]="italynorth.tts.speech.microsoft.com"
)

declare -a ORDER=(deepgram_stt revai_stt azure_stt openai_llm groq_llm mistral_llm deepgram_tts openai_tts azure_tts)

capture_one() {
  local name=$1
  local host=$2
  local pcap="${OUTDIR}/capture_${name}_${DATE}.pcap"

  echo ""
  echo "=== ${name} (host: ${host}) ==="
  echo "  Starting tcpdump..."
  sudo tcpdump -i ens5 -w "${pcap}" host "${host}" -s 0 -c 10000 2>/dev/null &
  local TCPDUMP_PID=$!
  sleep 1

  echo "  Running Layer-3 measurement (n=1)..."
  case ${name} in
    deepgram_stt)
      python -c "
import asyncio
from measurements.layer3.stt_deepgram import load_pcm, measure_once
pcm = load_pcm('measurements/layer3/sample.wav')
r = asyncio.run(measure_once('', pcm))
print(f'  Result: {r}')
"
      ;;
    revai_stt)
      python -c "
import asyncio
from measurements.layer3.stt_revai import load_pcm, measure_once
pcm = load_pcm('measurements/layer3/sample.wav')
r = asyncio.run(measure_once('', pcm))
print(f'  Result: {r}')
"
      ;;
    azure_stt)
      python -c "
import asyncio
from measurements.layer3.stt_azure import load_pcm, measure_once
pcm = load_pcm('measurements/layer3/sample.wav')
r = asyncio.run(measure_once('', pcm))
print(f'  Result: {r}')
"
      ;;
    openai_llm)
      python -c "
import asyncio
from measurements.layer3.llm_openai import measure_once
r = asyncio.run(measure_once(''))
print(f'  Result: {r}')
"
      ;;
    groq_llm)
      python -c "
import asyncio
from measurements.layer3.llm_groq import measure_once
r = asyncio.run(measure_once(''))
print(f'  Result: {r}')
"
      ;;
    mistral_llm)
      python -c "
import asyncio
from measurements.layer3.llm_mistral import measure_once
r = asyncio.run(measure_once(''))
print(f'  Result: {r}')
"
      ;;
    deepgram_tts)
      python -c "
import asyncio
from measurements.layer3.tts_deepgram import measure_once
r = asyncio.run(measure_once(''))
print(f'  Result: {r}')
"
      ;;
    openai_tts)
      python -c "
import asyncio
from measurements.layer3.tts_openai import measure_once
r = asyncio.run(measure_once(''))
print(f'  Result: {r}')
"
      ;;
    azure_tts)
      python -c "
import asyncio
from measurements.layer3.tts_azure import measure_once
r = asyncio.run(measure_once(''))
print(f'  Result: {r}')
"
      ;;
  esac

  echo "  Stopping tcpdump..."
  sleep 2
  sudo kill ${TCPDUMP_PID} 2>/dev/null || true
  wait ${TCPDUMP_PID} 2>/dev/null || true
  
  local size=$(stat -c%s "${pcap}" 2>/dev/null || echo 0)
  echo "  Saved: ${pcap} (${size} bytes)"
}

echo "=== Layer-2 Captures: ${DATE} ==="
echo "Output: ${OUTDIR}/"

for name in "${ORDER[@]}"; do
  host=${PROVIDERS[$name]}
  capture_one "${name}" "${host}"
done

echo ""
echo "=== Alle Captures fertig ==="
ls -lh ${OUTDIR}/capture_*_${DATE}.pcap
