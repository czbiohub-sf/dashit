#!/bin/bash

LICENSE_LOCATION=$HOME/.config/guide_design_tools.txt

if [ ! -f $LICENSE_LOCATION ]; then
    read -p "Please type 'I agree' to acknowledge that you have read the license (LICENSE) and accept the conditions: " AGREEMENT;
    if [ "$AGREEMENT" == "I agree" ]; then
	touch $LICENSE_LOCATION;
    else
	(echo "You did not agree to the license, exiting."; exit 1;)
    fi
fi
