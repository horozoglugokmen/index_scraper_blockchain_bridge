#!/usr/bin/env python3
"""
DeFi Token Oracle System - Market Index Integration
=================================================

A sophisticated oracle system designed for Solidity smart contracts that implements
dynamic fee calculation based on real-time market index data. This component is part
of a comprehensive DeFi token ecosystem with transfer guards and compliance modules.

SMART CONTRACT INTEGRATION:
- Automatically updates smart contract fee rates via Web3
- Inverse correlation algorithm: high market index = lower fees
- Real-time blockchain transaction processing
- Compatible with ERC-20 token contracts

TECHNICAL FEATURES:
- Advanced anti-detection web scraping (Level 5)
- Market data extraction with retry mechanisms
- Dynamic fee calculation engine
- Persistent data storage (CSV/JSON)
- Scheduled automation system
- Comprehensive error handling and logging

DEFI USE CASES:
- Dynamic transaction fee adjustment
- Market volatility response mechanisms  
- Automated token economics management
- Real-time contract parameter updates

CONFIGURATION:
Set up your smart contract integration via environment variables:
    export ORACLE_PRIVATE_KEY='your_oracle_wallet_private_key'
    export TRANSFERGUARD_ADDRESS='your_deployed_contract_address'
    export RPC_URL='your_blockchain_rpc_endpoint'
    export CHAIN_ID='target_blockchain_chain_id'

EXECUTION:
    python index_oracle_main.py now    # Single update
    python index_oracle_main.py        # Scheduled mode

NOTE: This is a production-ready component of a larger DeFi token project.
Configure TARGET_URL and TARGET_ELEMENT_ID for your specific market data source.
"""

import requests
from bs4 import BeautifulSoup
import random
import time
import json
import logging
import csv
import pandas as pd
from datetime import datetime, timedelta
import pytz
import schedule
import os
from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple
import threading

# Web3 imports for blockchain integration
try:
    from web3 import Web3
    from eth_account import Account
    WEB3_AVAILABLE = True
except ImportError:
    print("WARNING: Web3 not installed. Run: pip install web3 eth-account")
    WEB3_AVAILABLE = False

# MAIN CONFIGURATION
@dataclass
class OracleConfig:
    # REPLACE WITH YOUR ACTUAL TARGET
    TARGET_URL = "https://example-financial-data.com/index"
    TARGET_ELEMENT_ID = "price-value"  # HTML element containing the index
    
    # Scheduling
    TIMEZONE = "Europe/London"
    UPDATE_HOUR = 16  # 16:01 target time
    UPDATE_MINUTE = 1
    
    # Dynamic Fee Algorithm (customize for your use case)
    INDEX_BASELINE = 1500.0  # Your index baseline value
    MIN_FEE_RATE = 10        # 0.1% (10 basis points)
    MAX_FEE_RATE = 100       # 1.0% (100 basis points)
    DEFAULT_FEE_RATE = 50    # 0.5% (50 basis points)
    
    # File paths
    CSV_FILE = "index_data.csv"
    JSON_FILE = "index_backup.json"
    LOG_FILE = "oracle.log"
    
    # Session settings
    SESSION_DURATION_HOURS = 168  # 7 days
    
    # Timing settings (human-like delays)
    MIN_DELAY = 3
    MAX_DELAY = 8
    
    # Retry settings
    MAX_RETRIES = 3
    RETRY_DELAY = 60
    
    # BLOCKCHAIN CONFIGURATION (from environment variables)
    RPC_URL = os.getenv('RPC_URL', 'https://eth-sepolia.g.alchemy.com/v2/YOUR_API_KEY')
    PRIVATE_KEY = os.getenv('ORACLE_PRIVATE_KEY', '')
    CONTRACT_ADDRESS = os.getenv('TRANSFERGUARD_ADDRESS', '')
    CHAIN_ID = int(os.getenv('CHAIN_ID', '11155111'))  # Sepolia testnet
    
    # Blockchain settings
    GAS_LIMIT = 200000
    MAX_GAS_PRICE_GWEI = 50
    BLOCKCHAIN_RETRY_COUNT = 3
    BLOCKCHAIN_RETRY_DELAY = 30

# BLOCKCHAIN BRIDGE CLASS
class BlockchainBridge:
    """Connects oracle to blockchain for automatic contract updates"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.enabled = False
        self.w3 = None
        self.contract = None
        self.account = None
        
        if not WEB3_AVAILABLE:
            self.logger.warning("Web3 not available - blockchain updates disabled")
            return
            
        self._initialize_web3()
    
    def _initialize_web3(self):
        """Initialize Web3 connection"""
        try:
            # Check required parameters
            if not OracleConfig.RPC_URL or 'YOUR_API_KEY' in OracleConfig.RPC_URL:
                self.logger.warning("RPC_URL not configured - set RPC_URL environment variable")
                return
                
            if not OracleConfig.PRIVATE_KEY:
                self.logger.warning("ORACLE_PRIVATE_KEY not configured - blockchain updates disabled")
                return
                
            if not OracleConfig.CONTRACT_ADDRESS:
                self.logger.warning("TRANSFERGUARD_ADDRESS not configured - blockchain updates disabled")
                return
            
            # Setup Web3 connection
            self.w3 = Web3(Web3.HTTPProvider(OracleConfig.RPC_URL))
            
            if not self.w3.is_connected():
                self.logger.error("Cannot connect to blockchain RPC")
                return
            
            # Load account
            self.account = Account.from_key(OracleConfig.PRIVATE_KEY)
            
            # Contract ABI (update function signature)
            contract_abi = [
                {
                    "inputs": [
                        {"internalType": "uint256", "name": "newFeeRate", "type": "uint256"},
                        {"internalType": "uint256", "name": "indexValue", "type": "uint256"}
                    ],
                    "name": "updateDynamicFeeRate",
                    "outputs": [],
                    "stateMutability": "nonpayable",
                    "type": "function"
                }
            ]
            
            # Contract instance
            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(OracleConfig.CONTRACT_ADDRESS),
                abi=contract_abi
            )
            
            self.enabled = True
            self.logger.info(f"Blockchain bridge initialized")
            self.logger.info(f"   Oracle Address: {self.account.address}")
            self.logger.info(f"   Contract: {OracleConfig.CONTRACT_ADDRESS}")
            self.logger.info(f"   Network: Chain ID {OracleConfig.CHAIN_ID}")
            
        except Exception as e:
            self.logger.error(f"Blockchain bridge initialization failed: {e}")
            self.enabled = False
    
    def send_fee_update(self, fee_rate: int, index_value: float) -> Optional[str]:
        """
        Send fee update to smart contract
        
        Args:
            fee_rate: Fee rate in basis points (10-100)
            index_value: Index value for reference
            
        Returns:
            Transaction hash or None if failed
        """
        if not self.enabled:
            self.logger.warning("Blockchain bridge not enabled - skipping contract update")
            return None
        
        for attempt in range(OracleConfig.BLOCKCHAIN_RETRY_COUNT):
            try:
                self.logger.info(f"Sending fee update to blockchain (attempt {attempt + 1})")
                
                # Convert index value to integer (contract expects uint256)
                index_value_int = int(index_value)
                
                # Check gas price
                gas_price = self.w3.eth.gas_price
                max_gas_price = self.w3.to_wei(OracleConfig.MAX_GAS_PRICE_GWEI, 'gwei')
                
                if gas_price > max_gas_price:
                    self.logger.warning(f"Gas price too high: {self.w3.from_wei(gas_price, 'gwei')} Gwei > {OracleConfig.MAX_GAS_PRICE_GWEI} Gwei")
                
                # Build transaction
                transaction = self.contract.functions.updateDynamicFeeRate(
                    fee_rate,
                    index_value_int
                ).build_transaction({
                    'from': self.account.address,
                    'gas': OracleConfig.GAS_LIMIT,
                    'gasPrice': min(gas_price, max_gas_price),
                    'nonce': self.w3.eth.get_transaction_count(self.account.address),
                    'chainId': OracleConfig.CHAIN_ID
                })
                
                # Sign transaction
                signed_txn = self.w3.eth.account.sign_transaction(transaction, OracleConfig.PRIVATE_KEY)
                
                # Send to blockchain
                tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                tx_hash_hex = tx_hash.hex()
                
                self.logger.info(f"Transaction sent: {tx_hash_hex}")
                
                # Wait for receipt (optional)
                try:
                    receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                    if receipt.status == 1:
                        self.logger.info(f"Transaction confirmed in block {receipt.blockNumber}")
                        self.logger.info(f"   Gas used: {receipt.gasUsed:,}")
                        return tx_hash_hex
                    else:
                        self.logger.error(f"Transaction failed: {tx_hash_hex}")
                        return None
                        
                except Exception as receipt_error:
                    self.logger.warning(f"Could not get receipt: {receipt_error}")
                    return tx_hash_hex
                
            except Exception as e:
                self.logger.error(f"Blockchain update attempt {attempt + 1} failed: {e}")
                
                if attempt < OracleConfig.BLOCKCHAIN_RETRY_COUNT - 1:
                    self.logger.info(f"Waiting {OracleConfig.BLOCKCHAIN_RETRY_DELAY}s before retry...")
                    time.sleep(OracleConfig.BLOCKCHAIN_RETRY_DELAY)
        
        self.logger.error("All blockchain update attempts failed")
        return None

# DYNAMIC FEE CALCULATOR
class DynamicFeeCalculator:
    """Calculates dynamic fees based on index values (inverse correlation)"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def calculate_fee_rate(self, index_value: float) -> int:
        """
        Calculate dynamic fee rate from index value (INVERSE CORRELATION)
        
        Logic: High Index → Low Fee (good market conditions)
               Low Index → High Fee (bad market conditions)
        
        Args:
            index_value: Market index value
            
        Returns:
            Fee rate in basis points (10-100)
        """
        try:
            baseline = OracleConfig.INDEX_BASELINE
            min_fee = OracleConfig.MIN_FEE_RATE
            max_fee = OracleConfig.MAX_FEE_RATE
            
            # Input validation
            if index_value <= 0:
                self.logger.warning(f"Invalid index: {index_value}, using default")
                return OracleConfig.DEFAULT_FEE_RATE
            
            # Extreme value protection
            if index_value >= baseline * 2:  # Very high index
                self.logger.info(f"Index extremely high: {index_value} -> MIN fee")
                return min_fee
            
            if index_value <= baseline * 0.33:  # Very low index
                self.logger.info(f"Index extremely low: {index_value} -> MAX fee")
                return max_fee
            
            # Linear inverse correlation
            # Index 500 → Fee 1.0% (100 bp)
            # Index 1500 → Fee 0.5% (50 bp)
            # Index 3000 → Fee 0.1% (10 bp)
            
            lower_bound = baseline * 0.33
            upper_bound = baseline * 2
            
            fee_rate = max_fee - (index_value - lower_bound) * (max_fee - min_fee) / (upper_bound - lower_bound)
            
            # Enforce boundaries
            fee_rate = max(min_fee, min(max_fee, fee_rate))
            fee_rate_int = int(round(fee_rate))
            
            # Double check boundaries (paranoid mode)
            if fee_rate_int < min_fee:
                fee_rate_int = min_fee
            if fee_rate_int > max_fee:
                fee_rate_int = max_fee
            
            return fee_rate_int
            
        except Exception as e:
            self.logger.error(f"Fee calculation error: {e}")
            return OracleConfig.DEFAULT_FEE_RATE
    
    def get_fee_explanation(self, index_value: float, fee_rate: int) -> str:
        """Generate human-readable fee explanation"""
        baseline = OracleConfig.INDEX_BASELINE
        
        if index_value >= baseline:
            if index_value >= baseline * 1.5:
                trend = "INDEX VERY HIGH -> Market excellent -> Min fee"
            else:
                trend = "INDEX HIGH -> Market good -> Low fee"
        else:
            if index_value <= baseline * 0.5:
                trend = "INDEX VERY LOW -> Market stressed -> Max fee"
            else:
                trend = "INDEX LOW -> Market weak -> High fee"
        
        return f"{trend} | Index: {index_value} | Fee: {fee_rate/100:.2f}% ({fee_rate} bp)"

# LEVEL 5 ANTI-DETECTION SYSTEM
class Level5AntiDetection:
    """Advanced anti-detection with browser rotation and behavioral simulation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Browser combinations with realistic market share weights
        self.browser_combinations = {
            'chrome_windows': {
                'weight': 45,
                'agents': [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
                ],
                'headers': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
            },
            'safari_mac': {
                'weight': 25,
                'agents': [
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
                ],
                'headers': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive'
                }
            },
            'firefox_windows': {
                'weight': 20,
                'agents': [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
                ],
                'headers': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive'
                }
            },
            'edge_windows': {
                'weight': 10,
                'agents': [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
                ],
                'headers': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive'
                }
            }
        }
        
        # Session management
        self.current_session = None
        self.session_start_time = None
        self.session_duration = timedelta(hours=OracleConfig.SESSION_DURATION_HOURS)
        
    def get_session(self) -> requests.Session:
        """Get or create session with behavioral simulation"""
        now = datetime.now()
        
        if (self.current_session is None or 
            self.session_start_time is None or 
            now - self.session_start_time > self.session_duration):
            
            self.logger.info("Creating new browser session...")
            self._create_new_session()
            
        return self.current_session
    
    def _create_new_session(self):
        """Create new session with randomized browser characteristics"""
        browser_combo = self._select_browser_combination()
        
        self.current_session = requests.Session()
        
        user_agent = random.choice(browser_combo['agents'])
        headers = browser_combo['headers'].copy()
        headers['User-Agent'] = user_agent
        
        self.current_session.headers.update(headers)
        self.session_start_time = datetime.now()
        
        self.logger.info(f"New session: {user_agent[:50]}...")
        
    def _select_browser_combination(self) -> Dict[str, Any]:
        """Select browser based on market share weights"""
        weighted_choices = []
        for combo_name, combo_data in self.browser_combinations.items():
            weighted_choices.extend([combo_name] * combo_data['weight'])
        
        selected_combo = random.choice(weighted_choices)
        return self.browser_combinations[selected_combo]
    
    def human_delay(self):
        """Simulate human-like delay between requests"""
        delay = random.uniform(OracleConfig.MIN_DELAY, OracleConfig.MAX_DELAY)
        self.logger.info(f"Human delay: {delay:.2f} seconds")
        time.sleep(delay)

# INDEX DATA EXTRACTOR
class IndexExtractor:
    """Main data extraction class with retry mechanism"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.anti_detection = Level5AntiDetection()
        
    def extract_index_with_retry(self) -> Optional[Tuple[float, str]]:
        """Extract index value with retry mechanism"""
        for attempt in range(OracleConfig.MAX_RETRIES):
            try:
                self.logger.info(f"Index extraction attempt {attempt + 1}/{OracleConfig.MAX_RETRIES}")
                
                # Apply human-like delay
                self.anti_detection.human_delay()
                
                # Get session with anti-detection
                session = self.anti_detection.get_session()
                
                # Make request
                self.logger.info(f"Requesting: {OracleConfig.TARGET_URL}")
                response = session.get(OracleConfig.TARGET_URL, timeout=30)
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                index_element = soup.find('td', id=OracleConfig.TARGET_ELEMENT_ID)
                
                if not index_element:
                    raise Exception(f"Index element not found: id='{OracleConfig.TARGET_ELEMENT_ID}'")
                
                # Extract and clean value
                index_text = index_element.get_text().strip()
                self.logger.info(f"Raw index text: '{index_text}'")
                
                # Clean and convert
                index_clean = index_text.replace(',', '').replace(' ', '')
                index_value = float(index_clean)
                
                self.logger.info(f"Index extracted: {index_value}")
                return index_value, index_text
                
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed: {e}")
                
                if attempt < OracleConfig.MAX_RETRIES - 1:
                    self.logger.info(f"Waiting {OracleConfig.RETRY_DELAY} seconds before retry...")
                    time.sleep(OracleConfig.RETRY_DELAY)
        
        self.logger.error("All index extraction attempts failed")
        return None

# DATA STORAGE MANAGER
class DataStorageManager:
    """Handles data storage in CSV and JSON formats"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.csv_file = OracleConfig.CSV_FILE
        self.json_file = OracleConfig.JSON_FILE
        
        # Initialize CSV if not exists
        self._initialize_csv()
    
    def _initialize_csv(self):
        """Initialize CSV file with headers"""
        if not os.path.exists(self.csv_file):
            headers = [
                'timestamp', 'index_value', 'index_text', 'fee_rate_bp', 'fee_rate_percent',
                'fee_explanation', 'extraction_method', 'session_age_minutes',
                'blockchain_tx_hash', 'blockchain_status'
            ]
            
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            
            self.logger.info(f"CSV file initialized: {self.csv_file}")
    
    def save_oracle_data(self, data_record: Dict[str, Any]):
        """Save oracle data to both CSV and JSON"""
        try:
            # Save to CSV
            self._save_to_csv(data_record)
            
            # Save to JSON backup
            self._save_to_json(data_record)
            
            self.logger.info("Oracle data saved successfully")
            
        except Exception as e:
            self.logger.error(f"Data save error: {e}")
    
    def _save_to_csv(self, data_record: Dict[str, Any]):
        """Append data to CSV file"""
        with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            row = [
                data_record['timestamp'],
                data_record['index_value'],
                data_record['index_text'],
                data_record['fee_rate_bp'],
                data_record['fee_rate_percent'],
                data_record['fee_explanation'],
                data_record['extraction_method'],
                data_record['session_age_minutes'],
                data_record.get('blockchain_tx_hash', ''),
                data_record.get('blockchain_status', '')
            ]
            writer.writerow(row)
    
    def _save_to_json(self, data_record: Dict[str, Any]):
        """Save to JSON backup file"""
        json_data = []
        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
            except:
                json_data = []
        
        json_data.append(data_record)
        
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    def get_latest_data(self, limit: int = 10) -> pd.DataFrame:
        """Get latest data from CSV"""
        try:
            if os.path.exists(self.csv_file):
                df = pd.read_csv(self.csv_file)
                return df.tail(limit)
            return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Error reading CSV: {e}")
            return pd.DataFrame()

# MAIN ORACLE SYSTEM
class IndexOracleSystem:
    """Main oracle system with blockchain integration"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.extractor = IndexExtractor()
        self.fee_calculator = DynamicFeeCalculator()
        self.storage = DataStorageManager()
        self.blockchain_bridge = BlockchainBridge()
        self.running = False
        
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(OracleConfig.LOG_FILE),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def run_oracle_update(self):
        """Main oracle update process with blockchain integration"""
        self.logger.info("=== INDEX ORACLE UPDATE STARTED ===")
        
        try:
            # 1. Extract index data
            result = self.extractor.extract_index_with_retry()
            if not result:
                self.logger.error("Index extraction failed completely")
                return False
            
            index_value, index_text = result
            
            # 2. Calculate dynamic fee
            fee_rate = self.fee_calculator.calculate_fee_rate(index_value)
            fee_explanation = self.fee_calculator.get_fee_explanation(index_value, fee_rate)
            
            # 3. Display results
            print("\n" + "="*60)
            print("INDEX ORACLE RESULTS")
            print("="*60)
            print(f"Index Value: {index_value} ('{index_text}')")
            print(f"Calculated Fee: {fee_rate/100:.2f}% ({fee_rate} basis points)")
            print(f"Explanation: {fee_explanation}")
            print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 4. Send to blockchain
            blockchain_tx_hash = None
            blockchain_status = "disabled"
            
            if self.blockchain_bridge.enabled:
                print(f"Sending to blockchain...")
                blockchain_tx_hash = self.blockchain_bridge.send_fee_update(fee_rate, index_value)
                
                if blockchain_tx_hash:
                    blockchain_status = "success"
                    print(f"Blockchain updated: {blockchain_tx_hash}")
                else:
                    blockchain_status = "failed"
                    print(f"Blockchain update failed")
            else:
                print(f"Blockchain integration disabled")
            
            print("="*60)
            
            # 5. Calculate session age
            session_age = 0.0
            if self.extractor.anti_detection.session_start_time:
                delta = datetime.now() - self.extractor.anti_detection.session_start_time
                session_age = delta.total_seconds() / 60
            
            # 6. Save data
            data_record = {
                'timestamp': datetime.now().isoformat(),
                'index_value': index_value,
                'index_text': index_text,
                'fee_rate_bp': fee_rate,
                'fee_rate_percent': fee_rate / 100,
                'fee_explanation': fee_explanation,
                'extraction_method': 'Level5_Oracle_Production_Blockchain',
                'session_age_minutes': session_age,
                'blockchain_tx_hash': blockchain_tx_hash or '',
                'blockchain_status': blockchain_status
            }
            
            self.storage.save_oracle_data(data_record)
            
            # 7. Show recent history
            latest_df = self.storage.get_latest_data(5)
            if not latest_df.empty:
                print(f"\nLast 5 Records:")
                display_columns = ['timestamp', 'index_value', 'fee_rate_percent']
                if 'blockchain_status' in latest_df.columns:
                    display_columns.append('blockchain_status')
                
                display_df = latest_df[display_columns].copy()
                display_df['timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%m-%d %H:%M')
                display_df['fee_rate_percent'] = display_df['fee_rate_percent'].apply(lambda x: f"{x:.2f}%")
                print(display_df.to_string(index=False))
            
            self.logger.info("Oracle update completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Oracle update error: {e}")
            print(f"\nERROR: {e}")
            return False
    
    def start_daily_scheduler(self):
        """Start daily scheduled updates"""
        target_tz = pytz.timezone(OracleConfig.TIMEZONE)
        
        self.logger.info("Starting Index Oracle System...")
        self.logger.info(f"Daily update: {OracleConfig.UPDATE_HOUR:02d}:{OracleConfig.UPDATE_MINUTE:02d} {OracleConfig.TIMEZONE}")
        
        if self.blockchain_bridge.enabled:
            self.logger.info("Blockchain integration: ENABLED")
        else:
            self.logger.info("Blockchain integration: DISABLED")
        
        # Schedule daily update
        schedule.every().day.at(f"{OracleConfig.UPDATE_HOUR:02d}:{OracleConfig.UPDATE_MINUTE:02d}").do(
            self.run_oracle_update
        )
        
        self.running = True
        self.logger.info("Daily scheduler started! Press Ctrl+C to stop.")
        
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            self.logger.info("Oracle system stopped by user")
            self.running = False
    
    def stop(self):
        """Stop the oracle system"""
        self.running = False

# MAIN EXECUTION
if __name__ == "__main__":
    print("Advanced Index Oracle System - Production Ready")
    print("=" * 80)
    print(f"Target: {OracleConfig.TARGET_URL}")
    print(f"Update Time: {OracleConfig.UPDATE_HOUR:02d}:{OracleConfig.UPDATE_MINUTE:02d} {OracleConfig.TIMEZONE}")
    print(f"Fee Range: {OracleConfig.MIN_FEE_RATE/100:.1f}% - {OracleConfig.MAX_FEE_RATE/100:.1f}%")
    print(f"CSV Output: {OracleConfig.CSV_FILE}")
    print(f"JSON Backup: {OracleConfig.JSON_FILE}")
    
    # Blockchain configuration status
    if WEB3_AVAILABLE:
        print(f"Blockchain: Web3 available")
        if OracleConfig.CONTRACT_ADDRESS and OracleConfig.PRIVATE_KEY:
            print(f"Contract: {OracleConfig.CONTRACT_ADDRESS}")
            print(f"Network: Chain ID {OracleConfig.CHAIN_ID}")
        else:
            print(f"Blockchain: Not configured (set environment variables)")
    else:
        print(f"Blockchain: Web3 not installed")
    
    print("=" * 80)
    
    # Environment check
    if not WEB3_AVAILABLE:
        print("\nTo enable blockchain integration:")
        print("   pip install web3 eth-account")
    
    if not OracleConfig.PRIVATE_KEY:
        print("\nTo enable blockchain updates, set environment variables:")
        print("   export ORACLE_PRIVATE_KEY='your_oracle_wallet_private_key'")
        print("   export TRANSFERGUARD_ADDRESS='deployed_contract_address'")
        print("   export RPC_URL='https://your-rpc-endpoint'")
    
    print("\nUsage:")
    print("   python index_oracle_main.py now    # Single update")
    print("   python index_oracle_main.py        # Daily scheduler")
    
    print("\nCONFIGURATION REQUIRED:")
    print("   1. Replace TARGET_URL with your actual data source")
    print("   2. Update TARGET_ELEMENT_ID with correct HTML selector")
    print("   3. Set environment variables for blockchain integration")
    print("   4. Test thoroughly before production use")
    
    # Create oracle
    oracle = IndexOracleSystem()
    
    # Check command line arguments
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "now":
        print("Running single oracle update NOW...")
        oracle.run_oracle_update()
    else:
        print("Starting daily scheduler...")
        oracle.start_daily_scheduler() 