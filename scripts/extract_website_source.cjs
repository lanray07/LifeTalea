/* Extract only public editorial source; no environment credentials are evaluated. */
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
if(fs.existsSync(path.join(root,'website/src/dictionaries/en-GB.json'))){console.log('Canonical website dictionary exists; edit it directly.');process.exit(0);}
const ts = require(path.join(root, 'website/node_modules/typescript'));
const source = fs.readFileSync(path.join(root, 'website/src/content.ts'), 'utf8');
const compiled = ts.transpileModule(source, {compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText;
const exportsObject = {};
vm.runInNewContext(compiled, {exports:exportsObject,process:{env:{}}});
const articles = exportsObject.articles;
articles.languages.summary = 'The development app has a 22-locale translation matrix covering 17 priority languages. Native-language review is still required.';
articles.languages.sections[2].body = 'Changing the interface language does not translate personal memories or recordings. Unreviewed website translations are available in local preview only; production requires review.';
const dictionary = {
  ui:{skip:'Skip to content',mainNavigation:'Main navigation',features:'Features',privacy:'Privacy',support:'Support',languages:'Languages',pricing:'Pricing',faq:'Frequently asked questions',contact:'Contact',language:'Language',deviceLanguage:'Use browser language',footerNote:'In development. No account required.',brandNotice:'Working brand pending clearance',related:'Explore the next chapter',previewNotice:'Translation draft. Native-language review pending.',chooseLanguage:'Choose your language',home:'Home'},
  home:{titleFirst:'The little moments.',titleSecond:'The stories that stay.',subtitle:'A private place for photographs, voices and family stories.',explore:'Explore LifeTalea',imageAlt:'An open memory book with a golden bookmark and an olive branch',waysLabel:'Ways to preserve',personalTitle:'Keep it personal',personalBody:'Bring together photographs, recordings and stories in one private family journal.',personalLink:'Start with one memory',voiceTitle:'Make room for their voice',voiceBody:'Capture voices, memories and the details that bring a story to life.',voiceLink:'Explore voice stories',keepsakeTitle:'A keepsake to hold onto',keepsakeBody:'Build a lasting collection of your family’s stories to enjoy now and in years to come.',keepsakeLink:'Discover keepsakes',privacyTitle:'Some things are just for you.',privacyBody:'No public feed. No required account. Memories stay on your device unless you choose to export them.',privacyLink:'Read our privacy approach',storeLink:'View on Amazon Appstore',releaseNote:'Not yet published. Device validation, native-language review and Amazon purchasing verification are in progress.',metaTitle:'LifeTalea — Family stories and voice memories',metaDescription:'A private place for photographs, voices and family stories. Explore the LifeTalea development preview.'},
  articles
};
const directory=path.join(root,'website/src/dictionaries');fs.mkdirSync(directory,{recursive:true});
fs.writeFileSync(path.join(directory,'en-GB.json'),JSON.stringify(dictionary,null,2)+'\n');
console.log('Extracted public English website source');
