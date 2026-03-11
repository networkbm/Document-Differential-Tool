# System Security Plan — v2.0

## AC-2 Account Management
The organization manages information system accounts by establishing account types, establishing conditions for group and role membership, and notifying account managers. MFA is required for ALL users including standard and privileged accounts. Account reviews are conducted quarterly. Inactive accounts are automatically disabled after 30 days.

## IA-5 Authenticator Management
Passwords must be at least 12 characters for all accounts. Privileged accounts require 16-character passwords with special characters. Password complexity includes uppercase, lowercase, numbers, and special characters. Password history of 24 previous passwords is enforced.

## SC-7 Boundary Protection
The information system monitors and controls communications at the external boundary of the system and at key internal boundaries. A stateful firewall, Web Application Firewall (WAF), and network segmentation via VLANs are deployed. Zero trust architecture principles are applied to all internal traffic.

## AU-2 Audit Events
The organization determines auditable events and coordinates the audit function with other organizations requiring audit-related information.

## SI-2 Flaw Remediation
The organization identifies, reports, and corrects information system flaws. Critical security patches are applied within 15 days of release. High severity patches are applied within 30 days.

## AC-17 Remote Access
Remote access is managed via VPN with MFA. All remote sessions are logged and monitored in real-time.
