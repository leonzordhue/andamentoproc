# andamentoproc: andamento processual do TJAM

Você informa o número do processo e o programa monta uma **pasta com os PDFs oficiais** e um **relatório em Word** que explica a situação do processo em linguagem simples: distribuição, citação, contestação, audiência, decisões, sentença, recurso, trânsito em julgado e pagamento.

Usa só fontes públicas e oficiais. Nenhuma proteção (captcha, anti-robô) é contornada.

## Como usar

### No computador (Windows)
```bat
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python acompanhar.py                         & rem pergunta o número
.venv\Scripts\python acompanhar.py 0000000-00.0000.8.04.0000 --oab 1234/AM
```
A saída vai para `Desktop\Processos TJAM\<número>\`, ou para a pasta definida na variável `JUS_SAIDA`.

### Pelo site do GitHub (Actions)
1. **O repositório precisa ser privado.** O workflow não roda em repositório público, porque o relatório tem nomes de partes e advogados.
2. Abra **Actions → Consultar processo TJAM → Run workflow**, informe o número (e a OAB, se quiser) e confirme.
3. Quando o run terminar, baixe o artefato `processo-<número>`, que contém a pasta com os PDFs e o relatório. Ele fica disponível por 7 dias.

## O que vai na pasta do processo
| Arquivo | Conteúdo |
|---|---|
| `Relatorio_<número>.docx` | resumo em linguagem simples (etapa atual e marcos com data), dados do processo, linha do tempo, íntegra das publicações, fontes e limites |
| `publicacoes/*.pdf` | **certidão oficial** de cada publicação do processo no Diário de Justiça Eletrônico Nacional (DJEN) |
| `publicacoes/*.txt` | texto integral de cada publicação |
| `PROJUDI/` | onde você salva a página da consulta pública do PROJUDI (ver abaixo); o texto entra no relatório |
| `estado.json` | o que já foi visto: na próxima consulta, o relatório mostra só as **novidades** |

## Fontes
| Fonte | O que traz | Observação |
|---|---|---|
| DJEN / Comunica PJe (CNJ) | publicações (distribuição, intimações, despachos, decisões, sentenças) + certidão em PDF | pesquisa exata por número e por OAB |
| DataJud (API pública do CNJ) | todos os movimentos do processo (citação, juntada de contestação, conclusão…) | processos novos levam semanas para aparecer |
| PROJUDI/TJAM (Juizados) | andamento completo e documentos | a consulta pública tem **reCAPTCHA**: uma pessoa abre `https://projudi-consulta.tjam.jus.br/publica`, pesquisa e salva a página (Ctrl+S ou Ctrl+P → PDF) na pasta `PROJUDI/`. Os documentos dos autos exigem o acesso do advogado |

## Outras consultas (`jus.py`)
```bat
.venv\Scripts\python jus.py jurisprudencia "progressão funcional servidor"        & rem acórdãos do TJAM (xlsx)
.venv\Scripts\python jus.py processo 0620084-16.2022.8.04.0001                    & rem movimentos (DataJud) e novidades
.venv\Scripts\python jus.py intimacoes "termo" --desde 2026-10-01                 & rem DJEN, só TJAM
```
- **Jurisprudência:** via [juscraper](https://github.com/jtrecenti/juscraper) (MIT).
- **Dados pessoais:** os resultados (`saida/`, pasta do processo, `processos.txt`) ficam fora do git (`.gitignore`). Não versionar.
