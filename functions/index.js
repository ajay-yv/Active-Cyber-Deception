const { initializeApp } = require("firebase-admin/app");
const { getAuth } = require("firebase-admin/auth");
const { defineSecret } = require("firebase-functions/params");
const { onRequest } = require("firebase-functions/v2/https");

initializeApp();

const resendApiKey = defineSecret("RESEND_API_KEY");
const resendFromAddress = defineSecret("RESEND_FROM_ADDRESS");

exports.emailVerification = onRequest(
  {
    region: "us-central1",
    cors: true,
    secrets: [resendApiKey, resendFromAddress],
  },
  async (request, response) => {
    response.set("Cache-Control", "no-store");
    response.set("X-Content-Type-Options", "nosniff");

    if (request.method !== "POST") {
      response.set("Allow", "POST");
      response.status(405).json({ error: "Use POST to request email verification." });
      return;
    }

    const authorization = request.get("authorization") || "";
    const match = authorization.match(/^Bearer\s+(.+)$/i);
    if (!match) {
      response.status(401).json({ error: "Sign in with Firebase before requesting email verification." });
      return;
    }

    try {
      const decoded = await getAuth().verifyIdToken(match[1], true);
      const user = await getAuth().getUser(decoded.uid);
      if (!user.email) {
        response.status(400).json({ error: "This Firebase account does not have an email address." });
        return;
      }
      if (user.emailVerified) {
        response.status(409).json({ error: "This email address is already verified." });
        return;
      }

      const apiKey = resendApiKey.value().trim();
      const fromAddress = resendFromAddress.value().trim();
      if (!apiKey || !fromAddress) {
        response.status(503).json({ error: "Firebase email verification delivery is not configured." });
        return;
      }

      const verificationLink = await getAuth().generateEmailVerificationLink(user.email);
      const emailResponse = await fetch("https://api.resend.com/emails", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${apiKey}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          from: fromAddress,
          to: [user.email],
          subject: "Verify your EHR email address",
          text: `Confirm your email address by opening this link:\n\n${verificationLink}\n\nIf you did not request this, ignore this email.`,
          html: `<p>Confirm your email address by clicking the button below:</p><p><a href="${verificationLink}">Verify email address</a></p><p>If you did not request this, you can ignore this email.</p>`,
        }),
        signal: AbortSignal.timeout(10000),
      });

      if (!emailResponse.ok) {
        console.error("Resend rejected verification email (HTTP %s)", emailResponse.status);
        response.status(503).json({ error: "The email provider did not accept the verification email. Check the sender and provider settings." });
        return;
      }

      response.status(200).json({
        message: `A verification link was sent to ${user.email}. Firebase will verify it when the link is opened.`,
      });
    } catch (error) {
      console.error("Firebase email verification request failed (%s)", error.name || "Error");
      response.status(503).json({ error: "Could not send an email verification link. Check Firebase Auth and email-provider configuration." });
    }
  },
);
