#!/usr/bin/env python3
"""Usa o Kimi K3 na nuvem do Hugging Face; NAO roda o motor C local.

Python 3.9+ e biblioteca padrao; nao baixa os pesos do modelo.
Cada pergunta pode consumir creditos de inferencia remota.
"""
import argparse
import getpass
import json
import os
import sys
import urllib.error
import urllib.request

MODELO = "moonshotai/Kimi-K3"
URL_METADADOS = f"https://huggingface.co/api/models/{MODELO}"
URL_INFERENCIA = "https://router.huggingface.co/v1/chat/completions"
LIMITE_RESPOSTA = 4 * 1024 * 1024


def requisitar_json(url, *, metodo="GET", dados=None, token=None, timeout=60):
    cabecalhos = {"Accept": "application/json", "User-Agent": "Kimi-Altered/0.1"}
    corpo = None
    if dados is not None:
        corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        cabecalhos["Content-Type"] = "application/json"
    if token:
        cabecalhos["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=corpo, headers=cabecalhos, method=metodo)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resposta:
            recebido = resposta.read(LIMITE_RESPOSTA + 1)
    except urllib.error.HTTPError as erro:
        # O corpo HTTP pode conter dados sensiveis: nao o imprimir.
        raise RuntimeError(
            f"Servico retornou HTTP {erro.code}; confira token, permissoes e saldo"
        ) from None
    except urllib.error.URLError:
        raise RuntimeError("Falha de conexao com Hugging Face; verifique a internet") from None
    if len(recebido) > LIMITE_RESPOSTA:
        raise RuntimeError("Resposta inesperadamente grande; cancelando por seguranca")
    try:
        return json.loads(recebido.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise RuntimeError("O servidor nao retornou JSON valido") from None


def verificar():
    dados = requisitar_json(URL_METADADOS, timeout=25)
    arquivos = dados.get("siblings", [])
    pesos = [
        a.get("rfilename", "") for a in arquivos
        if a.get("rfilename", "").endswith(".safetensors")
        and a.get("rfilename", "").startswith("model-")
    ]
    print(f"Modelo hospedado: {dados.get('id', MODELO)}")
    print(f"Arquivos de pesos encontrados: {len(pesos)} (esperados: 96)")
    print("Pesos usados no armazenamento do PC: 0 GB")
    print("Consulta apenas metadados; nao executa inferencia.")
    print("Para conversar: --chat --autorizar-envio")
    return 0 if dados.get("id") == MODELO else 1


def texto_resposta(dados):
    escolhas = dados.get("choices") or []
    if not escolhas or not isinstance(escolhas[0], dict):
        raise RuntimeError("Provedor respondeu sem conteudo de chat")
    conteudo = escolhas[0].get("message", {}).get("content", "")
    if isinstance(conteudo, str):
        return conteudo.strip() or "(resposta vazia)"
    if isinstance(conteudo, list):
        return "\n".join(
            parte.get("text", "") for parte in conteudo
            if isinstance(parte, dict) and isinstance(parte.get("text"), str)
        ).strip() or "(resposta sem texto)"
    raise RuntimeError("Resposta em formato nao esperado")


def enviar(mensagens, token, max_tokens):
    dados = requisitar_json(
        URL_INFERENCIA,
        metodo="POST",
        dados={"model": f"{MODELO}:cheapest", "messages": mensagens, "max_tokens": max_tokens},
        token=token,
        timeout=180,
    )
    return texto_resposta(dados)


def executar_chat(token, max_tokens):
    print("Chat remoto Kimi K3. Digite /sair para terminar.")
    print("Cada mensagem enviada pode consumir creditos do Hugging Face.")
    mensagens = []
    while True:
        try:
            pergunta = input("\nVoce: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nChat encerrado.")
            return 0
        if pergunta.lower() in ("/sair", "/exit"):
            return 0
        if not pergunta:
            continue
        proximas = (mensagens + [{"role": "user", "content": pergunta}])[-12:]
        try:
            resposta = enviar(proximas, token, max_tokens)
        except RuntimeError as erro:
            print(f"Falha: {erro}", file=sys.stderr)
            continue
        print(f"\nKimi: {resposta}")
        mensagens = (proximas + [{"role": "assistant", "content": resposta}])[-12:]


def principal(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--verificar", action="store_true", help="Consulta metadados publicos (padrao)")
    modo.add_argument("--chat", action="store_true", help="Conversa por API remota")
    parser.add_argument("--autorizar-envio", action="store_true", help="Aceita consumo de creditos remotos")
    parser.add_argument("--max-tokens", type=int, default=128, help="Tokens maximos por resposta")
    args = parser.parse_args(argv)
    if args.max_tokens < 1 or args.max_tokens > 1024:
        parser.error("--max-tokens deve estar entre 1 e 1024")
    try:
        if not args.chat:
            return verificar()
        if not args.autorizar_envio:
            parser.error("--chat exige --autorizar-envio (pode consumir creditos)")
        token = os.environ.get("HF_TOKEN", "").strip() or getpass.getpass(
            "Token Hugging Face (nao sera salvo): "
        )
        if not token:
            parser.error("Token do Hugging Face necessario")
        return executar_chat(token, args.max_tokens)
    except RuntimeError as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(principal())
