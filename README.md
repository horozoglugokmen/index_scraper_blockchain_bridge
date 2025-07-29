# DeFi Token Oracle System with Blockchain Bridge

A sophisticated oracle system designed for DeFi applications that implements dynamic fee calculation based on real-time market index data with advanced web scraping and blockchain integration capabilities.

## Overview

This project combines advanced web scraping techniques with blockchain oracle functionality to create a production-ready DeFi token ecosystem. The system automatically adjusts smart contract parameters based on real-time market data using inverse correlation algorithms.

## Key Features

### Oracle System
- **Level 5 Anti-Detection**: Advanced browser rotation, behavioral simulation, and timing mechanisms
- **Dynamic Fee Calculation**: Inverse correlation algorithm (high market index = lower fees)
- **Real-time Data Processing**: Automated market data extraction with retry mechanisms
- **Persistent Storage**: CSV/JSON data logging with comprehensive analytics

### Blockchain Integration
- **Smart Contract Automation**: Direct Web3 integration for contract parameter updates
- **Multi-chain Support**: Compatible with EVM-based networks (Ethereum, Polygon, BSC, etc.)
- **Gas Optimization**: Intelligent gas price management and transaction handling
- **Error Recovery**: Circuit breaker patterns and fallback mechanisms

### DeFi Components
- **Token Contracts**: ERC-20 compliant with advanced security features
- **Transfer Guards**: Modular security architecture with compliance checks
- **Vesting Module**: Token distribution and vesting management
- **Compliance System**: Blacklist management and regulatory compliance

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Scraper   │───▶│  Oracle System   │───▶│ Smart Contracts │
│                 │    │                  │    │                 │
│ • Anti-Detection│    │ • Fee Calculator │    │ • Token Logic   │
│ • Data Extraction│    │ • Blockchain Bridge│  │ • Transfer Guards│
│ • Retry Logic   │    │ • Error Handling │    │ • Compliance    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Storage  │    │   Scheduling     │    │   Monitoring    │
│                 │    │                  │    │                 │
│ • CSV/JSON Logs │    │ • Daily Updates  │    │ • Transaction   │
│ • Analytics     │    │ • Time Zones     │    │   Tracking      │
│ • Backup System │    │ • Automation     │    │ • Error Alerts  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Technology Stack

### Backend
- **Python 3.8+**: Core oracle system
- **Web3.py**: Blockchain interaction
- **BeautifulSoup4**: HTML parsing and data extraction
- **Requests**: HTTP client with session management
- **Pandas**: Data processing and analytics

### Blockchain
- **Solidity 0.8+**: Smart contract development
- **Hardhat**: Development framework
- **OpenZeppelin**: Security libraries and upgradeable contracts
- **UUPS Proxy**: Upgradeable smart contract pattern

### Infrastructure
- **Environment Variables**: Secure configuration management
- **CSV/JSON**: Data persistence and backup
- **Logging**: Comprehensive error tracking and monitoring

## Installation

### Prerequisites
```bash
# Python dependencies
pip install -r requirements.txt

# Node.js dependencies (for smart contracts)
npm install
```

### Environment Setup
```bash
# Copy environment template
cp env.example .env

# Configure your environment variables
export ORACLE_PRIVATE_KEY='your_oracle_wallet_private_key'
export TRANSFERGUARD_ADDRESS='deployed_contract_address'
export RPC_URL='https://your-rpc-endpoint'
export CHAIN_ID='target_blockchain_chain_id'
```

## Usage

### Oracle System

#### Single Update
```bash
python scraping/index_data_scraper.py now
```

#### Scheduled Mode (Daily Updates)
```bash
python scraping/index_data_scraper.py
```

### Configuration

#### Oracle Parameters
```python
# Configure in scraping/index_data_scraper.py
TARGET_URL = "https://your-financial-data-source.com/index"
TARGET_ELEMENT_ID = "price-value"  # HTML element containing the index

# Fee calculation parameters
INDEX_BASELINE = 1500.0  # Your index baseline value
MIN_FEE_RATE = 10        # 0.1% (10 basis points)
MAX_FEE_RATE = 100       # 1.0% (100 basis points)
```

#### Scheduling
```python
TIMEZONE = "Europe/London"
UPDATE_HOUR = 16  # 16:01 daily update
UPDATE_MINUTE = 1
```

## Smart Contracts

### Contract Architecture
- **AABToken**: Main ERC-20 token with dynamic fees
- **TransferGuard**: Security and fee calculation module
- **ComplianceModule**: Regulatory compliance and blacklist management
- **VestingModule**: Token distribution and vesting logic

### Deployment
```bash
# Compile contracts
npx hardhat compile

# Deploy to testnet
npx hardhat run scripts/deploy.js --network sepolia

# Deploy to mainnet
npx hardhat run scripts/deploy.js --network mainnet
```

## Dynamic Fee Algorithm

The system implements an **inverse correlation** algorithm:

```
High Market Index → Low Transaction Fees (Good market conditions)
Low Market Index  → High Transaction Fees (Stressed market conditions)
```

### Algorithm Logic
1. **Data Extraction**: Real-time market index scraping
2. **Calculation**: Linear inverse correlation within min/max bounds
3. **Validation**: Boundary checks and error handling
4. **Execution**: Automatic smart contract parameter updates

### Example
- Index 3000 → Fee 0.1% (Excellent market)
- Index 1500 → Fee 0.5% (Normal market)  
- Index 500  → Fee 1.0% (Stressed market)

## Security Features

### Web Scraping Security
- **Browser Rotation**: Multiple user agents with realistic market share weights
- **Behavioral Simulation**: Human-like delays and session management
- **Request Randomization**: Timing variations and header rotation
- **Error Recovery**: Comprehensive retry mechanisms

### Blockchain Security
- **Private Key Management**: Environment variable configuration
- **Gas Price Protection**: Maximum gas price limits
- **Transaction Validation**: Receipt confirmation and error handling
- **Circuit Breaker**: Automatic failsafe mechanisms

### Smart Contract Security
- **Upgradeability**: UUPS proxy pattern for safe upgrades
- **Access Control**: Role-based permissions and ownership
- **Reentrancy Protection**: OpenZeppelin security guards
- **Emergency Controls**: Circuit breakers and pause functionality

## Monitoring and Analytics

### Data Tracking
- **CSV Output**: Structured data with timestamps and calculations
- **JSON Backup**: Complete data preservation with metadata
- **Error Logging**: Comprehensive error tracking and debugging

### Metrics
- Transaction success rates
- Fee calculation accuracy
- Blockchain interaction statistics
- System uptime and reliability

## API Integration

### Supported Data Sources
The system is designed to work with various financial data providers:
- Custom HTML element targeting
- Configurable URL endpoints
- Flexible data parsing logic

### Blockchain Networks
- **Ethereum Mainnet**
- **Polygon**
- **Binance Smart Chain**
- **Arbitrum**
- **Optimism**
- **Testnets**: Sepolia, Mumbai, etc.

## Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Install dependencies
4. Configure test environment
5. Run tests and validations

### Code Standards
- Follow Python PEP 8 style guide
- Implement comprehensive error handling
- Add logging for debugging purposes
- Write clear documentation

## Production Deployment

### Checklist
- [ ] Configure real data source URLs
- [ ] Set up production environment variables
- [ ] Deploy smart contracts to mainnet
- [ ] Test oracle functionality thoroughly
- [ ] Set up monitoring and alerting
- [ ] Implement backup and recovery procedures

### Scaling Considerations
- Load balancing for high-frequency updates
- Database integration for large-scale data storage
- API rate limiting and caching
- Distributed oracle network setup

## License

MIT License - see LICENSE file for details

## Disclaimer

This software is provided for educational and development purposes. Use in production environments requires thorough testing and security audits. The developers are not responsible for any financial losses or security breaches resulting from the use of this software.

## Support

For technical support and questions:
- Create an issue in the repository
- Review the documentation thoroughly
- Check the logs for debugging information

---

**Note**: This is a sanitized version for public repository. Actual production deployment requires configuration of real data sources and blockchain endpoints. 