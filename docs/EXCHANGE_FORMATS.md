# Exchange-Specific Email Format Guides

This document provides a reference for the email formats used by various cryptocurrency exchanges for purchase confirmations. Understanding these formats is crucial for both manual verification and for improving the accuracy of the Digital Asset Purchase Harvester.

The tool uses a combination of keyword filtering and LLM-based extraction to identify and parse these emails. The samples provided here are used for testing and refining the extraction process.

## Overview

Each exchange has unique email formats and patterns that the harvester uses to identify and extract purchase data. This guide helps you:

- **Understand** the structure of confirmation emails from major exchanges
- **Test** the email parsing functionality with realistic samples
- **Troubleshoot** extraction issues by comparing against known formats
- **Extend** the harvester to support additional exchanges

## Table of Contents

1.  [Coinbase Confirmation Email Format](#coinbase-confirmation-email-format)
2.  [Binance Confirmation Email Format](#binance-confirmation-email-format)
3.  [Kraken Confirmation Email Format](#kraken-confirmation-email-format)
4.  [Sample Emails for Testing](#sample-emails-for-testing)
5.  [Common Email Patterns](#common-email-patterns)
6.  [Troubleshooting Guide](#troubleshooting-guide)

---

## Coinbase Confirmation Email Format

Coinbase emails are typically straightforward and contain clear indicators of a purchase. They use consistent formatting and clear language.

### Key Identifiers

*   **Subject Lines:**
    *   "Your Coinbase purchase of [amount] [crypto]"
    *   "You received [amount] [crypto]"
    *   "Your recent purchase of [crypto] on Coinbase"
*   **Sender Addresses:** `noreply@coinbase.com`, `no-reply@coinbase.com`
*   **Primary Keywords:** "You bought", "You received", "purchased", "Total", "Subtotal", "Coinbase Fee"
*   **Content Type:** Usually HTML with fallback text

### Transaction Details Format

Coinbase emails typically include:

1.  **Purchase Amount:** Clear statement like "You bought 0.5 BTC"
2.  **Purchase Price:** Usually in format "$30,000.00 USD"
3.  **Transaction ID:** Alphanumeric code, often prefixed with "Transaction ID:" or in a code block
4.  **Fee Information:** Explicitly stated as "Coinbase Fee" or "A fee of..."
5.  **Date/Time:** RFC 2822 format in email headers

### Sample Coinbase Email

```eml
Subject: Your recent purchase of Digital Asset on Coinbase
From: Coinbase <noreply@coinbase.com>
To: user@example.com
Date: Tue, 15 Mar 2024 10:00:00 -0700

Content-Type: text/html; charset=utf-8
Content-Transfer-Encoding: quoted-printable

...

<p>You bought <strong>0.5 BTC</strong> for <strong>$30,000.00 USD</strong>.</p>
<p>Transaction ID: <code>QWERTY12345</code></p>
<p>A fee of <strong>$150.00 USD</strong> was included in this transaction.</p>
...
```

### Common Variations

*   **Recurring Buys:** Subject includes "Your recurring purchase"
*   **Receives:** For transfers, subject starts with "You received"
*   **Multiple Currencies:** May include conversion rates in body

### Extraction Tips

*   Look for strong tags `<strong>` containing amounts
*   Transaction IDs are usually in `<code>` tags
*   Fees may be embedded in totals or listed separately

---

## Binance Confirmation Email Format

Binance emails often contain detailed trade information with structured data. The format can vary between spot trades, futures, and P2P transactions.

### Key Identifiers

*   **Subject Lines:**
    *   "Trade Confirmation"
    *   "Your trade order is filled"
    *   "Your order to buy [amount] [crypto] has been filled"
    *   "Order Execution Notice"
*   **Sender Addresses:** `do-not-reply@binance.com`, `no_reply@directmail.binance.com`
*   **Primary Keywords:** "Filled", "executed", "Price", "Amount", "Total", "Fee", "Order Details"
*   **Content Type:** Both plain text and HTML variants

### Transaction Details Format

Binance emails typically include:

1.  **Order Status:** "Filled", "Completed", or "Executed"
2.  **Trading Pair:** Format like "ETH/USDT" or "BTC/USD"
3.  **Price per Unit:** Listed as "Price: X.XX USDT"
4.  **Amount:** Total cryptocurrency amount purchased
5.  **Total Cost:** Usually in stablecoin or fiat currency
6.  **Trading Fee:** Separate line item, often in BNB or trading currency
7.  **Order ID:** Numeric ID for tracking

### Sample Binance Email

```eml
Subject: Your trade order has been filled
From: Binance <do-not-reply@binance.com>
To: user@example.com
Date: Wed, 16 Mar 2024 12:30:00 +0000

Content-Type: text/plain; charset=utf-8

...

Your order to buy 10 ETH has been filled.

Order Details:
- Price: 3,000.00 USDT
- Amount: 10 ETH
- Total: 30,000.00 USDT
- Fee: 30.00 USDT

...
```

### Common Variations

*   **Spot Trading:** Clear price and amount in trading pair format
*   **P2P Orders:** Include payment method and seller information
*   **Limit Orders:** May include "limit order filled" terminology
*   **Market Orders:** Often use "market order" in subject

### Extraction Tips

*   Parse structured list format with dashes or bullets
*   Trading pairs use "/" separator
*   Fees may be in different currency than purchase (e.g., BNB)
*   Look for numeric patterns with comma separators

---

## Kraken Confirmation Email Format

Kraken emails are typically concise and focus on the core transaction details with a professional, minimalist style.

### Key Identifiers

*   **Subject Lines:**
    *   "Kraken - Trade Confirmation"
    *   "Trade Confirmation for [pair]"
    *   "Your Kraken Order"
*   **Sender Addresses:** `noreply@kraken.com`, `support@kraken.com`
*   **Primary Keywords:** "Trade confirmation", "you bought", "you sold", "cost", "fee", "order executed"
*   **Content Type:** Multipart with both text and HTML alternatives

### Transaction Details Format

Kraken emails typically include:

1.  **Currency Pair:** Using Kraken's unique ticker symbols (e.g., "XBT" for Bitcoin)
2.  **Trade Action:** "bought" or "sold"
3.  **Amount:** Cryptocurrency amount with Kraken ticker
4.  **Price:** Total cost in fiat currency
5.  **Fee:** Listed separately as a line item
6.  **Order Reference:** Alphanumeric order ID

### Sample Kraken Email

```eml
Subject: Trade Confirmation for XBT/USD
From: Kraken <noreply@kraken.com>
To: user@example.com
Date: Thu, 17 Mar 2024 08:00:00 -0500

Content-Type: multipart/alternative; boundary="--_boundary_--"

...

----_boundary_--
Content-Type: text/plain; charset=UTF-8

You bought 0.75 XBT (BTC) for $35,000.00 USD.
Cost: $35,000.00 USD
Fee: $105.00 USD
...
----_boundary_--
```

### Kraken-Specific Tickers

Kraken uses unique ticker symbols that differ from standard:

*   **XBT** = Bitcoin (BTC)
*   **XDG** = Dogecoin (DOGE)
*   **XRP** = Ripple
*   **ETH** = Ethereum (standard)

### Common Variations

*   **Instant Buy:** Subject may include "Instant Buy"
*   **Limit Orders:** Include limit price in email body
*   **Staking Rewards:** Different format for staking confirmations
*   **Multiple Trades:** May batch multiple fills in one email

### Extraction Tips

*   Always map XBT to BTC for standardization
*   Look for parenthetical standard ticker when available
*   Fees are typically calculated as percentage of trade
*   Cost and fee are always separated

---

## Sample Emails for Testing

This section provides a collection of sample emails that can be used for testing the email parsing and data extraction functionality. These samples are also used in the project's automated test suite (see `tests/fixtures/emails.py`).

### Coinbase Purchase

```eml
From: Coinbase <no-reply@coinbase.com>
Subject: Your Coinbase purchase of 0.001 BTC
To: user@example.com
Date: Tue, 15 Mar 2024 10:00:00 -0700
Content-Type: text/plain; charset=utf-8

You successfully purchased 0.001 BTC for $100.00 USD.
```

**Expected Extraction:**
- Amount: 0.001
- Cryptocurrency: BTC
- Price: $100.00
- Currency: USD
- Vendor: Coinbase

---

### Binance Purchase

```eml
From: Binance <do-not-reply@binance.com>
Subject: Your order to buy 0.1 ETH has been filled
To: user@example.com
Date: Wed, 16 Mar 2024 12:30:00 +0000
Content-Type: text/plain; charset=utf-8

Your order to buy 0.1 ETH for 200.00 USD has been filled.
```

**Expected Extraction:**
- Amount: 0.1
- Cryptocurrency: ETH
- Price: 200.00
- Currency: USD
- Vendor: Binance

---

### Kraken Purchase

```eml
From: Kraken <noreply@kraken.com>
Subject: Trade Confirmation: Buy 0.5 XMR
To: user@example.com
Date: Thu, 17 Mar 2024 08:15:00 -0500
Content-Type: text/plain; charset=utf-8

You have successfully bought 0.5 XMR for 50.00 EUR.
```

**Expected Extraction:**
- Amount: 0.5
- Cryptocurrency: XMR (Monero)
- Price: 50.00
- Currency: EUR
- Vendor: Kraken

---

### Complex Purchase (Crypto.com)

```eml
From: "Crypto Exchange" <noreply@crypto.com>
To: user@example.com
Subject: Your order #12345 has been executed
Date: Tue, 1 Jan 2024 12:30:00 +0000
Content-Type: text/plain; charset=utf-8

Your market order to buy 2.5 SOL has been filled at a price of $25.00 per SOL.
Total cost: $62.50 USD.
```

**Expected Extraction:**
- Amount: 2.5
- Cryptocurrency: SOL (Solana)
- Price per unit: $25.00
- Total: $62.50
- Currency: USD
- Vendor: Crypto.com
- Order ID: #12345

---

### Non-Purchase Email (Should be Filtered)

This is an example of an email that should be ignored by the harvester.

```eml
From: Crypto News <alerts@cryptonews.com>
Subject: Bitcoin Price Alert
To: user@example.com
Date: Fri, 18 Mar 2024 10:00:00 -0700
Content-Type: text/plain; charset=utf-8

Bitcoin is up 5% in the last 24 hours.
```

**Expected Result:** Should NOT be classified as a purchase email.

---

### Marketing Email (Should be Filtered)

```eml
From: Ledger <hello@ledger.com>
Subject: Ledger Nano X is back in stock!
To: user@example.com
Date: Mon, 20 Mar 2024 09:00:00 -0700
Content-Type: text/html; charset=utf-8

Don't miss out on our new hardware wallet. Order now!
```

**Expected Result:** Should be filtered out during preprocessing.

---

### Security Alert (Should be Filtered)

```eml
From: Gemini <security@gemini.com>
Subject: Security Alert: New device login
To: user@example.com
Date: Tue, 21 Mar 2024 14:30:00 -0400
Content-Type: text/plain; charset=utf-8

A new device has been logged into your account from IP 192.168.1.1.
```

**Expected Result:** Should be filtered out during preprocessing.

---

## Common Email Patterns

Understanding common patterns across exchanges helps improve the accuracy of email detection and parsing.

### Subject Line Patterns

Purchase confirmation emails typically use these subject patterns:

1.  **Action-based:** "Your [action] of [amount] [crypto]"
    - Examples: "Your purchase of 0.5 BTC", "Your order to buy 10 ETH"

2.  **Status-based:** "[Status]: [Order details]"
    - Examples: "Completed: Buy 100 USDC", "Filled: ETH/USD Order"

3.  **Notification-based:** "Trade Confirmation", "Order Executed"
    - Examples: "Trade Confirmation for BTC/EUR", "Order #12345 Executed"

### Body Content Patterns

Most purchase emails include these elements:

1.  **Purchase Statement:** Clear declaration of the action
    - "You bought", "You purchased", "Your order has been filled"

2.  **Amount and Asset:** Numeric amount followed by cryptocurrency ticker
    - "0.5 BTC", "100.5 ETH", "1,000 USDT"

3.  **Price Information:** Total cost with currency
    - "$30,000.00 USD", "25,000.00 EUR", "100,000 USDT"

4.  **Fee Details:** Transaction or trading fees
    - "Fee: $150.00", "Trading fee: 0.1%", "Network fee included"

5.  **Reference Number:** Transaction or order ID
    - "Transaction ID: ABC123", "Order #12345", "Ref: TXN-9876"

### Sender Address Patterns

Legitimate exchange emails come from predictable domains:

*   **noreply@ or no-reply@:** Most common for automated emails
*   **Exchange domain:** Matches the exchange name (e.g., @coinbase.com)
*   **Subdomain variations:** directmail, transactional, notifications

### Email Headers

Key headers to check for authenticity:

*   **From:** Should match exchange domain
*   **Reply-To:** Often same as From or a support address
*   **Return-Path:** Should be from exchange domain
*   **Content-Type:** Usually `text/html` or `multipart/alternative`

---

## Troubleshooting Guide

### Common Extraction Issues

#### Issue: Email Not Detected as Purchase

**Symptoms:**
- Purchase email not appearing in output
- Email skipped during preprocessing

**Possible Causes:**
1.  Subject line doesn't match known patterns
2.  Sender address not recognized
3.  Missing key purchase keywords
4.  Email classified as marketing/newsletter

**Solutions:**
- Check if exchange is in the supported list (see README.md)
- Verify email contains clear purchase indicators
- Review preprocessing logs for filtering reasons
- Lower confidence threshold in configuration

#### Issue: Incorrect Amount Extracted

**Symptoms:**
- Wrong cryptocurrency amount in output
- Fee included in purchase amount
- Price extracted instead of amount

**Possible Causes:**
1.  Multiple numeric values in email causing confusion
2.  Fee not separated from total
3.  Price per unit vs. total amount ambiguity
4.  Currency symbol parsing error

**Solutions:**
- Look for emails with clearly separated amounts
- Check if exchange uses unusual formatting
- Verify decimal separator (comma vs. period)
- Review LLM extraction prompt for clarity

#### Issue: Wrong Cryptocurrency Identified

**Symptoms:**
- Currency code misidentified
- Stablecoin vs. fiat confusion (e.g., USD vs. USDT)

**Possible Causes:**
1.  Ambiguous ticker symbols (USD vs. USDT)
2.  Exchange-specific tickers (XBT vs. BTC)
3.  Trading pair causing confusion (ETH/BTC)

**Solutions:**
- Use exchange-specific ticker mapping
- Check for context clues (blockchain, wallet, etc.)
- Verify against known cryptocurrency list
- Look for ticker in multiple locations in email

#### Issue: Missing Transaction Date

**Symptoms:**
- Date not extracted or incorrect
- Timezone issues

**Possible Causes:**
1.  Date only in email headers
2.  Multiple dates in email body
3.  Non-standard date format

**Solutions:**
- Parse email Date header as fallback
- Use email received date if purchase date unavailable
- Convert all dates to ISO 8601 format
- Handle timezone conversion properly

### Validation Failures

#### Low Confidence Score

When confidence score is below threshold:

1.  **Review extraction:** Check if all fields are populated
2.  **Verify format:** Ensure email matches known patterns
3.  **Check keywords:** Confirm purchase-related terms present
4.  **Inspect data:** Look for incomplete or ambiguous information

#### Failed Data Validation

Common validation errors:

*   **Negative amounts:** Check for parsing errors with minus signs
*   **Zero values:** Verify amount vs. fee extraction
*   **Invalid currency codes:** Check for typos or non-standard codes
*   **Missing vendor:** Ensure sender domain is recognized

### Testing Your Changes

To test extraction improvements:

1.  **Add test email:** Place sample in `tests/fixtures/emails.py`
2.  **Run specific tests:** `pytest tests/test_email_purchase_extractor.py -v`
3.  **Run full test suite:** `pytest tests/ -m "not integration and not performance"` to verify all functionality
4.  **Check output:** Verify extracted data matches expectations
5.  **Adjust prompts:** Modify extraction prompts if needed
6.  **Iterate:** Refine until accuracy improves

### Getting Help

If you encounter persistent issues:

1.  Check existing test cases for similar email formats
2.  Review logs with `DAP_ENABLE_DEBUG_OUTPUT=true`
3.  Consult the [TROUBLESHOOTING.md](TROUBLESHOOTING.md) guide
4.  Open an issue with sample email (redact personal info)

---

## Contributing

To add support for a new exchange:

1.  **Document the format:** Add a new section following the pattern above
2.  **Add test samples:** Include examples in the testing section
3.  **Update test fixtures:** Add to `tests/fixtures/emails.py`
4.  **Test extraction:** Verify the harvester correctly parses the format
5.  **Update README:** Add exchange to supported list

For questions or improvements to this guide, please open an issue or pull request.
