import asyncio
import json
import os
from datetime import datetime, timedelta
from playwright.async_api import async_playwright

# === Configuration ===
URL = "https://999okwin.com/#/login"
LOGIN_SUCCESS_URL = "https://999okwin.com/#/"
LOGIN_JSON_FILE = "css_and _id3.json"
CLICKS_JSON_FILE = "clicks2.json"
USERNAME = os.getenv("USERNAME", "")
PASSWORD = os.getenv("PASSWORD", "")
LOG_FILE_PATH = "bet_log.txt"

CRUCIAL_RANGES = [
    (10045, 10060), (10105, 10120), (10165, 10180), (10225, 10240),
    (10285, 10300), (10345, 10360), (10405, 10420), (10465, 10480),
    (10525, 10540), (10585, 10600), (10645, 10660), (10705, 10720),
    (10765, 10780), (10825, 10840), (10885, 10900), (10945, 10960),
    (11005, 11020), (11065, 11080), (11125, 11140), (11185, 11200),
    (11245, 11260), (11305, 11320), (11365, 11380), (11425, 11440)
]

BET_AMOUNTS = {
    "bet1": 1, "bet2": 2, "bet3": 5, "bet4": 10, "bet5": 20,
    "bet6": 50, "bet7": 100, "bet8": 200, "bet9": 500,
    "bet10": 1000, "bet11": 2000, "bet12": 5000
}


def log_event(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")


def is_in_crucial_range(period):
    try:
        last_digits = int(str(period)[-5:])
        return any(start <= last_digits <= end for start, end in CRUCIAL_RANGES)
    except Exception as e:
        log_event(f"Crucial range check failed: {e}")
        return False


async def load_json(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log_event(f"Failed to load {filepath}: {e}")
        return None


async def main():
    login_selectors = await load_json(LOGIN_JSON_FILE)
    click_data = await load_json(CLICKS_JSON_FILE)

    if not login_selectors or not click_data:
        return

    pre_assumed_amount = 8888
    current_bet_number = 1
    first_run = True

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
            viewport={"width": 480, "height": 720},
        )
        page = await context.new_page()

        await page.goto(URL)
        log_event("Opened login page")

        await page.locator(login_selectors[0]['css']).fill(USERNAME)
        await page.locator(login_selectors[1]['css']).fill(PASSWORD)
        await page.locator(login_selectors[2]['css']).click(timeout=10000)
        log_event("Login submitted")

        await page.wait_for_url(LOGIN_SUCCESS_URL, timeout=10000)
        log_event("Login successful and redirected")
        await asyncio.sleep(5)

        for i in range(3, len(login_selectors)):
            try:
                await page.locator(login_selectors[i]['css']).click(timeout=5000)
                log_event(f"Clicked post-login element #{i - 2}")
                await asyncio.sleep(2)
            except Exception as e:
                log_event(f"Failed to click post-login element #{i - 2}: {e}")

        async def check_condition():
            try:
                data_row = page.locator("div.van-row").nth(1)  # Use second row (index 1), skip header
                period_elem = data_row.locator("div.van-col--10")
                condition_elem = data_row.locator("div.van-col--5 span")

                await period_elem.wait_for(timeout=3000)
                await condition_elem.wait_for(timeout=3000)

                period = await period_elem.inner_text()
                cond = await condition_elem.inner_text()
                return cond.strip(), period.strip()[-5:]

            except Exception as e:
                try:
                    debug_html = await page.locator("div.van-row").nth(1).inner_html()
                    log_event(f"[DEBUG] Data row HTML:\n{debug_html}")
                except Exception as inner_e:
                    log_event(f"[DEBUG] Failed to get data row HTML: {inner_e}")

                log_event(f"Condition check failed: {e}")
                return None, None

        async def execute_bet(bet_number):
            nonlocal pre_assumed_amount
            bet_key = f"bet{bet_number}"
            if bet_key not in click_data:
                log_event(f"No data for {bet_key}. Terminating.")
                await browser.close()
                return

            log_event(f"Executing... {bet_key}")
            start_time = datetime.now()

            for click in click_data[bet_key]:
                try:
                    delay = click.get("delay", 0)
                    xpath = click.get("xpath")
                    if not xpath:
                        continue

                    while (datetime.now() - start_time).total_seconds() < delay:
                        await asyncio.sleep(0.05)

                    locator = page.locator(f"xpath={xpath}")
                    await locator.scroll_into_view_if_needed()
                    await locator.click(timeout=5000)

                except Exception as e:
                    log_event(f"Error executing click {xpath}: {e}")
                    await browser.close()
                    return
            log_event("Bet executed successfully.")    

            current_second = datetime.now().second
            wait_time = 70 - current_second
            if wait_time > 0:
                log_event(f"Waiting {wait_time} seconds for result...")
                await asyncio.sleep(wait_time)

            cond, period = await check_condition()
            if not cond or not period:
                return bet_number

            bet_amt = BET_AMOUNTS[bet_key]
            if cond == "Big":
                pre_assumed_amount = (pre_assumed_amount - bet_amt) + (bet_amt * 1.96)
                log_event(f"Won {bet_key}, Profit: {(pre_assumed_amount - 8888):.2f}")
                return 1
            else:
                pre_assumed_amount -= bet_amt
                log_event(f"Lost {bet_key}, Loss: {(pre_assumed_amount - 8888):.2f}")
                return bet_number + 1

        while True:
            try:
                if first_run:
                    target_time = (datetime.now() + timedelta(minutes=1)).replace(second=20, microsecond=0)
                    log_event(f"Waiting until {target_time} to start betting...")
                    while datetime.now() < target_time:
                        await asyncio.sleep(1)     
                    first_run = False

                cond, period = await check_condition()
                log_event(f"Period: {period}, Condition: {cond}")
                
                if cond and period and current_bet_number == 1 and is_in_crucial_range(period):
                    log_event(f"Skipping bet1 due to crucial range in period {period}")
                    await asyncio.sleep(60)
                    continue

                current_bet_number = await execute_bet(current_bet_number)

            except Exception as e:
                log_event(f"Fatal error in main loop: {e}")
                await browser.close()
                return

if __name__ == "__main__":
    asyncio.run(main())
