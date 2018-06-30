#!/bin/bash

result=`sqlite3 ./taginfo-wiki.db "SELECT DISTINCT lang FROM wikipages" `

echo "$(echo "$result" | sed 's/.*/\u&/')"