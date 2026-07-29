# 🌡️ Boiler App

CLI para monitorar temperatura de boilers e termostatos eWeLink.

## Instalação

```bash
git clone https://github.com/airtonGit/boiler-app.git
cd boiler-app
pip install -e .
```

Ou use `uv`:

```bash
uv pip install -e .
```

## Configuração

Crie um arquivo `.env` baseado no exemplo:

```bash
cp .env.example .env
```

Edite o `.env` com suas credenciais do eWeLink:

```env
EWELINK_EMAIL=seu-email@gmail.com
EWELINK_PASSWORD=sua-senha
EWELINK_COUNTRY_CODE=+55
EWELINK_REGION=us
```

## Uso

```bash
# Relatório completo com cards
boiler --email seu-email@gmail.com --password sua-senha

# Usando .env
boiler

# Resumo compacto (1 linha por dispositivo)
boiler --summary

# Saída em JSON
boiler --json
```

## Exemplo de saída

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃      🌡️  Boiler Monitor  •  29/07/2026 10:54:55     ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┌── 🟢  Boiler pousada 2  ⏻ OFF ──────────────────────┐
│ 🌡️  Temperatura    44.7°C                           │
│ 💧 Umidade          N/A                              │
│ 📏 Range            40.0°C — 65.0°C                  │
│ 📶 Sinal WiFi       ▂▄▆█ (-30 dBm)                  │
│ 🔧 Sensor           DS18B20                          │
│ 📟 Firmware          1.2.0                            │
│ ⏰ Auto-Controle                                      │
│   ├─ 00:00 - 04:59:  44° → 45°                       │
│   ├─ 05:00 - 06:59:  49° → 50°                       │
│   ├─ 07:00 - 16:59:  42° → 43°                       │
│   └─ 17:00 - 23:59:  59° → 60°                       │
└──────────────────────────────────────────────────────┘
```

## Credenciais do App

As credenciais do app eWeLink (`EWELINK_APP_ID` e `EWELINK_APP_SECRET`) são valores públicos
extraídos do APK oficial e já vêm pré-configurados. Você só precisa fornecer
seu email e senha da conta eWeLink.

## Licença

MIT
