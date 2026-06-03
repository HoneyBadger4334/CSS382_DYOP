# Auth0 Dashboard Changes Needed

## 1. Rename the application
- Auth0 Dashboard → **Applications** → your app → **Settings**
- Change **Name** from `My App` → `Campus Pulse`
- Save changes

---

## 2. Set tenant friendly name
- Auth0 Dashboard → **Settings** (top-level, not application settings)
- Change **Friendly Name** from blank/default → `Campus Pulse`
- Save changes
- This removes "dev-3qrvx8g0636dsdya" from the login page text

---

## 3. Disable username/password login
- Auth0 Dashboard → **Applications** → your app → **Connections** tab
- Turn **OFF** `Username-Password-Authentication`
- Leave **Google** enabled only
- This removes the email/password fields and Sign up link entirely

---

## 4. Restrict to UW emails only
- Auth0 Dashboard → **Actions** → **Flows** → **Login**
- Add a custom action that blocks non-UW emails — paste this code:
```javascript
exports.onExecutePostLogin = async (event, api) => {
  const email = event.user.email ?? "";
  if (!email.endsWith("@uw.edu") && !email.endsWith("@washington.edu")) {
    api.access.deny("Only UW email addresses are allowed.");
  }
};
```
- Deploy the action and drag it into the Login flow

---

## 5. Verify allowed URLs
- Auth0 Dashboard → **Applications** → your app → **Settings** → scroll to **Application URIs**
- Make sure these are all present:

| Field | Values |
|---|---|
| **Allowed Callback URLs** | `https://css382-dyop.vercel.app/api/auth/callback, http://localhost:3000/api/auth/callback` |
| **Allowed Logout URLs** | `https://css382-dyop.vercel.app, http://localhost:3000` |
| **Allowed Web Origins** | `https://css382-dyop.vercel.app, http://localhost:3000` |

---

## After all changes — test in incognito
- Login page should show only "Continue with Google" — no email/password fields
- Page should say "Log in to Campus Pulse to continue to Campus Pulse"
- A non-UW Google account should be blocked with the denial message
- A `@uw.edu` account should trigger Duo and land in the app
