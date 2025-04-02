#!/bin/bash
# This script is used to get the percentage of the song played in mpd
# and return the progress bar in the format of a string 50 characters long

# get the percentage of the song played in mpd
percentagePlayed=$(mpc status %percenttime% | sed 's/^[[:space:]]*//;s/%$//')

# get the number of full blocks
# each block represents 20% of the song played
fullBlocks=$((percentagePlayed / 2))

# get the width of the final partial block
partialBlock=$((percentagePlayed % 2))

# get the number of empty blocks
emptyBlocks=$((50 - fullBlocks - (partialBlock > 0 ? 1 : 0)))

# create the progress bar
progressBar=""
for ((i=0; i<fullBlocks; i++)); do
    progressBar+="█"
done
if ((partialBlock > 0)); then
    case $partialBlock in
        1) progressBar+="▌" ;; # half block for 1%
        *) progressBar+="█" ;; # should not happen
    esac
fi
# add empty blocks
for ((i=0; i<emptyBlocks; i++)); do
    progressBar+=" "
done

# print the progress bar
echo "$progressBar"
