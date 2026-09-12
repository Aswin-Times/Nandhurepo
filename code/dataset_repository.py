"""Allowlisted participant data loader and identifier-based context joins."""
import csv
import collections
from decimal import Decimal
from pathlib import Path
from financial_ledger import money

FILES=('requests','sample_requests','financial_profiles','financial_events','exchange_rates',
       'request_payment_options','messages','images')

class DatasetRepository:
    def __init__(self,dataset):
        self.dataset=Path(dataset)
        self.tables={}
        for name in FILES:
            with (self.dataset/(name+'.csv')).open(encoding='utf-8-sig',newline='') as f:
                self.tables[name]=list(csv.DictReader(f))
        self.profiles={p['user_id']:p for p in self.tables['financial_profiles']}
        self.index={}
        for name in ('financial_events','messages','images','request_payment_options'):
            key='request_id' if name=='request_payment_options' else 'user_id'
            index=collections.defaultdict(list)
            for row in self.tables[name]: index[row[key]].append(row)
            self.index[name]=index
        self.rates={(r['rate_date'],r['from_currency'],r['to_currency']):Decimal(r['rate'])
                    for r in self.tables['exchange_rates']}

    def context(self,request):
        uid,rid=request['user_id'],request['request_id']
        if uid not in self.profiles: raise ValueError('Financial profile missing')
        return dict(profile=dict(self.profiles[uid]),events=self.index['financial_events'][uid],
                    messages=[r for r in self.index['messages'][uid] if not r['request_id'] or r['request_id']==rid],
                    images=[r for r in self.index['images'][uid] if not r['request_id'] or r['request_id']==rid],
                    options=self.index['request_payment_options'][rid])
