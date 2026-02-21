import platform
from playwright.sync_api import sync_playwright
import subprocess
import time
import tempfile

class AIBrowser:
    
    def __init__(self, use_chrome: bool = False):
        self.browser = None
        self.context = None
        self.page = None
        self.platform = platform.system()
        self.pw_connection = None
        self.use_chrome = use_chrome

        print(f"Detected Platform: {self.platform}")

    def _kill_chrome(self):
        if self.platform == "Darwin":
            subprocess.run("pkill -x 'Google Chrome'", shell=True)
        elif self.platform == "Linux":
            subprocess.run("pkill -x chrome", shell=True)
        elif self.platform == "Windows":
            subprocess.run("taskkill /f /im chrome.exe", shell=True)
        else:
            raise ValueError(f"Unsupported platform: {self.platform}")

    def launch_chromium(self):
        self.pw_connection = sync_playwright().start()
        self.browser = self.pw_connection.chromium.launch(
            headless=False,
            args=[
                "--use-gl=angle",
                "--ignore-gpu-blocklist",
                "--enable-gpu-rasterization",
                "--enable-zero-copy",
                "--enable-accelerated-video-decode",
                "--enable-accelerated-2d-canvas",
                "--disable-gpu-vsync",           # reduces latency
            ]
        )
        self.context = self.browser.new_context()
        self.page = self.context.new_page()

    def launch_chrome(self):
        self._kill_chrome()
        if self.platform == "Darwin":
            command = '"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222 --no-first-run --user-data-dir=/tmp/chrome-debug'
        elif self.platform == "Linux":
            command = 'google-chrome --remote-debugging-port=9222 --no-first-run --user-data-dir=/tmp/chrome-debug'
        elif self.platform == "Windows":
            subprocess.run("taskkill /f /im chrome.exe", shell=True)
            command = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe --remote-debugging-port=9222 --no-first-run --user-data-dir=%TEMP%\\chrome-debug'
        else:
            raise ValueError(f"Unsupported platform: {self.platform}")

        time.sleep(1)
        subprocess.Popen(command, shell=True)
        self._connect_to_chrome()

    def _connect_to_chrome(self):
        self.pw_connection = sync_playwright().start()
        for attempt in range(20):
            try:
                print(f"Connecting to Chrome (attempt {attempt + 1}/20)")
                self.browser = self.pw_connection.chromium.connect_over_cdp("http://localhost:9222")
                self.context = self.browser.new_context()
                self.page = self.context.new_page()
                return self.browser
            except Exception as e:
                print(f"  Failed: {e}")
                time.sleep(1)
        raise RuntimeError("Could not connect to Chrome after 20 attempts")

    def launch_browser(self):

        if not self.pw_connection:

            if self.use_chrome:
                self.launch_chrome()
            else:
                self.launch_chromium()

        return self.browser


    def navigate_to(self, url: str):
        """Navigate to the given URL"""
        if self.page:
            self.page.goto(url)

    def close_browser(self):
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.pw_connection:
            self.pw_connection.stop()

    def take_screenshot(self) -> bytes:
        """Return a byte representation of the screenshot"""
        data = b""
        if self.page:
            with tempfile.NamedTemporaryFile(delete=True, suffix=".png") as temp_file:
                data = self.page.screenshot(path=temp_file.name)
                with open(temp_file.name, "rb") as f:
                    data = f.read()
        return data

    def get_snapshot(self) -> str:
        """Return a string representation of the page tree"""
        if self.page:
            return self.page.locator("html").aria_snapshot()
        return ""

    def click_element_by_text(self, text: str):
        """Click on the element"""
        if self.page:
            self.page.get_by_text(text).first.click()

    def click_element_by_id(self, id: str):
        """Click on the element"""
        if self.page:
            self.page.locator(f"#{id}").click()

if __name__ == "__main__":
    browser = AIBrowser(use_chrome=False)
    browser.launch_browser()
    browser.navigate_to("https://youweizhen.com")
    screenshot = browser.take_screenshot()
    time.sleep(3)
    print(f"Screenshot saved to: {screenshot[:100]}")
    page_tree = browser.get_snapshot()
    print(f"Page tree: {page_tree}")
    browser.click_element_by_text("resume")
    input("Browser is open. Press Enter to close...")
    browser.close_browser()