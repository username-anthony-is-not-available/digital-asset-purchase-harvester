# Exchange-Specific Email Format Guides

This document provides a reference for the email formats used by various cryptocurrency exchanges for purchase confirmations. Understanding these formats is crucial for both manual verification and for improving the accuracy of the Digital Asset Purchase Harvester.

The tool uses a combination of keyword filtering and LLM-based extraction to identify and parse these emails. The samples provided here are used for testing and refining the extraction process.

## Table of Contents

1.  [Coinbase Confirmation Email Format](#coinbase-confirmation-email-format)
2.  [Binance Confirmation Email Format](#binance-confirmation-email-format)
3.  [Kraken Confirmation Email Format](#kraken-confirmation-email-format)

---

## Coinbase Confirmation Email Format

Coinbase emails are typically straightforward and contain clear indicators of a purchase.

**Key Identifiers:**

*   **Subject:** "Your Coinbase purchase of..." or "You received..."
*   **Sender:** `noreply@coinbase.com`
*   **Keywords:** "You bought", "You received", "Total", "Subtotal", "Coinbase Fee"

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

---

## Binance Confirmation Email Format

Binance emails often contain detailed trade information, which can be more complex to parse.

**Key Identifiers:**

*   **Subject:** "Trade Confirmation", "Your trade order is filled"
*   **Sender:** `do-not-reply@binance.com`
*   **Keywords:** "Filled", "Price", "Amount", "Total", "Fee"

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

---

## Kraken Confirmation Email Format

Kraken emails are typically concise and focus on the core transaction details.

**Key Identifiers:**

*   **Subject:** "Kraken - Trade Confirmation"
*   **Sender:** `noreply@kraken.com`
*   **Keywords:** "Trade confirmation", "you bought", "cost", "fee"

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
