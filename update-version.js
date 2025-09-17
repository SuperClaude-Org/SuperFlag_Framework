// Script to update package.json version from central version.ts
import fs from 'fs';
import { VERSION } from './dist/version.js';

const packagePath = './package.json';
const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf-8'));
packageJson.version = VERSION;
fs.writeFileSync(packagePath, JSON.stringify(packageJson, null, 2) + '\n');
console.log(`Updated package.json version to ${VERSION}`);