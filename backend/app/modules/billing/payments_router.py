from __future__ import annotations

import uuid
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal
from urllib.parse import quote, urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException, Path, Request, Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_control_db
from app.modules.auth.models import User
from app.modules.auth.permissions import get_current_verified_user

from .api_service import BillingAPIService
from .enums import BillingProvider, SubscriptionStatus
from .models import BillingCustomer
from .payment_policy import verify_event
from .exemptions import is_billing_exempt
from .plans import PlanCode
from .repository import BillingRepository
from .workspace_billing import count_devices, device_limit, workspace_status, workspace_account


router = APIRouter(tags=["Billing"])
DB = Annotated[AsyncSession, Depends(get_control_db)]
CurrentUser = Annotated[User, Depends(get_current_verified_user)]


class CheckoutInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    plan_code: Literal["starter", "professional", "business"]
    interval: Literal["month", "year"]
    with_trial: bool = False
    workspace_id: uuid.UUID | None = None


async def stripe(method, path, fields=None, *, key=None):
    if not settings.stripe_secret_key:
        raise HTTPException(503, "Stripe is not configured.")
    headers = {
        "Authorization": f"Bearer {settings.stripe_secret_key}",
        "Stripe-Version": "2025-02-24.acacia",
    }
    if key:
        headers["Idempotency-Key"] = key
    try:
        async with httpx.AsyncClient(timeout=25) as client:
            result = await client.request(
                method, f"https://api.stripe.com/v1{path}", headers=headers,
                params=fields if method == "GET" else None,
                data=fields if method != "GET" else None,
            )
    except httpx.RequestError as exc:
        raise HTTPException(503, "Stripe is temporarily unavailable.") from exc
    if result.status_code >= 400:
        # Log only allowlisted diagnostics, never request fields, card data,
        # the raw provider body/message, or the Authorization header.
        try:
            error = result.json().get("error", {})
        except (ValueError, AttributeError):
            error = {}
        code = error.get("code") if isinstance(error, dict) else None
        param = error.get("param") if isinstance(error, dict) else None
        request_id = result.headers.get("request-id", "")
        code = code if isinstance(code, str) and re.fullmatch(r"[a-z_]{1,60}", code) else "provider_error"
        param = param if isinstance(param, str) and param in {
            "setup_intent_data[usage]", "customer_update[name]", "customer_update[address]",
            "custom_text[submit][message]", "payment_method_types", "currency", "customer",
            "line_items[0][price]", "success_url", "cancel_url",
        } else None
        request_id = request_id if re.fullmatch(r"req_[A-Za-z0-9]{1,80}", request_id) else "unavailable"
        logging.getLogger(__name__).warning(
            "stripe_request_rejected status=%s code=%s param=%s request_id=%s",
            result.status_code, code, param or "unavailable", request_id,
        )
        hint = f" Parameter: {param}." if param else ""
        raise HTTPException(502, f"Stripe rejected this request ({code}).{hint} Reference: {request_id}.")
    return result.json()


async def stripe_list(path, **fields):
    output = []
    while True:
        page = await stripe("GET", path, {**fields, "limit": 100})
        rows = page.get("data", [])
        output.extend(rows)
        if not page.get("has_more"):
            return output
        if not rows:
            raise HTTPException(502, "Stripe returned invalid pagination.")
        fields["starting_after"] = rows[-1]["id"]


def date(value):
    return datetime.fromtimestamp(value, timezone.utc) if value else None


def identifier(value):
    return value.get("id") if isinstance(value, dict) else value


def price_id(code, interval):
    return getattr(settings, f"stripe_price_{code}_{interval}", "").strip()


def return_url():
    return f"{settings.web_url.rstrip('/')}/billing"


async def account(db, user, *, create=False):
    # Serialize creation, Checkout and reconciliation for this account.
    await db.execute(select(User.id).where(User.id == user.id).with_for_update())
    repository = BillingRepository()
    customer = await repository.get_customer_for_user(db, user_id=user.id)
    if create and (customer is None or not customer.provider_customer_id):
        if customer is None:
            customer = await repository.ensure_customer(db, user_id=user.id)
        remote = await stripe("POST", "/customers", {
            "metadata[workforce_user_id]": str(user.id),
            "metadata[application]": "workforceos",
        }, key=f"workforce-customer-{user.id}")
        customer.provider = BillingProvider.STRIPE
        customer.provider_customer_id = remote["id"]
        await db.flush()
    return customer


async def reconcile(db, customer):
    if customer is None or not customer.provider_customer_id:
        return None, []
    history = await stripe_list(
        "/subscriptions", customer=customer.provider_customer_id, status="all",
    )
    ongoing = [s for s in history
               if s["status"] not in {"canceled", "incomplete_expired"}]
    if len(ongoing) > 1:
        raise HTTPException(409, "Multiple subscriptions require billing review.")
    current = ongoing[0] if ongoing else max(
        history, key=lambda s: s["created"], default=None,
    )
    if current is None:
        return None, history
    items = current.get("items", {}).get("data", [])
    if len(items) != 1 or current["items"].get("has_more"):
        raise HTTPException(409, "Unsupported subscription items require review.")
    remote_price = items[0]["price"]["id"]
    code = next((code for code in ("starter", "professional", "business")
                 if remote_price in {price_id(code, "month"), price_id(code, "year")}), None)
    if code is None:
        raise HTTPException(409, "Subscription price is not mapped to a plan.")
    status = {
        "incomplete": "none", "incomplete_expired": "canceled", "paused": "unpaid",
    }.get(current["status"], current["status"])
    if current.get("pause_collection"):
        status = "unpaid"
    repository = BillingRepository()
    subscription = await repository.ensure_subscription(db, user_id=customer.user_id)
    if (subscription.provider == BillingProvider.STRIPE and
            subscription.provider_subscription_id is None and
            subscription.status == SubscriptionStatus.TRIALING and
            subscription.current_period_end is not None and
            current['status'] in {'incomplete', 'incomplete_expired', 'canceled'}):
        # An abandoned/failed paid checkout must not erase a verified local
        # trial's remaining time. Paid activation replaces it normally.
        from .payment_policy import effective_status
        if effective_status(subscription.status, subscription.current_period_end) == 'trialing':
            return current, history
    subscription.plan_code = PlanCode(code)
    subscription.provider = BillingProvider.STRIPE
    subscription.provider_subscription_id = current["id"]
    subscription.status = SubscriptionStatus(status)
    subscription.current_period_start = date(current.get("current_period_start"))
    subscription.current_period_end = date(current.get("current_period_end"))
    await db.flush()
    return current, history


async def trial_used(db, user_id, history):
    local = await BillingRepository().get_subscription_for_user(db, user_id=user_id)
    # Keep the original trial dates after expiry. Never reset eligibility at logout.
    return bool(history or (local and local.provider == BillingProvider.STRIPE and
                           (local.current_period_start is not None or
                            local.provider_subscription_id)))


async def reconcile_trial(db, customer, history):
    """Called with the payer's User row locked. No subscription/charge is created."""
    if (customer is None or not customer.provider_customer_id or
            await trial_used(db, customer.user_id, history)):
        return
    sessions = await stripe_list('/checkout/sessions', customer=customer.provider_customer_id)
    candidates = [s for s in sessions if s.get('mode') == 'setup' and
                  s.get('status') == 'complete' and
                  (s.get('metadata') or {}).get('workforce_trial') == 'manual_v2' and
                  (s.get('metadata') or {}).get('workforce_user_id') == str(customer.user_id)]
    for session in sorted(candidates, key=lambda s: s['created']):
        code = (session.get('metadata') or {}).get('plan_code')
        if code not in {'starter', 'professional', 'business'} or not session.get('setup_intent'):
            continue
        intent = await stripe('GET', '/setup_intents/' + quote(identifier(session['setup_intent']), safe=''))
        if (intent.get('status') != 'succeeded' or
                identifier(intent.get('customer')) != customer.provider_customer_id or
                not intent.get('payment_method')):
            continue
        method = await stripe('GET', '/payment_methods/' + quote(identifier(intent['payment_method']), safe=''))
        if (method.get('type') != 'card' or
                identifier(method.get('customer')) != customer.provider_customer_id):
            continue
        # Only Stripe stores card details; this database stores the plan and dates.
        await stripe('POST', '/customers/' + quote(customer.provider_customer_id, safe=''), {
            'invoice_settings[default_payment_method]': method['id'],
        })
        local = await BillingRepository().ensure_subscription(db, user_id=customer.user_id)
        local.provider = BillingProvider.STRIPE
        local.provider_subscription_id = None
        local.plan_code = PlanCode(code)
        local.status = SubscriptionStatus.TRIALING
        local.current_period_start = datetime.now(timezone.utc)
        local.current_period_end = local.current_period_start + timedelta(days=3)
        await db.flush()
        return


async def checkout_user(db, user, workspace_id):
    if workspace_id is None:
        return user
    state = await workspace_status(db, workspace_id, user.id)
    if not state['can_manage_billing']:
        raise HTTPException(403, 'Workspace payment permission is required.')
    owner_id = await workspace_account(db, workspace_id, user.id)
    payer = await db.get(User, owner_id)
    if payer is None:
        raise HTTPException(404, 'Billing account not found.')
    return payer


async def catalog():
    configured = [price_id(code, interval)
                  for code in ("starter", "professional", "business")
                  for interval in ("month", "year") if price_id(code, interval)]
    if len(configured) != len(set(configured)):
        raise HTTPException(409, "Each plan and interval must use a unique Stripe price.")
    result = []
    for code, name, devices, workspaces, retention, ai, channels in [
        ("starter", "Starter", 30, 1, 30, False, False),
        ("professional", "Plus", 50, 1, 40, True, True),
        ("business", "Advanced", settings.billing_advanced_device_limit,
         3, settings.billing_advanced_retention_days, True, True),
    ]:
        amounts = {}
        currency = None
        for interval in ("month", "year"):
            value = None
            remote_id = price_id(code, interval)
            if remote_id:
                price = await stripe("GET", f"/prices/{quote(remote_id, safe='')}")
                recurring = price.get("recurring") or {}
                if (not price.get("active") or price.get("billing_scheme") != "per_unit"
                        or recurring.get("interval") != interval
                        or recurring.get("interval_count") != 1
                        or recurring.get("usage_type") != "licensed"
                        or price.get("unit_amount") is None):
                    raise HTTPException(409, "Configure fixed recurring plan prices.")
                if currency and currency != price["currency"]:
                    raise HTTPException(409, "Plan currencies must match.")
                currency = price["currency"]
                value = price["unit_amount"]
            amounts[interval] = value
        result.append({
            "code": code, "name": name,
            "description": f"{workspaces} workspace allowance with managed device monitoring.",
            "device_limit": devices, "workspace_limit": workspaces,
            "retention_days": retention, "reporting": True, "payroll": True,
            "channels": channels, "meetings": True, "monitoring": True,
            "live_screen": True, "ai_assistance": ai,
            "monthly_amount_minor": amounts["month"],
            "yearly_amount_minor": amounts["year"],
            "currency": currency or "usd",
            "checkout_enabled": devices is not None and retention is not None
                                and any(v is not None for v in amounts.values()),
        })
    return result


async def public_invoice(item):
    lines = await stripe_list(f"/invoices/{quote(item['id'], safe='')}/lines")
    address = item.get("customer_address") or {}
    return {
        "id": item["id"], "number": item.get("number") or item["id"],
        "issued_at": date(item["created"]), "due_at": date(item.get("due_date")),
        "paid_at": date((item.get("status_transitions") or {}).get("paid_at")),
        "period_start": date(item.get("period_start")),
        "period_end": date(item.get("period_end")),
        "description": item.get("description") or "Workspace subscription",
        "status": item["status"], "currency": item["currency"],
        "subtotal_minor": item["subtotal"], "total_minor": item["total"],
        "tax_minor": sum(t["amount"] for t in item.get("total_tax_amounts", [])),
        "amount_due_minor": item["amount_remaining"],
        "account_name": item.get("customer_name"),
        "invoice_email": item.get("customer_email"),
        "billing_address": [address[k] for k in
                            ("line1", "line2", "city", "state", "postal_code", "country")
                            if address.get(k)],
        "lines": [{"description": line.get("description") or "Subscription",
                   "quantity": line.get("quantity") or 1,
                   "amount_minor": line["amount"]} for line in lines],
    }


@router.get("/details")
async def details(db: DB, user: CurrentUser):
    exempt = await is_billing_exempt(db, user.id)
    customer = None if exempt else await account(db, user)
    current, history = (None, []) if exempt else await reconcile(db, customer)
    if not exempt:
        await reconcile_trial(db, customer, history)
    local = await BillingRepository().get_subscription_for_user(db, user_id=user.id)
    await db.commit()  # Release the account lock before loading invoice history.
    remote = {}
    cards = []
    invoices = []
    if customer and customer.provider_customer_id:
        customer_id = customer.provider_customer_id
        remote = await stripe("GET", f"/customers/{quote(customer_id, safe='')}")
        cards = await stripe_list("/payment_methods", customer=customer_id, type="card")
        invoices = await stripe_list("/invoices", customer=customer_id)
    default = identifier((current or {}).get("default_payment_method")) or identifier(
        (remote.get("invoice_settings") or {}).get("default_payment_method"))
    entitlements = await BillingAPIService(db).get_current_entitlements(user_id=user.id)
    address = remote.get("address") or {}
    registered = None
    try:
        registered = await count_devices(db, user.id)
    except HTTPException as exc:
        if exc.status_code != 503:
            raise
    result = {
        "can_manage_billing": not exempt,
        "billing_exempt": exempt,
        "trial_eligible": not exempt and not await trial_used(db, user.id, history),
        "trial_end": None if exempt else (local.current_period_end if local and local.status == SubscriptionStatus.TRIALING
                      else date((current or {}).get("trial_end"))),
        "billing_interval": ((current or {}).get("items", {}).get("data") or
                             [{"price": {"recurring": {"interval": "month"}}}]
                             )[0]["price"]["recurring"]["interval"],
        "cancel_at_period_end": bool((current or {}).get("cancel_at_period_end")),
        "access_status": entitlements.subscription_status.value,
        "invoice_email": remote.get("email"), "account_name": remote.get("name"),
        "billing_address": [address[k] for k in
                            ("line1", "line2", "city", "state", "postal_code", "country")
                            if address.get(k)],
        "seller_name": settings.billing_seller_name, "seller_address": settings.billing_seller_address,
        "logo_url": settings.billing_logo_url or None, "tax_id": settings.billing_tax_id or None,
        "catalog": [] if exempt else await catalog(),
        "payment_methods": [{"id": card["id"], "brand": card["card"]["brand"],
                             "last4": card["card"]["last4"],
                             "exp_month": card["card"]["exp_month"],
                             "exp_year": card["card"]["exp_year"],
                             "is_default": card["id"] == default} for card in cards],
        "invoices": [await public_invoice(item) for item in invoices],
        "usage": {
            # Null means unavailable; it must not be displayed as zero usage.
            "devices": {"used": registered, "limit": None if exempt else device_limit(entitlements.plan_code)},
            "workspaces": {"used": entitlements.workspace_count,
                           "limit": entitlements.workspace_limit},
            "storage_bytes": {"used": None, "limit": None},
            "ai_requests": {"used": None, "limit": None},
        },
    }
    if result["access_status"] not in {"active", "trialing", "none"}:
        result["access_status"] = "restricted"
    await db.commit()
    return result


@router.post("/checkout")
async def checkout(payload: CheckoutInput, db: DB, user: CurrentUser):
    payer = await checkout_user(db, user, payload.workspace_id)
    if await is_billing_exempt(db, payer.id) or await is_billing_exempt(db, user.id):
        raise HTTPException(409, "This account has unlimited billing access. No plan payment or trial is required.")
    plans = await catalog()
    plan = next(p for p in plans if p['code'] == payload.plan_code)
    if plan['device_limit'] is None or plan['retention_days'] is None:
        raise HTTPException(409, 'Configure this plan device and retention limits first.')
    if not payload.with_trial and (not plan['checkout_enabled'] or plan[
        'monthly_amount_minor' if payload.interval == 'month' else 'yearly_amount_minor'
    ] is None):
        raise HTTPException(409, 'Configure the Stripe recurring Price ID for this plan and interval.')
    customer = await account(db, payer, create=True)
    current, history = await reconcile(db, customer)
    await reconcile_trial(db, customer, history)
    if current and current['status'] not in {'canceled', 'incomplete_expired'}:
        # Let permitted workspace managers pay the outstanding invoice, without
        # opening the owner's private customer portal or saved-card list.
        invoice_id = identifier(current.get('latest_invoice'))
        if current['status'] in {'past_due', 'unpaid', 'incomplete'} and invoice_id:
            invoice = await stripe('GET', '/invoices/' + quote(invoice_id, safe=''))
            if (identifier(invoice.get('customer')) == customer.provider_customer_id and
                    invoice.get('status') == 'open' and invoice.get('hosted_invoice_url')):
                await db.commit()
                return {'url': invoice['hosted_invoice_url']}
        raise HTTPException(409, 'An existing subscription needs review. Refresh billing or ask the billing owner to manage it.')
    if payload.with_trial and await trial_used(db, payer.id, history):
        raise HTTPException(409, 'This billing account has already used its trial.')
    sessions = await stripe_list('/checkout/sessions', customer=customer.provider_customer_id)
    for session in sessions:
        if session.get('mode') in {'subscription', 'setup'} and session.get('status') == 'open':
            await stripe('POST', '/checkout/sessions/' + quote(session['id'], safe='') + '/expire')
    current, history = await reconcile(db, customer)
    await reconcile_trial(db, customer, history)
    if current and current['status'] not in {'canceled', 'incomplete_expired'}:
        raise HTTPException(409, 'A subscription was created. Refresh billing.')
    if payload.with_trial and await trial_used(db, payer.id, history):
        raise HTTPException(409, 'This billing account is no longer trial eligible.')
    destination = return_url() if payload.workspace_id is None else settings.web_url.rstrip('/') + '/billing/workspace'
    fields = {
        'mode': 'setup' if payload.with_trial else 'subscription',
        'customer': customer.provider_customer_id,
        'payment_method_types[0]': 'card', 'billing_address_collection': 'required',
        'customer_update[name]': 'auto', 'customer_update[address]': 'auto',
        'client_reference_id': str(payer.id),
        'success_url': destination + '?checkout=returned',
        'cancel_url': destination + '?checkout=canceled',
    }
    if payload.with_trial:
        fields.update({
            'metadata[workforce_trial]': 'manual_v2',
            'metadata[workforce_user_id]': str(payer.id),
            'metadata[plan_code]': payload.plan_code,
            'custom_text[submit][message]': 'Save your card to start a 3-day trial. No subscription charge today. Access stops after the trial until you choose and pay for a plan. No automatic trial-end charge.',
        })
    else:
        fields.update({
            'line_items[0][price]': price_id(payload.plan_code, payload.interval),
            'line_items[0][quantity]': '1', 'payment_method_collection': 'always',
            'subscription_data[metadata][workforce_user_id]': str(payer.id),
        })
    session = await stripe('POST', '/checkout/sessions', fields,
                           key=f'workforce-checkout-{uuid.uuid4()}')
    await db.commit()
    return {'url': session['url']}


@router.post("/portal")
async def portal(db: DB, user: CurrentUser):
    if await is_billing_exempt(db, user.id):
        raise HTTPException(409, "This account has unlimited billing access. Manage any pre-existing subscription directly in Stripe.")
    customer = await account(db, user, create=True)
    session = await stripe("POST", "/billing_portal/sessions", {
        "customer": customer.provider_customer_id, "return_url": return_url(),
    })
    await db.commit()
    return {"url": session["url"]}


@router.post("/webhook")
async def webhook(request: Request, db: DB):
    if not settings.stripe_webhook_secret:
        raise HTTPException(503, "Webhook verification is not configured.")
    payload = bytearray()
    async for chunk in request.stream():
        payload.extend(chunk)
        if len(payload) > 1024 * 1024:
            raise HTTPException(413, "Webhook payload is too large.")
    try:
        event = verify_event(bytes(payload), request.headers.get("stripe-signature", ""),
                             settings.stripe_webhook_secret)
    except (ValueError, TypeError, UnicodeError) as exc:
        raise HTTPException(400, "Invalid Stripe webhook.") from exc
    if not event.get("type", "").startswith(("customer.subscription.", "invoice.", "checkout.session.")):
        return {"received": True}
    customer_id = identifier((event.get("data", {}).get("object") or {}).get("customer"))
    customer = await db.scalar(select(BillingCustomer).where(
        BillingCustomer.provider_customer_id == customer_id,
        BillingCustomer.provider == BillingProvider.STRIPE,
    )) if customer_id else None
    if customer is not None:
        await db.execute(select(User.id).where(User.id == customer.user_id).with_for_update())
        # Apply current provider state, never stale event snapshots.
        # Repeated deliveries perform the same state assignment; no charge is created here.
        _, history = await reconcile(db, customer)
        await reconcile_trial(db, customer, history)
        await db.commit()
    return {"received": True}


@router.get("/invoices/{invoice_id}/pdf")
async def invoice_pdf(
    invoice_id: Annotated[str, Path(pattern=r"^in_[A-Za-z0-9]+$", max_length=255)],
    db: DB, user: CurrentUser,
):
    customer = await BillingRepository().get_customer_for_user(db, user_id=user.id)
    if customer is None or not customer.provider_customer_id:
        raise HTTPException(404, "Invoice not found.")
    item = await stripe("GET", f"/invoices/{quote(invoice_id, safe='')}")
    if identifier(item.get("customer")) != customer.provider_customer_id:
        raise HTTPException(404, "Invoice not found.")
    url = item.get("invoice_pdf")
    if not url:
        raise HTTPException(409, "The invoice PDF is not available yet.")
    try:
        async with httpx.AsyncClient(timeout=25) as client:
            for _ in range(5):
                parsed = urlparse(url)
                if parsed.scheme != "https" or not (parsed.hostname or "").endswith(".stripe.com"):
                    raise HTTPException(502, "Invalid invoice download address.")
                remote = await client.get(url, follow_redirects=False)
                if remote.is_redirect:
                    url = str(remote.url.join(remote.headers["location"]))
                    continue
                if remote.status_code != 200 or not remote.content.startswith(b"%PDF-"):
                    raise HTTPException(502, "Unable to download the invoice PDF.")
                return Response(remote.content, media_type="application/pdf", headers={
                    "Content-Disposition": f'attachment; filename="{invoice_id}.pdf"',
                    "Cache-Control": "private, no-store",
                })
    except httpx.RequestError as exc:
        raise HTTPException(503, "Invoice download is temporarily unavailable.") from exc
    raise HTTPException(502, "Too many invoice download redirects.")


@router.get("/workspaces/{workspace_id}/status")
async def get_workspace_status(workspace_id: uuid.UUID, db: DB, user: CurrentUser):
    return await workspace_status(db, workspace_id, user.id)


@router.get('/workspaces/{workspace_id}/renewal')
async def workspace_renewal(workspace_id: uuid.UUID, db: DB, user: CurrentUser):
    payer = await checkout_user(db, user, workspace_id)
    state = await workspace_status(db, workspace_id, user.id)
    if state["billing_exempt"]:
        return {"workspace_id": workspace_id, "trial_eligible": False, "catalog": [], "status": state}
    customer = await account(db, payer)
    _, history = await reconcile(db, customer)
    await reconcile_trial(db, customer, history)
    await db.commit()
    return {'workspace_id': workspace_id, 'trial_eligible': not await trial_used(db, payer.id, history),
            'catalog': await catalog(), 'status': await workspace_status(db, workspace_id, user.id)}
