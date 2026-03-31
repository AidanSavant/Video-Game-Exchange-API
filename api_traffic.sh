#!/bin/bash

BASE_URL="http://localhost:8080"
SLEEP=0.2

echo "=== Registering users ==="
curl -s -X POST "$BASE_URL/api/register" \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@test.com","password":"password123","street_address":"123 Main St"}' | jq .

curl -s -X POST "$BASE_URL/api/register" \
  -H "Content-Type: application/json" \
  -d '{"name":"Bob","email":"bob@test.com","password":"password123","street_address":"456 Elm St"}' | jq .

sleep $SLEEP

echo ""
echo "=== Logging in ==="
ALICE_JWT=$(curl -s -X POST "$BASE_URL/api/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@test.com","password":"password123"}' | jq -r '.jwt')

BOB_JWT=$(curl -s -X POST "$BASE_URL/api/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"bob@test.com","password":"password123"}' | jq -r '.jwt')

echo "Alice JWT: $ALICE_JWT"
echo "Bob JWT:   $BOB_JWT"

sleep $SLEEP

echo ""
echo "=== Adding games for Alice ==="
curl -s -X POST "$BASE_URL/api/games" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ALICE_JWT" \
  -d '{"name":"Halo","publisher":"Bungie","year":2001,"platform":"Xbox","condition":"Good"}' | jq .

curl -s -X POST "$BASE_URL/api/games" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ALICE_JWT" \
  -d '{"name":"Zelda","publisher":"Nintendo","year":1998,"platform":"N64","condition":"Excellent"}' | jq .

sleep $SLEEP

echo ""
echo "=== Adding games for Bob ==="
curl -s -X POST "$BASE_URL/api/games" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BOB_JWT" \
  -d '{"name":"Mario Kart","publisher":"Nintendo","year":1996,"platform":"N64","condition":"Fair"}' | jq .

curl -s -X POST "$BASE_URL/api/games" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BOB_JWT" \
  -d '{"name":"Doom","publisher":"id Software","year":1993,"platform":"PC","condition":"Good"}' | jq .

sleep $SLEEP

echo ""
echo "=== Spamming GET requests to generate latency data ==="
for i in $(seq 1 30); do
  curl -s "$BASE_URL/api/self" \
    -H "Authorization: Bearer $ALICE_JWT" > /dev/null

  curl -s "$BASE_URL/api/self" \
    -H "Authorization: Bearer $BOB_JWT" > /dev/null

  curl -s "$BASE_URL/api/games/Halo" \
    -H "Authorization: Bearer $ALICE_JWT" > /dev/null

  curl -s "$BASE_URL/api/games/Mario Kart" \
    -H "Authorization: Bearer $BOB_JWT" > /dev/null

  curl -s "$BASE_URL/api/trades" \
    -H "Authorization: Bearer $ALICE_JWT" > /dev/null

  sleep $SLEEP
done

echo ""
echo "=== Initiating a trade ==="
TRADE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/trades" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ALICE_JWT" \
  -d '{"receiver":"bob@test.com","offered_game":"Halo","requested_game":"Mario Kart"}')

echo $TRADE_RESPONSE | jq .
TRADE_ID=$(echo $TRADE_RESPONSE | jq -r '.trade_id')

sleep $SLEEP

echo ""
echo "=== Accepting the trade ==="
curl -s -X POST "$BASE_URL/api/trades/accept/$TRADE_ID" \
  -H "Authorization: Bearer $BOB_JWT" | jq .

sleep $SLEEP

echo ""
echo "=== Simulating bad auth requests to generate 401s ==="
for i in $(seq 1 10); do
  curl -s "$BASE_URL/api/self" \
    -H "Authorization: Bearer invalidtoken123" > /dev/null
  sleep $SLEEP
done

echo ""
echo "=== Final burst of mixed traffic ==="
for i in $(seq 1 20); do
  curl -s "$BASE_URL/api/self" -H "Authorization: Bearer $ALICE_JWT" > /dev/null
  curl -s "$BASE_URL/api/self" -H "Authorization: Bearer $BOB_JWT" > /dev/null
  curl -s "$BASE_URL/api/trades" -H "Authorization: Bearer $ALICE_JWT" > /dev/null
  curl -s "$BASE_URL/api/games/Zelda" -H "Authorization: Bearer $ALICE_JWT" > /dev/null
  curl -s "$BASE_URL/api/games/Doom" -H "Authorization: Bearer $BOB_JWT" > /dev/null
  sleep $SLEEP
done

echo ""
echo "=== Done! Check Grafana at http://localhost:3000 ==="
