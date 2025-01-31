{
    "name":"KIS E-Wallet Usage",
    "category":"Kings International School/Human Resources",
    "author":"Han Zaw Nyein",
    "license":"LGPL-3",
    "depends":['loyalty','point_of_sale','pos_loyalty'],
    "data":[
        'security/ir.model.access.csv',
        'views/kis_ewallet_usage.xml',

        'reports/report_wallet_usage_xls_view.xml',
        'wizard/wallet_usage_report.xml',
    ]
}