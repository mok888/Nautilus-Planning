use crate::config::Credential;
use crate::error::{LighterAdapterError, Result};
use crate::http::signing::{generate_timestamp, Signer};
use hyper::header::{HeaderName, HeaderValue, CONTENT_TYPE};
use hyper::Method;
use hyper::{Request, Response, StatusCode};
use hyper::body::Incoming;
use hyper_rustls::HttpsConnector;
use hyper_util::client::legacy::connect::HttpConnector;
use hyper_util::client::legacy::Client;
use hyper_util::rt::TokioExecutor;
use serde::de::DeserializeOwned;
use serde::Serialize;

pub struct HttpClient {
    inner: Client<HttpsConnector<HttpConnector>, Incoming>,
    base_url: String,
    chain_id: String,
    credential: Option<Credential>,
    signer: Option<Signer>,
}

impl HttpClient {
    pub fn new(base_url: String, chain_id: String, credential: Option<Credential>) -> Self {
        let https = hyper_rustls::HttpsConnectorBuilder::new()
            .with_native_roots()
            .unwrap()
            .https_or_http()
            .enable_http1()
            .build();

        let inner = Client::builder(TokioExecutor::new()).build(https);

        let signer = credential.as_ref().map(|c| Signer::new(c.api_secret.clone()));

        Self {
            inner,
            base_url,
            chain_id,
            credential,
            signer,
        }
    }

    async fn send_request(
        &self,
        method: Method,
        path: &str,
        body_bytes: Vec<u8>,
        auth: bool,
    ) -> Result<Response<Incoming>> {
        let url = format!("{}{}", self.base_url, path);
        
        // Calculate signature if auth is required
        let timestamp = generate_timestamp();
        let body_str = String::from_utf8(body_bytes.clone())?;
        
        let signature = if auth {
            if let Some(signer) = &self.signer {
                Some(signer.sign(timestamp, method.as_str(), path, &body_str)?)
            } else {
                return Err(LighterAdapterError::InvalidCredentials);
            }
        } else {
            None
        };

        let mut request_builder = Request::builder()
            .method(method)
            .uri(&url);

        // Set Headers
        request_builder = request_builder.header("x-lighter-chain-id", &self.chain_id);
        request_builder = request_builder.header(CONTENT_TYPE, HeaderValue::from_static("application/json"));
        
        if auth {
            if let Some(cred) = &self.credential {
                request_builder = request_builder.header("x-api-key", &cred.api_key);
                request_builder = request_builder.header("x-timestamp", timestamp.to_string());
                if let Some(sig) = signature {
                    request_builder = request_builder.header("x-signature", sig);
                }
            }
        }

        let request = request_builder.body(body_bytes.into())?;
        let response = self.inner.request(request).await?;
        
        let status = response.status();
        if !status.is_success() {
            let error_bytes = hyper::body::to_bytes(response.into_body()).await?;
            let error_msg = String::from_utf8_lossy(&error_bytes).to_string();
            
            if status == StatusCode::UNAUTHORIZED || status == StatusCode::FORBIDDEN {
                return Err(LighterAdapterError::AuthError(error_msg));
            } else if status == StatusCode::TOO_MANY_REQUESTS {
                return Err(LighterAdapterError::RateLimitExceeded);
            } else {
                return Err(LighterAdapterError::ExchangeError {
                    code: status.as_u16() as i32,
                    msg: error_msg,
                });
            }
        }

        Ok(response)
    }

    pub async fn get<T: DeserializeOwned>(&self, path: &str, auth: bool) -> Result<T> {
        let response = self.send_request(Method::GET, path, vec![], auth).await?;
        let body_bytes = hyper::body::to_bytes(response.into_body()).await?;
        serde_json::from_slice(&body_bytes).map_err(Into::into)
    }

    pub async fn post<T: DeserializeOwned, B: Serialize>(
        &self,
        path: &str,
        body: B,
        auth: bool,
    ) -> Result<T> {
        let json_body = serde_json::to_vec(&body)?;
        let response = self
            .send_request(Method::POST, path, json_body, auth)
            .await?;
        let body_bytes = hyper::body::to_bytes(response.into_body()).await?;
        serde_json::from_slice(&body_bytes).map_err(Into::into)
    }
}