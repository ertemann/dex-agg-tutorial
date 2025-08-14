import os
import json
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User

from core.models import Pair
from core.queries import get_token_price


class PairAPITest(APITestCase):
    """Test API with real sample data."""
    
    def setUp(self):
        """Load sample pairs and create admin."""
        self.admin = User.objects.create_superuser(
            username='admin',
            password='testpass'
        )
        
        # Load sample pairs from JSON
        sample_file = os.path.join(os.path.dirname(__file__), 'sample_pairs.json')
        with open(sample_file, 'r') as f:
            self.sample_pairs = json.load(f)
        
        # Create pairs in database
        for i, pair_data in enumerate(self.sample_pairs, 1):
            Pair.objects.create(uid=i, **pair_data)
    
    def test_list_pairs(self):
        """Test GET /pairs/ returns all sample pairs."""
        response = self.client.get('/pairs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(self.sample_pairs))
        
        # Check that all our sample pairs are present
        pair_ids = [pair['pair_id'] for pair in response.data]
        expected_ids = [pair['pair_id'] for pair in self.sample_pairs]
        for expected_id in expected_ids:
            self.assertIn(expected_id, pair_ids)
    
    def test_create_pair_via_api(self):
        """Test creating a new pair via POST /pairs/."""
        self.client.force_authenticate(user=self.admin)
        
        new_pair = {
            "pair_id": "LINKUSDC",
            "base_token": "LINK", 
            "quote_token": "USDC",
            "base_token_decimals": 18,
            "quote_token_decimals": 6,
            "active_exchanges": ["uniswap"],
            "pool_contracts": {"uniswap": "0x1234567890abcdef"}
        }
        
        response = self.client.post('/pairs/', new_pair, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("Created pair LINKUSDC", response.data['message'])
        
        # Verify the pair was actually created by querying the API
        get_response = self.client.get('/pairs/')
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        
        # Check that LINKUSDC is now in the list
        pair_ids = [pair['pair_id'] for pair in get_response.data]
        self.assertIn("LINKUSDC", pair_ids)
        
        # Find the created pair and verify its attributes
        created_pair = next((p for p in get_response.data if p['pair_id'] == 'LINKUSDC'), None)
        self.assertIsNotNone(created_pair)
        self.assertEqual(created_pair['base_token'], 'LINK')
        self.assertEqual(created_pair['quote_token'], 'USDC')
        self.assertEqual(created_pair['base_token_decimals'], 18)
        self.assertEqual(created_pair['quote_token_decimals'], 6)
    
    def test_price_endpoint_structure(self):
        """Test that price endpoints return correct structure."""
        for sample_pair in self.sample_pairs:
            pair_id = sample_pair['pair_id']
            response = self.client.get(f'/price/{pair_id}/')
            
            # Should return 200 and have correct structure
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('token_pair', response.data)
            self.assertEqual(response.data['token_pair'], pair_id)
            
            # If we got actual prices (not an error), verify best_price logic
            if 'prices' in response.data and 'best_price' in response.data:
                prices = response.data['prices']
                best_price = response.data['best_price']
                
                # best_price should be the minimum of all exchange prices
                if prices:  # Only check if we have prices
                    expected_best = min(prices.values())
                    self.assertEqual(best_price, expected_best)
                    print(f"{pair_id}: best_price ({best_price}) = min of {list(prices.values())}")
    
    def test_price_endpoint_nonexistent_pair(self):
        """Test price endpoint with non-existent pair."""
        response = self.client.get('/price/NONEXISTENT/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PricingIntegrationTest(TestCase):
    """Integration tests with real sample data and pricing functions."""
    
    def setUp(self):
        """Load sample pairs into database."""
        sample_file = os.path.join(os.path.dirname(__file__), 'sample_pairs.json')
        with open(sample_file, 'r') as f:
            sample_pairs = json.load(f)
        
        for i, pair_data in enumerate(sample_pairs, 1):
            Pair.objects.create(uid=i, **pair_data)
    
    def test_pairs_loaded_correctly(self):
        """Test that all sample pairs loaded with correct attributes."""
        pairs = Pair.objects.all()
        self.assertGreater(pairs.count(), 0)
        
        for pair in pairs:
            # Basic validation
            self.assertIsNotNone(pair.pair_id)
            self.assertIsNotNone(pair.base_token)
            self.assertIsNotNone(pair.quote_token)
            self.assertIsInstance(pair.base_token_decimals, int)
            self.assertIsInstance(pair.quote_token_decimals, int)
            self.assertIsInstance(pair.active_exchanges, list)
            self.assertIsInstance(pair.pool_contracts, dict)
            self.assertGreater(len(pair.active_exchanges), 0)
            
            print(f"✓ {pair.pair_id}: {pair.base_token}({pair.base_token_decimals}) / {pair.quote_token}({pair.quote_token_decimals}) on {pair.active_exchanges}")
    
    def test_pricing_function_calls(self):
        """Test that pricing functions can be called (takes RPC from.env)."""
        pairs = Pair.objects.all()
        
        for pair in pairs:
            print(f"\n--- Testing {pair.pair_id} ---")
            
            # Call the main pricing function
            result = get_token_price(pair.pair_id)
            
            # Should always return a dict with token_pair
            self.assertIsInstance(result, dict)
            self.assertIn('token_pair', result)
            self.assertEqual(result['token_pair'], pair.pair_id)
            
            if 'error' in result:
                print(f"{pair.pair_id}: {result['error']}")
                # This is expected if we don't have RPC URLs configured
            else:
                # We got actual prices!
                self.assertIn('best_price', result)
                self.assertIn('prices', result)
                
                print(f"{pair.pair_id}: Best price = {result['best_price']}")
                
                # Validate price structure
                for exchange, price in result['prices'].items():
                    self.assertIsInstance(price, (int, float))
                    self.assertGreater(price, 0)
                    print(f"  {exchange}: {price}")
                
                # Basic sanity checks for known pairs
                if pair.pair_id == "WBTCUSDC":
                    # BTC should be > $10,000 
                    self.assertGreater(result['best_price'], 10000)
                elif pair.pair_id == "APTUSDC":
                    # APT should be reasonable (> $1, < $1000)
                    self.assertGreater(result['best_price'], 1)
                    self.assertLess(result['best_price'], 1000)