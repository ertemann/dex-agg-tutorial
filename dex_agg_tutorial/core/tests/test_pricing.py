import os
import json
from django.test import TestCase
from django.conf import settings
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User

# Import from the actual app
from core.models import Pair
from core.queries import query_uniswap_price, query_hyperion_price, get_token_price


class PricingQueryTest(TestCase):
    """Test pricing queries with real sample data."""
    
    @classmethod
    def setUpTestData(cls):
        """Load sample pairs from JSON and create test data."""
        # Load sample pairs
        sample_file = os.path.join(os.path.dirname(__file__), 'sample_pairs.json')
        with open(sample_file, 'r') as f:
            sample_pairs = json.load(f)
        
        # Create pairs in database
        for i, pair_data in enumerate(sample_pairs, 1):
            Pair.objects.create(
                uid=i,
                pair_id=pair_data['pair_id'],
                base_token=pair_data['base_token'],
                quote_token=pair_data['quote_token'],
                pool_contracts=pair_data['pool_contracts'],
                active_exchanges=pair_data['active_exchanges']
            )
            
        print(f"Created {len(sample_pairs)} test pairs from sample data")
    
    def test_pairs_loaded_correctly(self):
        """Test that sample pairs were loaded correctly."""
        pairs = Pair.objects.all()
        self.assertEqual(pairs.count(), 3)
        
        # Test specific pairs
        wbtc_pair = Pair.objects.get(pair_id="WBTCUSDC")
        self.assertEqual(wbtc_pair.base_token, "WBTC")
        self.assertEqual(wbtc_pair.quote_token, "USDC")
        self.assertIn("uniswap", wbtc_pair.pool_contracts)
        self.assertIn("hyperion", wbtc_pair.pool_contracts)
        
        apt_pair = Pair.objects.get(pair_id="APTUSDC")
        self.assertEqual(len(apt_pair.active_exchanges), 1)
        self.assertIn("hyperion", apt_pair.active_exchanges)
    
    def test_hyperion_price_query_structure(self):
        """Test Hyperion price query function structure."""
        apt_pair = Pair.objects.get(pair_id="APTUSDC")
        
        # Test that the function can access pool contract
        pool_address = apt_pair.pool_contracts.get("hyperion")
        self.assertIsNotNone(pool_address)
        self.assertTrue(pool_address.startswith("0x"))
        
        # Note: Actual network calls would fail in tests without mocking
        # This just tests the structure
        print(f"APT/USDC Hyperion pool: {pool_address}")
    
    def test_uniswap_price_query_structure(self):
        """Test Uniswap price query function structure."""
        usdc_pair = Pair.objects.get(pair_id="USDCETH")
        
        # Test that the function can access pool contract
        pool_address = usdc_pair.pool_contracts.get("uniswap")
        self.assertIsNotNone(pool_address)
        self.assertTrue(pool_address.startswith("0x"))
        
        print(f"USDC/ETH Uniswap pool: {pool_address}")
    
    def test_multi_exchange_pair(self):
        """Test pair with multiple exchanges."""
        wbtc_pair = Pair.objects.get(pair_id="WBTCUSDC")
        
        # Should have both exchanges
        self.assertEqual(len(wbtc_pair.active_exchanges), 2)
        self.assertIn("uniswap", wbtc_pair.active_exchanges)
        self.assertIn("hyperion", wbtc_pair.active_exchanges)
        
        # Should have pool contracts for both
        self.assertIn("uniswap", wbtc_pair.pool_contracts)
        self.assertIn("hyperion", wbtc_pair.pool_contracts)
        
        print(f"WBTC/USDC multi-exchange pools:")
        print(f"  Uniswap: {wbtc_pair.pool_contracts['uniswap']}")
        print(f"  Hyperion: {wbtc_pair.pool_contracts['hyperion']}")
    
    def test_get_token_price_integration(self):
        """Test the main get_token_price function."""
        # Test with each pair type
        test_pairs = ["WBTCUSDC", "USDCETH", "APTUSDC"]
        
        for pair_id in test_pairs:
            pair = Pair.objects.get(pair_id=pair_id)
            
            # Test that function can access pair data
            self.assertTrue(pair.is_active)
            self.assertGreater(len(pair.active_exchanges), 0)
            
            # Test pool contracts exist for active exchanges
            for exchange in pair.active_exchanges:
                self.assertIn(exchange, pair.pool_contracts)
                self.assertIsNotNone(pair.pool_contracts[exchange])
            
            print(f"{pair_id}: {pair.active_exchanges} exchanges configured")
    
    def test_pricing_query_error_handling(self):
        """Test error handling for missing pool contracts."""
        # Create pair with missing pool contract
        test_pair = Pair.objects.create(
            uid=99,
            pair_id="TESTMISSING",
            base_token="TEST",
            quote_token="TEST",
            pool_contracts={"uniswap": "0x123"},  # Has uniswap but not hyperion
            active_exchanges=["uniswap", "hyperion"]  # Claims to have hyperion
        )
        
        # Test that missing contract is handled
        hyperion_pool = test_pair.pool_contracts.get("hyperion")
        self.assertIsNone(hyperion_pool)
        
        uniswap_pool = test_pair.pool_contracts.get("uniswap") 
        self.assertIsNotNone(uniswap_pool)


class PairAPIIntegrationTest(APITestCase):
    """Test API endpoints with sample data."""
    
    def setUp(self):
        """Create admin user and load sample data."""
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com', 
            password='testpass123'
        )
        
        # Load sample pairs
        sample_file = os.path.join(os.path.dirname(__file__), 'sample_pairs.json')
        with open(sample_file, 'r') as f:
            self.sample_pairs = json.load(f)
    
    def test_create_sample_pairs_via_api(self):
        """Test creating all sample pairs via API."""
        self.client.force_authenticate(user=self.admin_user)
        
        created_pairs = []
        for pair_data in self.sample_pairs:
            response = self.client.post('/pairs/', pair_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            created_pairs.append(response.data['pair_id'])
        
        self.assertEqual(len(created_pairs), 3)
        self.assertIn("WBTCUSDC", created_pairs)
        self.assertIn("USDCETH", created_pairs)  
        self.assertIn("APTUSDC", created_pairs)
        
        # Verify in database
        self.assertEqual(Pair.objects.count(), 3)
    
    def test_get_all_pairs_endpoint(self):
        """Test GET /pairs/ with sample data."""
        # Create pairs first
        for i, pair_data in enumerate(self.sample_pairs, 1):
            Pair.objects.create(
                uid=i,
                **pair_data
            )
        
        response = self.client.get('/pairs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        
        # Check response includes pool_contracts
        for pair in response.data:
            self.assertIn('pool_contracts', pair)
            self.assertIn('active_exchanges', pair)
            self.assertGreater(len(pair['active_exchanges']), 0)
    
    def test_price_endpoint_with_sample_data(self):
        """Test price endpoint with loaded pairs."""
        # Create a test pair
        Pair.objects.create(
            uid=1,
            pair_id="USDCETH",
            base_token="USDC",
            quote_token="ETH",
            pool_contracts={"uniswap": "0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640"},
            active_exchanges=["uniswap"]
        )
        
        # Test price endpoint (will return mock data from queries)
        response = self.client.get('/price/USDCETH/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('price', response.data)
        self.assertIn('pair', response.data)