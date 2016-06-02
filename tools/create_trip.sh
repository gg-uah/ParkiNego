#!/bin/bash
# 道路網を定義したファイルの指定 -n
# 開始時刻 -b 0 sec
# 終了時刻 -e 86grid9x9.00 sec
# 出発間隔 -p 1 sec
# 端からスタートしやすくする 10 times
# 最短距離を縦と同じ 2250 m よくわからんけどnet.xmlでは1995.25が一番大きい(-1.65,-1.65)-> (2001.65, 2001.65)
# 出力ファイル名の指定 -o
$SUMO_HOME/trip/randomTrips.py \
    -n ../network/grid9x9.net.xml \
    -b 0 \
    -e 1000 \
    -p 1 \
    --fringe-factor 10 \
    --min-distance 1900 \
    -o grid9x9.trip.xml
duarouter -n ../network/grid9x9.net.xml -t ./grid9x9.trip.xml -o grid9x9.rou.xml