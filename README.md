# MyBallot — Secure Identity-Powered Digital Balloting System
<p align="center">
<img width="370" height="208" alt="MyBallot_whiteBg" src="https://github.com/user-attachments/assets/3021317c-6819-4ff9-ade8-09b73bc28457"/>
</p>
MyBallot is a prototype for a next-generation digital balloting platform that leverages national ID verification, AI-assisted fraud detection, and **secure edge-to-cloud architecture**.  
It is designed for government-level use but flexible enough for universities, corporations, and communities that require trusted voting.

This repository contains a **demo prototype** of the kiosk software, showcasing the system’s workflow, UI mock logic, and security architecture.

Presentation Video:
<p align="center"><a href="https://youtu.be/Uks-9vKHu70">
<img width="500" height="735" alt="image" src="https://github.com/user-attachments/assets/0f6aeb82-51d1-4beb-a00a-26ba9def1753" />
</a>
</p>

Prototype Demo Video:
<p align="center"><a href="https://youtu.be/nvVLlrOSvQY">
<img width="500" height="960" alt="image" src="https://github.com/user-attachments/assets/bd4204f9-e361-4bc1-a2b5-3ca92f86031a" />
</a>
</p>

---

## Concept

Traditional voting systems rely on manual authentication, centralized networks, and physical ballots — all of which introduce risks such as identity fraud, tampering, and downtime.

**MyBallot solves this by combining:**

- Strong ID verification (via **Persona API**)  
- Secure edge voting terminals running on **Raspberry Pi**
- Independent mobile-network connectivity using **SIM-based data**
- End-to-end encrypted vote transport
- Instant replication to an off-site secure server
- Tamper-resistant design with embedded battery backup
- Optional multimodal authentication (e.g., fingerprint sensor)

The system is built around the principle that **identity verification + secure hardware + independent networking = trustworthy digital voting**.


---

## Security-Focused Technical Overview

MyBallot is designed with a “security-first” mindset across every layer:

### **1. Device Security**
- Raspberry Pi runs in **kiosk mode**, locking down shell access.
- Python backend isolates sensitive actions in sandboxed modules.
- Hardware ID + SIM card pairing prevents rogue devices.

### **2. Network Security**
- Each kiosk communicates *only* through its own SIM-based data connection.
- VPN-tunneled carrier network.
- No reliance on local organization networks, eliminating LAN-based attacks.

### **3. Identity Verification**
- Persona API performs:
  - Document verification  
  - AI-based fraud detection
  - Keeps records on inquiries

### **4. Vote Integrity**
Votes are:
- Encrypted on-device using AES-256 with rotating key 
- Signed using device private key (Ed25519)  
- Transmitted over HTTPS with pinned certificates

### **5. Data Privacy**
- No PII stored on the kiosk.
- Votes transmitted as anonymous, signed payloads.
- Verification token is ephemeral and cannot be reused.

### **6. Auditability**
- Backend produces:
  - Cryptographic audit logs  
  - Timestamped vote receipts  
  - Integrity proofs per batch  

---

## System Architecture

<p align="center">
  <img alt="MyBallotDiagram" src="https://github.com/user-attachments/assets/d6e022fc-9a3c-4d4e-ad2d-371b5cd070ba"/>
</p>

### **1. User Interaction**
- User places national ID card in front of camera at kiosk.
- Kiosk captures ID photo + facial verification and/or fingerprint
- Persona API verifies identity → returns verification token.

### **2. Vote Casting**
- User selects candidate via kiosk UI.
- Vote is:
  1. Encrypted with public key of central server  
  2. Signed with device key  
  3. Transmitted instantly via SIM network  

### **3. Secure Transmission**
- HTTPS + certificate pinning  
- Encrypted payload + signed vote  

### **4. Backend Processing**
- Validates device signature  
- Validates verification token  
- Appends vote to one-time ledger  
- Replicates vote to off-site backup server  
- Issues anonymous hash receipt



---

## Threat Model & Mitigations

### **Potential Threats**
| Attack Type | Description | Mitigation |
|------------|-------------|------------|
| Device Tampering | Physical access to kiosk | Kiosk mode, sealed hardware, locked casing and security guards |
| Network Interception | Fake base stations, MITM | Private SIM VPN/APN, TLS pinning, vote encryption |
| Identity Spoofing | Fake IDs or deepfakes | Persona AI fraud filters, liveness checks |
| Server Breach | Modify votes | Write-once ledger, hash chaining, backups |
| Insider Attacks | Rogue administrators | Multi-key signing + audit logs |
| Data Loss | Power failure or outages | Kiosk battery + local backup |

