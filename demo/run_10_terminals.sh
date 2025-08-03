#!/bin/bash

echo "Starting 100 curl requests to vLLM service..."

total_terminals=100
launched=0

while [ $launched -lt $total_terminals ]; do
    batch_size=$((RANDOM % 10 + 1))
    if [ $((launched + batch_size)) -gt $total_terminals ]; then
        batch_size=$((total_terminals - launched))
    fi

    for ((j=1; j<=batch_size; j++)); do
        terminal_id=$((launched + j))
        echo "Launching terminal $terminal_id..."
        (
            echo "Terminal $terminal_id: Starting request..."
            curl -s -X POST http://localhost:8000/v1/completions \
                -H "Content-Type: application/json" \
                -d '{
                    "model": "Qwen/Qwen2.5-7B-Instruct",
                    "prompt": "San Francisco is a... Explain the significance of this city in the tech industry.",
                    "max_tokens": 512,
                    "temperature": 0
                }'
        ) &
    done

    launched=$((launched + batch_size))

    sleep_time=$(awk -v min=0 -v max=2 'BEGIN{srand(); print min+rand()*(max-min)}')
    sleep $sleep_time
done

echo "All $total_terminals terminals launched. Waiting for completion..."

wait

echo "All curl requests completed!"