"""
Seismic Testnet Telegram Bot
- Auto wallet generation
- Faucet claim
- Balance check
- Contract deployment
- ETH transfers
- Multi-wallet management
- Auto run all tasks
"""

import json
import os
import logging
import time
from pathlib import Path

import aiohttp
from eth_account import Account
from web3 import Web3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# ─── Config ──────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

SEISMIC_RPC = "https://testnet-1.seismictest.net/rpc"
SEISMIC_CHAIN_ID = 5124
SEISMIC_EXPLORER = "https://seismic-testnet.socialscan.io"
SEISMIC_FAUCET = "https://faucet-2.seismicdev.net"
SEISMIC_COMMUNITY_FAUCET = "https://community-faucet.seismictest.net"

WALLETS_FILE = Path("wallets.json")

# Simple storage contract bytecode for testnet deployment
SIMPLE_STORAGE_BYTECODE = (
    "0x608060405234801561001057600080fd5b5060f78061001f6000396000f3fe"
    "6080604052348015600f57600080fd5b5060043610603c5760003560e01c8063"
    "209652551460415780632096525514605b57806355241077146075575b600080fd5b"
    "60476087565b60405190815260200160405180910390f35b60616087565b60405190"
    "815260200160405180910390f35b608560048036036020811015608957600080fd5b"
    "50356090565b005b60005490565b60005556fea264697066735822122000000000"
    "0000000000000000000000000000000000000000000000000000000064736f6c"
    "6343000812003300000000000000000000000000000000000000000000000000"
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

w3 = Web3(Web3.HTTPProvider(SEISMIC_RPC))


# ─── Wallet Storage ─────────────────────────────────────────────────
def load_wallets() -> dict:
    if WALLETS_FILE.exists():
        with open(WALLETS_FILE) as f:
            return json.load(f)
    return {}


def save_wallets(wallets: dict) -> None:
    with open(WALLETS_FILE, "w") as f:
        json.dump(wallets, f, indent=2)


def get_user_wallets(user_id: str) -> list[dict]:
    wallets = load_wallets()
    return wallets.get(user_id, [])


def add_user_wallet(user_id: str, wallet: dict) -> None:
    wallets = load_wallets()
    if user_id not in wallets:
        wallets[user_id] = []
    wallets[user_id].append(wallet)
    save_wallets(wallets)


# ─── Helpers ─────────────────────────────────────────────────────────
def short_addr(addr: str) -> str:
    return f"{addr[:6]}...{addr[-4:]}"


def explorer_link(addr: str, link_type: str = "address") -> str:
    return f"{SEISMIC_EXPLORER}/{link_type}/{addr}"


def get_balance(address: str) -> float:
    try:
        balance_wei = w3.eth.get_balance(Web3.to_checksum_address(address))
        return float(Web3.from_wei(balance_wei, "ether"))
    except Exception:
        return 0.0


# ─── Bot Commands ────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "🚀 *Seismic Testnet Bot*\n\n"
        "Seismic Layer-1 Blockchain Testnet ke liye automated bot!\n\n"
        "📋 *Commands:*\n"
        "/generate `<count>` — Wallets generate karo (default 1, max 20)\n"
        "/wallets — Apne saare wallets dekho\n"
        "/balance — Saare wallets ka balance check karo\n"
        "/faucet — Faucet se testnet ETH claim karo\n"
        "/deploy — Smart contract deploy karo\n"
        "/send `<to_address>` `<amount>` — ETH transfer karo\n"
        "/transfer\\_all — Saare wallets ke beech ETH distribute karo\n"
        "/run\\_all — Saare wallets pe automated tasks chalao\n"
        "/export — Wallet details export karo\n"
        "/delete\\_wallet `<index>` — Wallet delete karo\n"
        "/network — Seismic network info dekho\n"
        "/help — Help message\n\n"
        f"🔗 *Network:* Seismic Testnet (Chain ID: {SEISMIC_CHAIN_ID})\n"
        f"🌐 *Explorer:* [SocialScan]({SEISMIC_EXPLORER})\n"
        f"💧 *Faucet:* [Seismic Faucet]({SEISMIC_COMMUNITY_FAUCET})"
    )
    await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, context)


async def network_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        block_number = w3.eth.block_number
        chain_id = w3.eth.chain_id
        gas_price = Web3.from_wei(w3.eth.gas_price, "gwei")
        status = "✅ Connected"
    except Exception:
        block_number = "N/A"
        chain_id = "N/A"
        gas_price = "N/A"
        status = "❌ Disconnected"

    text = (
        "🌐 *Seismic Testnet Network Info*\n\n"
        f"Status: {status}\n"
        f"Chain ID: `{chain_id}`\n"
        f"Block: `{block_number}`\n"
        f"Gas Price: `{gas_price} Gwei`\n"
        f"RPC: `{SEISMIC_RPC}`\n"
        f"Explorer: [SocialScan]({SEISMIC_EXPLORER})\n\n"
        "*Add to Wallet:*\n"
        f"Network Name: `Seismic Testnet`\n"
        f"RPC URL: `{SEISMIC_RPC}`\n"
        f"Chain ID: `{SEISMIC_CHAIN_ID}`\n"
        f"Currency: `ETH`\n"
        f"Explorer: `{SEISMIC_EXPLORER}`"
    )
    await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)


# ─── Wallet Generation ───────────────────────────────────────────────
async def generate_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    count = 1
    if context.args:
        try:
            count = int(context.args[0])
            count = min(max(count, 1), 20)
        except ValueError:
            await update.message.reply_text("❌ Valid number do (1-20)")
            return

    user_id = str(update.effective_user.id)
    msg = await update.message.reply_text(f"⏳ {count} wallet(s) generate ho rahe hain...")

    generated = []
    for i in range(count):
        acct = Account.create()
        wallet_data = {
            "address": acct.address,
            "private_key": acct.key.hex(),
            "created_at": int(time.time()),
            "index": len(get_user_wallets(user_id)) + 1,
        }
        add_user_wallet(user_id, wallet_data)
        generated.append(wallet_data)

    text = f"✅ *{count} Wallet(s) Generated!*\n\n"
    for w in generated:
        text += (
            f"📌 *Wallet #{w['index']}*\n"
            f"Address: `{w['address']}`\n"
            f"Private Key: `{w['private_key']}`\n"
            f"[Explorer]({explorer_link(w['address'])})\n\n"
        )

    text += (
        "⚠️ *Private keys safe rakhna!*\n"
        "🔗 *Add to MetaMask:*\n"
        f"RPC: `{SEISMIC_RPC}`\n"
        f"Chain ID: `{SEISMIC_CHAIN_ID}`"
    )

    await msg.edit_text(text, parse_mode="Markdown", disable_web_page_preview=True)


# ─── View Wallets ────────────────────────────────────────────────────
async def view_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    user_wallets = get_user_wallets(user_id)

    if not user_wallets:
        await update.message.reply_text(
            "❌ Koi wallet nahi hai. `/generate` se banao.", parse_mode="Markdown"
        )
        return

    text = f"👛 *Aapke Wallets ({len(user_wallets)}):*\n\n"
    for i, w in enumerate(user_wallets, 1):
        balance = get_balance(w["address"])
        text += (
            f"*#{i}* `{short_addr(w['address'])}`\n"
            f"   💰 {balance:.6f} ETH\n"
            f"   [Explorer]({explorer_link(w['address'])})\n\n"
        )

    await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)


# ─── Balance Check ───────────────────────────────────────────────────
async def check_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    user_wallets = get_user_wallets(user_id)

    if not user_wallets:
        await update.message.reply_text(
            "❌ Koi wallet nahi hai. `/generate` se banao.", parse_mode="Markdown"
        )
        return

    msg = await update.message.reply_text("⏳ Balances check ho rahe hain...")

    total = 0.0
    text = "💰 *Wallet Balances:*\n\n"
    for i, w in enumerate(user_wallets, 1):
        balance = get_balance(w["address"])
        total += balance
        text += f"*#{i}* `{short_addr(w['address'])}` → *{balance:.6f} ETH*\n"

    text += f"\n📊 *Total: {total:.6f} ETH*"

    await msg.edit_text(text, parse_mode="Markdown", disable_web_page_preview=True)


# ─── Faucet ──────────────────────────────────────────────────────────
async def claim_faucet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    user_wallets = get_user_wallets(user_id)

    if not user_wallets:
        await update.message.reply_text(
            "❌ Pehle wallet banao: `/generate`", parse_mode="Markdown"
        )
        return

    msg = await update.message.reply_text("💧 Faucet claim ho raha hai, wait karo...")

    # Step 1: Try all known faucet API endpoints
    claimed_wallets = []
    faucet_endpoints = [
        ("https://faucet.seismictest.net/api/claim", "Seismic Testnet"),
        ("https://community-faucet.seismictest.net/api/claim", "Community"),
        ("https://faucet-2.seismicdev.net/api/claim", "Dev Faucet"),
    ]

    for w in user_wallets:
        for endpoint, name in faucet_endpoints:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        endpoint,
                        json={"address": w["address"]},
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get("hash") or data.get("success"):
                                claimed_wallets.append((w, name))
                                break
            except Exception:
                continue

    # Step 2: Auto-distribute from funded wallets to unfunded ones
    funded = []
    unfunded = []
    for w in user_wallets:
        bal = get_balance(w["address"])
        if bal > 0.002:
            funded.append((w, bal))
        elif bal <= 0.001:
            unfunded.append(w)

    distributed = []
    if funded and unfunded:
        source_w, source_bal = max(funded, key=lambda x: x[1])
        amount_each = min((source_bal * 0.7) / len(unfunded), 0.1)
        if amount_each > 0.0005:
            acct = Account.from_key(source_w["private_key"])
            nonce = w3.eth.get_transaction_count(acct.address)
            for uw in unfunded:
                try:
                    tx = {
                        "nonce": nonce,
                        "to": Web3.to_checksum_address(uw["address"]),
                        "value": Web3.to_wei(amount_each, "ether"),
                        "gas": 21000,
                        "gasPrice": w3.eth.gas_price,
                        "chainId": SEISMIC_CHAIN_ID,
                    }
                    signed = acct.sign_transaction(tx)
                    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
                    w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
                    distributed.append(
                        f"✅ `{short_addr(uw['address'])}` ← {amount_each:.4f} ETH"
                    )
                    nonce += 1
                except Exception as e:
                    distributed.append(
                        f"❌ `{short_addr(uw['address'])}` ← Failed: {str(e)[:40]}"
                    )

    # Build response
    text = "💧 *Faucet Results:*\n\n"

    if claimed_wallets:
        text += "*API Faucet Claims:*\n"
        for w, name in claimed_wallets:
            text += f"✅ `{short_addr(w['address'])}` via {name}\n"
        text += "\n"

    if distributed:
        text += "*Auto-Distribution (funded → unfunded):*\n"
        text += "\n".join(distributed) + "\n\n"
        text += f"📤 Source: `{short_addr(source_w['address'])}`\n"
    elif not claimed_wallets:
        if not funded:
            text += (
                "❌ Koi funded wallet nahi mila!\n\n"
                "Pehle ek wallet mein manually ETH bhejo:\n"
            )
            text += f"Address: `{user_wallets[0]['address']}`\n\n"
            text += (
                "*MetaMask se fund karo:*\n"
                f"RPC: `{SEISMIC_RPC}`\n"
                f"Chain ID: `{SEISMIC_CHAIN_ID}`\n\n"
                "Ya neeche faucet link se claim karo:\n"
            )
            keyboard = [
                [
                    InlineKeyboardButton(
                        "💧 Seismic Faucet", url=SEISMIC_COMMUNITY_FAUCET
                    ),
                ],
            ]
            await msg.edit_text(
                text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True,
            )
            return
        else:
            text += "✅ Saare wallets already funded hain!\n"

    # Show final balances
    text += "\n*Updated Balances:*\n"
    for i, w in enumerate(user_wallets, 1):
        bal = get_balance(w["address"])
        text += f"#{i} `{short_addr(w['address'])}` → {bal:.6f} ETH\n"

    await msg.edit_text(text, parse_mode="Markdown", disable_web_page_preview=True)


# ─── Deploy Contract ─────────────────────────────────────────────────
async def deploy_contract(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    user_wallets = get_user_wallets(user_id)

    if not user_wallets:
        await update.message.reply_text(
            "❌ Pehle wallet banao: `/generate`", parse_mode="Markdown"
        )
        return

    # Use first funded wallet or first wallet
    funded_wallet = None
    for w in user_wallets:
        if get_balance(w["address"]) > 0:
            funded_wallet = w
            break

    if not funded_wallet:
        await update.message.reply_text(
            "❌ Kisi bhi wallet mein balance nahi hai!\n"
            "Pehle `/faucet` se ETH claim karo.",
            parse_mode="Markdown",
        )
        return

    msg = await update.message.reply_text(
        f"⏳ Contract deploy ho raha hai wallet `{short_addr(funded_wallet['address'])}` se...",
        parse_mode="Markdown",
    )

    try:
        acct = Account.from_key(funded_wallet["private_key"])
        nonce = w3.eth.get_transaction_count(acct.address)
        gas_price = w3.eth.gas_price

        tx = {
            "nonce": nonce,
            "gasPrice": gas_price,
            "gas": 500000,
            "data": SIMPLE_STORAGE_BYTECODE,
            "chainId": SEISMIC_CHAIN_ID,
            "value": 0,
        }

        signed = acct.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        contract_addr = receipt.contractAddress
        tx_hash_hex = tx_hash.hex()

        text = (
            "✅ *Contract Deploy Successful!*\n\n"
            f"📄 Contract: `{contract_addr}`\n"
            f"🔗 [Contract on Explorer]({explorer_link(contract_addr)})\n"
            f"📝 Tx Hash: `{short_addr(tx_hash_hex)}`\n"
            f"🔗 [Transaction]({explorer_link(tx_hash_hex, 'tx')})\n"
            f"⛽ Gas Used: `{receipt.gasUsed}`\n"
            f"📦 Block: `{receipt.blockNumber}`\n"
            f"👛 From: `{short_addr(funded_wallet['address'])}`"
        )

        await msg.edit_text(text, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        await msg.edit_text(
            f"❌ *Deploy Failed!*\n\nError: `{str(e)[:200]}`\n\n"
            "Possible reasons:\n"
            "• Insufficient ETH balance\n"
            "• Network congestion\n"
            "• RPC issue\n\n"
            "Pehle `/faucet` se ETH claim karo.",
            parse_mode="Markdown",
        )


# ─── Send ETH ────────────────────────────────────────────────────────
async def send_eth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    user_wallets = get_user_wallets(user_id)

    if not user_wallets:
        await update.message.reply_text(
            "❌ Pehle wallet banao: `/generate`", parse_mode="Markdown"
        )
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage: `/send <to_address> <amount_in_ETH>`\n"
            "Example: `/send 0x1234...abcd 0.01`",
            parse_mode="Markdown",
        )
        return

    to_address = context.args[0]
    try:
        amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Valid amount do (e.g., 0.01)")
        return

    if not Web3.is_address(to_address):
        await update.message.reply_text("❌ Invalid address!")
        return

    funded_wallet = None
    for w in user_wallets:
        if get_balance(w["address"]) >= amount:
            funded_wallet = w
            break

    if not funded_wallet:
        await update.message.reply_text(
            "❌ Kisi wallet mein itna balance nahi hai!", parse_mode="Markdown"
        )
        return

    msg = await update.message.reply_text("⏳ Transaction send ho rahi hai...")

    try:
        acct = Account.from_key(funded_wallet["private_key"])
        nonce = w3.eth.get_transaction_count(acct.address)

        tx = {
            "nonce": nonce,
            "to": Web3.to_checksum_address(to_address),
            "value": Web3.to_wei(amount, "ether"),
            "gas": 21000,
            "gasPrice": w3.eth.gas_price,
            "chainId": SEISMIC_CHAIN_ID,
        }

        signed = acct.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        text = (
            "✅ *Transaction Successful!*\n\n"
            f"📤 From: `{short_addr(funded_wallet['address'])}`\n"
            f"📥 To: `{short_addr(to_address)}`\n"
            f"💰 Amount: *{amount} ETH*\n"
            f"📝 Tx: `{short_addr(tx_hash.hex())}`\n"
            f"🔗 [View Transaction]({explorer_link(tx_hash.hex(), 'tx')})\n"
            f"⛽ Gas: `{receipt.gasUsed}`\n"
            f"📦 Block: `{receipt.blockNumber}`"
        )

        await msg.edit_text(text, parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        await msg.edit_text(f"❌ *Transaction Failed!*\n\nError: `{str(e)[:200]}`", parse_mode="Markdown")


# ─── Transfer All (Distribute ETH) ──────────────────────────────────
async def transfer_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    user_wallets = get_user_wallets(user_id)

    if len(user_wallets) < 2:
        await update.message.reply_text(
            "❌ Kam se kam 2 wallets chahiye! `/generate 2` se banao.",
            parse_mode="Markdown",
        )
        return

    # Find wallet with highest balance
    max_balance = 0.0
    source_wallet = None
    for w in user_wallets:
        bal = get_balance(w["address"])
        if bal > max_balance:
            max_balance = bal
            source_wallet = w

    if not source_wallet or max_balance <= 0:
        await update.message.reply_text("❌ Kisi wallet mein balance nahi hai!")
        return

    other_wallets = [w for w in user_wallets if w["address"] != source_wallet["address"]]
    amount_each = (max_balance * 0.8) / len(other_wallets)  # 80% distribute, 20% gas reserve

    if amount_each <= 0:
        await update.message.reply_text("❌ Distribute karne ke liye insufficient balance!")
        return

    msg = await update.message.reply_text(
        f"⏳ {len(other_wallets)} wallets mein ETH distribute ho rahi hai...\n"
        f"Source: `{short_addr(source_wallet['address'])}` ({max_balance:.6f} ETH)\n"
        f"Amount each: ~{amount_each:.6f} ETH",
        parse_mode="Markdown",
    )

    acct = Account.from_key(source_wallet["private_key"])
    results = []
    nonce = w3.eth.get_transaction_count(acct.address)

    for w in other_wallets:
        try:
            tx = {
                "nonce": nonce,
                "to": Web3.to_checksum_address(w["address"]),
                "value": Web3.to_wei(amount_each, "ether"),
                "gas": 21000,
                "gasPrice": w3.eth.gas_price,
                "chainId": SEISMIC_CHAIN_ID,
            }
            signed = acct.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            results.append(f"✅ #{user_wallets.index(w)+1} `{short_addr(w['address'])}` → {amount_each:.6f} ETH")
            nonce += 1
        except Exception as e:
            results.append(f"❌ #{user_wallets.index(w)+1} `{short_addr(w['address'])}` → Failed: {str(e)[:50]}")

    text = "📊 *ETH Distribution Results:*\n\n" + "\n".join(results)
    await msg.edit_text(text, parse_mode="Markdown", disable_web_page_preview=True)


# ─── Run All (Automated Tasks) ──────────────────────────────────────
async def run_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    user_wallets = get_user_wallets(user_id)

    if not user_wallets:
        await update.message.reply_text(
            "❌ Pehle wallets banao: `/generate 5`", parse_mode="Markdown"
        )
        return

    msg = await update.message.reply_text(
        f"🤖 *Auto Run Started!*\n\n"
        f"📋 {len(user_wallets)} wallets pe tasks chal rahe hain...\n\n"
        f"Tasks:\n"
        f"1️⃣ Balance check\n"
        f"2️⃣ Self-transfer (activity generate)\n"
        f"3️⃣ Contract deploy (funded wallets)\n"
        f"4️⃣ Inter-wallet transfers\n\n"
        f"⏳ Please wait...",
        parse_mode="Markdown",
    )

    results = []

    # Step 1: Check balances
    funded_wallets = []
    unfunded_wallets = []
    for w in user_wallets:
        bal = get_balance(w["address"])
        if bal > 0.001:
            funded_wallets.append((w, bal))
        else:
            unfunded_wallets.append(w)

    results.append(f"💰 *Balance Check:* {len(funded_wallets)} funded, {len(unfunded_wallets)} empty")

    if not funded_wallets:
        results.append("\n❌ Koi funded wallet nahi! Pehle `/faucet` se ETH claim karo.")
        text = "🤖 *Auto Run Results:*\n\n" + "\n".join(results)
        await msg.edit_text(text, parse_mode="Markdown")
        return

    # Step 2: Self-transfers (activity generate)
    self_tx_count = 0
    for w, bal in funded_wallets:
        if bal < 0.001:
            continue
        try:
            acct = Account.from_key(w["private_key"])
            nonce = w3.eth.get_transaction_count(acct.address)
            tx = {
                "nonce": nonce,
                "to": acct.address,
                "value": Web3.to_wei(0.0001, "ether"),
                "gas": 21000,
                "gasPrice": w3.eth.gas_price,
                "chainId": SEISMIC_CHAIN_ID,
            }
            signed = acct.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            self_tx_count += 1
        except Exception:
            pass

    results.append(f"🔄 *Self-Transfers:* {self_tx_count}/{len(funded_wallets)} successful")

    # Step 3: Contract deployment (first funded wallet)
    deploy_count = 0
    for w, bal in funded_wallets[:3]:  # Deploy from up to 3 wallets
        if bal < 0.01:
            continue
        try:
            acct = Account.from_key(w["private_key"])
            nonce = w3.eth.get_transaction_count(acct.address)

            tx = {
                "nonce": nonce,
                "gasPrice": w3.eth.gas_price,
                "gas": 500000,
                "data": SIMPLE_STORAGE_BYTECODE,
                "chainId": SEISMIC_CHAIN_ID,
                "value": 0,
            }
            signed = acct.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            if receipt.contractAddress:
                deploy_count += 1
        except Exception:
            pass

    results.append(f"📄 *Contracts Deployed:* {deploy_count}")

    # Step 4: Inter-wallet transfers
    inter_tx_count = 0
    if len(funded_wallets) >= 2:
        for i in range(len(funded_wallets) - 1):
            w_from, bal_from = funded_wallets[i]
            w_to, _ = funded_wallets[i + 1]
            if bal_from < 0.002:
                continue
            try:
                acct = Account.from_key(w_from["private_key"])
                nonce = w3.eth.get_transaction_count(acct.address)
                tx = {
                    "nonce": nonce,
                    "to": Web3.to_checksum_address(w_to["address"]),
                    "value": Web3.to_wei(0.0001, "ether"),
                    "gas": 21000,
                    "gasPrice": w3.eth.gas_price,
                    "chainId": SEISMIC_CHAIN_ID,
                }
                signed = acct.sign_transaction(tx)
                tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
                w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
                inter_tx_count += 1
            except Exception:
                pass

    results.append(f"↔️ *Inter-wallet Transfers:* {inter_tx_count}")

    # Final summary
    text = (
        "🤖 *Auto Run Complete!*\n\n"
        + "\n".join(results)
        + "\n\n✅ Saare automated tasks complete ho gaye!"
        + "\n\n💡 Tip: Baar baar `/run_all` chalao activity badhane ke liye."
    )
    await msg.edit_text(text, parse_mode="Markdown", disable_web_page_preview=True)


# ─── Export Wallets ──────────────────────────────────────────────────
async def export_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    user_wallets = get_user_wallets(user_id)

    if not user_wallets:
        await update.message.reply_text(
            "❌ Koi wallet nahi hai.", parse_mode="Markdown"
        )
        return

    text = "📋 *Wallet Export (Private Keys):*\n\n"
    text += "⚠️ *Ye message save karke delete kar dena!*\n\n"

    for i, w in enumerate(user_wallets, 1):
        balance = get_balance(w["address"])
        text += (
            f"*Wallet #{i}*\n"
            f"Address: `{w['address']}`\n"
            f"Key: `{w['private_key']}`\n"
            f"Balance: {balance:.6f} ETH\n\n"
        )

    text += (
        f"*Network Config:*\n"
        f"RPC: `{SEISMIC_RPC}`\n"
        f"Chain ID: `{SEISMIC_CHAIN_ID}`\n"
        f"Explorer: `{SEISMIC_EXPLORER}`"
    )

    # Send as private message
    await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)


# ─── Delete Wallet ───────────────────────────────────────────────────
async def delete_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)

    if not context.args:
        await update.message.reply_text(
            "Usage: `/delete_wallet <index>`\n`/wallets` se index dekho.",
            parse_mode="Markdown",
        )
        return

    try:
        index = int(context.args[0]) - 1
    except ValueError:
        await update.message.reply_text("❌ Valid index do!")
        return

    wallets = load_wallets()
    user_wallets = wallets.get(user_id, [])

    if index < 0 or index >= len(user_wallets):
        await update.message.reply_text("❌ Invalid wallet index!")
        return

    removed = user_wallets.pop(index)
    # Re-index
    for i, w in enumerate(user_wallets):
        w["index"] = i + 1
    wallets[user_id] = user_wallets
    save_wallets(wallets)

    await update.message.reply_text(
        f"🗑️ Wallet `{short_addr(removed['address'])}` delete ho gaya!",
        parse_mode="Markdown",
    )


# ─── Main ────────────────────────────────────────────────────────────
def main() -> None:
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ TELEGRAM_BOT_TOKEN set karo!")
        print("   export TELEGRAM_BOT_TOKEN='your_token_here'")
        print("   ya .env file mein set karo")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("network", network_info))
    app.add_handler(CommandHandler("generate", generate_wallets))
    app.add_handler(CommandHandler("wallets", view_wallets))
    app.add_handler(CommandHandler("balance", check_balance))
    app.add_handler(CommandHandler("faucet", claim_faucet))
    app.add_handler(CommandHandler("deploy", deploy_contract))
    app.add_handler(CommandHandler("send", send_eth))
    app.add_handler(CommandHandler("transfer_all", transfer_all))
    app.add_handler(CommandHandler("run_all", run_all))
    app.add_handler(CommandHandler("export", export_wallets))
    app.add_handler(CommandHandler("delete_wallet", delete_wallet))

    print("🚀 Seismic Testnet Bot started!")
    print(f"🔗 Network: Seismic Testnet (Chain ID: {SEISMIC_CHAIN_ID})")
    print(f"🌐 RPC: {SEISMIC_RPC}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
