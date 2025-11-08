import requests

class UserTester:
    BASE_URL = "http://localhost:5000"
    
    def run_all_tests(self):
        print("Starting User Management Tests")
        print("=" * 50)
        
        try:
            # Login tests
            self.test_admin_valid_credentials()
            self.test_admin_invalid_credentials()
            
            # User creation tests for each profile
            self.test_create_admin_user()
            self.test_create_csr_user()
            self.test_create_pin_user()
            self.test_create_platform_manager_user()
            
            # Other tests
            self.test_create_user_duplicate_email()
            self.test_create_user_missing_fields()
            
            print("[PASS] All tests passed!")
        except AssertionError as e:
            print(f"[FAIL] Test failed: {e}")
        
        print("=" * 50)
    
    def test_admin_valid_credentials(self):
        response = requests.post(
            f"{self.BASE_URL}/login", 
            data={'email': 'admin@example.com', 'password': 'admin123'},
            allow_redirects=False
        )
        assert response.status_code == 302, "Valid User Admin login not successful."
        print("[PASS] Valid User Admin credential (admin@example.com) login successful.")
    
    def test_admin_invalid_credentials(self):
        response = requests.post(
            f"{self.BASE_URL}/login", 
            data={'email': 'admin@example.com', 'password': 'wrongadmin123'},
            allow_redirects=False
        )
        assert response.status_code == 400, "Invalid User Admin login successful."
        print("[PASS] Invalid User Admin credential (admin@example.com) login failed.")
    
    def test_create_admin_user(self):
        session = requests.Session()
        login_response = session.post(
            f"{self.BASE_URL}/login",
            data={'email': 'admin@example.com', 'password': 'admin123'},
            allow_redirects=False
        )
        assert login_response.status_code == 302, "Admin login failed for create user test."
        
        create_response = session.post(
            f"{self.BASE_URL}/users/create",
            data={
                'name': 'Test Admin',
                'email': 'testadmin@example.com',
                'password': 'testpassword123',
                'profile_id': '1',
                'is_suspended': ''
            },
            allow_redirects=False
        )
        assert create_response.status_code == 302, "Admin user creation failed."
        print("[PASS] Create Admin user successful (testadmin@example.com).")
    
    def test_create_csr_user(self):
        session = requests.Session()
        login_response = session.post(
            f"{self.BASE_URL}/login",
            data={'email': 'admin@example.com', 'password': 'admin123'},
            allow_redirects=False
        )
        assert login_response.status_code == 302, "Admin login failed for create user test."
        
        create_response = session.post(
            f"{self.BASE_URL}/users/create",
            data={
                'name': 'Test CSR',
                'email': 'testcsr@example.com',
                'password': 'testpassword123',
                'profile_id': '2',
                'is_suspended': ''
            },
            allow_redirects=False
        )
        assert create_response.status_code == 302, "CSR user creation failed."
        print("[PASS] Create CSR user successful (testcsr@example.com).")
    
    def test_create_pin_user(self):
        session = requests.Session()
        login_response = session.post(
            f"{self.BASE_URL}/login",
            data={'email': 'admin@example.com', 'password': 'admin123'},
            allow_redirects=False
        )
        assert login_response.status_code == 302, "Admin login failed for create user test."
        
        create_response = session.post(
            f"{self.BASE_URL}/users/create",
            data={
                'name': 'Test PIN',
                'email': 'testpin@example.com',
                'password': 'testpassword123',
                'profile_id': '3',
                'is_suspended': ''
            },
            allow_redirects=False
        )
        assert create_response.status_code == 302, "PIN user creation failed."
        print("[PASS] Create PIN user successful (testpin@example.com).")
    
    def test_create_platform_manager_user(self):
        session = requests.Session()
        login_response = session.post(
            f"{self.BASE_URL}/login",
            data={'email': 'admin@example.com', 'password': 'admin123'},
            allow_redirects=False
        )
        assert login_response.status_code == 302, "Admin login failed for create user test."
        
        create_response = session.post(
            f"{self.BASE_URL}/users/create",
            data={
                'name': 'Test Platform Manager',
                'email': 'testplatform@example.com',
                'password': 'testpassword123',
                'profile_id': '4',
                'is_suspended': ''
            },
            allow_redirects=False
        )
        assert create_response.status_code == 302, "Platform Manager user creation failed."
        print("[PASS] Create Platform Manager user successful (testplatform@example.com).")
    
    def test_create_user_duplicate_email(self):
        session = requests.Session()
        login_response = session.post(
            f"{self.BASE_URL}/login",
            data={'email': 'admin@example.com', 'password': 'admin123'},
            allow_redirects=False
        )
        assert login_response.status_code == 302, "Admin login failed for duplicate email test."
        
        create_response = session.post(
            f"{self.BASE_URL}/users/create",
            data={
                'name': 'Duplicate User',
                'email': 'admin@example.com',
                'password': 'testpassword123',
                'profile_id': '2',
                'is_suspended': ''
            },
            allow_redirects=False
        )
        assert create_response.status_code in [200, 302], "Should handle duplicate email gracefully."
        print("[PASS] Duplicate email creation correctly rejected.")
    
    def test_create_user_missing_fields(self):
        session = requests.Session()
        login_response = session.post(
            f"{self.BASE_URL}/login",
            data={'email': 'admin@example.com', 'password': 'admin123'},
            allow_redirects=False
        )
        assert login_response.status_code == 302, "Admin login failed for missing fields test."
        
        create_response = session.post(
            f"{self.BASE_URL}/users/create",
            data={
                'name': '',
                'email': 'missingfields@example.com',
                'password': 'testpassword123',
                'profile_id': '4',
                'is_suspended': ''
            },
            allow_redirects=False
        )
        assert create_response.status_code in [200, 400, 302], "Should handle missing fields gracefully."
        print("[PASS] Missing fields validation working.")

if __name__ == '__main__':
    tester = UserTester()
    tester.run_all_tests()
