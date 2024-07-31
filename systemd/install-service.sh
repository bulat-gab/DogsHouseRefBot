#!/bin/bash

sudo cp ./dogsbot.service /etc/systemd/system/dogsbot.service
sudo systemctl daemon-reload
sudo systemctl enable dogsbot.service