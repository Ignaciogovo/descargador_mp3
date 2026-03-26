#!/bin/bash
# Script para añadir un usuario a la lista de autorizados
# Uso: ./agregar_usuario.sh <user_id>

USUARIO=$1

if [ -z "$USUARIO" ]; then
    echo "Uso: $0 <user_id>"
    echo "Ejemplo: $0 123456789"
    exit 1
fi

CONFIG_FILE="./config/usuarios_autorizados.txt"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Creando archivo de configuración..."
    mkdir -p ./config
    touch "$CONFIG_FILE"
fi

if grep -q "^${USUARIO}$" "$CONFIG_FILE"; then
    echo "El usuario $USUARIO ya está en la lista"
else
    echo "$USUARIO" >> "$CONFIG_FILE"
    echo "Usuario $USUARIO añadido correctamente"
fi
