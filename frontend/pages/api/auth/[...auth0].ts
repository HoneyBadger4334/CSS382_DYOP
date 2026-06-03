import { handleAuth, handleCallback, handleLogin } from "@auth0/nextjs-auth0";

const UW_EMAIL_DOMAINS = ["uw.edu", "washington.edu"];

const afterCallback = (req: any, res: any, session: any) => {
  const email: string | undefined = session.user?.email;
  if (!email || !UW_EMAIL_DOMAINS.some((domain) => email.toLowerCase().endsWith(`@${domain}`))) {
    res.status(403).end(
      "Only UW accounts are allowed. Please sign in with a @uw.edu or @washington.edu email."
    );
    return;
  }
  return session;
};

export default handleAuth({
  login: handleLogin({
    authorizationParams: {
      prompt: "login select_account",
    },
  }),

  async callback(req, res) {
    try {
      await handleCallback(req, res, { afterCallback });
    } catch (error: any) {
      console.error(error);
      res.status(error.status || 500).end(error.message || "Authentication failed.");
    }
  },
});
