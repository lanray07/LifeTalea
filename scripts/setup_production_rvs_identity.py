"""Create the server assertion identity outside Git, without replacing an existing key."""
from pathlib import Path
import base64, json, os, subprocess
import stat
from uuid import uuid4
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

def main():
    private=Path.home()/'.codex/private/lifetalea/production-rvs'
    private.mkdir(mode=0o700,parents=True,exist_ok=True)
    if os.name=='nt':
        account=os.environ['USERDOMAIN']+'\\'+os.environ['USERNAME']
        subprocess.run(['icacls',str(private),'/inheritance:r','/grant:r',account+':(OI)(CI)F','SYSTEM:(OI)(CI)F'],check=True,capture_output=True)
    path=private/'assertion.private.pem'
    if os.name != 'nt':
        directory = private.lstat()
        if not stat.S_ISDIR(directory.st_mode) or directory.st_uid != os.getuid() or directory.st_mode & 0o077:
            raise PermissionError("The signing directory must be owned by this user and have mode 0700")
        # Use the checked directory descriptor for both creation and reuse.
        dir_fd = os.open(private, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            checked = os.fstat(dir_fd)
            if (checked.st_dev, checked.st_ino) != (directory.st_dev, directory.st_ino):
                raise PermissionError("The signing directory changed while opening it")
            try:
                os.stat(path.name, dir_fd=dir_fd, follow_symlinks=False)
            except FileNotFoundError:
                key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
                staging = '.assertion-' + uuid4().hex
                fd = os.open(staging, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=dir_fd)
                try:
                    with os.fdopen(fd, 'wb') as out:
                        out.write(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
                        out.flush()
                        os.fsync(out.fileno())
                    try:
                        os.link(staging, path.name, src_dir_fd=dir_fd, dst_dir_fd=dir_fd, follow_symlinks=False)
                    except FileExistsError:
                        pass
                finally:
                    os.unlink(staging, dir_fd=dir_fd)
            fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=dir_fd)
            with os.fdopen(fd, 'rb') as source:
                info = os.fstat(source.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
                    raise PermissionError("The private signing key must be an owner-only regular file")
                key = serialization.load_pem_private_key(source.read(), password=None)
        finally:
            os.close(dir_fd)
    else:
        if not path.exists():
            key=rsa.generate_private_key(public_exponent=65537,key_size=3072)
            with path.open('xb') as out:out.write(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
        key=serialization.load_pem_private_key(path.read_bytes(),password=None)
    public=base64.b64encode(key.public_key().public_bytes(serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo)).decode()
    target=Path(__file__).resolve().parents[1]/'server/receipt-verifier/supabase/public-signing-key.json'
    target.write_text(json.dumps({'algorithm':'RS256','publicKeySpkiBase64':public},indent=2)+'\n')
    print('Production signing identity ready outside Git; public pin exported.')

if __name__=='__main__':main()
