#!/bin/bash
python ./tools/image_size_adjuster.py ./temp -ww 1080 -hh 1080 -stripe 0 -margin 0 --output ./temp --allow_overwrite
python ./tools/image_size_adjuster.py ./temp -ww 620 -stripe 20 -margin 80 -bmw 10 -tmw 10 --output ./temp
