"""Build a separate unsigned Amazon LAT candidate with only public backend configuration."""
from pathlib import Path
import argparse,json,os,shutil,subprocess
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--log',type=Path,default=ROOT/'deliverables/android/build-logs/amazon-lat-build.log')
    options=parser.parse_args()
    log_path=options.log.resolve()
    assert log_path.is_relative_to(ROOT) and not log_path.is_symlink()
    log_path.parent.mkdir(parents=True,exist_ok=True)
    pin=json.loads((ROOT/'server/receipt-verifier/supabase/public-signing-key.json').read_text())['publicKeySpkiBase64']
    java=str(Path(os.environ['JAVA_HOME'])/'bin/java.exe') if os.environ.get('JAVA_HOME') else shutil.which('java')
    args=[java,'-classpath',str(ROOT/'android/gradle/wrapper/gradle-wrapper.jar'),'org.gradle.wrapper.GradleWrapperMain','-p','android','--no-daemon','assembleAmazonTest',
          '-PlifetaleaRvsUrl=https://guigiqacxpvcxrnajvlz.supabase.co/functions/v1/lifetalea-receipts/v1/verify','-PlifetaleaRvsPublicKey='+pin]
    with log_path.open('w') as log:subprocess.run(args,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    print('Amazon LAT candidate built; no production purchase test or public release approval implied.')

if __name__=='__main__':main()
