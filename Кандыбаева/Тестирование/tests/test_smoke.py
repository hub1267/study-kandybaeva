"""Selenium smoke tests for the local educational shoe store."""
import os
import unittest
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

URL = os.environ.get("APP_URL", "http://127.0.0.1:8000")


class OrdersPage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)

    def open(self):
        self.driver.get(URL)
        self.wait.until(EC.visibility_of_element_located((By.ID, "login-form")))
        return self

    def login(self, login):
        self.driver.find_element(By.NAME, "login").send_keys(login)
        self.driver.find_element(By.CSS_SELECTOR, "#login-form button[type=submit], #login-form button:not([type])").click()
        return self

    def visible(self, css):
        return self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, css)))


class SmokeTests(unittest.TestCase):
    def setUp(self):
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(options=options)
        self.addCleanup(self.driver.quit)
        self.page = OrdersPage(self.driver).open()

    def tearDown(self):
        # unittest records failures before tearDown; preserve evidence only on actual failures.
        outcome = self._outcome.result
        if any(test is self for test, _ in outcome.failures + outcome.errors):
            Path("screenshots").mkdir(exist_ok=True)
            self.driver.save_screenshot("screenshots/{}.png".format(self._testMethodName))

    def test_page_opens(self):
        self.assertEqual("Заказы", self.driver.find_element(By.TAG_NAME, "h1").text)

    def test_manager_sees_order_list(self):
        self.page.login("manager")
        self.assertIn("Менеджер", self.page.visible("#current-user").text)
        self.assertTrue(self.page.visible("#orders-section").is_displayed())

    def test_unknown_user(self):
        self.page.login("unknown-user")
        self.assertIn("не найден", self.page.visible("#message").text)

    def test_administrator_opens_order(self):
        self.page.login("admin")
        self.page.visible("#orders button").click()
        self.assertIn("Заказ №", self.page.visible("#order-title").text)
        self.assertTrue(self.driver.find_element(By.ID, "save").is_displayed())

    def test_logout(self):
        self.page.login("manager")
        self.page.visible("#orders-section")
        self.driver.find_element(By.ID, "logout").click()
        self.assertEqual("Гость", self.driver.find_element(By.ID, "current-user").text)
        self.assertFalse(self.driver.find_element(By.ID, "orders-section").is_displayed())


if __name__ == "__main__":
    unittest.main(verbosity=2)
