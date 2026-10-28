import {defineConfig,devices} from '@playwright/test';
export default defineConfig({testDir:'./tests/browser',fullyParallel:false,retries:0,reporter:'list',use:{...devices['Pixel 7'],baseURL:'http://127.0.0.1:4173'},webServer:{command:'npm run preview -- --port 4173',url:'http://127.0.0.1:4173',reuseExistingServer:false},outputDir:'test-results'});
