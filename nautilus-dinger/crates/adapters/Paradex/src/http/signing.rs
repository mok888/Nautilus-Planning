use starknet_core::crypto::compute_hash_on_elements;
use starknet_core::utils::starknet_keccak;
use starknet_crypto::{rfc6979_generate_k, sign};
use starknet_ff::FieldElement;

// Domain: StarkNetDomain(name:felt,chainId:felt,version:felt)
// Order: Order(timestamp:felt,market:felt,side:felt,orderType:felt,size:felt,price:felt)
// Request (auth): Request(method:felt,path:felt,body:felt,timestamp:felt,expiration:felt)

fn get_domain_type_hash() -> FieldElement {
    starknet_keccak("StarkNetDomain(name:felt,chainId:felt,version:felt)".as_bytes())
}

fn get_order_type_hash() -> FieldElement {
    starknet_keccak(
        "Order(timestamp:felt,market:felt,side:felt,orderType:felt,size:felt,price:felt)"
            .as_bytes(),
    )
}

fn get_modify_order_type_hash() -> FieldElement {
    starknet_keccak(
        "ModifyOrder(timestamp:felt,market:felt,side:felt,orderType:felt,size:felt,price:felt,id:felt)"
            .as_bytes(),
    )
}

fn get_auth_request_type_hash() -> FieldElement {
    starknet_keccak(
        "Request(method:felt,path:felt,body:felt,timestamp:felt,expiration:felt)".as_bytes(),
    )
}

/// Convert a short string (ASCII < 31 chars) to a FieldElement.
pub fn short_string_to_felt(text: &str) -> Result<FieldElement, String> {
    if text.len() > 31 {
        return Err(format!("Short string too long: {} > 31", text.len()));
    }
    if text.is_empty() {
        return Ok(FieldElement::ZERO);
    }
    let bytes = text.as_bytes();
    let mut buffer = [0u8; 32];
    buffer[32 - bytes.len()..].copy_from_slice(bytes);
    FieldElement::from_bytes_be(&buffer).map_err(|e| format!("Felt conversion error: {}", e))
}

// --- Order Params Struct ---
pub struct OrderParams {
    pub chain_id: String,
    pub timestamp: u64, // milliseconds
    pub market: String,
    pub side: String,
    pub order_type: String,
    pub size: String,
    pub price: String,
}

pub struct ModifyOrderParams {
    pub chain_id: String,
    pub timestamp: u64, // milliseconds
    pub market: String,
    pub side: String,
    pub order_type: String,
    pub size: String,
    pub price: String,
    pub id: String,
}

fn compute_domain_hash(chain_id: &FieldElement) -> FieldElement {
    let name = short_string_to_felt("Paradex").unwrap();
    let version = FieldElement::ONE;
    compute_hash_on_elements(&[get_domain_type_hash(), name, *chain_id, version])
}

fn sign_with_seed_32(
    private_key: &FieldElement,
    message_hash: &FieldElement,
) -> Result<(FieldElement, FieldElement), String> {
    let seed = FieldElement::from(32u64);
    let k = rfc6979_generate_k(message_hash, private_key, Some(&seed));
    let sig = sign(private_key, message_hash, &k).map_err(|e| format!("Signing error: {}", e))?;
    Ok((sig.r, sig.s))
}

/// Parse a chain_id string (hex, decimal, or short string) into a FieldElement.
fn parse_chain_id(chain_id: &str) -> Result<FieldElement, String> {
    FieldElement::from_hex_be(chain_id)
        .or_else(|_| FieldElement::from_dec_str(chain_id))
        .or_else(|_| short_string_to_felt(chain_id))
        .map_err(|e| format!("Invalid chain_id: {}", e))
}

/// Sign the auth request message to obtain a JWT.
/// This matches paradex-py's `build_auth_message` TypedData:
///   Request(method:felt, path:felt, body:felt, timestamp:felt, expiration:felt)
///   message: { method: "POST", path: "/v1/auth", body: "", timestamp, expiration }
///   domain: { name: "Paradex", chainId: hex(chain_id), version: "1" }
pub fn sign_auth_message(
    private_key_hex: &str,
    account_address_hex: &str,
    chain_id_str: &str,
    timestamp: u64,  // seconds
    expiration: u64, // seconds (timestamp + 86400)
) -> Result<String, String> {
    let pk =
        FieldElement::from_hex_be(private_key_hex).map_err(|e| format!("Invalid PK: {}", e))?;
    let message_hash = auth_message_hash(account_address_hex, chain_id_str, timestamp, expiration)?;

    let (r, s) = sign_with_seed_32(&pk, &message_hash)?;
    Ok(format!("[\"{}\",\"{}\"]", r, s))
}

pub fn auth_message_hash(
    account_address_hex: &str,
    chain_id_str: &str,
    timestamp: u64,
    expiration: u64,
) -> Result<FieldElement, String> {
    let addr = FieldElement::from_hex_be(account_address_hex)
        .map_err(|e| format!("Invalid Addr: {}", e))?;
    let chain_id_felt = parse_chain_id(chain_id_str)?;

    let domain_hash = compute_domain_hash(&chain_id_felt);

    let method_felt = short_string_to_felt("POST")?;
    let path_felt = short_string_to_felt("/v1/auth")?;
    let body_felt = FieldElement::ZERO;
    let timestamp_felt = FieldElement::from(timestamp);
    let expiration_felt = FieldElement::from(expiration);

    let request_hash = compute_hash_on_elements(&[
        get_auth_request_type_hash(),
        method_felt,
        path_felt,
        body_felt,
        timestamp_felt,
        expiration_felt,
    ]);

    let prefix = short_string_to_felt("StarkNet Message").unwrap();
    Ok(compute_hash_on_elements(&[prefix, domain_hash, addr, request_hash]))
}

/// Sign an order for submission.
/// Matches paradex-py's `build_order_message` TypedData.
/// timestamp is in milliseconds (used as nonce).
pub fn sign_order(
    private_key_hex: &str,
    account_address_hex: &str,
    params: OrderParams,
) -> Result<String, String> {
    let pk =
        FieldElement::from_hex_be(private_key_hex).map_err(|e| format!("Invalid PK hex: {}", e))?;
    let addr = FieldElement::from_hex_be(account_address_hex)
        .map_err(|e| format!("Invalid Addr hex: {}", e))?;
    let chain_id_felt = parse_chain_id(&params.chain_id)?;

    let domain_hash = compute_domain_hash(&chain_id_felt);

    let market_felt = short_string_to_felt(&params.market)?;
    let side_felt =
        FieldElement::from_dec_str(&params.side).or_else(|_| short_string_to_felt(&params.side))?;
    let type_felt = short_string_to_felt(&params.order_type)?;
    let size_felt =
        FieldElement::from_dec_str(&params.size).or_else(|_| short_string_to_felt(&params.size))?;
    let price_felt = FieldElement::from_dec_str(&params.price)
        .or_else(|_| short_string_to_felt(&params.price))?;
    let timestamp_felt = FieldElement::from(params.timestamp);

    let order_hash = compute_hash_on_elements(&[
        get_order_type_hash(),
        timestamp_felt,
        market_felt,
        side_felt,
        type_felt,
        size_felt,
        price_felt,
    ]);

    let prefix = short_string_to_felt("StarkNet Message").unwrap();
    let message_hash = compute_hash_on_elements(&[prefix, domain_hash, addr, order_hash]);

    let (r, s) = sign_with_seed_32(&pk, &message_hash)?;
    Ok(format!("[\"{}\",\"{}\"]", r, s))
}

pub fn sign_modify_order(
    private_key_hex: &str,
    account_address_hex: &str,
    params: ModifyOrderParams,
) -> Result<String, String> {
    let pk =
        FieldElement::from_hex_be(private_key_hex).map_err(|e| format!("Invalid PK hex: {}", e))?;
    let addr = FieldElement::from_hex_be(account_address_hex)
        .map_err(|e| format!("Invalid Addr hex: {}", e))?;
    let chain_id_felt = parse_chain_id(&params.chain_id)?;

    let domain_hash = compute_domain_hash(&chain_id_felt);

    let market_felt = short_string_to_felt(&params.market)?;
    let side_felt =
        FieldElement::from_dec_str(&params.side).or_else(|_| short_string_to_felt(&params.side))?;
    let type_felt = short_string_to_felt(&params.order_type)?;
    let size_felt =
        FieldElement::from_dec_str(&params.size).or_else(|_| short_string_to_felt(&params.size))?;
    let price_felt = FieldElement::from_dec_str(&params.price)
        .or_else(|_| short_string_to_felt(&params.price))?;
    let id_felt =
        FieldElement::from_dec_str(&params.id).or_else(|_| short_string_to_felt(&params.id))?;
    let timestamp_felt = FieldElement::from(params.timestamp);

    let order_hash = compute_hash_on_elements(&[
        get_modify_order_type_hash(),
        timestamp_felt,
        market_felt,
        side_felt,
        type_felt,
        size_felt,
        price_felt,
        id_felt,
    ]);

    let prefix = short_string_to_felt("StarkNet Message").unwrap();
    let message_hash = compute_hash_on_elements(&[prefix, domain_hash, addr, order_hash]);

    let (r, s) = sign_with_seed_32(&pk, &message_hash)?;
    Ok(format!("[\"{}\",\"{}\"]", r, s))
}
