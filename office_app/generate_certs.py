"""Generate self-signed SSL certificates for secure communication

Run this script to generate self-signed certificates for the Raspberry Pi backend.
"""
import os
import subprocess
from pathlib import Path

def generate_self_signed_cert():
    """Generate self-signed SSL certificate"""
    cert_dir = Path(__file__).parent / 'certs'
    cert_dir.mkdir(exist_ok=True)

    cert_file = cert_dir / 'server.crt'
    key_file = cert_dir / 'server.key'

    # Check if certificates already exist
    if cert_file.exists() and key_file.exists():
        print(f"✓ Certificates already exist at {cert_dir}")
        return

    print("Generating self-signed SSL certificates...")
    print(f"Certificate directory: {cert_dir}")

    # Generate private key and certificate using OpenSSL
    cmd = [
        'openssl', 'req', '-x509', '-newkey', 'rsa:2048',
        '-keyout', str(key_file),
        '-out', str(cert_file),
        '-days', '365',
        '-nodes',
        '-subj', '/C=US/ST=State/L=City/O=HerdLinx/CN=herdlinx-pi.local'
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✓ Certificate created: {cert_file}")
            print(f"✓ Private key created: {key_file}")
            print("\nCertificate details:")
            print(f"  - Valid for: 365 days")
            print(f"  - Algorithm: RSA 2048-bit")
            print(f"  - Common Name: herdlinx-pi.local")
            print("\n⚠️  WARNING: Self-signed certificate")
            print("  - Add to trusted certificates on client machines")
            print("  - Or disable SSL verification (development only)")
        else:
            print(f"✗ Error generating certificate: {result.stderr}")

    except FileNotFoundError:
        print("✗ OpenSSL not found. Please install OpenSSL:")
        print("  - Ubuntu/Debian: sudo apt-get install openssl")
        print("  - macOS: brew install openssl")
        print("  - Windows: Install from https://slproweb.com/products/Win32OpenSSL.html")
        return False

    return True


def generate_with_cryptography():
    """Alternative: Generate using Python cryptography library"""
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from datetime import datetime, timedelta

        cert_dir = Path(__file__).parent / 'certs'
        cert_dir.mkdir(exist_ok=True)

        cert_file = cert_dir / 'server.crt'
        key_file = cert_dir / 'server.key'

        # Check if certificates already exist
        if cert_file.exists() and key_file.exists():
            print(f"✓ Certificates already exist at {cert_dir}")
            return True

        print("Generating self-signed SSL certificates (using cryptography)...")

        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        # Generate certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"State"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, u"City"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"HerdLinx"),
            x509.NameAttribute(NameOID.COMMON_NAME, u"herdlinx-pi.local"),
        ])

        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(u"localhost"),
                x509.DNSName(u"127.0.0.1"),
                x509.DNSName(u"herdlinx-pi.local"),
            ]),
            critical=False,
        ).sign(
            private_key, hashes.SHA256(), default_backend()
        )

        # Write private key
        with open(key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))

        # Write certificate
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        print(f"✓ Certificate created: {cert_file}")
        print(f"✓ Private key created: {key_file}")
        print("\nCertificate details:")
        print(f"  - Valid for: 365 days")
        print(f"  - Algorithm: RSA 2048-bit")
        print(f"  - Common Name: herdlinx-pi.local")
        print("\n⚠️  WARNING: Self-signed certificate")
        print("  - Add to trusted certificates on client machines")
        print("  - Or disable SSL verification (development only)")

        return True

    except ImportError:
        return None


if __name__ == '__main__':
    print("=" * 60)
    print("HerdLinx SSL Certificate Generator")
    print("=" * 60)

    # Try OpenSSL first
    success = generate_self_signed_cert()

    if success is False:
        # Fallback to cryptography library
        print("\nTrying alternative method (cryptography library)...")
        success = generate_with_cryptography()

        if success is True:
            print("\n✓ Certificates generated successfully!")
        elif success is False:
            print("\n✗ Failed to generate certificates")
            print("Please install cryptography: pip install cryptography")
        else:
            print("\n✗ Cryptography library not found")
            print("Install with: pip install cryptography")
    else:
        print("\n✓ Certificates generated successfully!")

    print("=" * 60)
