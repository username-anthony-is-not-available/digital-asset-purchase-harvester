import pytest
from playwright.sync_api import Page, expect


def test_homepage(page: Page, live_server_url):
    page.goto(live_server_url)

    # Check for the main heading
    heading = page.locator("h1")
    expect(heading).to_have_text("Digital Asset Purchase Harvester")

    # Check for the introductory paragraph
    paragraph = page.locator("p")
    expect(paragraph).to_have_text("Upload your mbox file to extract cryptocurrency purchase information.")

    # Check for the file input
    file_input = page.locator("input[type='file']")
    expect(file_input).to_be_visible()

    # Check for the submit button
    submit_button = page.locator("input[type='submit']")
    expect(submit_button).to_have_value("Upload and Process")


def test_upload_file_and_get_results(page: Page, live_server_url):
    page.goto(live_server_url)

    # Upload a valid mbox file
    test_mbox_path = "tests/fixtures/test_emails.mbox"
    page.set_input_files("input[type='file']", test_mbox_path)
    page.click("input[type='submit']")

    # Wait for the results to be displayed
    page.wait_for_selector("#results-section")

    # Check for the results heading
    heading = page.locator("#results-section h1")
    expect(heading).to_have_text("Extracted Purchases")

    # Check for the export buttons
    export_csv_button = page.locator("#export-csv button")
    expect(export_csv_button).to_have_text("Export to CSV")
    export_json_button = page.locator("#export-json button")
    expect(export_json_button).to_have_text("Export to JSON")

    # Check for the "Process Another File" button
    process_another_button = page.locator("a[href='/'] button")
    expect(process_another_button).to_have_text("Process Another File")

    # Check for the results table
    results_table = page.locator("table")
    expect(results_table).to_be_visible()

    # Check for specific data in the results table
    coinbase_row = results_table.locator("tr", has_text="Coinbase")
    expect(coinbase_row).to_contain_text("Your Coinbase purchase of 0.001 BTC")
    expect(coinbase_row).to_contain_text("Coinbase")
    expect(coinbase_row).to_contain_text("100.00")
    expect(coinbase_row).to_contain_text("0.001")

    binance_row = results_table.locator("tr", has_text="Binance")
    expect(binance_row).to_contain_text("Your order to buy 0.1 ETH has been filled")
    expect(binance_row).to_contain_text("Binance")
    expect(binance_row).to_contain_text("200.00")
    expect(binance_row).to_contain_text("0.1")


def test_confidence_filtering(page: Page, live_server_url):
    page.goto(live_server_url)

    # Upload and get to results
    test_mbox_path = "tests/fixtures/test_emails.mbox"
    page.set_input_files("input[type='file']", test_mbox_path)
    page.click("input[type='submit']")
    page.wait_for_selector("#results-section")

    # Check that both rows are visible (default threshold 0)
    expect(page.locator("tr", has_text="Coinbase")).to_be_visible()
    expect(page.locator("tr", has_text="Binance")).to_be_visible()

    # Set threshold to 1.0 (both should disappear since mock has 0.95)
    page.locator("#confidence-threshold").evaluate("el => { el.value = 1.0; el.dispatchEvent(new Event('input')); }")

    expect(page.locator("tr", has_text="Coinbase")).not_to_be_visible()
    expect(page.locator("tr", has_text="Binance")).not_to_be_visible()

    # Set threshold back to 0.5
    page.locator("#confidence-threshold").evaluate("el => { el.value = 0.5; el.dispatchEvent(new Event('input')); }")
    expect(page.locator("tr", has_text="Coinbase")).to_be_visible()
    expect(page.locator("tr", has_text="Binance")).to_be_visible()


def test_manual_edit(page: Page, live_server_url):
    page.goto(live_server_url)

    # Upload and get to results
    test_mbox_path = "tests/fixtures/test_emails.mbox"
    page.set_input_files("input[type='file']", test_mbox_path)
    page.click("input[type='submit']")
    page.wait_for_selector("#results-section")

    # Click Edit on the first row (Coinbase)
    coinbase_row = page.locator("#row-0")
    coinbase_row.get_by_role("button", name="Edit").click()

    # Change the vendor
    vendor_input = coinbase_row.locator(".edit-vendor")
    vendor_input.fill("Updated Coinbase")

    # Change the amount
    amount_input = coinbase_row.locator(".edit-amount")
    amount_input.fill("150.00")

    # Save
    coinbase_row.get_by_role("button", name="Save").click()

    # Verify changes in view mode
    expect(coinbase_row.locator(".view-vendor")).to_have_text("Updated Coinbase")
    expect(coinbase_row.locator(".view-amount")).to_have_text("150.00")


def test_approve_record(page: Page, live_server_url):
    page.goto(live_server_url)

    # Upload and get to results
    test_mbox_path = "tests/fixtures/test_emails.mbox"
    page.set_input_files("input[type='file']", test_mbox_path)
    page.click("input[type='submit']")
    page.wait_for_selector("#results-section")

    # Click Approve on the first row
    coinbase_row = page.locator("#row-0")
    expect(coinbase_row.locator(".view-status")).to_have_text("pending")
    coinbase_row.get_by_role("button", name="Approve").click()

    # Verify status changed to approved and button disappeared
    expect(coinbase_row.locator(".view-status")).to_have_text("approved")
    expect(coinbase_row.get_by_role("button", name="Approve")).not_to_be_visible()

    # Check progress bar
    expect(page.locator("#progress-text")).to_contain_text("1 / 2 Approved")


def test_batch_approve(page: Page, live_server_url):
    page.goto(live_server_url)

    # Upload and get to results
    test_mbox_path = "tests/fixtures/test_emails.mbox"
    page.set_input_files("input[type='file']", test_mbox_path)
    page.click("input[type='submit']")
    page.wait_for_selector("#results-section")

    # Select both rows
    page.locator("#select-all").click()

    # Click Batch Approve
    page.get_by_role("button", name="Approve Selected (a)").click()

    # Verify both rows are approved
    expect(page.locator("#row-0 .view-status")).to_have_text("approved")
    expect(page.locator("#row-1 .view-status")).to_have_text("approved")

    # Check progress bar
    expect(page.locator("#progress-text")).to_contain_text("2 / 2 Approved")
