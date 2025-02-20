#!/bin/bash
python ./tools/image_size_adjuster.py ./temp -ww 1080 -stripe 0 -margin 0 --output ./original_images
python ./tools/image_size_adjuster.py ./temp -ww 1080 -stripe 20 -margin 60 --output ./temp --bottom_mergin_width 20 --top_mergin_width 40 --allow_overwrite
#python ./tools/image_size_adjuster.py ./temp -ww 640 -stripe 20 -margin 60 --output ./temp --bottom_mergin_width 20 --top_mergin_width 40 --allow_overwrite
