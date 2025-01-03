import csv


def write_purchase_data_to_csv(output_file, purchase_data):
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Date', 'Sent Amount', 'Sent Currency', 'Received Amount', 'Received Currency',
                                               'Fee Amount', 'Fee Currency', 'Net Worth Amount', 'Net Worth Currency',
                                               'Label', 'Description', 'TxHash', 'Email Subject'])
        writer.writeheader()
        for purchase in purchase_data:
            writer.writerow({
                'Date': purchase.get('purchase_date', ''),
                'Sent Amount': purchase.get('total_spent', ''),
                'Sent Currency': purchase.get('currency', ''),
                'Received Amount': purchase.get('amount', ''),
                'Received Currency': purchase.get('item_name', ''),
                'Fee Amount': '',
                'Fee Currency': '',
                'Net Worth Amount': '',
                'Net Worth Currency': '',
                'Label': '',
                'Description': f"Purchase from {purchase.get('vendor', '')}",
                'TxHash': '',
                'Email Subject': purchase.get('email_subject', '')
            })
