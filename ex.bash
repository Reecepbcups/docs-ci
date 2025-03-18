#!/bin/bash

# Example variable
count=7

# If statement with echo commands
if [ $count -gt 5 ]; then
    echo "Count is greater than 5"
    echo "The value is: $count"
else
    echo "Count is 5 or less"
    echo "The value is: $count" # this is a comment
    echo "hashtag in comment # inside"
fi

# Another echo outside the if statement
echo "Script completed successfully"


# make a complex if statement
[ $count -gt 5 ] && echo "Count is greater than 5" || echo "Count is 5 or less"

# check statement check if a command is installed
if command -v git &> /dev/null; then
    echo "Git is installed"
else
    echo "Git is not installed"
fi


function myEchoer() {
    echo "This is a function"
}
myEchoer
