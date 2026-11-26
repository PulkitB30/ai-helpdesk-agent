# VPN (Remote Access)

## Who needs VPN
You need VPN to reach the file server, ERP system and printers from home or while travelling.
In the office you do not need VPN.

## Setup
1. Install **FortiClient VPN** from the Software Center (Windows) or Self Service (Mac).
2. Open FortiClient and add a new connection:
   - Name: `Company VPN`
   - Server: `vpn.example.com`
   - Port: `443`
3. Log in with your normal company email and password.
4. Confirm the login in Microsoft Authenticator (MFA).

## Common problems
- **"Credential or SSLVPN configuration is wrong"**: check that the server is exactly `vpn.example.com`. Your account may be locked after 5 wrong passwords.
- **Connected but no file server**: disconnect, wait 10 seconds, connect again. If it still fails, restart your laptop.
- **Very slow VPN**: close large downloads and video calls. Hotel Wi-Fi often blocks VPN; try your phone hotspot.

If none of this helps, create a ticket with category `network`.
