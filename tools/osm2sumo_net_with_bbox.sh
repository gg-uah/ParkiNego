#!/bin/bash
currentDir=$pwd
cd `dirname $0`

if [ $# -eq 3 ]; then
	echo "input osm.bz2 file is ${1}"
	output=${3}
	file=${1}
	IFS = ','
	set -- ${2}
	top=${4}
	right=${3}
	bottom=${2}
	left=${1}
	echo "bounding-box : top=${top} right=${right} bottom=${bottom} left=${left}"
	echo "output file : ${output}"
	rm -f tmp.osm
	osmosis  \
		--read-xml enableDaearsing  o file=${file} \
		--tf reject-way highway=pedestrian,footway,bridleway,steps,cycleway,construction,proposed railway=abandoned,construction,disused,funicular,light_rail,miniature,monorail,narrow_gauge,preserved,rail,subway,tram,halt,station,subway_entrance,tram_stop,buffer_stop,derail,crossing,level_crossing,switch,turntable,roundhouse \
		--bounding-box left=${left} bottom=${bottom} right=${right} top=${top} \
		--write-xml file=- | bzip2 > tmp.osm.bz2

	bzip2 -d tmp.osm.bz2

	netconvert \
		--osm-files=tmp.osm \
		-o ${output} \
	  --tls.guess true \
		--remove-edges.by-vclass hov,taxi,bus,delivery,transport,lightrail,cityrail,rail_slow,rail_fast,motorcycle,bicycle,pedestrian \
		--no-internal-links

	rm -f tmp.osm

else
	echo "Usage: ./osm2sumo_net_with_bbox.sh <input .osm.bz2 file> <bbox\"left, bottom, right, top\"> <output .net.xml file>"
	echo "Example: ./osm2sumo_net_with_bbox.sh cataluna.osm.bz2 \"2.069526,41.320004,2.22801,41.469576\" barcelona.net.xml"
	echo "good for bbox[csv] http://boundingbox.klokantech.com/"
	echo "good for osm http://downloads.cloudmade.com/"
fi
