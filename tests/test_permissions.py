import unittest
from unittest.mock import patch, MagicMock
from src.cloudflare_api import CloudflareAPI
from src.app import main_menu, rotator_tools_menu, zone_management_menu
from cloudflare import APIError

class TestPermissions(unittest.TestCase):

    @patch('src.cloudflare_api.CloudflareAPI.get_token_permissions')
    def test_token_with_full_permissions(self, mock_get_permissions):
        """Test that a token with all required permissions can access all features."""
        mock_get_permissions.return_value = ["Zone.DNS", "Zone.Zone", "API Tokens Read"]
        
        cf_api = CloudflareAPI(api_token="fake-token-full")
        
        self.assertTrue(cf_api.has_permission("ip_rotation"))
        self.assertTrue(cf_api.has_permission("zone_management"))
        self.assertTrue(cf_api.has_permission("token_validation"))
        self.assertIn("ip_rotation", cf_api.get_usable_features())
        self.assertIn("zone_management", cf_api.get_usable_features())

    @patch('src.cloudflare_api.CloudflareAPI.get_token_permissions')
    def test_token_with_partial_permissions(self, mock_get_permissions):
        """Test that a token with partial permissions can only access allowed features."""
        mock_get_permissions.return_value = ["Zone.DNS"] # Only has DNS permission
        
        cf_api = CloudflareAPI(api_token="fake-token-partial")
        
        self.assertTrue(cf_api.has_permission("ip_rotation"))
        self.assertFalse(cf_api.has_permission("zone_management"))
        self.assertFalse(cf_api.has_permission("token_validation"))
        self.assertIn("ip_rotation", cf_api.get_usable_features())
        self.assertNotIn("zone_management", cf_api.get_usable_features())

    @patch('src.cloudflare_api.CloudflareAPI.get_token_permissions')
    def test_token_with_no_permissions(self, mock_get_permissions):
        """Test that a token with no relevant permissions cannot access any features."""
        mock_get_permissions.return_value = ["User.Read", "Account.Read"] # Valid, but not useful permissions
        
        cf_api = CloudflareAPI(api_token="fake-token-none")
        
        self.assertFalse(cf_api.has_permission("ip_rotation"))
        self.assertFalse(cf_api.has_permission("zone_management"))
        self.assertFalse(cf_api.has_permission("token_validation"))
        self.assertEqual(cf_api.get_usable_features(), [])

    @patch('src.cloudflare_api.CloudflareAPI.get_token_permissions')
    def test_token_lacking_permission_to_read_tokens(self, mock_get_permissions):
        """Test the fallback mechanism for a token that can't read its own permissions."""
        # Simulate an APIError when trying to get permissions
        mock_get_permissions.side_effect = APIError("No permission to read tokens", request=None, body=None)
        
        cf_api = CloudflareAPI(api_token="fake-token-no-read")

        # Mock the list_zones call on the cf object inside the CloudflareAPI instance
        with patch.object(cf_api.cf.zones, 'list') as mock_list:
            # Assume it succeeds, meaning the token is valid for zone operations
            mock_list.return_value = [MagicMock(id="123", name="example.com")]
            
            # The permissions list should be empty
            self.assertEqual(cf_api.token_permissions, [])
            
            # has_permission should return False for features requiring specific perms
            self.assertFalse(cf_api.has_permission("zone_management"))
            
            # verify_token should succeed due to the fallback
            self.assertTrue(cf_api.verify_token())

    @patch('src.cloudflare_api.CloudflareAPI.get_token_permissions')
    def test_unusable_token_raises_error_on_verify(self, mock_get_permissions):
        """Test that verify_token raises an error if the token has no usable permissions."""
        mock_get_permissions.return_value = ["User.Read"] # No permissions for our features
        
        cf_api = CloudflareAPI(api_token="fake-token-unusable")
        
        with self.assertRaises(APIError) as cm:
            cf_api.verify_token()
        
        self.assertIn("no permissions for any of the tool's features", str(cm.exception))

    @patch('src.app.select_from_list')
    @patch('src.app.confirm_action', return_value=True)
    @patch('builtins.input', side_effect=['1', '0', '0']) # Select account, then exit menus
    def test_ui_blocks_access(self, mock_input, mock_confirm, mock_select):
        """Test that the UI menus correctly disable and block access to features."""
        
        # Mock config to return a single account with a partial-permission token
        mock_config = {
            "accounts": [{"name": "test-account", "api_token": "fake-token-partial"}]
        }
        
        # This token only has Zone.DNS
        with patch('src.cloudflare_api.CloudflareAPI.get_token_permissions', return_value=["Zone.DNS"]):
             with patch('src.app.load_config', return_value=mock_config):
                
                # Mock a CloudflareAPI instance to be used by the menus
                cf_api = CloudflareAPI(api_token="fake-token-partial")

                # Test zone_management_menu directly
                with patch('builtins.print') as mock_print:
                    zone_management_menu(cf_api, "test-account")
                    # Check that the permission error message was printed
                    mock_print.assert_any_call("❌ Your token does not have permission to manage zones.")

                # Test rotator_tools_menu directly
                # It should succeed because it has the required 'ip_rotation' permission
                with patch('builtins.print') as mock_print:
                    rotator_tools_menu(cf_api, "test-account")
                    # Check that it doesn't print an error and instead prints a menu option
                    mock_print.assert_any_call("1. 🔄 Rotate Based on a List of IPs (Single-Record)")


if __name__ == '__main__':
    unittest.main()
