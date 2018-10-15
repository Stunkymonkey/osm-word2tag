#!/bin/bash
curl -d '{"query":"highway", "amount":5, "nearest_neighbor":10}'  -H "Content-Type: application/json" -X POST http://localhost:8080
