import pytest
import re
from playwright.sync_api import Page, expect

def test_auto_asset_id_update(page: Page, live_server_url):
    page.goto(live_server_url)

    # Upload and get to results
    test_mbox_path = "tests/fixtures/test_emails.mbox"
    page.set_input_files("input[type='file']", test_mbox_path)
    page.click("input[type='submit']")
    page.wait_for_selector("#results-section")

    # Click Edit on the first row (Coinbase BTC)
    coinbase_row = page.locator("#row-0")
    coinbase_row.get_by_role("button", name="Edit").click()

    # Verify initial asset_id is bitcoin (from fixture)
    expect(coinbase_row.locator(".view-aid")).to_have_text("bitcoin")

    # Change the crypto currency to Ethereum
    cc_input = coinbase_row.locator(".edit-cc")
    cc_input.fill("Ethereum")

    # Clear asset_id to trigger auto-update
    aid_input = coinbase_row.locator(".edit-aid")
    aid_input.fill("")

    # Save
    coinbase_row.get_by_role("button", name="Save").click()

    # Verify asset_id changed to ethereum
    expect(coinbase_row.locator(".view-aid")).to_have_text("ethereum")

def test_reject_record(page: Page, live_server_url):
    page.goto(live_server_url)

    # Upload and get to results
    test_mbox_path = "tests/fixtures/test_emails.mbox"
    page.set_input_files("input[type='file']", test_mbox_path)
    page.click("input[type='submit']")
    page.wait_for_selector("#results-section")

    # Click Reject on the first row
    coinbase_row = page.locator("#row-0")
    expect(coinbase_row.locator(".view-status")).to_have_text("pending")
    coinbase_row.get_by_role("button", name="Reject").click()

    # Verify status changed to rejected and Reject button disappeared, Approve appeared
    expect(coinbase_row.locator(".view-status")).to_have_text("rejected")
    expect(coinbase_row.get_by_role("button", name="Reject")).not_to_be_visible()
    expect(coinbase_row.get_by_role("button", name="Approve")).to_be_visible()

    # Check progress bar - should be 0/1 because 1 out of 2 is rejected
    expect(page.locator("#progress-text")).to_contain_text("0 / 1 Approved (excluding rejected)")

def test_batch_reject(page: Page, live_server_url):
    page.goto(live_server_url)

    # Upload and get to results
    test_mbox_path = "tests/fixtures/test_emails.mbox"
    page.set_input_files("input[type='file']", test_mbox_path)
    page.click("input[type='submit']")
    page.wait_for_selector("#results-section")

    # Select both rows
    page.locator("#select-all").click()

    # Click Batch Reject
    page.get_by_role("button", name="Reject Selected (r)").click()

    # Verify both rows are rejected
    expect(page.locator("#row-0 .view-status")).to_have_text("rejected")
    expect(page.locator("#row-1 .view-status")).to_have_text("rejected")

    # Check progress bar - 0/0 Approved
    expect(page.locator("#progress-text")).to_contain_text("0 / 0 Approved (excluding rejected)")

def test_hide_rejected_filter(page: Page, live_server_url):
    page.goto(live_server_url)

    # Upload and get to results
    test_mbox_path = "tests/fixtures/test_emails.mbox"
    page.set_input_files("input[type='file']", test_mbox_path)
    page.click("input[type='submit']")
    page.wait_for_selector("#results-section")

    # Reject the first row
    page.locator("#row-0").get_by_role("button", name="Reject").click()
    expect(page.locator("#row-0")).to_have_class(re.compile(r"status-rejected"))

    # Both rows should be visible initially
    expect(page.locator("#row-0")).to_be_visible()
    expect(page.locator("#row-1")).to_be_visible()

    # Click Hide Rejected
    page.locator("#hide-rejected").click()

    # Row 0 should be hidden, Row 1 should be visible
    expect(page.locator("#row-0")).not_to_be_visible()
    expect(page.locator("#row-1")).to_be_visible()

    # Uncheck Hide Rejected
    page.locator("#hide-rejected").click()
    expect(page.locator("#row-0")).to_be_visible()
    expect(page.locator("#row-1")).to_be_visible()

def test_take_screenshots(page: Page, live_server_url):
    page.goto(live_server_url)
    test_mbox_path = "tests/fixtures/test_emails.mbox"
    page.set_input_files("input[type='file']", test_mbox_path)
    page.click("input[type='submit']")
    page.wait_for_selector("#results-section")

    # 1. Show Rejected
    page.locator("#row-0").get_by_role("button", name="Reject").click()
    page.screenshot(path="/home/jules/verification/rejected_row.png")

    # 2. Hide Rejected
    page.locator("#hide-rejected").click()
    page.screenshot(path="/home/jules/verification/hidden_rejected.png")

    # 3. Auto Asset ID
    page.locator("#hide-rejected").click() # show it again
    binance_row = page.locator("#row-1")
    binance_row.get_by_role("button", name="Edit").click()
    binance_row.locator(".edit-cc").fill("Solana")
    binance_row.locator(".edit-aid").fill("")
    binance_row.get_by_role("button", name="Save").click()
    page.screenshot(path="/home/jules/verification/auto_asset_id.png")
