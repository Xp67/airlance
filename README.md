# airlance

A freelance starter pack.

## Firestore collections

The application relies on a few Firestore collections. The tables below
describe the expected fields and composite indexes configured for each
collection.

### `bookings`

| Field        | Type      | Description                               |
|--------------|-----------|-------------------------------------------|
| `tenant_id`  | string    | Tenant to which the booking belongs.      |
| `staff_id`   | string    | Staff member associated with the booking. |
| `resource_id`| string    | Resource reserved by the booking.         |
| `start_utc`  | timestamp | Start time in UTC.                        |
| `end_utc`    | timestamp | End time in UTC.                          |
| `status`     | string    | Current status of the booking.            |

Indexes:

- (`tenant_id`, `start_utc`)
- (`tenant_id`, `staff_id`, `start_utc`)
- (`tenant_id`, `resource_id`, `start_utc`)

### `holds`

| Field        | Type      | Description                          |
|--------------|-----------|--------------------------------------|
| `tenant_id`  | string    | Tenant to which the hold belongs.    |
| `expire_at`  | timestamp | When the hold automatically expires. |
| `slot`       | string    | Slot or resource being held.         |

Index:

- (`tenant_id`, `expire_at`)

### `slot_cache`

| Field       | Type   | Description                            |
|-------------|--------|----------------------------------------|
| `tenant_id` | string | Tenant to which the cache belongs.     |
| `key`       | string | Cache key.                             |
| `data`      | object | Cached payload.                        |

Index:

- (`tenant_id`, `key`)

