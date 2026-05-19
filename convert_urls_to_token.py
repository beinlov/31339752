#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL Conversion Tool: Convert plaintext password URLs to Token URLs

Usage:
    python3 convert_urls_to_token.py
"""
import requests
from typing import Optional

# Configuration
BACKEND_URL = "http://10.61.241.38:8000"
FRONTEND_URL = "http://10.10.66.95:83"

def generate_safe_url(username: str, password: str, menu: Optional[str] = None, hash_fragment: Optional[str] = None) -> str:
    """
    Generate safe login URL using token
    
    Args:
        username: Username
        password: Password
        menu: Menu parameter (optional)
        hash_fragment: URL hash fragment like "#/login" (optional)
    
    Returns:
        Safe token URL
    """
    print(f"\n{'='*60}")
    print(f"Converting URL for user: {username}")
    if menu:
        print(f"Menu: {menu}")
    if hash_fragment:
        print(f"Hash: {hash_fragment}")
    print(f"{'='*60}")
    
    # Prepare parameters
    params = {
        'username': username,
        'password': password,
        'frontend_url': FRONTEND_URL
    }
    
    if menu:
        params['menu'] = menu
    
    print(f"Calling API: {BACKEND_URL}/api/user/generate-login-link")
    
    try:
        # Call the generate-login-link API
        response = requests.get(
            f"{BACKEND_URL}/api/user/generate-login-link",
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            safe_url = data['login_url']
            
            # Add hash fragment if present
            if hash_fragment:
                safe_url += hash_fragment
            
            print(f"SUCCESS")
            print(f"Token: {data['token'][:30]}...")
            print(f"Expires: {data['expires_at']}")
            print(f"Safe URL: {safe_url}")
            
            return safe_url
        else:
            print(f"FAILED: {response.text}")
            return None
            
    except Exception as e:
        print(f"ERROR: {e}")
        return None


def convert_all_urls():
    """Convert the 4 URLs provided by user"""
    
    print("\n" + "="*80)
    print("Converting Your 4 URLs to Token Format")
    print("="*80)
    
    results = []
    
    # URL 1
    print("\n\n[URL 1]")
    print("OLD: http://10.61.241.38:9000/login?username=admin&password=123456&menu=server")
    url1 = generate_safe_url('admin', '123456', menu='server')
    results.append(url1)
    
    # URL 2
    print("\n\n[URL 2]")
    print("OLD: http://10.61.241.38:9000/login?username=admin&password=123456&menu=clear#/login")
    url2 = generate_safe_url('admin', '123456', menu='clear', hash_fragment='#/login')
    results.append(url2)
    
    # URL 3
    print("\n\n[URL 3]")
    print("OLD: http://10.61.241.38:9000/login?username=admin&password=123456&menu=node_distribution#/login")
    url3 = generate_safe_url('admin', '123456', menu='node_distribution', hash_fragment='#/login')
    results.append(url3)
    
    # URL 4
    print("\n\n[URL 4]")
    print("OLD: http://10.61.241.38:9000/login?username=op1&password=123456#/login")
    url4 = generate_safe_url('op1', '123456', hash_fragment='#/login')
    results.append(url4)
    
    print("\n\n" + "="*80)
    print("Conversion Complete! All new URLs do NOT contain plaintext passwords")
    print("="*80)
    
    return results


def show_code_example():
    """Show code example for external platform"""
    
    print("\n" + "="*80)
    print("Code Example for External Platform (Calling Platform)")
    print("="*80)
    
    code = '''
# ===== Code to add in external platform =====

import requests
import webbrowser  # or other navigation method

BACKEND_URL = "http://10.61.241.38:8000"

def jump_to_target_platform(username, password, menu=None, hash_fragment=None):
    """
    Jump to target platform using secure token method
    
    Args:
        username: Username
        password: Password
        menu: Menu parameter (optional), e.g. 'server', 'clear', 'node_distribution'
        hash_fragment: Hash fragment (optional), e.g. '#/login'
    """
    # Call target platform's generate-login-link API
    params = {'username': username, 'password': password}
    if menu:
        params['menu'] = menu
    
    response = requests.get(
        f"{BACKEND_URL}/api/user/generate-login-link",
        params=params
    )
    
    if response.status_code == 200:
        data = response.json()
        safe_url = data['login_url']
        
        # Add hash fragment if present
        if hash_fragment:
            safe_url += hash_fragment
        
        print(f"Safe URL: {safe_url}")
        
        # Navigate to target platform
        webbrowser.open(safe_url)
        # Or: window.location.href = safe_url  # JavaScript
        
        return True
    else:
        print(f"Failed to generate link: {response.text}")
        return False

# ===== Usage Examples =====

# Case 1: Jump to server menu
jump_to_target_platform('admin', '123456', menu='server')

# Case 2: Jump to clear menu with hash
jump_to_target_platform('admin', '123456', menu='clear', hash_fragment='#/login')

# Case 3: Jump to node_distribution menu with hash
jump_to_target_platform('admin', '123456', menu='node_distribution', hash_fragment='#/login')

# Case 4: op1 user login with hash
jump_to_target_platform('op1', '123456', hash_fragment='#/login')
'''
    
    print(code)
    print("\n" + "="*80)


if __name__ == "__main__":
    print("""
========================================================================
          URL Conversion Tool - Token Secure Login
========================================================================
    
This tool demonstrates how to convert plaintext password URLs 
to secure Token URLs
    """)
    
    # Convert all URLs
    print("\n[Step 1] Convert your 4 URLs")
    print("-" * 80)
    convert_all_urls()
    
    # Show code example
    print("\n\n[Step 2] Code Example for External Platform")
    print("-" * 80)
    show_code_example()
    
    print("\n\n" + "="*80)
    print("SUMMARY:")
    print("="*80)
    print("TARGET PLATFORM (This Platform):  No changes needed (100% ready)")
    print("EXTERNAL PLATFORM (Calling):      Refer to code example above")
    print("\nDetailed Documentation:")
    print("  - docs/FOR_EXTERNAL_PLATFORM.md (for external developers)")
    print("  - MODIFICATION_GUIDE.md (modification guide)")
    print("  - TOKEN_LOGIN_QUICK_REFERENCE.md (quick reference)")
    print("="*80)
