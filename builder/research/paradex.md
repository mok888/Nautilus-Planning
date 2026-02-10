# Paradex Integration Research

## Overview
Paradex is a Starknet-based L2 derivative exchange.

## Authentication
Paradex uses Starknet signatures (on the STARK curve). Standard Ed25519 or HMAC libraries **will not work**.

### Verified Method: Subkey Authentication (L2-Only)
We verified that you can authenticate using **only** L2 credentials (Subkeys), bypassing the need for an Ethereum (L1) private key.

**Required Credentials:**
1.  `PARADEX_MAIN_ACCOUNT_L2_ADDRESS`: The Starknet address of the main trading account.
2.  `PARADEX_SUBKEY_PRIVATE_KEY`: The private key of an authorized subkey.

**Helper Library:**
You **MUST** use the official `paradex-py` library (or a Rust equivalent like `starknet-rs`) to generate valid signatures.

**Python Implementation:**
See `src/auth_builders.py`: `paradex_sign` function.
It uses `paradex_py.account.subkey_account.SubkeyAccount` to generate the following headers:
- `PARADEX-STARKNET-ACCOUNT`
- `PARADEX-STARKNET-SIGNATURE` (JSON array `["r", "s"]`)
- `PARADEX-TIMESTAMP`
- `PARADEX-SIGNATURE-EXPIRATION`

### Endpoints
- **Testnet REST**: `https://api.testnet.paradex.trade/v1`
- **Mainnet REST**: `https://api.prod.paradex.trade/v1`

## Dependencies
- `paradex-py>=0.5.4`
- `starknet-py`
- `crypto-cpp-py`
