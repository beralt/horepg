#!/bin/bash

python /horepg/horepgd.py -s /epggrab/xmltv.sock -tvh $TVH_HOST -tvh_username $TVH_USERNAME -tvh_password $TVH_PASSWORD -nr $NUM_DAYS -i $INTERVAL
