const puppeteer = require('puppeteer-core');
const assert = require('node:assert/strict');

(async () => {
  if (!process.env.CHROME_PATH) throw new Error('Укажите путь к браузеру в CHROME_PATH');
  const browser = await puppeteer.launch({
    executablePath: process.env.CHROME_PATH,
    headless: true,
    args: ['--no-sandbox']
  });
  try {
    const page = await browser.newPage();
    await page.goto(process.env.APP_URL || 'http://127.0.0.1:8001/', {waitUntil: 'networkidle0'});
    assert.equal(await page.$eval('h1', element => element.textContent), 'Ближайшие мероприятия');
    await page.click('#account-button');
    await page.type('[name=login]', 'admin');
    await page.type('[name=password]', 'Admin12345');
    await page.click('#auth-submit');
    await page.waitForFunction(() => document.querySelector('#account-button').textContent.includes('admin'));
    await page.click('#applications-link');
    await page.waitForFunction(() => document.querySelector('#applications-title').textContent === 'Все заявки');
    console.log('PASS: страница открылась, вход администратора и список заявок работают');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
