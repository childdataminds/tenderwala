#!/bin/bash
set -e

cd /var/www/tenderwala
git pull origin main
sudo systemctl restart tenderwala
