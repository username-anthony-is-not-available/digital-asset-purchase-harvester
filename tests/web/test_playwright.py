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
