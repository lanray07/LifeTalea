"""Create disposable localhost-only TLS/signing identities outside Git for App Tester.

Requires the locally installed cryptography package. No production secret is used.
Only public certificates/resources and a local context path enter ignored build output.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import base64, hashlib, ipaddress, json, os, subprocess, tempfile
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID

ROOT=Path(__file__).resolve().parents[1]

def main():
    parent=Path.home()/'.codex/private/lifetalea';parent.mkdir(parents=True,exist_ok=True)
    private=Path(tempfile.mkdtemp(prefix='app-tester-',dir=parent))
    assert private.resolve().parent==parent.resolve() and not private.resolve().is_relative_to(ROOT)
    if os.name=='nt':
        account=os.environ['USERDOMAIN']+'\\'+os.environ['USERNAME']
        subprocess.run(['icacls',str(private),'/inheritance:r','/grant:r',account+':(OI)(CI)F','SYSTEM:(OI)(CI)F'],check=True,capture_output=True)
    now=datetime.now(timezone.utc)
    ca_key=rsa.generate_private_key(public_exponent=65537,key_size=3072)
    ca_name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'LifeTalea disposable local billing QA CA')])
    ca=x509.CertificateBuilder().subject_name(ca_name).issuer_name(ca_name).public_key(ca_key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(minutes=5)).not_valid_after(now+timedelta(days=7)).add_extension(x509.BasicConstraints(ca=True,path_length=0),critical=True).add_extension(x509.KeyUsage(digital_signature=True,key_encipherment=False,key_cert_sign=True,key_agreement=False,content_commitment=False,data_encipherment=False,crl_sign=True,encipher_only=False,decipher_only=False),critical=True).sign(ca_key,hashes.SHA256())
    tls_key=rsa.generate_private_key(public_exponent=65537,key_size=3072)
    tls=x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'localhost')])).issuer_name(ca_name).public_key(tls_key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(minutes=5)).not_valid_after(now+timedelta(days=7)).add_extension(x509.BasicConstraints(ca=False,path_length=None),critical=True).add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost'),x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]),critical=False).add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),critical=False).sign(ca_key,hashes.SHA256())
    signing=rsa.generate_private_key(public_exponent=65537,key_size=3072)
    for name,key in [('tls.private.pem',tls_key),('assertion.private.pem',signing)]:
        with (private/name).open('xb') as output:output.write(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
    (private/'tls.crt').write_bytes(tls.public_bytes(serialization.Encoding.PEM))
    public=base64.b64encode(signing.public_key().public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo)).decode('ascii')
    res=ROOT/'android/app/build/generated/localBillingQa/res';(res/'raw').mkdir(parents=True,exist_ok=True);(res/'xml').mkdir(exist_ok=True)
    (res/'raw/local_billing_qa_ca.pem').write_bytes(ca.public_bytes(serialization.Encoding.PEM))
    (res/'xml/local_billing_network_security.xml').write_text('''<network-security-config><base-config cleartextTrafficPermitted="false"><trust-anchors><certificates src="system" /></trust-anchors></base-config><domain-config cleartextTrafficPermitted="false"><domain>localhost</domain><trust-anchors><certificates src="@raw/local_billing_qa_ca" /></trust-anchors></domain-config></network-security-config>''',encoding='utf-8')
    context=ROOT/'android/app/build/localBillingQa/context.json';context.parent.mkdir(parents=True,exist_ok=True)
    context.write_text(json.dumps({'environment':'sandbox','privateDirectory':str(private),'publicKey':public,'endpoint':'https://localhost:8443/v1/verify','caFile':str(res/'raw/local_billing_qa_ca.pem')},indent=2),encoding='utf-8')
    print(json.dumps({'context':str(context),'privateKeysOutsideRepository':True,'publicKeySha256':hashlib.sha256(base64.b64decode(public)).hexdigest(),'expiresAt':(now+timedelta(days=7)).isoformat()}))

if __name__=='__main__':main()
