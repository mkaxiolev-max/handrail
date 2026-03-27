#!/usr/bin/env python3
import os,json
import stripe

stripe.api_key=os.environ.get('STRIPE_SECRET_KEY')

def create_subscription(email,plan):
    # Free: no charge
    if plan=='free':
        return {'status':'active','plan':'free','customer_id':None}
    
    # Pro: $29/mo
    if plan=='pro':
        customer=stripe.Customer.create(email=email)
        subscription=stripe.Subscription.create(
            customer=customer.id,
            items=[{'price':'price_1ABC123XYZ'}]  # Replace with your price ID
        )
        return {
            'status':'active',
            'plan':'pro',
            'customer_id':customer.id,
            'subscription_id':subscription.id
        }
    
    return {'status':'error','message':'unknown plan'}

def verify_subscription(customer_id):
    subscription=stripe.Subscription.list(customer=customer_id,limit=1)
    if subscription.data:
        return {'status':'active','plan':subscription.data[0].items.data[0].price.nickname}
    return {'status':'inactive'}
