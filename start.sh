#!/usr/bin/zsh

#One bad thing about this script is that it has 2 main dependencies:
#1. You must be on a POSIX-compliant OS.
#2. You must use zsh as your default shell.

#This script should run just fine if you're using linux or mac, but windows will probably not work well with it.

#Find project path and cd there.
path2launch=$(dirname "$0")
cd "$path2launch"

#Checks if the virtual environment already exists and activates it.
if [[ -d "venv" ]]; then
    echo "Found 'venv' folder. Activating..."
    source venv/bin/activate
else
    #Prompt the user to set up the venv if missing
    echo "It seems that you don't have a venv setup."
    read "choice?Do you want me to do it for you? [Y/n]: "

    #Defaults to 'y' if user gives empty input
    if [[ -z "$choice" ]]; then
        choice=y
    fi

    #Converts to lowercase (this is a zsh specific feature)
    choice="${choice:l}"

    if [[ "$choice" == "y" || "$choice" == "yes" ]]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
        source venv/bin/activate

        if [[ -f "requirements.txt" ]]; then
            echo "Installing dependencies..."
            pip install -r requirements.txt
        else
            echo "Warning: requirements.txt not found. Skipping pip install."
        fi
    elif [[ "$choice" == "n" || "$choice" == "no" ]]; then
        echo "Skipping venv creation. Proceeding without activation..."
    else
        echo "Invalid input."
        exit 1
    fi
fi

#Creates a sort of list that we can iterate over in order to kill each process cleanly
typeset -a bg_pids

cleanup() {
    echo "\nShutting down cleanly..."
    for pid in "${bg_pids[@]}"; do
        kill "$pid" 2>/dev/null
    done
    sleep 1.5
    exit 0
}

trap cleanup INT TERM

#Starts uvicorn in the background
uvicorn main:app --reload &
bg_pids+=($!)

#Waits for server to Start up
sleep 2

#Opens browser in the background
firefox http://127.0.0.1:8000 &
bg_pids+=($!)

#Keeps the script alive to catch traps
wait
