#!/bin/sh
IP=${1:-127.0.0.1}
mkdir -p certs && cd certs
openssl req -x509 -newkey rsa:2048 -nodes -days 365 -keyout server.key -out server.crt -subj "/CN=glowlight-broker" -addext "subjectAltName=DNS:localhost,DNS:$IP,IP:127.0.0.1,IP:$IP"
cp server.crt ca.crt
chmod 644 server.key