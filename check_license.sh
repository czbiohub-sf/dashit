#!/bin/bash

LICENSE_LOCATION=$HOME/.config/czbiohub/guide_design_tools.txt
shopt -s nocasematch

if [ ! -f $LICENSE_LOCATION ]; then
    EULA_VERSION=`head -n 1 LICENSE.md`
    echo "Your use of this software is governed by the $EULA_VERSION."
    read -p "Press <RETURN> to view the $EULA_VERSION. Read the license carefully and press <Q> when you are finished."
    less LICENSE.md 
    read -p "Please type 'I agree' to acknowledge that you have read the license ($EULA_VERSION) and accept the conditions: " AGREEMENT;
    if [[ "$AGREEMENT" == "i agree" ]]; then
	mkdir $HOME/.config
	mkdir $HOME/.config/czbiohub
	echo "User $USER accepted the conditions in $EULA_VERSION on `date`" > $LICENSE_LOCATION
    else
	(echo "You did not agree to the license, exiting."; exit 1;)
    fi
fi
