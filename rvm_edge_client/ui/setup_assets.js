const fs = require('fs');
const path = require('path');

const src = path.join('C:', 'Users', 'jaydi', '.gemini', 'antigravity', 'brain', 'd549a22f-d10e-459b-974b-61b3ae2f3440', 'ecopoints_icon_1779971145431.png');
const assetsDir = path.join(__dirname, 'assets');

if (!fs.existsSync(assetsDir)) {
  fs.mkdirSync(assetsDir);
}

const files = ['favicon.png', 'icon.png', 'splash-icon.png', 'adaptive-icon.png'];
files.forEach(f => {
  fs.copyFileSync(src, path.join(assetsDir, f));
  console.log(`Created: assets/${f}`);
});
console.log('Done!');
