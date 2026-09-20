import os
import re
import subprocess
import PyInstaller.__main__

spec_file = "PhotoCompare.spec" # Nome do seu arquivo .spec

print(f"Lendo as configurações do arquivo {spec_file}...")

# 1. Função auxiliar para extrair as variáveis do arquivo .spec usando Expressões Regulares
def ler_config_spec(caminho_spec):
    nome_proj = "App"
    versao_proj = "1.0.0"
    
    if os.path.exists(caminho_spec):
        with open(caminho_spec, "r", encoding="utf-8") as f:
            conteudo = f.read()
            
            # Procura por NOME_PROJETO = "Valor"
            match_nome = re.search(r'NOME_PROJETO\s*=\s*["\']([^"\']+)["\']', conteudo)
            if match_nome:
                nome_proj = match_nome.group(1)
                
            # Procura por VERSAO_PROJETO = "Valor"
            match_versao = re.search(r'VERSAO_PROJETO\s*=\s*["\']([^"\']+)["\']', conteudo)
            if match_versao:
                versao_proj = match_versao.group(1)
                
    return nome_proj, versao_proj

# Obtém o nome e a versão direto do .spec
nome, versao = ler_config_spec(spec_file)

print(f"Projeto: {nome} | Versão: {versao}")
print("Iniciando o empacotamento com PyInstaller...\n")

# 2. Executa o PyInstaller passando o arquivo .spec
PyInstaller.__main__.run([
    spec_file,
    '--clean',
    '--noconfirm'
])

print("\nProcesso de build finalizado com sucesso!")
print(f"O executável gerado já possui o padrão: {nome}_v{versao}.exe na pasta 'dist/'.")