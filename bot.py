
import os
import requests
from decimal import Decimal, InvalidOperation
from datetime import datetime
from zoneinfo import ZoneInfo

SERVIX_URL = "https://servix.cc/api/v1/assets"
EITAA_URL = "https://eitaayar.ir/api/bot{}/sendMessage"

ASSET_CODES = {
    "دلار آمریکا": "USD_RLS",
    "یورو": "EUR_RLS",
    "طلای ۱۸ عیار": "GOLD_18_RLS",
    "طلای ۲۴ عیار": "GOLD_24_RLS",
    "اونس طلا": "GOLD_OUNCE_USD",
    "سکه امامی": "SEKKEH_RLS",
    "نیم سکه": "NIM_SEKKEH_RLS",
    "ربع سکه": "ROB_SEKKEH_RLS",
    "سکه بهار آزادی": "BAHAR_RLS",
    "سکه گرمی": "GERAMI_SEKKEH_RLS",
    "اونس نقره": "SILVER_OUNCE_USD",
    "بیت‌کوین": "BTC_USD",
}

PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def persian_number(value):
    return f"{value:,}".translate(PERSIAN_DIGITS).replace(",", "٬")


def get_prices():
    api_key = os.environ["SERVIX_API_KEY"]
    response = requests.get(
        SERVIX_URL,
        headers={"X-API-Key": api_key},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()

    if not isinstance(payload, list):
        raise ValueError("پاسخ API قیمت‌ها قالب مورد انتظار را ندارد.")

    return {
        item.get("code"): item.get("value")
        for item in payload
        if isinstance(item, dict) and item.get("code")
    }


def format_price(raw_value, code):
    if raw_value is None:
        return "ناموجود"

    try:
        value = Decimal(str(raw_value))
    except (InvalidOperation, ValueError):
        return "ناموجود"

    if not value.is_finite():
        return "ناموجود"

    # قیمت‌های ریالی به تومان تبدیل می‌شوند.
    if code.endswith("_RLS"):
        value /= Decimal("10")

    return persian_number(int(value))


def make_report(prices):
    now = datetime.now(ZoneInfo("Asia/Tehran"))
    lines = [
        "📊 بازارنما | گزارش قیمت بازار",
        now.strftime("%Y-%m-%d  %H:%M"),
        "━━━━━━━━━━━━━━━━━━",
    ]

    for name, code in ASSET_CODES.items():
        lines.append(f"{name}: {format_price(prices.get(code), code)}")

    lines.extend([
        "━━━━━━━━━━━━━━━━━━",
        "منبع داده: Servix",
    ])

    return "\n".join(lines)


def send_to_eitaa(message):
    token = os.environ["EITAAYAR_TOKEN"]
    chat_id = os.environ["EITAAYAR_CHAT_ID"]

    url = EITAA_URL.format(token)
    response = requests.post(
        url,
        data={"chat_id": chat_id, "text": message},
        timeout=30,
    )
    response.raise_for_status()

    result = response.json()
    if not result.get("ok"):
        raise RuntimeError(f"ارسال ایتا ناموفق بود: {result}")

    print("گزارش با موفقیت به ایتا ارسال شد.")


def main():
    print("دریافت قیمت‌ها از Servix...")
    prices = get_prices()

    missing = [
        code for code in ASSET_CODES.values()
        if prices.get(code) is None
    ]
    if missing:
        raise ValueError(
            "قیمت برخی دارایی‌ها موجود نیست: " + ", ".join(missing)
        )

    report = make_report(prices)
    print(report)
    send_to_eitaa(report)


if __name__ == "__main__":
    main()
