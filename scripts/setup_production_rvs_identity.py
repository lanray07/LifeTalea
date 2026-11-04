"""Create the server assertion identity outside Git, without replacing an existing key."""
from pathlib import Path
import base64, json, os, subprocess
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

def main():
    private=Path.home()/'.codex/private/lifetalea/production-rvs'
    private.mkdir(parents=True,exist_ok=True)
    if os.name=='nt':
        account=os.environ['USERDOMAIN']+'\\'+os.environ['USERNAME']
        subprocess.run(['icacls',str(private),'/inheritance:r','/grant:r',account+':(OI)(CI)F','SYSTEM:(OI)(CI)F'],check=True,capture_output=True)
    path=private/'assertion.private.pem'
    if not path.exists():
        key=rsa.generate_private_key(public_exponent=65537,key_size=3072)
        with path.open('xb') as out:out.write(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
    key=serialization.load_pem_private_key(path.read_bytes(),password=None)
    public=base64.b64encode(key.public_key().public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo)).decode()
    target=Path(__file__).resolve().parents[1]/'server/receipt-verifier/supabase/public-signing-key.json'
    target.write_text(json.dumps({'algorithm':'RS256','publicKeySpkiBase64':public},indent=2)+'\n')
    print('Production signing identity ready outside Git; public pin exported.')

if __name__=='__main__':main()
