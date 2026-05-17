# Seismic Testnet Telegram Bot

Seismic Layer-1 Blockchain Testnet ke liye automated Python Telegram bot.

## Features

- **Auto Wallet Generate** — Multiple wallets auto-generate with private keys
- **Faucet Claim** — Testnet ETH claim karne ke liye faucet links
- **Balance Check** — Saare wallets ka balance ek command se
- **Contract Deploy** — Smart contract deploy on Seismic testnet
- **ETH Transfer** — Wallets ke beech ETH transfer
- **Multi-wallet Management** — 20 wallets tak manage karo
- **Auto Run All** — Ek command se saare tasks automated

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Get Telegram Bot Token from [@BotFather](https://t.me/BotFather)

3. Set environment variable:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
```

4. Run the bot:
```bash
python bot.py
```

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Bot start karo |
| `/generate <count>` | Wallets generate karo (1-20) |
| `/wallets` | Saare wallets dekho |
| `/balance` | Balance check karo |
| `/faucet` | Faucet links aur wallet addresses |
| `/deploy` | Smart contract deploy karo |
| `/send <address> <amount>` | ETH transfer karo |
| `/transfer_all` | Saare wallets mein ETH distribute karo |
| `/run_all` | Automated tasks chalao (self-tx, deploy, inter-transfers) |
| `/export` | Wallet private keys export karo |
| `/delete_wallet <index>` | Wallet delete karo |
| `/network` | Seismic network info |
| `/help` | Help message |

## Network Info

| Property | Value |
|----------|-------|
| Network | Seismic Testnet |
| Chain ID | 5124 |
| RPC | https://testnet-1.seismictest.net/rpc |
| Explorer | https://seismic-testnet.socialscan.io |
| Currency | ETH |

## Auto Run (`/run_all`)

Ye command automatically saare funded wallets pe ye tasks chalata hai:
1. Balance check
2. Self-transfers (activity generate)
3. Contract deployment (up to 3 wallets)
4. Inter-wallet transfers

## Security

- Private keys locally `wallets.json` mein store hoti hain
- Bot token environment variable se set karo
- Export command se keys safely backup karo
