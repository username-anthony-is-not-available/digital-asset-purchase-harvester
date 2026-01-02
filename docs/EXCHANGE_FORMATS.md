# Exchange-Specific Email Format Guides

This document provides a comprehensive reference for the email formats used by various cryptocurrency exchanges for purchase confirmations. Understanding these formats is crucial for both manual verification and for improving the accuracy of the Digital Asset Purchase Harvester.

The tool uses a combination of keyword filtering and LLM-based extraction to identify and parse these emails. The samples provided here are used for testing and refining the extraction process.

## Table of Contents

1.  [Coinbase Confirmation Email Format](#coinbase-confirmation-email-format)
2.  [Binance Confirmation Email Format](#binance-confirmation-email-format)
3.  [Kraken Confirmation Email Format](#kraken-confirmation-email-format)
4.  [Sample Emails for Testing](#sample-emails-for-testing)
5.  [Parsing Tips and Edge Cases](#parsing-tips-and-edge-cases)

---

## Coinbase Confirmation Email Format

Coinbase is one of the most popular cryptocurrency exchanges and sends clear, well-structured purchase confirmation emails. These emails are typically HTML-formatted but contain plain text alternatives.

### Email Structure

**Header Information:**

*   **Subject Line Patterns:**
    *   `"Your Coinbase purchase of [amount] [crypto]"`
    *   `"You received [amount] [crypto]"`
    *   `"Your recent purchase of [crypto] on Coinbase"`
*   **From Address:** `noreply@coinbase.com` or `no-reply@coinbase.com`
*   **Reply-To:** Usually none (no-reply address)

**Body Content Structure:**

Coinbase emails typically contain the following sections in order:

1.  **Greeting**: Personalized with user's first name or email
2.  **Transaction Summary**: Clear statement of the purchase
3.  **Transaction Details Table**: Breakdown of costs
4.  **Transaction ID**: Unique identifier for the transaction
5.  **Footer**: Standard Coinbase branding and links

### Key Data Fields

| Field | Location | Format Example | Notes |
|-------|----------|----------------|-------|
| Crypto Amount | Body | `0.5 BTC`, `1.2345 ETH` | Usually in bold or strong tags |
| Fiat Amount | Body | `$30,000.00 USD` | Includes currency symbol and code |
| Fee | Body or Details | `$150.00 USD` | May be labeled as "Coinbase Fee" |
| Transaction ID | Body | `QWERTY12345`, `abc123xyz789` | Alphanumeric, typically in code tags |
| Date/Time | Header or Body | RFC 2822 format | Timezone included |
| Payment Method | Body | `Bank account ending in 1234` | Optional, may not always be present |

### Keyword Indicators

Look for these phrases to identify Coinbase purchase emails:

*   **Primary:** "You bought", "You received"
*   **Secondary:** "Total", "Subtotal", "Coinbase Fee", "Transaction completed"
*   **Negative (non-purchase):** "price alert", "newsletter", "market update"

### Sample Coinbase Email (Detailed)

```eml
Subject: Your Coinbase purchase of 0.5 BTC
From: Coinbase <noreply@coinbase.com>
To: user@example.com
Date: Tue, 15 Mar 2024 10:00:00 -0700
Message-ID: <abc123@coinbase.com>
Content-Type: text/html; charset=utf-8
Content-Transfer-Encoding: quoted-printable

<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Your Coinbase Purchase</title>
</head>
<body>
  <div style="font-family: Arial, sans-serif;">
    <h2>Hi John,</h2>
    <p>You bought <strong>0.5 BTC</strong> for <strong>$30,000.00 USD</strong>.</p>
    
    <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
      <tr>
        <td>Subtotal</td>
        <td align="right">$29,850.00 USD</td>
      </tr>
      <tr>
        <td>Coinbase Fee</td>
        <td align="right">$150.00 USD</td>
      </tr>
      <tr style="font-weight: bold;">
        <td>Total</td>
        <td align="right">$30,000.00 USD</td>
      </tr>
    </table>
    
    <p>Transaction ID: <code>QWERTY12345</code></p>
    <p>Payment method: Bank account ending in 1234</p>
    <p>Date: March 15, 2024 at 10:00 AM PST</p>
    
    <p><a href="https://www.coinbase.com/transactions/QWERTY12345">View transaction details</a></p>
  </div>
</body>
</html>
```

### Format Variations

1.  **Recurring Buys**: Subject may include "recurring" or "scheduled"
2.  **Coinbase Pro**: Uses `noreply@pro.coinbase.com` with slightly different format
3.  **Rewards/Earn**: "You received" subject for crypto earned through promotions
4.  **Converted Crypto**: May have "converted" in subject when converting between cryptos

---

## Binance Confirmation Email Format

Binance is the world's largest cryptocurrency exchange by trading volume. Their confirmation emails can be more complex due to the variety of trading pairs and order types they support.

### Email Structure

**Header Information:**

*   **Subject Line Patterns:**
    *   `"Trade Confirmation"`
    *   `"Your trade order is filled"`
    *   `"Your order has been filled"`
    *   `"[Binance] Order Filled Notification"`
*   **From Address:** `do-not-reply@binance.com`, `do_not_reply@directmail.binance.com`
*   **Reply-To:** Usually none

**Body Content Structure:**

Binance emails typically follow this structure:

1.  **Header/Logo**: Binance branding
2.  **Order Status**: Clear indication that order was filled
3.  **Order Details Table**: Trading pair, amounts, prices
4.  **Transaction Metadata**: Order ID, time, fee
5.  **Action Links**: View on Binance, trading links
6.  **Footer**: Disclaimers and unsubscribe links

### Key Data Fields

| Field | Location | Format Example | Notes |
|-------|----------|----------------|-------|
| Trading Pair | Body | `BTC/USDT`, `ETH/BUSD` | Base/Quote format |
| Side | Body | `BUY`, `SELL` | Order direction |
| Order Type | Body | `Market`, `Limit`, `Stop-Limit` | Type of order executed |
| Price | Body | `3,000.00 USDT`, `50000.00 USD` | Per unit price |
| Amount | Body | `10 ETH`, `0.5 BTC` | Quantity purchased |
| Total | Body | `30,000.00 USDT` | Total transaction value |
| Fee | Body | `30.00 USDT`, `0.1%` | Trading fee |
| Order ID | Body | `1234567890` | Numeric order identifier |
| Time | Body | ISO 8601 or local format | Execution timestamp |

### Keyword Indicators

Look for these phrases to identify Binance purchase emails:

*   **Primary:** "filled", "order filled", "trade confirmation"
*   **Secondary:** "Price", "Amount", "Total", "Fee", "Order ID"
*   **Order Types:** "Market", "Limit", "Stop", "OCO"
*   **Negative (non-purchase):** "cancelled", "rejected", "price alert", "security"

### Sample Binance Email (Detailed)

```eml
Subject: Your trade order has been filled
From: Binance <do-not-reply@binance.com>
To: user@example.com
Date: Wed, 16 Mar 2024 12:30:00 +0000
Message-ID: <trade123@binance.com>
Content-Type: text/plain; charset=utf-8

Dear Binance User,

Your order to buy 10 ETH has been filled.

Order Details:
==============
Trading Pair: ETH/USDT
Side: BUY
Type: Market Order
Price: 3,000.00 USDT
Amount: 10 ETH
Total: 30,000.00 USDT
Fee: 30.00 USDT (0.10%)

Order ID: 9876543210
Executed: 2024-03-16 12:30:00 UTC

You can view your trade history here:
https://www.binance.com/en/my/orders/exchange/tradehistory

Thank you for trading with Binance!

Best regards,
Binance Team

---
This is an automated message. Please do not reply.
```

### Format Variations

1.  **Spot Trading**: Standard format as shown above
2.  **Margin Trading**: Includes leverage information and borrowed amounts
3.  **Futures/Derivatives**: Additional fields for contracts, position size, margin
4.  **P2P Trading**: Different format with peer information and payment methods
5.  **Multiple Fills**: Partial fills may be listed separately or aggregated
6.  **Binance.US**: Similar format but from `@binance.us` domain

### HTML vs Plain Text

*   **HTML Version**: Typically includes tables, colored buttons, and Binance branding
*   **Plain Text Version**: Simpler format with ASCII separators and aligned columns
*   Most emails are multipart with both versions available

---

## Kraken Confirmation Email Format

Kraken is known for its security-focused approach and professional trading features. Their confirmation emails are concise and focus on essential transaction details.

### Email Structure

**Header Information:**

*   **Subject Line Patterns:**
    *   `"Kraken - Trade Confirmation"`
    *   `"Trade Confirmation for [PAIR]"`
    *   `"Kraken Trade Executed: [PAIR]"`
*   **From Address:** `noreply@kraken.com`, `support@kraken.com`
*   **Reply-To:** May include `support@kraken.com` for user replies

**Body Content Structure:**

Kraken emails follow a minimalist structure:

1.  **Greeting**: Simple salutation
2.  **Trade Summary**: One-line description of the trade
3.  **Trade Details**: Structured list or table
4.  **Reference Information**: Order/Trade IDs
5.  **Footer**: Links to account and support

### Key Data Fields

| Field | Location | Format Example | Notes |
|-------|----------|----------------|-------|
| Trading Pair | Subject/Body | `XBT/USD`, `ETH/EUR` | Kraken uses XBT for Bitcoin |
| Volume | Body | `0.75 XBT`, `10.0 ETH` | Amount purchased |
| Price | Body | `$47,000.00`, `€3,200.00` | Price per unit |
| Cost | Body | `$35,250.00 USD` | Total cost including fees |
| Fee | Body | `$105.00 USD`, `0.26%` | Trading fee amount/percentage |
| Order ID | Body | `OXXXXX-XXXXX-XXXXXX` | Kraken's order format |
| Trade ID | Body | `TXXXXX-XXXXX-XXXXXX` | Kraken's trade format |
| Time | Body | RFC 2822 or local | Execution timestamp |

### Keyword Indicators

Look for these phrases to identify Kraken purchase emails:

*   **Primary:** "trade confirmation", "you bought", "executed"
*   **Secondary:** "cost", "fee", "volume", "price"
*   **Kraken-Specific:** "XBT" (for Bitcoin), "Order ID", "Trade ID"
*   **Negative (non-purchase):** "cancelled", "deposit", "withdrawal", "alert"

### Sample Kraken Email (Detailed)

```eml
Subject: Trade Confirmation for XBT/USD
From: Kraken <noreply@kraken.com>
To: user@example.com
Date: Thu, 17 Mar 2024 08:00:00 -0500
Message-ID: <trade456@kraken.com>
Content-Type: multipart/alternative; boundary="--_boundary_--"

----_boundary_--
Content-Type: text/plain; charset=UTF-8

Hello,

You bought 0.75 XBT (Bitcoin) for $35,250.00 USD.

Trade Details:
--------------
Pair:     XBT/USD
Type:     Buy
Volume:   0.75 XBT
Price:    $47,000.00 USD
Cost:     $35,250.00 USD
Fee:      $105.75 USD (0.30%)

Order ID: O12345-ABCDE-67890F
Trade ID: T98765-ZYXWV-54321S
Time:     2024-03-17 13:00:00 UTC

You can view this trade in your account history:
https://www.kraken.com/u/history/trades

If you have any questions, please contact our support team.

Best regards,
Kraken Support Team

----_boundary_--
Content-Type: text/html; charset=UTF-8

<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
</head>
<body style="font-family: Arial, sans-serif; color: #333;">
  <div style="max-width: 600px; margin: 0 auto;">
    <h2>Trade Confirmation</h2>
    <p>You bought <strong>0.75 XBT</strong> (Bitcoin) for <strong>$35,250.00 USD</strong>.</p>
    
    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
      <tr>
        <td style="padding: 8px; border-bottom: 1px solid #ddd;">Pair</td>
        <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;"><strong>XBT/USD</strong></td>
      </tr>
      <tr>
        <td style="padding: 8px; border-bottom: 1px solid #ddd;">Type</td>
        <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">Buy</td>
      </tr>
      <tr>
        <td style="padding: 8px; border-bottom: 1px solid #ddd;">Volume</td>
        <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">0.75 XBT</td>
      </tr>
      <tr>
        <td style="padding: 8px; border-bottom: 1px solid #ddd;">Price</td>
        <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">$47,000.00 USD</td>
      </tr>
      <tr>
        <td style="padding: 8px; border-bottom: 1px solid #ddd;">Cost</td>
        <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;"><strong>$35,250.00 USD</strong></td>
      </tr>
      <tr>
        <td style="padding: 8px; border-bottom: 1px solid #ddd;">Fee</td>
        <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">$105.75 USD (0.30%)</td>
      </tr>
    </table>
    
    <p style="font-size: 12px; color: #666;">
      Order ID: O12345-ABCDE-67890F<br>
      Trade ID: T98765-ZYXWV-54321S<br>
      Time: 2024-03-17 13:00:00 UTC
    </p>
    
    <p><a href="https://www.kraken.com/u/history/trades" style="color: #5741D9;">View in account history</a></p>
  </div>
</body>
</html>
----_boundary_--
```

### Format Variations

1.  **Market Orders**: Simple format as shown above
2.  **Limit Orders**: May include additional fields for limit price
3.  **Partial Fills**: Multiple emails for orders filled in parts
4.  **Advanced Order Types**: Stop-loss, take-profit orders have additional data
5.  **Margin/Futures**: Different format with leverage and position information
6.  **Currency Codes**: 
    *   XBT = Bitcoin (BTC)
    *   XDG = Dogecoin (DOGE)
    *   XRP = Ripple
    *   Other cryptos typically use standard symbols

### Special Considerations

*   **XBT Notation**: Kraken uses XBT instead of BTC for Bitcoin (following ISO 4217)
*   **Order vs Trade ID**: Orders may result in multiple trades
*   **Fee Structure**: Maker/taker fees vary; percentage shown in email
*   **Currency Pairs**: First currency is always the base (what you're buying/selling)

---

## Sample Emails for Testing

This section provides a comprehensive collection of sample emails that can be used for testing the email parsing and data extraction functionality. These samples represent realistic scenarios and are used in the project's automated test suite.

### Complete Coinbase Purchase Examples

#### Standard Purchase

```eml
From: Coinbase <no-reply@coinbase.com>
Subject: Your Coinbase purchase of 0.001 BTC
To: user@example.com
Date: Tue, 15 Mar 2024 10:00:00 -0700
Message-ID: <purchase001@coinbase.com>
Content-Type: text/plain; charset=utf-8

Hi there,

You successfully purchased 0.001 BTC for $100.00 USD.

Subtotal: $99.00 USD
Coinbase Fee: $1.00 USD
Total: $100.00 USD

Transaction ID: CB-TXN-123456789
Payment method: Bank account ending in 5678
Date: March 15, 2024

Thanks,
The Coinbase Team
```

#### Coinbase Recurring Buy

```eml
From: Coinbase <noreply@coinbase.com>
Subject: Your recurring Coinbase purchase of 0.005 BTC
To: user@example.com
Date: Mon, 01 Apr 2024 08:00:00 -0700
Message-ID: <recurring001@coinbase.com>
Content-Type: text/plain; charset=utf-8

Your recurring purchase was successful!

You bought 0.005 BTC for $250.00 USD.

This is part of your recurring buy schedule (weekly).

Transaction ID: CB-REC-987654321
Next purchase: April 8, 2024
```

#### Coinbase Earn/Rewards

```eml
From: Coinbase <noreply@coinbase.com>
Subject: You received 5 USDC
To: user@example.com
Date: Wed, 10 Apr 2024 14:30:00 -0700
Message-ID: <earn001@coinbase.com>
Content-Type: text/plain; charset=utf-8

Congratulations!

You received 5 USDC for completing the crypto education quiz.

Amount: 5 USDC
Value: ~$5.00 USD
Reason: Educational reward

This crypto has been added to your account.
```

### Complete Binance Purchase Examples

#### Market Buy Order

```eml
From: Binance <do-not-reply@binance.com>
Subject: Your order to buy 0.1 ETH has been filled
To: user@example.com
Date: Wed, 16 Mar 2024 12:30:00 +0000
Message-ID: <order001@binance.com>
Content-Type: text/plain; charset=utf-8

Dear Binance User,

Your order to buy 0.1 ETH for 200.00 USDT has been filled.

Order Details:
Trading Pair: ETH/USDT
Side: BUY
Type: Market
Price: 2,000.00 USDT
Amount: 0.1 ETH
Total: 200.00 USDT
Fee: 0.2 USDT (0.10%)

Order ID: 1234567890
Time: 2024-03-16 12:30:45 UTC

View your order: https://www.binance.com/en/my/orders

Best regards,
Binance Team
```

#### Limit Buy Order Filled

```eml
From: Binance <do-not-reply@directmail.binance.com>
Subject: [Binance] Order Filled Notification
To: user@example.com
Date: Thu, 21 Mar 2024 03:15:22 +0000
Message-ID: <limit001@binance.com>
Content-Type: text/html; charset=utf-8

Your limit order has been filled!

Trading Pair: BTC/USDT
Side: BUY
Type: Limit Order
Limit Price: 50,000.00 USDT
Executed Price: 49,999.50 USDT
Amount: 0.02 BTC
Total: 999.99 USDT
Fee: 1.00 USDT

Order ID: 9876543210
Execution Time: 2024-03-21 03:15:22 UTC

Your order was filled at a better price than expected!
```

#### Binance Convert

```eml
From: Binance <do-not-reply@binance.com>
Subject: Your Binance Convert Order has been completed
To: user@example.com
Date: Fri, 22 Mar 2024 16:45:00 +0000
Message-ID: <convert001@binance.com>
Content-Type: text/plain; charset=utf-8

Your Binance Convert order has been completed successfully.

From: 1,000 USDT
To: 0.02 BTC
Rate: 50,000 USDT per BTC

Transaction ID: CNV123456789
Time: 2024-03-22 16:45:00 UTC

View transaction history:
https://www.binance.com/en/my/convert/history
```

### Complete Kraken Purchase Examples

#### Standard Market Buy

```eml
From: Kraken <noreply@kraken.com>
Subject: Kraken - Trade Confirmation
To: user@example.com
Date: Thu, 17 Mar 2024 08:00:00 -0500
Message-ID: <trade001@kraken.com>
Content-Type: text/plain; charset=utf-8

Hello,

You bought 0.05 XBT for $2,500.00 USD.

Pair: XBT/USD
Volume: 0.05 XBT
Price: $50,000.00 USD
Cost: $2,500.00 USD
Fee: $7.50 USD (0.30%)

Order ID: O1A2B3-C4D5E-6F7G8H
Trade ID: T9I0J1-K2L3M-4N5O6P
Time: 2024-03-17 13:00:00 UTC

View trade history:
https://www.kraken.com/u/history/trades
```

#### Ethereum Purchase

```eml
From: Kraken <support@kraken.com>
Subject: Trade Confirmation for ETH/EUR
To: user@example.com
Date: Mon, 25 Mar 2024 11:22:33 +0100
Message-ID: <trade002@kraken.com>
Content-Type: text/plain; charset=utf-8

Trade confirmation:

You bought 5.0 ETH for €15,000.00.

Pair: ETH/EUR
Volume: 5.0 ETH
Price: €3,000.00
Cost: €15,000.00
Fee: €45.00 (0.30%)

Order ID: OABCDE-12345-FGHIJK
Trade ID: TZYXWV-98765-QRSTUV
```

### Non-Purchase Email Examples

These emails should be filtered out and NOT identified as purchases:

#### Price Alert

```eml
From: Crypto News <alerts@cryptonews.com>
Subject: Bitcoin Price Alert
To: user@example.com
Date: Fri, 18 Mar 2024 10:00:00 -0700
Message-ID: <alert001@cryptonews.com>
Content-Type: text/plain; charset=utf-8

Bitcoin (BTC) Price Alert

Current Price: $52,000
Change: +5% in the last 24 hours

This is an automated alert based on your preferences.
```

#### Newsletter

```eml
From: Coinbase <newsletter@coinbase.com>
Subject: This Week in Crypto - Market Roundup
To: user@example.com
Date: Sun, 20 Mar 2024 09:00:00 -0700
Message-ID: <news001@coinbase.com>
Content-Type: text/html; charset=utf-8

Weekly Crypto Newsletter

Market Highlights:
- Bitcoin reached new highs
- Ethereum updates announced
- Altcoin trends to watch

[This is a promotional email]
```

#### Security Alert

```eml
From: Binance <security@binance.com>
Subject: [Binance] New Device Login Detected
To: user@example.com
Date: Tue, 22 Mar 2024 14:20:00 +0000
Message-ID: <security001@binance.com>
Content-Type: text/plain; charset=utf-8

Security Alert

A new device has logged into your account.

Device: Chrome on Windows
Location: New York, USA
Time: 2024-03-22 14:20:00 UTC

If this wasn't you, please secure your account immediately.
```

#### Deposit/Withdrawal Confirmation

```eml
From: Kraken <noreply@kraken.com>
Subject: Withdrawal Confirmed
To: user@example.com
Date: Wed, 23 Mar 2024 16:00:00 -0500
Message-ID: <withdrawal001@kraken.com>
Content-Type: text/plain; charset=utf-8

Your withdrawal has been processed.

Amount: 1.0 ETH
Destination: 0x1234...5678
Fee: 0.005 ETH

Transaction ID: 0xabcd...ef12
Status: Completed
```

### Testing Recommendations

When using these samples for testing:

1.  **Positive Tests**: Use purchase examples to verify correct extraction
2.  **Negative Tests**: Use non-purchase examples to verify filtering
3.  **Edge Cases**: Test with malformed or partial data
4.  **Variations**: Test different currencies, amounts, and formats
5.  **Multi-part Messages**: Test both HTML and plain text parsing
6.  **Character Encoding**: Test with various character sets and special symbols

---

## Parsing Tips and Edge Cases

This section provides guidance for handling common challenges when parsing cryptocurrency exchange emails.

### General Parsing Strategies

#### 1. Multi-part MIME Messages

Most exchange emails are sent as multipart MIME messages containing both HTML and plain text versions:

*   **Best Practice**: Try parsing plain text first as it's simpler and more reliable
*   **Fallback**: If plain text is empty or malformed, parse HTML version
*   **HTML Parsing**: Strip HTML tags but preserve structure (tables, lists)
*   **Character Encoding**: Handle UTF-8, quoted-printable, and base64 encodings

#### 2. Numeric Value Extraction

Cryptocurrency and fiat amounts can be formatted in various ways:

*   **Decimal Separators**: Handle both `.` (US) and `,` (EU) decimal points
*   **Thousands Separators**: Remove commas, spaces, or dots used as separators
*   **Currency Symbols**: Strip `$`, `€`, `£`, `¥` and other symbols
*   **Scientific Notation**: Some amounts may use `1.5e-3` format
*   **Precision**: Maintain full precision for crypto amounts (8+ decimals)

**Examples:**
```
"0.001 BTC" → 0.001
"$1,234.56" → 1234.56
"1.234,56 EUR" → 1234.56
"1,234,567.89" → 1234567.89
```

#### 3. Date and Time Parsing

Exchanges use different datetime formats:

*   **RFC 2822**: Standard email header format (e.g., `Tue, 15 Mar 2024 10:00:00 -0700`)
*   **ISO 8601**: Common in JSON/APIs (e.g., `2024-03-15T10:00:00Z`)
*   **Custom Formats**: Various text formats (e.g., `March 15, 2024 at 10:00 AM PST`)
*   **Timezone Handling**: Always preserve timezone information when available

**Libraries:**
*   Python: `dateutil.parser` for flexible parsing
*   JavaScript: `moment.js` or native `Date.parse()`
*   Go: `time.Parse()` with multiple layouts

#### 4. Cryptocurrency Symbol Variations

Different exchanges use different ticker symbols:

| Exchange | Bitcoin | Ethereum | Tether | Notes |
|----------|---------|----------|--------|-------|
| Coinbase | BTC | ETH | USDT | Standard symbols |
| Binance | BTC | ETH | USDT | Standard symbols |
| Kraken | XBT | ETH | USDT | XBT instead of BTC |
| General | BTC/XBT | ETH | USDT/USD | Normalize to standard |

**Normalization Strategy:**
```python
SYMBOL_MAPPING = {
    "XBT": "BTC",
    "XDG": "DOGE",
    # Add more mappings as needed
}
```

### Exchange-Specific Edge Cases

#### Coinbase Edge Cases

1.  **Multiple Fee Types**
    *   Coinbase Fee (standard trading fee)
    *   Network Fee (for on-chain transactions)
    *   Spread (built into price for instant buys)
    *   **Solution**: Sum all fees or track separately

2.  **Recurring Buys**
    *   May have "recurring" in subject
    *   May reference schedule (daily, weekly, monthly)
    *   **Solution**: Flag as recurring purchase with schedule info

3.  **Coinbase Pro vs Regular**
    *   Different sender addresses
    *   Different fee structures
    *   Different email formats
    *   **Solution**: Detect based on sender domain and adjust parsing

4.  **Convert vs Buy**
    *   Converting between cryptos shows different format
    *   May have two crypto amounts (from and to)
    *   **Solution**: Track conversion separately or treat as two transactions

#### Binance Edge Cases

1.  **Partial Fills**
    *   Large orders may fill in multiple parts
    *   May receive multiple emails for same order
    *   **Solution**: Group by Order ID and aggregate amounts

2.  **Trading Pairs**
    *   Need to determine which currency was purchased
    *   BUY ETH/USDT means buying ETH with USDT
    *   SELL ETH/USDT means selling ETH for USDT
    *   **Solution**: Parse "Side" field (BUY/SELL) to determine direction

3.  **Stablecoin Purchases**
    *   Buying USDT with USD may not be reportable
    *   Need to distinguish crypto purchases from fiat-to-stablecoin
    *   **Solution**: Filter or flag stablecoin transactions based on preferences

4.  **Multiple Order Types**
    *   Market, Limit, Stop-Limit, OCO, etc.
    *   Each may have slightly different format
    *   **Solution**: Use flexible parsing that handles optional fields

5.  **Binance Regional Variants**
    *   Binance.US, Binance.com, regional domains
    *   May have slightly different formats
    *   **Solution**: Detect domain and adjust parsing rules

#### Kraken Edge Cases

1.  **XBT vs BTC**
    *   Always uses XBT for Bitcoin
    *   Must normalize to BTC for compatibility
    *   **Solution**: Apply symbol mapping consistently

2.  **Order ID vs Trade ID**
    *   One order can result in multiple trades
    *   Each trade gets separate email
    *   **Solution**: Track by Order ID to avoid duplicates

3.  **Multiple Currencies**
    *   Supports many fiat currencies (USD, EUR, GBP, CAD, JPY, etc.)
    *   Different currency symbols and formatting
    *   **Solution**: Parse currency code and handle formatting per locale

4.  **Maker vs Taker Fees**
    *   Different fee percentages based on order type
    *   Usually indicated in email
    *   **Solution**: Extract fee percentage for accurate cost basis

### Common Pitfalls and Solutions

#### 1. HTML Rendering Issues

**Problem**: HTML emails may have inline styles, images, or complex layouts that complicate parsing.

**Solutions:**
*   Use HTML parser libraries (BeautifulSoup, jsdom) instead of regex
*   Look for table structures with `<table>`, `<tr>`, `<td>` tags
*   Extract text content and remove all formatting
*   Fallback to plain text version when available

#### 2. Missing or Incomplete Data

**Problem**: Some emails may be missing expected fields (transaction ID, fees, etc.).

**Solutions:**
*   Make fields optional in data schema
*   Log warnings for missing data
*   Use LLM to infer missing information when possible
*   Flag records with incomplete data for manual review

#### 3. False Positives

**Problem**: Non-purchase emails may be incorrectly identified as purchases.

**Solutions:**
*   Implement strong negative keyword filtering:
    *   "cancelled", "rejected", "failed"
    *   "price alert", "newsletter", "promotion"
    *   "security", "login", "password"
    *   "withdraw", "deposit" (without "purchase")
*   Check for explicit purchase indicators:
    *   "you bought", "order filled", "trade confirmation"
    *   Transaction ID with crypto amount and fiat amount
*   Use confidence scoring to flag uncertain results

#### 4. Duplicate Detection

**Problem**: Receiving multiple emails about the same transaction.

**Solutions:**
*   Track Transaction IDs and skip duplicates
*   For partial fills, aggregate by Order ID
*   Check timestamps to identify very close duplicate sends
*   Implement deduplication logic based on:
    *   Exchange + Transaction ID
    *   Exchange + Amount + Date (within seconds)

#### 5. Character Encoding Issues

**Problem**: Special characters, currency symbols, or non-ASCII text may be garbled.

**Solutions:**
*   Always decode with proper charset (UTF-8 preferred)
*   Handle quoted-printable and base64 encoding
*   Normalize Unicode characters (NFD/NFC)
*   Test with international characters: `€`, `£`, `¥`, `ñ`, `ü`, etc.

### Validation Best Practices

After parsing, validate extracted data:

1.  **Required Fields Check**
    ```python
    required = ['amount', 'currency', 'date', 'vendor']
    if not all(data.get(field) for field in required):
        log_warning("Missing required fields")
    ```

2.  **Numeric Range Validation**
    ```python
    if not (0 < amount < 1000000):  # Reasonable range
        log_warning("Amount out of expected range")
    ```

3.  **Currency Code Validation**
    ```python
    VALID_CRYPTOS = ['BTC', 'ETH', 'USDT', ...]
    VALID_FIATS = ['USD', 'EUR', 'GBP', ...]
    if crypto not in VALID_CRYPTOS:
        log_warning("Unknown crypto currency")
    ```

4.  **Date Reasonableness**
    ```python
    if date > datetime.now() or date < datetime(2009, 1, 3):  # Before Bitcoin
        log_warning("Date outside valid range")
    ```

5.  **Fee Reasonableness**
    ```python
    if fee_percent > 10:  # More than 10% seems wrong
        log_warning("Fee percentage unusually high")
    ```

### LLM-Assisted Parsing

When using LLMs for extraction:

1.  **Preprocessing**: Clean and normalize text before LLM
2.  **Structured Prompts**: Request JSON output with specific schema
3.  **Validation**: Always validate LLM output against schema
4.  **Confidence Scoring**: Ask LLM to provide confidence level
5.  **Fallback**: Have rule-based extraction as backup
6.  **Cost Management**: Cache results and avoid redundant calls

### Testing Strategies

1.  **Unit Tests**: Test each parsing function independently
2.  **Integration Tests**: Test end-to-end with sample emails
3.  **Regression Tests**: Keep library of known good/bad emails
4.  **Edge Case Tests**: Specifically test problematic scenarios
5.  **Performance Tests**: Ensure parsing scales with email volume

### Troubleshooting Checklist

When parsing fails:

- [ ] Check email encoding (UTF-8, quoted-printable, base64)
- [ ] Verify correct MIME part is being parsed (text vs HTML)
- [ ] Look for HTML artifacts in extracted text
- [ ] Check for non-standard number formatting
- [ ] Verify date format matches expected patterns
- [ ] Check for exchange-specific symbol variations (XBT vs BTC)
- [ ] Look for partial fills or split transactions
- [ ] Verify transaction isn't a withdrawal, deposit, or other non-purchase
- [ ] Check for new email format not yet documented
- [ ] Enable debug logging to see intermediate parsing steps

### Resources and Tools

**Email Parsing Libraries:**
*   Python: `email`, `mailparser`, `BeautifulSoup`
*   JavaScript: `mailparser`, `node-email-reply-parser`, `jsdom`
*   Go: `net/mail`, `mime/multipart`, `golang.org/x/net/html`

**Testing Tools:**
*   Create mbox files from sample emails for repeatable testing
*   Use email header analyzers to understand structure
*   Validate against real emails from test accounts

**Regular Expressions:**
*   Crypto amounts: `r'[\d,.]+\s*(?:BTC|ETH|etc)'`
*   Fiat amounts: `r'[$€£¥]\s*[\d,.]+|\d[\d,.]+\s*(?:USD|EUR|etc)'`
*   Transaction IDs: Exchange-specific patterns

---

## Contributing

If you encounter email formats not covered in this guide, please contribute:

1.  Create sanitized samples (remove personal information)
2.  Document key fields and patterns
3.  Submit pull request with updates to this file
4.  Include test cases for new formats

## Version History

*   **v1.0.0** (2024-03): Initial comprehensive documentation
    *   Detailed Coinbase, Binance, and Kraken formats
    *   Extensive sample emails
    *   Parsing tips and edge cases
    *   Testing recommendations
