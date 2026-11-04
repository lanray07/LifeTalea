"""Build a separate unsigned Amazon LAT candidate with only public backend configuration."""
from pathlib import Path
import json,os,shutil,subprocess
ROOT=Path(__file__).resolve().parents[1]

def main():
    pin=json.loads((ROOT/'server/receipt-verifier/supabase/public-signing-key.json').read_text())['publicKeySpkiBase64']
    java=str(Path(os.environ['JAVA_HOME'])/'bin/java.exe') if os.environ.get('JAVA_HOME') else shutil.which('java')
    args=[java,'-classpath',str(ROOT/'android/gradle/wrapper/gradle-wrapper.jar'),'org.gradle.wrapper.GradleWrapperMain','-p','android','--no-daemon','assembleAmazonTest',
          '-PlifetaleaRvsUrl=https://guigiqacxpvcxrnajvlz.supabase.co/functions/v1/lifetalea-receipts/v1/verify','-PlifetaleaRvsPublicKey='+pin]
    with (ROOT/'deliverables/android/build-logs/amazon-lat-build.log').open('w') as log:subprocess.run(args,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    print('Amazon LAT candidate built; no production purchase test or public release approval implied.')

if __name__=='__main__':main()
