#!/bin/bash
echo "=== INSTALAÇÃO GLOBAL DO MEDIA-CONVERTER ==="

# 1. Criar wrapper
echo "1. Criando wrapper..."
cat > media-converter << 'WRAPPER_EOF'
#!/usr/bin/env bash
REAL_SCRIPT_PATH="$(readlink -f "$0")"
PROJECT_DIR="$(dirname "$REAL_SCRIPT_PATH")"

cd "$PROJECT_DIR" || {
    echo "Erro: Não foi possível acessar: $PROJECT_DIR" >&2
    exit 1
}

[ -d "venv" ] && source venv/bin/activate

# Execute CLI manager (interactive mode if no args)
if [ $# -eq 0 ]; then
    exec python3 scripts/cli_manager.py "interactive"
else
    exec python3 scripts/cli_manager.py "$@"
fi
WRAPPER_EOF

chmod +x media-converter
echo "✅ Wrapper criado"

# 2. Criar links
echo "2. Criando links simbólicos..."
mkdir -p ~/.local/bin
ln -sf "$(pwd)/media-converter" ~/.local/bin/media-converter
ln -sf "$(pwd)/media-converter" ~/.local/bin/converter
echo "✅ Links criados"

# 3. Verificar PATH
echo "3. Verificando PATH..."
if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
    echo "Adicionando ~/.local/bin ao PATH..."
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    source ~/.bashrc 2>/dev/null
    echo "✅ PATH atualizado"
fi

# 4. Testar
echo "4. Testando..."
cd /tmp
if media-converter --help 2>&1 | grep -q "Universal HEIC & HEVC Converter"; then
    echo "✅ media-converter instalado com sucesso!"
fi
if converter --help 2>&1 | grep -q "Universal HEIC & HEVC Converter"; then
    echo "✅ converter (alias) instalado com sucesso!"
fi

echo -e "\n🎉 Instalação completa!"
echo "Comandos disponíveis:"
echo "  media-converter [opções]"
echo "  converter [opções] (alias)"
