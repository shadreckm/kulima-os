const fs = require('fs');
const path = require('path');
const parser = require('@babel/parser');
const filePath = path.join(__dirname, 'app', 'page.jsx');
const code = fs.readFileSync(filePath, 'utf8');
try {
  parser.parse(code, { sourceType: 'module', plugins: ['jsx'] });
  console.log('PARSE_OK');
} catch (e) {
  console.error(e.message);
  process.exit(1);
}
