# Kimi-Altered

Projeto de inferência remota pelo Hugging Face, diagnóstico e testes locais para executar o motor [kimi-k3-in-c](https://github.com/FareedKhan-dev/kimi-k3-in-c), de Fareed Khan. **Ainda não contém pesos. O cliente de chat remoto depende de credenciais válidas e de disponibilidade do serviço; a execução do motor C com pesos completos não foi testada.**

## Sem espaço no PC: Kimi K3 pelo Hugging Face

Os **96 arquivos do modelo completo (1,56 TB)** já estão hospedados em [moonshotai/Kimi-K3](https://huggingface.co/moonshotai/Kimi-K3). Não é necessário copiá-los nem enviá-los a outra conta.

Para executar **inferência remota**, sem armazenar pesos no PC, há um cliente em Python 3.9+ que usa os [Inference Providers do Hugging Face](https://huggingface.co/docs/inference-providers/index). Ele funciona no Windows, macOS e Linux. **A computação acontece no provedor, não na CPU local com o motor C.** Requer internet e pode consumir créditos.

Primeiro, teste somente a disponibilidade dos metadados (gratuito, sem login e sem baixar os pesos):

```powershell
python scripts/inferencia_hf.py --verificar
```

Para conversar com o Kimi K3 remotamente:

1. Consulte os [créditos e preços de inferência](https://huggingface.co/docs/inference-providers/pricing) e confirme as permissões da sua conta.
2. Crie um token de acesso com permissão para Inference Providers nas [configurações de tokens](https://huggingface.co/settings/tokens).
3. Execute:

```powershell
python scripts/inferencia_hf.py --chat --autorizar-envio
```

O programa solicitará seu token de forma oculta caso a variável de ambiente `HF_TOKEN` não esteja definida. **Não publique nem envie seu token.** Os pesos não são baixados, e o cliente não grava histórico no disco. O modelo usado pela API é `moonshotai/Kimi-K3:cheapest` (provedor disponível de menor custo conforme a política de roteamento).

**Importante:** esta é uma opção de uso remoto. O motor independente `kimi-k3-in-c` exige arquivos locais e leituras aleatórias de dados; não reconhece automaticamente caminhos `hf://`. Adaptá-lo para acessar os 1,56 TB remotamente exigiria uma camada de I/O adicional e largura de banda imensa. Não foi implementado nem validado streaming direto de pesos para a CPU local.

## Estado

- Scripts em português para diagnóstico do Windows e preparo do motor C.
- Fonte oficial fixada no lançamento **v1.0.0**, sem alterações no código do autor.
- A instalação do motor roda `make` e `make test` **sem baixar o checkpoint**.
- Os pesos, caches e segredos não devem ser enviados ao GitHub (veja `.gitignore`).
- A inferência com o modelo completo **não foi realizada neste projeto**.

## O que as especificações realmente significam

Segundo os dados publicados pelo projeto original, Kimi K3 tem 2,78 trilhões de parâmetros, mas o checkpoint completo ocupa cerca de **1,56 TB no disco**, mais **109 GB** para o trunk preparado. A memória de **8,24 GB** refere-se ao pico do **processo** nos testes apresentados, não ao total consumido pelo Windows e outras aplicações. É aconselhável ter mais RAM para margem operacional.

A CPU precisa suportar **AVX2 + FMA** no x86-64. O motor pode operar sem GPU, mas a maior parte dos pesos permanece no SSD. Os tempos publicados foram medidos em hardware de servidor, então não são promessa de velocidade em computador doméstico.

## 1. Diagnóstico no Windows (não altera o PC)

Abra o PowerShell na pasta clonada e execute:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\diagnostico.ps1
```

O diagnóstico informa processador, núcleos, RAM, espaço livre de cada unidade e ferramentas detectadas. **Não verifica automaticamente** AVX2/FMA nem a velocidade real do SSD.

## 2. Instalar ferramentas no Windows

Instale o [MSYS2](https://www.msys2.org/) e abra **MSYS2 MinGW x64** (não o terminal MSYS2 simples ou UCRT64). Atualize o MSYS2 conforme as instruções oficiais e execute no terminal MinGW x64:

```bash
pacman -S --needed mingw-w64-x86_64-gcc make git python
```

Entre na pasta deste repositório (exemplo para a unidade C: `cd /c/Projetos/Kimi-Altered`) e rode:

```bash
bash scripts/preparar.sh
```

O script clona a versão v1.0.0 do motor em `engine/kimi-k3-in-c`, compila e executa os testes **sem pesos**. Se o clone já existir, não altera arquivos locais nem atualiza versões automaticamente.

O mesmo script pode ser usado em Linux com Git, GCC e GNU Make instalados.

## 3. Verificar os requisitos do motor

No terminal MinGW x64:

```bash
cd engine/kimi-k3-in-c
bash scripts/k3-doctor.sh
```

Para executar o **modelo completo**, planeje aproximadamente **1,7 TB livres** em disco local rápido. Os pesos não são inclusos nem baixados por este repositório.

## 4. Download completo: somente após confirmar o hardware

Consulte o [Quick start oficial](https://github.com/FareedKhan-dev/kimi-k3-in-c#full-setup) e a licença dos pesos da Moonshot AI antes de baixar:

```bash
# Exemplos no MSYS2: escolha UMA unidade com muito espaço livre.
export HF_TOKEN='seu_token_privado'
bash scripts/download-model.sh /d/k3model
bash scripts/pack-trunk.sh /d/k3model /d/k3trunk
./bin/k3 /d/k3model --trunk /d/k3trunk --preset ultra --tok /d/k3model --prompt "Ola, mundo" --gen 4
```

**Cuidado:** nunca inclua token real no terminal compartilhado, prints, commits ou logs. Prefira ler o token sem eco, por exemplo `read -r -s HF_TOKEN; export HF_TOKEN` no Bash. O comando acima é apenas ilustrativo; o download inteiro requer armazenamento e rede adequados, e as opções podem mudar em versões futuras.

### Para testar sem 1,7 TB

A versão v1.0.0 também documenta o download parcial para execução com `--layers N`; isso **não é o modelo completo** e serve apenas para validar o pipeline. Veja a documentação original.

## Segurança e limites

Este repositório não distribui código-fonte ou pesos da Moonshot AI. O motor `kimi-k3-in-c` é um projeto independente sob Apache 2.0; os pesos do Kimi K3 possuem sua própria licença. O diagnóstico não garante funcionamento completo, e os testes sem checkpoint não demonstram a qualidade do modelo real.

**Fontes:** [repositório upstream](https://github.com/FareedKhan-dev/kimi-k3-in-c), [release v1.0.0](https://github.com/FareedKhan-dev/kimi-k3-in-c/releases/tag/v1.0.0).
