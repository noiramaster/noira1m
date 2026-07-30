import logging, json, time, requests
from pathlib import Path
from web3 import Web3

logger = logging.getLogger("noira1m.testnet")

DATA_DIR = Path(__file__).parent.parent / "data"

# Testnet RPCs
NETWORKS = {
    "sepolia": {"rpc": "https://rpc.sepolia.org", "chain_id": 11155111, "explorer": "https://sepolia.etherscan.io"},
    "goerli": {"rpc": "https://rpc.ankr.com/eth_goerli", "chain_id": 5, "explorer": "https://goerli.etherscan.io"},
    "holesky": {"rpc": "https://ethereum-holesky.publicnode.com", "chain_id": 17000, "explorer": "https://holesky.etherscan.io"},
    "bsc_testnet": {"rpc": "https://data-seed-prebsc-1-s1.binance.org:8545", "chain_id": 97, "explorer": "https://testnet.bscscan.com"},
    "mumbai": {"rpc": "https://rpc-mumbai.maticvigil.com", "chain_id": 80001, "explorer": "https://mumbai.polygonscan.com"},
    "optimism_goerli": {"rpc": "https://goerli.optimism.io", "chain_id": 420, "explorer": "https://goerli-optimism.etherscan.io"},
    "arbitrum_goerli": {"rpc": "https://goerli-rollup.arbitrum.io/rpc", "chain_id": 421613, "explorer": "https://goerli.arbiscan.io"},
    "scroll_sepolia": {"rpc": "https://sepolia-rpc.scroll.io", "chain_id": 534351, "explorer": "https://sepolia.scrollscan.com"},
    "base_goerli": {"rpc": "https://goerli.base.org", "chain_id": 84531, "explorer": "https://goerli.basescan.org"},
    "linea_goerli": {"rpc": "https://rpc.goerli.linea.build", "chain_id": 59140, "explorer": "https://goerli.lineascan.build"},
}

def get_testnet_eth(address: str) -> bool:
    faucets = [
        lambda a: requests.get(f"https://faucet.quicknode.com/ethereum/sepolia/{a}", timeout=10),
        lambda a: requests.get(f"https://www.infura.io/faucet/sepolia/{a}", timeout=10),
    ]
    for faucet in faucets:
        try:
            resp = faucet(address)
            if resp.status_code == 200:
                logger.info(f"Testnet ETH claimed for {address[:10]}...")
                return True
        except:
            continue
    return False

def send_transaction(private_key: str, to_address: str, network: str = "sepolia") -> str:
    net = NETWORKS.get(network)
    if not net:
        return ""
    w3 = Web3(Web3.HTTPProvider(net["rpc"]))
    if not w3.is_connected():
        return ""
    account = w3.eth.account.from_key(private_key)
    try:
        tx = {
            "nonce": w3.eth.get_transaction_count(account.address),
            "to": to_address,
            "value": w3.to_wei(0.0001, "ether"),
            "gas": 21000,
            "gasPrice": w3.eth.gas_price,
            "chainId": net["chain_id"],
        }
        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        logger.info(f"Tx sent: {net['explorer']}/tx/{w3.to_hex(tx_hash)}")
        return w3.to_hex(tx_hash)
    except Exception as e:
        logger.debug(f"Tx error: {e}")
        return ""

def farm_all() -> dict:
    result = {"wallets_created": 0, "tx_sent": 0, "testnet_claimed": 0}
    # Create wallets
    from farming.wallets import generate_wallets, get_unused_wallets, mark_used
    generate_wallets(5)
    result["wallets_created"] = 5
    
    # Get testnet ETH for wallets
    wallets = get_unused_wallets(3)
    for w in wallets:
        if get_testnet_eth(w["address"]):
            result["testnet_claimed"] += 1
            time.sleep(3)
    
    # Send transactions
    wallets = get_unused_wallets(2)
    for w in wallets:
        # Send to self or random
        tx = send_transaction(w["private_key"], w["address"], "sepolia")
        if tx:
            mark_used(w["address"], tx)
            result["tx_sent"] += 1
            time.sleep(2)
    
    logger.info(f"Farming: {result}")
    return result
