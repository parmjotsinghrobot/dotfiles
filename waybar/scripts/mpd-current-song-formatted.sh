#!/bin/bash
echo $(mpc current | sed 's/&/&amp;/g' | sed 's/\//, /g')
