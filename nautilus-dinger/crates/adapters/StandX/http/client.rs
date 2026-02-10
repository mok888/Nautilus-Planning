use crate::common::urls::REST_BASE_URL;
use crate::config::StandXConfig;
use crate::error::StandXError;
use crate::http::signing::StandXSigner;
use bytes::Bytes;
use http_body_util::{BodyExt, Full};
use http::{HeaderMap, HeaderValue, Method, Request, StatusCode, Uri};
use hyper_util::client::legacy::Client;
use hyper_util::client::legacy::connect::HttpConnector;
use hyper_rustls::HttpsConnectorBuilder;
use serde::Serialize;
use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};
use uuid::Uuid;

pub struct HttpClient {
    client: Client<hyper_rustls::HttpsConnector<HttpConnector>, Full<Bytes>>,
    config: Arc<StandXConfig>,
    signer: Option<StandXSigner>,
}

impl HttpClient {
    pub fn new(config: StandXConfig) -> Result<Self, StandXError> {
        let https = HttpsConnectorBuilder::new()
            .with_native_roots()
            .https_only()
            .enable_http1()
            .build();

        let client = Client::builder(tokio::runtime::Handle::current()).build(https);

        let signer = if let (Some(_), Some(secret)) = (&config.api_key, &config.secret) {
            Some(StandXSigner::new(secret.clone()))
        } else {
            None
        };

        Ok(Self {
            client,
            config: Arc::new(config),
            signer,
        })
    }

    async fn request_raw<T: Serialize>(
        &self,
        method: Method,
        path: &str,
        body: Option<&T>,
        auth_required: bool,
    ) -> Result<(StatusCode, Bytes), StandXError> {
        let base_url = self.config.get_rest_url();
        let url_str = format!("{}{}", base_url, path);
        let uri: Uri = url_str.parse().map_err(|e| StandXError::HttpError(e.to_string()))?;

        // Timestamp in milliseconds
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_millis()
            .to_string();

        let request_id = Uuid::new_v4().to_string();
        
        let body_str = if let Some(b) = body {
            serde_json::to_string(b)?
        } else {
            String::new()
        };

        let mut builder = Request::builder().method(method.clone()).uri(uri);

        // Headers
        builder = builder.header("Content-Type", "application/json");
        builder = builder.header("x-request-id", &request_id);
        builder = builder.header("x-request-timestamp", &timestamp);
        builder = builder.header("x-request-sign-version", "1");

        if auth_required {
            if let (Some(signer), Some(api_key)) = (&self.signer, &self.config.api_key) {
                let signature = signer.sign("1", &request_id, &timestamp, &body_str)?;
                builder = builder.header("x-request-signature", signature);
                builder = builder.header("Authorization", format!("Bearer {}", api_key));
            } else {
                return Err(StandXError::AuthError(
                    "API Key or Secret missing for authenticated request".to_string(),
                ));
            }
        }

        // Body
        let req_body = Full::new(Bytes::from(body_str));
        let req = builder.body(req_body).map_err(|e| StandXError::HttpError(e.to_string()))?;

        let res = self.client.request(req).await.map_err(|e| StandXError::HttpError(e.to_string()))?;
        let status = res.status();
        let body_bytes = res.collect().await.map_err(|e| StandXError::HttpError(e.to_string()))?.to_bytes();

        if status.as_u16() >= 400 {
            let err_msg = String::from_utf8_lossy(&body_bytes).to_string();
            return Err(StandXError::HttpError(format!("Status: {}, Body: {}", status, err_msg)));
        }

        Ok((status, body_bytes))
    }

    pub async fn get<T: Serialize, R: for<'de> serde::Deserialize<'de>>(
        &self,
        path: &str,
        params: Option<&T>,
        auth_required: bool,
    ) -> Result<R, StandXError> {
        // In GET, body is usually empty, but we pass params in query string logic if needed.
        // Simplified here: GET with empty body, relying on `self.request_raw` handling the body structure.
        let (_, body) = self.request_raw(Method::GET, path, &None::<()>, auth_required).await?;
        let parsed: R = serde_json::from_slice(&body)?;
        Ok(parsed)
    }

    pub async fn post<T: Serialize, R: for<'de> serde::Deserialize<'de>>(
        &self,
        path: &str,
        body: &T,
        auth_required: bool,
    ) -> Result<R, StandXError> {
        let (_, res_body) = self.request_raw(Method::POST, path, Some(body), auth_required).await?;
        let parsed: R = serde_json::from_slice(&res_body)?;
        Ok(parsed)
    }
}
