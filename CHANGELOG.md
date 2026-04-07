# CHANGELOG

<!-- version list -->

## v0.23.0 (2026-04-07)

### Features

- **unified**: :sparkles: add unified exchange client layer
  ([`157cf29`](https://github.com/vispar-tech/aiotrade/commit/157cf29118b06feb4283b2eca07525d904a514b5))


## v0.22.0 (2026-03-23)

### Features

- **kucoin**: :sparkles: add broker parameters to KuCoin client and HTTP client
  ([`5332b03`](https://github.com/vispar-tech/aiotrade/commit/5332b039ebaafdc54321a9a9d76511d794b2dac4))

- **kucoin**: :sparkles: add support for additional API partner header masking
  ([`a630673`](https://github.com/vispar-tech/aiotrade/commit/a630673f885b40f0b67079c974008d5d027a8be4))


## v0.21.0 (2026-03-19)

### Features

- **kucoin**: :sparkles: enhance KuCoin client tests and update URLs
  ([`c3c77f9`](https://github.com/vispar-tech/aiotrade/commit/c3c77f9962ecfb3c7fb3263961820d1cc250cec0))


## v0.20.0 (2026-03-18)

### Bug Fixes

- **kucoin**: :wrench: update token request URL construction in BrokerClient
  ([`dffa545`](https://github.com/vispar-tech/aiotrade/commit/dffa5452392ef3b0fa7f1369f99dd73f31af8b04))

### Features

- **kucoin**: :sparkles: implement OAuth 2.0 flow and enhance BrokerClient functionality
  ([`005590d`](https://github.com/vispar-tech/aiotrade/commit/005590d107192fc6891afe48fd78f52c1582305a))


## v0.19.0 (2026-03-18)

### Features

- **kucoin**: :sparkles: add KuCoin support and update dependencies
  ([`1b18673`](https://github.com/vispar-tech/aiotrade/commit/1b1867369b48ad9b9220516b5c9cb54488c99ae8))


## v0.18.1 (2026-03-13)

### Bug Fixes

- Update RSA decryption padding method in RSAUtils
  ([`9a661f9`](https://github.com/vispar-tech/aiotrade/commit/9a661f933105468353194ff0227dda13d1791c64))


## v0.18.0 (2026-03-12)

### Features

- Integrate cryptography library for RSA operations
  ([`21dc2c1`](https://github.com/vispar-tech/aiotrade/commit/21dc2c116afb6f2c01db632a9c56c5fa35343b0b))


## v0.17.0 (2026-03-11)

### Features

- **trade**: Add get_position_info_v3 method for retrieving current position information
  ([`2218505`](https://github.com/vispar-tech/aiotrade/commit/2218505430337e3ccd096dd72f67dd72ce5b29c7))


## v0.16.3 (2026-03-10)

### Bug Fixes

- Update content type and data handling in BrokerClient
  ([`c365000`](https://github.com/vispar-tech/aiotrade/commit/c36500036881a0276da9cce2f1baf26a8b21f220))


## v0.16.2 (2026-03-10)

### Bug Fixes

- Update TOKEN_URL for OKX API endpoint
  ([`8ef7c2e`](https://github.com/vispar-tech/aiotrade/commit/8ef7c2ed32492c344eb093c2652895792a4a7a52))


## v0.16.1 (2026-03-10)

### Bug Fixes

- Downgrade pycryptodome version to 3.20.0 in dependencies
  ([`4f33560`](https://github.com/vispar-tech/aiotrade/commit/4f33560aa992400beab985b767e8689c364df8a5))


## v0.16.0 (2026-03-10)

### Features

- **clients**: :sparkles: add client_user_id parameter to BrokerClient
  ([`48c60ca`](https://github.com/vispar-tech/aiotrade/commit/48c60caf27927ea7cfbe2dbcf06a2a1c10acf494))


## v0.15.0 (2026-03-10)

### Features

- **clients**: :sparkles: integrate BrokerClient into Bitget and OKX clients
  ([`9914d56`](https://github.com/vispar-tech/aiotrade/commit/9914d56f26f417bd1af13ef6152947278378e9c7))


## v0.14.2 (2026-03-09)

### Bug Fixes

- **clients**: :bug: ensure proper handling of response codes in BinanceHttpClient
  ([`6e59328`](https://github.com/vispar-tech/aiotrade/commit/6e5932830f1a721e3df2eb0830c41fd92755b9bb))


## v0.14.1 (2026-03-07)

### Bug Fixes

- **clients**: :wrench: enhance OKX client with new broker tag parameter
  ([`0bbfa62`](https://github.com/vispar-tech/aiotrade/commit/0bbfa62b8f6fa11aaa133a456c89e536c5c6615f))


## v0.14.0 (2026-03-07)

### Features

- **clients**: :sparkles: enhance Binance and Bitget clients with new parameters
  ([`7f1ecb6`](https://github.com/vispar-tech/aiotrade/commit/7f1ecb6b3d73966a4152fd6d5258f3df40331a24))


## v0.13.0 (2026-03-07)

### Features

- **clients**: :sparkles: update logging and add new methods across exchange clients
  ([`119ed0f`](https://github.com/vispar-tech/aiotrade/commit/119ed0f3473e2e58577f07920d71d822689a008f))


## v0.12.0 (2026-02-27)

### Features

- **bybit**: :sparkles: integrate BrokerClient into BybitClient
  ([`84e8c36`](https://github.com/vispar-tech/aiotrade/commit/84e8c360d0617d8b298fa8201630e0218006230d))


## v0.11.0 (2026-02-27)

### Features

- **binance**: :sparkles: add Binance exchange client support
  ([`e9c15a1`](https://github.com/vispar-tech/aiotrade/commit/e9c15a1537bd75d2946d5e64705abd79b0d7ccb2))


## v0.10.0 (2026-02-23)

### Features

- **bitget**: :sparkles: add Bitget exchange client support
  ([`9728dcc`](https://github.com/vispar-tech/aiotrade/commit/9728dcc2abd212d71cd885dad29d2b8d35d33069))


## v0.9.0 (2026-02-23)

### Features

- **okx**: :sparkles: add OKX exchange client support
  ([`f0024d3`](https://github.com/vispar-tech/aiotrade/commit/f0024d350265d4c84534be077a92bec5e91d1ead))


## v0.8.0 (2026-02-19)

### Features

- **clients**: :sparkles: integrate helper classes into BingX and Bybit clients
  ([`bc420ba`](https://github.com/vispar-tech/aiotrade/commit/bc420ba118b8705a612986a540ea7ac76288c7f7))


## v0.7.1 (2026-02-17)

### Bug Fixes

- **errors**: :wrench: improve string representation of ExchangeResponseError
  ([`02f9f8a`](https://github.com/vispar-tech/aiotrade/commit/02f9f8a336d329fa9726375906e8dce709b2f56a))


## v0.7.0 (2026-02-17)

### Features

- **docs**: :sparkles: update README and method names for clarity
  ([`61344d6`](https://github.com/vispar-tech/aiotrade/commit/61344d646e22993f229d61973e785810883578d6))


## v0.6.0 (2026-02-17)

### Bug Fixes

- **trade**: :wrench: update get_swap_position_history method parameters
  ([`dc62c61`](https://github.com/vispar-tech/aiotrade/commit/dc62c614c1065528a6486293564dd7732e427a19))

### Features

- **http**: :sparkles: add decode_str method for URL decoding
  ([`0120a8e`](https://github.com/vispar-tech/aiotrade/commit/0120a8ee525408c63e7e34e45b4ca8e32eadb38b))


## v0.5.0 (2026-02-17)

### Features

- **bingx**: :sparkles: add get_account_uid method to SubMixin
  ([`3c4f9fd`](https://github.com/vispar-tech/aiotrade/commit/3c4f9fdf3adf2a69e7f6f69a2739daf7e456d1b9))

- **clients**: :sparkles: add copy trading and risk limit APIs
  ([`0f34d70`](https://github.com/vispar-tech/aiotrade/commit/0f34d70c142022ed6933921e19a89ee3dbb3008c))


## v0.4.1 (2026-02-16)

### Bug Fixes

- **bingx**: :wrench: improve error handling for API response in BingxHttpClient
  ([`5d8d848`](https://github.com/vispar-tech/aiotrade/commit/5d8d8487d3b7b06021f401361da4d684679c9c80))


## v0.4.0 (2026-02-15)

### Features

- **bybit**: :sparkles: add UserMixin with API key info endpoint
  ([`de6d84d`](https://github.com/vispar-tech/aiotrade/commit/de6d84d8f8d6723fd1136cddb65981f070817f42))


## v0.3.2 (2026-02-07)

### Bug Fixes

- **bybit**: :wrench: add order_filter to field mapping in TradeMixin
  ([`15243c1`](https://github.com/vispar-tech/aiotrade/commit/15243c1f39db356a08f353063daaaf05157a0957))


## v0.3.1 (2026-02-07)

### Bug Fixes

- **bingx**: :wrench: update method names and enhance order parameters
  ([`d9516c0`](https://github.com/vispar-tech/aiotrade/commit/d9516c06fbcdc45734d3a270348ebb5c908c94e8))


## v0.3.0 (2026-02-07)

### Features

- **bingx**: :sparkles: add place_spot_order method and update payload preparation logic
  ([`0adf3c1`](https://github.com/vispar-tech/aiotrade/commit/0adf3c1a98e891631d97212a2a5322819c499580))


## v0.2.1 (2026-02-02)

### Bug Fixes

- **dependencies**: :wrench: update Python version constraints in pyproject.toml and poetry.lock to
  support Python 4.0
  ([`22060ee`](https://github.com/vispar-tech/aiotrade/commit/22060ee989ae43d1de09a321c300f13777b1f275))


## v0.2.0 (2026-02-01)

### Features

- **bybit**: :sparkles: add account API methods and transaction log types
  ([`b16e5b2`](https://github.com/vispar-tech/aiotrade/commit/b16e5b261c8375e4ef4f4b4d9b26dddbbfd6d132))


## v0.1.0 (2026-01-29)

- Initial Release
