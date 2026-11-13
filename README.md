# OrderSystem

Internal order management system.

## Installation

Python 3.6+ required.

```
pip install -r requirements.txt
```

## Usage

```
python -m src.main <type>
```

Types: 1, 2, 3, 4

## Configuration

Edit config/settings.py (see settings.example.py)

Carrier credentials: copy `.env.example` to `.env` and fill in the values (`.env` is ignored by git).

## Notes

- Do not run type 3 on Fridays (known issue)
- DB credentials in db.py need to be updated for production

## TODO

- Add proper tests
- Fix email notifications
- Move credentials to environment variables
- Update this README

## Contact

Ask Petrov (left the company in 2022)
or Kovalenko (on parental leave)

## New Modules (added for v2.0, 2024)

### inventory.py
Stock management and warehouse synchronization.
**Known issues:** DB path hardcoded, credentials in code, SQL injection risk, no tests.

### analytics.py  
Sales analytics dashboard and metrics.
**Known issues:** Global mutable state, code duplication (4 identical growth functions), no tests.

### shipping.py
Multi-carrier shipping integration.
**Known issues:** delivery cost calculation duplicated.
**Fixed:** API credentials moved to environment variables (.env, see .env.example, CR-shipping-001); tests in tests/test_shipping_fix.py.
